"""
Comprehensive unit tests for OAuth flows and token management.
Tests OAuth authorization, token exchange, refresh, and management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from moto import mock_aws
import boto3

# Test imports
from src.services.google_oauth import GoogleOAuthService, GOOGLE_SCOPES
from src.services.microsoft_oauth import MicrosoftOAuthService
from src.services.oauth_manager import OAuthManager
from src.services.token_refresh_service import TokenRefreshService
from src.utils.token_errors import TokenError, TokenExpiredError, TokenRefreshError


class TestGoogleOAuthFlows:
    """Comprehensive tests for Google OAuth flows."""
    
    @pytest.fixture
    def mock_aws_services(self):
        """Set up mocked AWS services."""
        with mock_aws():
            # Create DynamoDB table
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.create_table(
                TableName='Connections',
                KeySchema=[{'AttributeName': 'pk', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'pk', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create Secrets Manager secret
            secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
            secrets_client.create_secret(
                Name='google-oauth-credentials',
                SecretString=json.dumps({
                    'client_id': 'test-client-id',
                    'client_secret': 'test-client-secret'
                })
            )
            
            # Create KMS key
            kms_client = boto3.client('kms', region_name='us-east-1')
            key_response = kms_client.create_key(Description='Test key for OAuth tokens')
            
            yield {
                'table': table,
                'secrets_client': secrets_client,
                'kms_client': kms_client,
                'key_id': key_response['KeyMetadata']['KeyId']
            }
    
    @pytest.fixture
    def oauth_service(self, mock_aws_services):
        """Create GoogleOAuthService instance with mocked AWS services."""
        with patch.dict('os.environ', {
            'CONNECTIONS_TABLE': 'Connections',
            'GOOGLE_OAUTH_SECRET': 'google-oauth-credentials',
            'KMS_KEY_ID': mock_aws_services['key_id']
        }):
            return GoogleOAuthService()
    
    def test_generate_authorization_url_with_pkce(self, oauth_service):
        """Test authorization URL generation with PKCE parameters."""
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        
        # Verify response structure
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        
        # Verify URL parameters
        auth_url = result['authorization_url']
        assert 'client_id=test-client-id' in auth_url
        assert 'code_challenge=' in auth_url
        assert 'code_challenge_method=S256' in auth_url
        assert 'scope=' in auth_url
        
        # Verify state is UUID format
        import uuid
        try:
            uuid.UUID(result['state'])
        except ValueError:
            pytest.fail("State should be a valid UUID")
        
        # Verify expiration is in the future
        expires_at = datetime.fromisoformat(result['expires_at'])
        assert expires_at > datetime.utcnow()
    
    @patch('src.services.google_oauth.requests.post')
    @patch('src.services.google_oauth.requests.get')
    def test_token_exchange_success_flow(self, mock_get, mock_post, oauth_service):
        """Test complete successful token exchange flow."""
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        # Step 1: Generate authorization URL
        auth_result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        state = auth_result['state']
        
        # Step 2: Mock token exchange response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'expires_in': 3600,
            'scope': ' '.join(GOOGLE_SCOPES)
        }
        
        # Step 3: Mock user profile response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 'google-user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg'
        }
        
        # Step 4: Exchange code for tokens
        result = oauth_service.exchange_code_for_tokens(
            user_id=user_id,
            authorization_code='test-auth-code',
            state=state
        )
        
        # Verify result
        assert result['connection_id'] == f"{user_id}#google"
        assert result['provider'] == 'google'
        assert result['profile']['email'] == 'test@example.com'
        assert result['scopes'] == GOOGLE_SCOPES
        
        # Verify token exchange request
        mock_post.assert_called_once()
        token_request = mock_post.call_args
        assert 'grant_type=authorization_code' in str(token_request)
        assert 'code=test-auth-code' in str(token_request)
    
    def test_token_exchange_invalid_state(self, oauth_service):
        """Test token exchange with invalid state parameter."""
        user_id = 'test-user-123'
        
        with pytest.raises(Exception, match="Invalid or expired authorization state"):
            oauth_service.exchange_code_for_tokens(
                user_id=user_id,
                authorization_code='test-auth-code',
                state='invalid-state-12345'
            )
    
    def test_token_exchange_expired_state(self, oauth_service):
        """Test token exchange with expired state."""
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        # Generate auth URL
        auth_result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        state = auth_result['state']
        
        # Manually expire the PKCE data
        table = oauth_service.dynamodb.Table('Connections')
        expired_time = datetime.utcnow() - timedelta(minutes=30)
        table.update_item(
            Key={'pk': f"pkce#{user_id}#{state}"},
            UpdateExpression="SET expires_at = :exp",
            ExpressionAttributeValues={':exp': expired_time.isoformat()}
        )
        
        with pytest.raises(Exception, match="Invalid or expired authorization state"):
            oauth_service.exchange_code_for_tokens(
                user_id=user_id,
                authorization_code='test-auth-code',
                state=state
            )
    
    @patch('src.services.google_oauth.requests.post')
    def test_token_refresh_success(self, mock_post, oauth_service):
        """Test successful token refresh flow."""
        user_id = 'test-user-123'
        
        # Create existing connection with expired token
        table = oauth_service.dynamodb.Table('Connections')
        with patch('src.services.google_oauth.encrypt_token') as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
            
            table.put_item(Item={
                'pk': f"{user_id}#google",
                'user_id': user_id,
                'provider': 'google',
                'access_token_encrypted': 'encrypted_old_access_token',
                'refresh_token_encrypted': 'encrypted_refresh_token',
                'expires_at': (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
                'status': 'active',
                'scopes': GOOGLE_SCOPES
            })
        
        # Mock token refresh response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'new-access-token',
            'expires_in': 3600
        }
        
        with patch('src.services.google_oauth.decrypt_token') as mock_decrypt, \
             patch('src.services.google_oauth.encrypt_token') as mock_encrypt:
            mock_decrypt.return_value = 'refresh_token'
            mock_encrypt.return_value = 'encrypted_new_access_token'
            
            result = oauth_service.refresh_access_token(user_id)
            
            assert result['connection_id'] == f"{user_id}#google"
            assert result['status'] == 'active'
            assert 'expires_at' in result
            assert 'last_refresh' in result
            
            # Verify refresh request
            mock_post.assert_called_once()
            refresh_request = mock_post.call_args
            assert 'grant_type=refresh_token' in str(refresh_request)
    
    @patch('src.services.google_oauth.requests.post')
    def test_token_refresh_failure(self, mock_post, oauth_service):
        """Test token refresh failure handling."""
        user_id = 'test-user-123'
        
        # Create existing connection
        table = oauth_service.dynamodb.Table('Connections')
        with patch('src.services.google_oauth.encrypt_token') as mock_encrypt:
            mock_encrypt.return_value = 'encrypted_refresh_token'
            
            table.put_item(Item={
                'pk': f"{user_id}#google",
                'user_id': user_id,
                'provider': 'google',
                'refresh_token_encrypted': 'encrypted_refresh_token',
                'status': 'active'
            })
        
        # Mock failed refresh response
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Token has been expired or revoked.'
        }
        
        with patch('src.services.google_oauth.decrypt_token') as mock_decrypt:
            mock_decrypt.return_value = 'refresh_token'
            
            with pytest.raises(TokenRefreshError):
                oauth_service.refresh_access_token(user_id)
    
    def test_pkce_code_generation(self, oauth_service):
        """Test PKCE code verifier and challenge generation."""
        code_verifier, code_challenge = oauth_service._generate_pkce_pair()
        
        # Verify code verifier format
        assert len(code_verifier) >= 43
        assert len(code_verifier) <= 128
        
        # Verify code challenge format
        assert len(code_challenge) >= 43
        assert code_verifier != code_challenge
        
        # Verify challenge is properly generated from verifier
        import hashlib
        import base64
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        assert code_challenge == expected_challenge
    
    def test_scope_validation(self, oauth_service):
        """Test OAuth scope validation."""
        # Valid scopes
        valid_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        assert oauth_service._validate_scopes(valid_scopes) is True
        
        # Invalid scopes
        invalid_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/invalid.scope'
        ]
        assert oauth_service._validate_scopes(invalid_scopes) is False
        
        # Empty scopes
        assert oauth_service._validate_scopes([]) is False


class TestMicrosoftOAuthFlows:
    """Comprehensive tests for Microsoft OAuth flows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch.dict('os.environ', {
            'CONNECTIONS_TABLE': 'Connections',
            'MICROSOFT_OAUTH_SECRET': 'microsoft-oauth-credentials',
            'KMS_KEY_ID': 'test-key-id'
        }):
            self.oauth_service = MicrosoftOAuthService()
    
    @patch('src.services.microsoft_oauth.msal.ConfidentialClientApplication')
    def test_generate_authorization_url(self, mock_msal):
        """Test Microsoft authorization URL generation."""
        # Mock MSAL client
        mock_client = Mock()
        mock_msal.return_value = mock_client
        mock_client.get_authorization_request_url.return_value = 'https://login.microsoftonline.com/oauth2/authorize?...'
        
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        result = self.oauth_service.generate_authorization_url(user_id, redirect_uri)
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        
        # Verify MSAL was called correctly
        mock_client.get_authorization_request_url.assert_called_once()
    
    @patch('src.services.microsoft_oauth.msal.ConfidentialClientApplication')
    def test_token_exchange_success(self, mock_msal):
        """Test successful Microsoft token exchange."""
        # Mock MSAL client
        mock_client = Mock()
        mock_msal.return_value = mock_client
        mock_client.acquire_token_by_authorization_code.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'expires_in': 3600,
            'scope': ['https://graph.microsoft.com/calendars.readwrite']
        }
        
        user_id = 'test-user-123'
        
        # First generate auth URL to create state
        with patch.object(self.oauth_service, '_store_oauth_state') as mock_store:
            mock_store.return_value = 'test-state'
            auth_result = self.oauth_service.generate_authorization_url(user_id, 'https://example.com/callback')
            state = auth_result['state']
        
        # Mock profile fetch
        with patch('src.services.microsoft_oauth.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'id': 'ms-user-123',
                'mail': 'test@example.com',
                'displayName': 'Test User'
            }
            
            result = self.oauth_service.exchange_code_for_tokens(
                user_id=user_id,
                authorization_code='test-auth-code',
                state=state
            )
        
        assert result['provider'] == 'microsoft'
        assert result['profile']['email'] == 'test@example.com'


