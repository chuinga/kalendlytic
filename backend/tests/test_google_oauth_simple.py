"""
Simple tests for Google OAuth service implementation.
"""

import pytest
from unittest.mock import Mock, patch
from src.services.google_oauth import GoogleOAuthService, GOOGLE_SCOPES


class TestGoogleOAuthServiceBasic:
    """Basic test cases for GoogleOAuthService."""
    
    @patch('src.services.google_oauth.get_dynamodb_resource')
    @patch('src.services.google_oauth.get_secrets_client')
    def test_init(self, mock_secrets, mock_dynamodb):
        """Test service initialization."""
        service = GoogleOAuthService()
        assert service is not None
        mock_dynamodb.assert_called_once()
        mock_secrets.assert_called_once()
    
    def test_validate_scopes_valid(self):
        """Test scope validation with valid scopes."""
        with patch('src.services.google_oauth.get_dynamodb_resource'), \
             patch('src.services.google_oauth.get_secrets_client'):
            service = GoogleOAuthService()
            
            valid_scopes = [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/gmail.send'
            ]
            
            result = service._validate_scopes(valid_scopes)
            assert result is True
    
    def test_validate_scopes_invalid(self):
        """Test scope validation with invalid scopes."""
        with patch('src.services.google_oauth.get_dynamodb_resource'), \
             patch('src.services.google_oauth.get_secrets_client'):
            service = GoogleOAuthService()
            
            invalid_scopes = [
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/invalid.scope'
            ]
            
            result = service._validate_scopes(invalid_scopes)
            assert result is False
    
    def test_generate_pkce_pair(self):
        """Test PKCE code verifier and challenge generation."""
        with patch('src.services.google_oauth.get_dynamodb_resource'), \
             patch('src.services.google_oauth.get_secrets_client'):
            service = GoogleOAuthService()
            
            code_verifier, code_challenge = service._generate_pkce_pair()
            
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
    
    @patch('src.services.google_oauth.get_dynamodb_resource')
    @patch('src.services.google_oauth.get_secrets_client')
    def test_get_oauth_credentials(self, mock_secrets_client, mock_dynamodb):
        """Test OAuth credentials retrieval."""
        # Mock secrets client
        mock_secrets_instance = Mock()
        mock_secrets_client.return_value = mock_secrets_instance
        mock_secrets_instance.get_secret_value.return_value = {
            'SecretString': '{"client_id": "test-client-id", "client_secret": "test-client-secret"}'
        }
        
        service = GoogleOAuthService()
        credentials = service._get_oauth_credentials()
        
        assert credentials['client_id'] == 'test-client-id'
        assert credentials['client_secret'] == 'test-client-secret'
    
    def test_scopes_constant(self):
        """Test that required scopes are properly defined."""
        expected_scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send',
            'openid',
            'email',
            'profile'
        ]
        
        assert GOOGLE_SCOPES == expected_scopes