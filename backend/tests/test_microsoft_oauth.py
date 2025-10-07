"""
Tests for Microsoft OAuth service functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.services.microsoft_oauth import MicrosoftOAuthService, MICROSOFT_SCOPES


class TestMicrosoftOAuthService:
    """Test cases for Microsoft OAuth service."""
    
    @pytest.fixture
    def mock_dynamodb(self):
        """Mock DynamoDB resource."""
        with patch('src.services.microsoft_oauth.get_dynamodb_resource') as mock:
            mock_table = Mock()
            mock_resource = Mock()
            mock_resource.Table.return_value = mock_table
            mock.return_value = mock_resource
            yield mock_table
    
    @pytest.fixture
    def mock_secrets(self):
        """Mock Secrets Manager client."""
        with patch('src.services.microsoft_oauth.get_secrets_client') as mock:
            mock_client = Mock()
            mock_client.get_secret_value.return_value = {
                'SecretString': json.dumps({
                    'client_id': 'test-client-id',
                    'client_secret': 'test-client-secret',
                    'tenant_id': 'common'
                })
            }
            mock.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def oauth_service(self, mock_dynamodb, mock_secrets):
        """Create MicrosoftOAuthService instance with mocked dependencies."""
        return MicrosoftOAuthService()
    
    def test_generate_authorization_url(self, oauth_service, mock_dynamodb):
        """Test authorization URL generation."""
        user_id = "test-user-123"
        redirect_uri = "https://example.com/callback"
        
        # Mock DynamoDB put_item
        mock_dynamodb.put_item.return_value = {}
        
        result = oauth_service.generate_authorization_url(user_id, redirect_uri)
        
        assert 'authorization_url' in result
        assert 'state' in result
        assert 'expires_at' in result
        assert 'login.microsoftonline.com' in result['authorization_url']
        assert 'client_id=test-client-id' in result['authorization_url']
        assert 'code_challenge=' in result['authorization_url']
        assert 'code_challenge_method=S256' in result['authorization_url']
        
        # Verify PKCE data was stored
        mock_dynamodb.put_item.assert_called_once()
        call_args = mock_dynamodb.put_item.call_args[1]['Item']
        assert call_args['pk'].startswith(f'pkce#{user_id}#')
        assert 'pkce_data' in call_args
    
    @patch('src.services.microsoft_oauth.requests.post')
    @patch('src.services.microsoft_oauth.requests.get')
    def test_exchange_code_for_tokens(self, mock_get, mock_post, oauth_service, mock_dynamodb):
        """Test authorization code exchange for tokens."""
        user_id = "test-user-123"
        auth_code = "test-auth-code"
        state = "test-state"
        
        # Mock PKCE data retrieval
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'pkce_data': {
                    'code_verifier': 'test-verifier',
                    'redirect_uri': 'https://example.com/callback',
                    'state': state,
                    'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat()
                }
            }
        }
        
        # Mock token exchange response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'expires_in': 3600,
            'scope': ' '.join(MICROSOFT_SCOPES)
        }
        
        # Mock profile fetch response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': 'test-microsoft-id',
            'displayName': 'Test User',
            'mail': 'test@example.com',
            'jobTitle': 'Developer'
        }
        
        # Mock DynamoDB operations
        mock_dynamodb.put_item.return_value = {}
        mock_dynamodb.delete_item.return_value = {}
        
        with patch('src.services.microsoft_oauth.encrypt_token') as mock_encrypt:
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
            
            result = oauth_service.exchange_code_for_tokens(user_id, auth_code, state)
        
        assert result['connection_id'] == f"{user_id}#microsoft"
        assert result['provider'] == 'microsoft'
        assert 'profile' in result
        assert result['profile']['email'] == 'test@example.com'
        assert result['profile']['name'] == 'Test User'
        
        # Verify token storage
        mock_dynamodb.put_item.assert_called()
        stored_data = mock_dynamodb.put_item.call_args[1]['Item']
        assert stored_data['pk'] == f"{user_id}#microsoft"
        assert stored_data['provider'] == 'microsoft'
        assert stored_data['access_token_encrypted'] == 'encrypted_test-access-token'
        assert stored_data['refresh_token_encrypted'] == 'encrypted_test-refresh-token'
        
        # Verify PKCE cleanup
        mock_dynamodb.delete_item.assert_called_with(
            Key={'pk': f"pkce#{user_id}#{state}"}
        )
    
    @patch('src.services.microsoft_oauth.requests.post')
    def test_refresh_access_token(self, mock_post, oauth_service, mock_dynamodb):
        """Test access token refresh."""
        user_id = "test-user-123"
        
        # Mock connection retrieval
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'pk': f"{user_id}#microsoft",
                'refresh_token_encrypted': 'encrypted_refresh_token',
                'status': 'active'
            }
        }
        
        # Mock token refresh response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'access_token': 'new-access-token',
            'expires_in': 3600
        }
        
        # Mock DynamoDB update
        mock_dynamodb.update_item.return_value = {}
        
        with patch('src.services.microsoft_oauth.decrypt_token') as mock_decrypt, \
             patch('src.services.microsoft_oauth.encrypt_token') as mock_encrypt:
            mock_decrypt.return_value = 'decrypted_refresh_token'
            mock_encrypt.return_value = 'encrypted_new-access-token'
            
            result = oauth_service.refresh_access_token(user_id)
        
        assert result['connection_id'] == f"{user_id}#microsoft"
        assert result['status'] == 'active'
        assert 'expires_at' in result
        assert 'last_refresh' in result
        
        # Verify token update
        mock_dynamodb.update_item.assert_called_once()
    
    def test_get_valid_access_token(self, oauth_service, mock_dynamodb):
        """Test getting valid access token."""
        user_id = "test-user-123"
        
        # Mock connection with valid token
        future_time = datetime.utcnow() + timedelta(hours=1)
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'pk': f"{user_id}#microsoft",
                'access_token_encrypted': 'encrypted_token',
                'expires_at': future_time.isoformat(),
                'status': 'active'
            }
        }
        
        with patch('src.services.microsoft_oauth.decrypt_token') as mock_decrypt:
            mock_decrypt.return_value = 'decrypted_access_token'
            
            token = oauth_service.get_valid_access_token(user_id)
        
        assert token == 'decrypted_access_token'
        mock_decrypt.assert_called_once_with('encrypted_token')
    
    def test_get_connection_status_connected(self, oauth_service, mock_dynamodb):
        """Test connection status for connected account."""
        user_id = "test-user-123"
        
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'pk': f"{user_id}#microsoft",
                'status': 'active',
                'profile': {'email': 'test@example.com'},
                'scopes': MICROSOFT_SCOPES,
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        status = oauth_service.get_connection_status(user_id)
        
        assert status['connected'] is True
        assert status['provider'] == 'microsoft'
        assert status['status'] == 'active'
        assert status['is_expired'] is False
        assert 'profile' in status
    
    def test_get_connection_status_not_connected(self, oauth_service, mock_dynamodb):
        """Test connection status for non-connected account."""
        user_id = "test-user-123"
        
        mock_dynamodb.get_item.return_value = {}
        
        status = oauth_service.get_connection_status(user_id)
        
        assert status['connected'] is False
        assert status['provider'] == 'microsoft'
        assert status['status'] == 'not_connected'
    
    def test_disconnect(self, oauth_service, mock_dynamodb):
        """Test account disconnection."""
        user_id = "test-user-123"
        
        # Mock connection exists
        mock_dynamodb.get_item.return_value = {
            'Item': {
                'pk': f"{user_id}#microsoft",
                'access_token_encrypted': 'encrypted_token'
            }
        }
        
        # Mock DynamoDB delete
        mock_dynamodb.delete_item.return_value = {}
        
        with patch('src.services.microsoft_oauth.decrypt_token') as mock_decrypt, \
             patch('src.services.microsoft_oauth.requests.get') as mock_get:
            mock_decrypt.return_value = 'decrypted_token'
            mock_get.return_value.status_code = 200
            
            success = oauth_service.disconnect(user_id)
        
        assert success is True
        mock_dynamodb.delete_item.assert_called_with(
            Key={'pk': f"{user_id}#microsoft"}
        )
    
    def test_validate_scopes(self, oauth_service):
        """Test scope validation."""
        # Valid scopes
        assert oauth_service._validate_scopes(MICROSOFT_SCOPES) is True
        
        # Invalid scope
        invalid_scopes = MICROSOFT_SCOPES + ['invalid.scope']
        assert oauth_service._validate_scopes(invalid_scopes) is False
    
    def test_generate_pkce_pair(self, oauth_service):
        """Test PKCE code verifier and challenge generation."""
        verifier, challenge = oauth_service._generate_pkce_pair()
        
        assert len(verifier) >= 43
        assert len(challenge) >= 43
        assert verifier != challenge
        # Verify base64url encoding (no padding)
        assert '=' not in verifier
        assert '=' not in challenge