class TestTokenRefreshService:
    """Comprehensive tests for token refresh service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = TokenRefreshService()
        self.user_id = "test_user_123"
    
    @patch('src.services.token_refresh_service.GoogleOAuthService')
    @patch('src.services.token_refresh_service.MicrosoftOAuthService')
    def test_refresh_all_tokens_success(self, mock_ms_oauth, mock_google_oauth):
        """Test successful refresh of all user tokens."""
        # Mock Google OAuth service
        mock_google_instance = Mock()
        mock_google_oauth.return_value = mock_google_instance
        mock_google_instance.refresh_access_token.return_value = {
            'connection_id': f'{self.user_id}#google',
            'status': 'active',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        # Mock Microsoft OAuth service
        mock_ms_instance = Mock()
        mock_ms_oauth.return_value = mock_ms_instance
        mock_ms_instance.refresh_access_token.return_value = {
            'connection_id': f'{self.user_id}#microsoft',
            'status': 'active',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        # Mock connections
        connections = [
            {'provider': 'google', 'status': 'active'},
            {'provider': 'microsoft', 'status': 'active'}
        ]
        
        with patch.object(self.service, '_get_user_connections') as mock_get_connections:
            mock_get_connections.return_value = connections
            
            result = self.service.refresh_all_tokens(self.user_id)
            
            assert result['user_id'] == self.user_id
            assert result['total_connections'] == 2
            assert result['successful_refreshes'] == 2
            assert result['failed_refreshes'] == 0
    
    def test_is_token_expired(self):
        """Test token expiration checking."""
        # Expired token
        expired_time = datetime.utcnow() - timedelta(minutes=5)
        assert self.service._is_token_expired(expired_time.isoformat()) is True
        
        # Valid token
        valid_time = datetime.utcnow() + timedelta(hours=1)
        assert self.service._is_token_expired(valid_time.isoformat()) is False
        
        # Token expiring soon (within buffer)
        soon_time = datetime.utcnow() + timedelta(minutes=2)
        assert self.service._is_token_expired(soon_time.isoformat(), buffer_minutes=5) is True
    
    def test_handle_refresh_failure(self):
        """Test handling of token refresh failures."""
        error = TokenRefreshError("Refresh token expired")
        
        result = self.service._handle_refresh_failure(self.user_id, 'google', error)
        
        assert result['connection_id'] == f'{self.user_id}#google'
        assert result['status'] == 'refresh_failed'
        assert 'error' in result
        assert result['requires_reauth'] is True


class TestOAuthManager:
    """Comprehensive tests for OAuth manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = OAuthManager()
        self.user_id = "test_user_123"
    
    @patch('src.services.oauth_manager.GoogleOAuthService')
    @patch('src.services.oauth_manager.MicrosoftOAuthService')
    def test_get_authorization_url_google(self, mock_ms_oauth, mock_google_oauth):
        """Test getting authorization URL for Google."""
        mock_google_instance = Mock()
        mock_google_oauth.return_value = mock_google_instance
        mock_google_instance.generate_authorization_url.return_value = {
            'authorization_url': 'https://accounts.google.com/oauth2/auth?...',
            'state': 'test-state',
            'expires_at': datetime.utcnow().isoformat()
        }
        
        result = self.manager.get_authorization_url(
            provider='google',
            user_id=self.user_id,
            redirect_uri='https://example.com/callback'
        )
        
        assert 'authorization_url' in result
        assert result['provider'] == 'google'
        mock_google_instance.generate_authorization_url.assert_called_once()
    
    def test_get_authorization_url_invalid_provider(self):
        """Test getting authorization URL for invalid provider."""
        with pytest.raises(ValueError, match="Unsupported OAuth provider"):
            self.manager.get_authorization_url(
                provider='invalid',
                user_id=self.user_id,
                redirect_uri='https://example.com/callback'
            )
    
    @patch('src.services.oauth_manager.GoogleOAuthService')
    def test_exchange_code_for_tokens(self, mock_google_oauth):
        """Test token exchange through manager."""
        mock_google_instance = Mock()
        mock_google_oauth.return_value = mock_google_instance
        mock_google_instance.exchange_code_for_tokens.return_value = {
            'connection_id': f'{self.user_id}#google',
            'provider': 'google',
            'status': 'active'
        }
        
        result = self.manager.exchange_code_for_tokens(
            provider='google',
            user_id=self.user_id,
            authorization_code='test-code',
            state='test-state'
        )
        
        assert result['provider'] == 'google'
        mock_google_instance.exchange_code_for_tokens.assert_called_once()
    
    def test_validate_provider(self):
        """Test provider validation."""
        # Valid providers
        assert self.manager._validate_provider('google') is True
        assert self.manager._validate_provider('microsoft') is True
        
        # Invalid provider
        assert self.manager._validate_provider('invalid') is False


if __name__ == '__main__':
    pytest.main([__file__])