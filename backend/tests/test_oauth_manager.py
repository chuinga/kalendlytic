"""
Tests for unified OAuth manager functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.oauth_manager import UnifiedOAuthManager, OAuthProvider


class TestUnifiedOAuthManager:
    """Test cases for unified OAuth manager."""
    
    @pytest.fixture
    def mock_google_service(self):
        """Mock Google OAuth service."""
        mock = Mock()
        mock.generate_authorization_url.return_value = {
            'authorization_url': 'https://accounts.google.com/oauth',
            'state': 'test-state'
        }
        mock.exchange_code_for_tokens.return_value = {
            'connection_id': 'user#google',
            'provider': 'google'
        }
        mock.get_connection_status.return_value = {
            'connected': True,
            'provider': 'google',
            'status': 'active'
        }
        return mock
    
    @pytest.fixture
    def mock_microsoft_service(self):
        """Mock Microsoft OAuth service."""
        mock = Mock()
        mock.generate_authorization_url.return_value = {
            'authorization_url': 'https://login.microsoftonline.com/oauth',
            'state': 'test-state'
        }
        mock.exchange_code_for_tokens.return_value = {
            'connection_id': 'user#microsoft',
            'provider': 'microsoft'
        }
        mock.get_connection_status.return_value = {
            'connected': True,
            'provider': 'microsoft',
            'status': 'active'
        }
        return mock
    
    @pytest.fixture
    def oauth_manager(self, mock_google_service, mock_microsoft_service):
        """Create UnifiedOAuthManager with mocked services."""
        with patch('src.services.oauth_manager.GoogleOAuthService') as mock_google_class, \
             patch('src.services.oauth_manager.MicrosoftOAuthService') as mock_microsoft_class:
            
            mock_google_class.return_value = mock_google_service
            mock_microsoft_class.return_value = mock_microsoft_service
            
            manager = UnifiedOAuthManager()
            return manager, mock_google_service, mock_microsoft_service
    
    def test_generate_authorization_url_google(self, oauth_manager):
        """Test authorization URL generation for Google."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        result = manager.generate_authorization_url(
            'google', 'user-123', 'https://example.com/callback'
        )
        
        assert result['provider'] == 'google'
        assert 'authorization_url' in result
        mock_google.generate_authorization_url.assert_called_once_with(
            'user-123', 'https://example.com/callback', None
        )
    
    def test_generate_authorization_url_microsoft(self, oauth_manager):
        """Test authorization URL generation for Microsoft."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        result = manager.generate_authorization_url(
            'microsoft', 'user-123', 'https://example.com/callback'
        )
        
        assert result['provider'] == 'microsoft'
        assert 'authorization_url' in result
        mock_microsoft.generate_authorization_url.assert_called_once_with(
            'user-123', 'https://example.com/callback', None
        )
    
    def test_generate_authorization_url_invalid_provider(self, oauth_manager):
        """Test authorization URL generation with invalid provider."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        with pytest.raises(Exception) as exc_info:
            manager.generate_authorization_url(
                'invalid', 'user-123', 'https://example.com/callback'
            )
        
        assert 'Unsupported OAuth provider' in str(exc_info.value)
    
    def test_exchange_code_for_tokens_google(self, oauth_manager):
        """Test token exchange for Google."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        result = manager.exchange_code_for_tokens(
            'google', 'user-123', 'auth-code', 'state'
        )
        
        assert result['provider'] == 'google'
        mock_google.exchange_code_for_tokens.assert_called_once_with(
            'user-123', 'auth-code', 'state'
        )
    
    def test_exchange_code_for_tokens_microsoft(self, oauth_manager):
        """Test token exchange for Microsoft."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        result = manager.exchange_code_for_tokens(
            'microsoft', 'user-123', 'auth-code', 'state'
        )
        
        assert result['provider'] == 'microsoft'
        mock_microsoft.exchange_code_for_tokens.assert_called_once_with(
            'user-123', 'auth-code', 'state'
        )
    
    def test_get_valid_access_token_google(self, oauth_manager):
        """Test getting valid access token for Google."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        # Mock Google credentials
        mock_credentials = Mock()
        mock_credentials.token = 'google-access-token'
        mock_google.get_valid_credentials.return_value = mock_credentials
        
        token = manager.get_valid_access_token('google', 'user-123')
        
        assert token == 'google-access-token'
        mock_google.get_valid_credentials.assert_called_once_with('user-123')
    
    def test_get_valid_access_token_microsoft(self, oauth_manager):
        """Test getting valid access token for Microsoft."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        mock_microsoft.get_valid_access_token.return_value = 'microsoft-access-token'
        
        token = manager.get_valid_access_token('microsoft', 'user-123')
        
        assert token == 'microsoft-access-token'
        mock_microsoft.get_valid_access_token.assert_called_once_with('user-123')
    
    def test_get_all_connections(self, oauth_manager):
        """Test getting all connections for a user."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        connections = manager.get_all_connections('user-123')
        
        assert len(connections) == 2
        assert any(conn['provider'] == 'google' for conn in connections)
        assert any(conn['provider'] == 'microsoft' for conn in connections)
        
        mock_google.get_connection_status.assert_called_once_with('user-123')
        mock_microsoft.get_connection_status.assert_called_once_with('user-123')
    
    def test_disconnect_google(self, oauth_manager):
        """Test disconnecting Google account."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        mock_google.disconnect.return_value = True
        
        success = manager.disconnect('google', 'user-123')
        
        assert success is True
        mock_google.disconnect.assert_called_once_with('user-123')
    
    def test_disconnect_microsoft(self, oauth_manager):
        """Test disconnecting Microsoft account."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        mock_microsoft.disconnect.return_value = True
        
        success = manager.disconnect('microsoft', 'user-123')
        
        assert success is True
        mock_microsoft.disconnect.assert_called_once_with('user-123')
    
    def test_disconnect_all(self, oauth_manager):
        """Test disconnecting all accounts."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        mock_google.disconnect.return_value = True
        mock_microsoft.disconnect.return_value = True
        
        results = manager.disconnect_all('user-123')
        
        assert results['google'] is True
        assert results['microsoft'] is True
        mock_google.disconnect.assert_called_once_with('user-123')
        mock_microsoft.disconnect.assert_called_once_with('user-123')
    
    def test_get_supported_providers(self, oauth_manager):
        """Test getting supported providers."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        providers = manager.get_supported_providers()
        
        assert 'google' in providers
        assert 'microsoft' in providers
        assert len(providers) == 2
    
    def test_is_provider_connected(self, oauth_manager):
        """Test checking if provider is connected."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        # Mock connected status
        mock_google.get_connection_status.return_value = {
            'connected': True,
            'status': 'active'
        }
        
        is_connected = manager.is_provider_connected('google', 'user-123')
        
        assert is_connected is True
        mock_google.get_connection_status.assert_called_once_with('user-123')
    
    def test_is_provider_not_connected(self, oauth_manager):
        """Test checking if provider is not connected."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        # Mock not connected status
        mock_google.get_connection_status.return_value = {
            'connected': False,
            'status': 'not_connected'
        }
        
        is_connected = manager.is_provider_connected('google', 'user-123')
        
        assert is_connected is False
    
    def test_get_connected_providers(self, oauth_manager):
        """Test getting list of connected providers."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        # Mock Google connected, Microsoft not connected
        mock_google.get_connection_status.return_value = {
            'connected': True,
            'status': 'active'
        }
        mock_microsoft.get_connection_status.return_value = {
            'connected': False,
            'status': 'not_connected'
        }
        
        connected = manager.get_connected_providers('user-123')
        
        assert 'google' in connected
        assert 'microsoft' not in connected
        assert len(connected) == 1
    
    def test_get_required_scopes_google(self, oauth_manager):
        """Test getting required scopes for Google."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        with patch('src.services.google_oauth.GOOGLE_SCOPES', ['scope1', 'scope2']):
            scopes = manager.get_required_scopes('google')
            assert scopes == ['scope1', 'scope2']
    
    def test_get_required_scopes_microsoft(self, oauth_manager):
        """Test getting required scopes for Microsoft."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        with patch('src.services.microsoft_oauth.MICROSOFT_SCOPES', ['scope3', 'scope4']):
            scopes = manager.get_required_scopes('microsoft')
            assert scopes == ['scope3', 'scope4']
    
    def test_validate_provider_scopes(self, oauth_manager):
        """Test validating provider scopes."""
        manager, mock_google, mock_microsoft = oauth_manager
        
        mock_google._validate_scopes.return_value = True
        
        is_valid = manager.validate_provider_scopes('google', ['scope1', 'scope2'])
        
        assert is_valid is True
        mock_google._validate_scopes.assert_called_once_with(['scope1', 'scope2'])