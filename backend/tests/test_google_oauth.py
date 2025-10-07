"""
Tests for Google OAuth service implementation.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from moto import mock_dynamodb, mock_secretsmanager, mock_kms
import boto3

from src.services.google_oauth import GoogleOAuthService, GOOGLE_SCOPES


@pytest.fixture
def mock_aws_services():
    """Set up mocked AWS services."""
    with mock_dynamodb(), mock_secretsmanager(), mock_kms():
        # Create DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='Connections',
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'}
            ],
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
        key_response = kms_client.create_key(
            Description='Test key for OAuth tokens'
        )
        
        yield {
            'table': table,
            'secrets_client': secrets_client,
            'kms_client': kms_client,
            'key_id': key_response['KeyMetadata']['KeyId']
        }


@pytest.fixture
def oauth_service(mock_aws_services):
    """Create GoogleOAuthService instance with mocked AWS services."""
    with patch.dict('os.environ', {
        'CONNECTIONS_TABLE': 'Connections',
        'GOOGLE_OAUTH_SECRET': 'google-oauth-credentials',
        'KMS_KEY_ID': mock_aws_services['key_id']
    }):
        return GoogleOAuthService()


class TestGoogleOAuthService:
    """Test cases for GoogleOAuthService."""
    
    def test_generate_authorization_url(self, oauth_service):
        """Test authorization URL generation with PKCE."""
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        
        # Verify URL contains required parameters
        auth_url = result['authorization_url']
        assert 'client_id=test-client-id' in auth_url
        assert 'redirect_uri=' + redirect_uri.replace(':', '%3A').replace('/', '%2F') in auth_url
        assert 'code_challenge=' in auth_url
        assert 'code_challenge_method=S256' in auth_url
        assert 'scope=' in auth_url
        
        # Verify PKCE data is stored
        table = oauth_service.dynamodb.Table('Connections')
        pkce_response = table.get_item(
            Key={'pk': f"pkce#{user_id}#{result['state']}"}
        )
        assert 'Item' in pkce_response
        assert 'pkce_data' in pkce_response['Item']
    
    @patch('src.services.google_oauth.requests.post')
    @patch('src.services.google_oauth.requests.get')
    def test_exchange_code_for_tokens_success(self, mock_get, mock_post, oauth_service):
        """Test successful token exchange."""
        user_id = 'test-user-123'
        redirect_uri = 'https://example.com/callback'
        
        # First generate auth URL to create PKCE data
        auth_result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        state = auth_result['state']
        
        # Mock token exchange response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'expires_in': 3600,
            'scope': ' '.join(GOOGLE_SCOPES)
        }
        
        # Mock profile response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 'google-user-123',
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg'
        }
        
        result = oauth_service.exchange_code_for_tokens(
            user_id=user_id,
            authorization_code='test-auth-code',
            state=state
        )
        
        assert result['connection_id'] == f"{user_id}#google"
        assert result['provider'] == 'google'
        assert result['profile']['email'] == 'test@example.com'
        assert result['scopes'] == GOOGLE_SCOPES
        
        # Verify connection is stored
        table = oauth_service.dynamodb.Table('Connections')
        connection_response = table.get_item(
            Key={'pk': f"{user_id}#google"}
        )
        assert 'Item' in connection_response
        connection = connection_response['Item']
        assert connection['provider'] == 'google'
        assert connection['status'] == 'active'
        assert 'access_token_encrypted' in connection
        assert 'refresh_token_encrypted' in connection
    
    def test_exchange_code_invalid_state(self, oauth_service):
        """Test token exchange with invalid state."""
        user_id = 'test-user-123'
        
        with pytest.raises(Exception, match="Invalid or expired authorization state"):
            oauth_service.exchange_code_for_tokens(
                user_id=user_id,
                authorization_code='test-auth-code',
                state='invalid-state'
            )
    
    @patch('src.services.google_oauth.requests.post')
    def test_refresh_access_token_success(self, mock_post, oauth_service):
        """Test successful token refresh."""
        user_id = 'test-user-123'
        
        # Create existing connection
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
                'status': 'active'
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
    
    def test_get_connection_status_connected(self, oauth_service):
        """Test connection status for connected account."""
        user_id = 'test-user-123'
        
        # Create connection
        table = oauth_service.dynamodb.Table('Connections')
        table.put_item(Item={
            'pk': f"{user_id}#google",
            'user_id': user_id,
            'provider': 'google',
            'status': 'active',
            'profile': {
                'email': 'test@example.com',
                'name': 'Test User'
            },
            'scopes': GOOGLE_SCOPES,
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'created_at': datetime.utcnow().isoformat()
        })
        
        result = oauth_service.get_connection_status(user_id)
        
        assert result['connected'] is True
        assert result['provider'] == 'google'
        assert result['status'] == 'active'
        assert result['profile']['email'] == 'test@example.com'
        assert result['is_expired'] is False
    
    def test_get_connection_status_not_connected(self, oauth_service):
        """Test connection status for non-connected account."""
        user_id = 'test-user-123'
        
        result = oauth_service.get_connection_status(user_id)
        
        assert result['connected'] is False
        assert result['provider'] == 'google'
        assert result['status'] == 'not_connected'
    
    @patch('src.services.google_oauth.requests.post')
    def test_disconnect_success(self, mock_post, oauth_service):
        """Test successful account disconnection."""
        user_id = 'test-user-123'
        
        # Create connection
        table = oauth_service.dynamodb.Table('Connections')
        with patch('src.services.google_oauth.encrypt_token') as mock_encrypt:
            mock_encrypt.return_value = 'encrypted_access_token'
            
            table.put_item(Item={
                'pk': f"{user_id}#google",
                'user_id': user_id,
                'provider': 'google',
                'access_token_encrypted': 'encrypted_access_token',
                'status': 'active'
            })
        
        # Mock token revocation
        mock_post.return_value.status_code = 200
        
        with patch('src.services.google_oauth.decrypt_token') as mock_decrypt:
            mock_decrypt.return_value = 'access_token'
            
            result = oauth_service.disconnect(user_id)
            
            assert result is True
            
            # Verify connection is deleted
            connection_response = table.get_item(
                Key={'pk': f"{user_id}#google"}
            )
            assert 'Item' not in connection_response
    
    def test_validate_scopes_valid(self, oauth_service):
        """Test scope validation with valid scopes."""
        valid_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        
        result = oauth_service._validate_scopes(valid_scopes)
        assert result is True
    
    def test_validate_scopes_invalid(self, oauth_service):
        """Test scope validation with invalid scopes."""
        invalid_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/invalid.scope'
        ]
        
        result = oauth_service._validate_scopes(invalid_scopes)
        assert result is False
    
    def test_generate_pkce_pair(self, oauth_service):
        """Test PKCE code verifier and challenge generation."""
        code_verifier, code_challenge = oauth_service._generate_pkce_pair()
        
        assert len(code_verifier) >= 43
        assert len(code_challenge) >= 43
        assert code_verifier != code_challenge
        
        # Verify code challenge is properly generated from verifier
        import hashlib
        import base64
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        assert code_challenge == expected_challenge