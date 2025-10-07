"""
Unified OAuth token management interface for both Google and Microsoft providers.
Provides a single interface for managing OAuth connections across multiple providers.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from .google_oauth import GoogleOAuthService
from .microsoft_oauth import MicrosoftOAuthService

logger = logging.getLogger(__name__)

class OAuthProvider(Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class UnifiedOAuthManager:
    """Unified interface for managing OAuth connections across multiple providers."""
    
    def __init__(self):
        self.google_service = GoogleOAuthService()
        self.microsoft_service = MicrosoftOAuthService()
        self._services = {
            OAuthProvider.GOOGLE: self.google_service,
            OAuthProvider.MICROSOFT: self.microsoft_service
        }
    
    def _get_service(self, provider: str):
        """Get the appropriate OAuth service for the provider."""
        try:
            provider_enum = OAuthProvider(provider.lower())
            return self._services[provider_enum]
        except ValueError:
            raise Exception(f"Unsupported OAuth provider: {provider}")
    
    def generate_authorization_url(self, provider: str, user_id: str, 
                                 redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate OAuth authorization URL for the specified provider.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dictionary containing authorization URL and metadata
        """
        try:
            service = self._get_service(provider)
            result = service.generate_authorization_url(user_id, redirect_uri, state)
            result['provider'] = provider.lower()
            return result
        except Exception as e:
            logger.error(f"Failed to generate authorization URL for {provider}: {str(e)}")
            raise Exception(f"Authorization URL generation failed for {provider}: {str(e)}")
    
    def exchange_code_for_tokens(self, provider: str, user_id: str, 
                               authorization_code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            authorization_code: Authorization code from OAuth callback
            state: State parameter for CSRF validation
            
        Returns:
            Dictionary containing token information and user profile
        """
        try:
            service = self._get_service(provider)
            result = service.exchange_code_for_tokens(user_id, authorization_code, state)
            result['provider'] = provider.lower()
            return result
        except Exception as e:
            logger.error(f"Token exchange failed for {provider}: {str(e)}")
            raise Exception(f"Token exchange failed for {provider}: {str(e)}")
    
    def refresh_access_token(self, provider: str, user_id: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            
        Returns:
            Dictionary containing new token information
        """
        try:
            service = self._get_service(provider)
            result = service.refresh_access_token(user_id)
            result['provider'] = provider.lower()
            return result
        except Exception as e:
            logger.error(f"Token refresh failed for {provider}: {str(e)}")
            raise Exception(f"Token refresh failed for {provider}: {str(e)}")
    
    def get_valid_access_token(self, provider: str, user_id: str) -> str:
        """
        Get valid access token for the specified provider, refreshing if necessary.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            
        Returns:
            Valid access token string
        """
        try:
            service = self._get_service(provider)
            
            # Google service returns Credentials object, Microsoft returns token string
            if provider.lower() == 'google':
                credentials = service.get_valid_credentials(user_id)
                return credentials.token
            else:
                return service.get_valid_access_token(user_id)
                
        except Exception as e:
            logger.error(f"Failed to get valid access token for {provider}: {str(e)}")
            raise Exception(f"Failed to get valid access token for {provider}: {str(e)}")
    
    def get_connection_status(self, provider: str, user_id: str) -> Dict[str, Any]:
        """
        Get connection status and health information for the specified provider.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            
        Returns:
            Dictionary containing connection status and metadata
        """
        try:
            service = self._get_service(provider)
            result = service.get_connection_status(user_id)
            result['provider'] = provider.lower()
            return result
        except Exception as e:
            logger.error(f"Failed to get connection status for {provider}: {str(e)}")
            return {
                'connected': False,
                'provider': provider.lower(),
                'status': 'error',
                'error': str(e)
            }
    
    def get_all_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get connection status for all providers for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of connection status dictionaries
        """
        connections = []
        
        for provider in OAuthProvider:
            try:
                status = self.get_connection_status(provider.value, user_id)
                connections.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for {provider.value}: {str(e)}")
                connections.append({
                    'connected': False,
                    'provider': provider.value,
                    'status': 'error',
                    'error': str(e)
                })
        
        return connections
    
    def disconnect(self, provider: str, user_id: str) -> bool:
        """
        Disconnect the specified provider account and revoke tokens.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            
        Returns:
            True if disconnection was successful
        """
        try:
            service = self._get_service(provider)
            return service.disconnect(user_id)
        except Exception as e:
            logger.error(f"Failed to disconnect {provider} account: {str(e)}")
            return False
    
    def disconnect_all(self, user_id: str) -> Dict[str, bool]:
        """
        Disconnect all provider accounts for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary mapping provider names to disconnection success status
        """
        results = {}
        
        for provider in OAuthProvider:
            try:
                results[provider.value] = self.disconnect(provider.value, user_id)
            except Exception as e:
                logger.error(f"Failed to disconnect {provider.value}: {str(e)}")
                results[provider.value] = False
        
        return results
    
    def validate_provider_scopes(self, provider: str, scopes: List[str]) -> bool:
        """
        Validate that the provided scopes are valid for the specified provider.
        
        Args:
            provider: OAuth provider (google or microsoft)
            scopes: List of scopes to validate
            
        Returns:
            True if all scopes are valid for the provider
        """
        try:
            service = self._get_service(provider)
            return service._validate_scopes(scopes)
        except Exception as e:
            logger.error(f"Scope validation failed for {provider}: {str(e)}")
            return False
    
    def get_required_scopes(self, provider: str) -> List[str]:
        """
        Get the list of required scopes for the specified provider.
        
        Args:
            provider: OAuth provider (google or microsoft)
            
        Returns:
            List of required scopes
        """
        try:
            if provider.lower() == 'google':
                from .google_oauth import GOOGLE_SCOPES
                return GOOGLE_SCOPES
            elif provider.lower() == 'microsoft':
                from .microsoft_oauth import MICROSOFT_SCOPES
                return MICROSOFT_SCOPES
            else:
                raise Exception(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to get required scopes for {provider}: {str(e)}")
            return []
    
    def get_supported_providers(self) -> List[str]:
        """
        Get list of supported OAuth providers.
        
        Returns:
            List of supported provider names
        """
        return [provider.value for provider in OAuthProvider]
    
    def is_provider_connected(self, provider: str, user_id: str) -> bool:
        """
        Check if a specific provider is connected and active for a user.
        
        Args:
            provider: OAuth provider (google or microsoft)
            user_id: User identifier
            
        Returns:
            True if provider is connected and active
        """
        try:
            status = self.get_connection_status(provider, user_id)
            return status.get('connected', False) and status.get('status') == 'active'
        except Exception as e:
            logger.error(f"Failed to check connection status for {provider}: {str(e)}")
            return False
    
    def get_connected_providers(self, user_id: str) -> List[str]:
        """
        Get list of connected and active providers for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of connected provider names
        """
        connected = []
        
        for provider in OAuthProvider:
            if self.is_provider_connected(provider.value, user_id):
                connected.append(provider.value)
        
        return connected