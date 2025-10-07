"""
Google OAuth 2.0 service with PKCE support for secure authorization flows.
Handles token exchange, refresh, and secure storage with KMS encryption.
"""

import os
import json
import secrets
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from ..utils.aws_clients import get_dynamodb_resource, get_secrets_client
from ..utils.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)

# Required scopes for Google Calendar and Gmail
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send',
    'openid',
    'email',
    'profile'
]

class GoogleOAuthService:
    """Service for handling Google OAuth 2.0 flows with PKCE."""
    
    def __init__(self):
        self.dynamodb = get_dynamodb_resource()
        self.secrets_client = get_secrets_client()
        self.connections_table = self.dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'Connections'))
        
    def _get_oauth_credentials(self) -> Dict[str, str]:
        """Retrieve Google OAuth credentials from AWS Secrets Manager."""
        try:
            secret_name = os.environ.get('GOOGLE_OAUTH_SECRET', 'google-oauth-credentials')
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve Google OAuth credentials: {str(e)}")
            raise Exception("OAuth credentials not configured")
    
    def _generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def _validate_scopes(self, requested_scopes: list) -> bool:
        """Validate that requested scopes are allowed."""
        for scope in requested_scopes:
            if scope not in GOOGLE_SCOPES:
                logger.warning(f"Invalid scope requested: {scope}")
                return False
        return True
    
    def generate_authorization_url(self, user_id: str, redirect_uri: str, 
                                 state: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate Google OAuth authorization URL with PKCE.
        
        Args:
            user_id: User identifier
            redirect_uri: OAuth redirect URI
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dictionary containing authorization URL and PKCE parameters
        """
        try:
            credentials = self._get_oauth_credentials()
            code_verifier, code_challenge = self._generate_pkce_pair()
            
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Store PKCE parameters temporarily (expires in 10 minutes)
            pkce_data = {
                'code_verifier': code_verifier,
                'redirect_uri': redirect_uri,
                'state': state,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
            }
            
            # Store in DynamoDB with TTL
            self.connections_table.put_item(
                Item={
                    'pk': f"pkce#{user_id}#{state}",
                    'user_id': user_id,
                    'pkce_data': pkce_data,
                    'ttl': int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
                }
            )
            
            # Build authorization URL
            auth_params = {
                'client_id': credentials['client_id'],
                'redirect_uri': redirect_uri,
                'scope': ' '.join(GOOGLE_SCOPES),
                'response_type': 'code',
                'state': state,
                'access_type': 'offline',
                'prompt': 'consent',
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256'
            }
            
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
            
            return {
                'authorization_url': auth_url,
                'state': state,
                'expires_at': pkce_data['expires_at']
            }
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {str(e)}")
            raise Exception(f"Authorization URL generation failed: {str(e)}")
    
    def exchange_code_for_tokens(self, user_id: str, authorization_code: str, 
                               state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            user_id: User identifier
            authorization_code: Authorization code from OAuth callback
            state: State parameter for CSRF validation
            
        Returns:
            Dictionary containing token information and user profile
        """
        try:
            # Retrieve PKCE data
            pkce_response = self.connections_table.get_item(
                Key={'pk': f"pkce#{user_id}#{state}"}
            )
            
            if 'Item' not in pkce_response:
                raise Exception("Invalid or expired authorization state")
            
            pkce_data = pkce_response['Item']['pkce_data']
            
            # Check expiration
            expires_at = datetime.fromisoformat(pkce_data['expires_at'])
            if datetime.utcnow() > expires_at:
                raise Exception("Authorization state expired")
            
            credentials = self._get_oauth_credentials()
            
            # Exchange code for tokens
            token_data = {
                'client_id': credentials['client_id'],
                'client_secret': credentials['client_secret'],
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': pkce_data['redirect_uri'],
                'code_verifier': pkce_data['code_verifier']
            }
            
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception("Token exchange failed")
            
            token_response = response.json()
            
            # Get user profile information
            profile_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {token_response['access_token']}"}
            )
            
            if profile_response.status_code != 200:
                logger.error(f"Profile fetch failed: {profile_response.text}")
                raise Exception("Failed to fetch user profile")
            
            profile_data = profile_response.json()
            
            # Validate scopes
            granted_scopes = token_response.get('scope', '').split()
            if not self._validate_scopes(granted_scopes):
                raise Exception("Required scopes not granted")
            
            # Store encrypted tokens
            connection_data = {
                'pk': f"{user_id}#google",
                'user_id': user_id,
                'provider': 'google',
                'access_token_encrypted': encrypt_token(token_response['access_token']),
                'refresh_token_encrypted': encrypt_token(token_response['refresh_token']),
                'scopes': granted_scopes,
                'expires_at': (datetime.utcnow() + timedelta(seconds=token_response['expires_in'])).isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'last_refresh': datetime.utcnow().isoformat(),
                'profile': {
                    'email': profile_data.get('email'),
                    'name': profile_data.get('name'),
                    'picture': profile_data.get('picture'),
                    'google_id': profile_data.get('id')
                },
                'status': 'active'
            }
            
            self.connections_table.put_item(Item=connection_data)
            
            # Clean up PKCE data
            self.connections_table.delete_item(
                Key={'pk': f"pkce#{user_id}#{state}"}
            )
            
            return {
                'connection_id': f"{user_id}#google",
                'provider': 'google',
                'profile': connection_data['profile'],
                'scopes': granted_scopes,
                'expires_at': connection_data['expires_at'],
                'created_at': connection_data['created_at']
            }
            
        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise Exception(f"Token exchange failed: {str(e)}")
    
    def refresh_access_token(self, user_id: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing new token information
        """
        try:
            # Get current connection
            response = self.connections_table.get_item(
                Key={'pk': f"{user_id}#google"}
            )
            
            if 'Item' not in response:
                raise Exception("Google connection not found")
            
            connection = response['Item']
            
            # Decrypt refresh token
            refresh_token = decrypt_token(connection['refresh_token_encrypted'])
            credentials = self._get_oauth_credentials()
            
            # Request new access token
            token_data = {
                'client_id': credentials['client_id'],
                'client_secret': credentials['client_secret'],
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                # If refresh fails, mark connection as invalid
                self.connections_table.update_item(
                    Key={'pk': f"{user_id}#google"},
                    UpdateExpression='SET #status = :status, last_refresh = :timestamp',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'invalid',
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                raise Exception("Token refresh failed - re-authorization required")
            
            token_response = response.json()
            
            # Update connection with new token
            update_expression = 'SET access_token_encrypted = :access_token, expires_at = :expires_at, last_refresh = :timestamp'
            expression_values = {
                ':access_token': encrypt_token(token_response['access_token']),
                ':expires_at': (datetime.utcnow() + timedelta(seconds=token_response['expires_in'])).isoformat(),
                ':timestamp': datetime.utcnow().isoformat()
            }
            
            # Update refresh token if provided
            if 'refresh_token' in token_response:
                update_expression += ', refresh_token_encrypted = :refresh_token'
                expression_values[':refresh_token'] = encrypt_token(token_response['refresh_token'])
            
            self.connections_table.update_item(
                Key={'pk': f"{user_id}#google"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            return {
                'connection_id': f"{user_id}#google",
                'expires_at': expression_values[':expires_at'],
                'last_refresh': expression_values[':timestamp'],
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise Exception(f"Token refresh failed: {str(e)}")
    
    def get_valid_credentials(self, user_id: str) -> Credentials:
        """
        Get valid Google credentials, refreshing if necessary.
        
        Args:
            user_id: User identifier
            
        Returns:
            Google OAuth2 Credentials object
        """
        try:
            # Get connection
            response = self.connections_table.get_item(
                Key={'pk': f"{user_id}#google"}
            )
            
            if 'Item' not in response:
                raise Exception("Google connection not found")
            
            connection = response['Item']
            
            if connection.get('status') != 'active':
                raise Exception("Google connection is not active")
            
            # Check if token needs refresh
            expires_at = datetime.fromisoformat(connection['expires_at'])
            if datetime.utcnow() >= expires_at - timedelta(minutes=5):  # Refresh 5 minutes early
                logger.info(f"Refreshing expired token for user {user_id}")
                self.refresh_access_token(user_id)
                
                # Re-fetch updated connection
                response = self.connections_table.get_item(
                    Key={'pk': f"{user_id}#google"}
                )
                connection = response['Item']
            
            # Decrypt tokens
            access_token = decrypt_token(connection['access_token_encrypted'])
            refresh_token = decrypt_token(connection['refresh_token_encrypted'])
            
            # Create credentials object
            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self._get_oauth_credentials()['client_id'],
                client_secret=self._get_oauth_credentials()['client_secret'],
                scopes=connection['scopes']
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get valid credentials: {str(e)}")
            raise Exception(f"Failed to get valid credentials: {str(e)}")
    
    def get_connection_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get Google connection status and health information.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing connection status and metadata
        """
        try:
            response = self.connections_table.get_item(
                Key={'pk': f"{user_id}#google"}
            )
            
            if 'Item' not in response:
                return {
                    'connected': False,
                    'provider': 'google',
                    'status': 'not_connected'
                }
            
            connection = response['Item']
            expires_at = datetime.fromisoformat(connection['expires_at'])
            is_expired = datetime.utcnow() >= expires_at
            
            return {
                'connected': True,
                'provider': 'google',
                'status': connection.get('status', 'unknown'),
                'profile': connection.get('profile', {}),
                'scopes': connection.get('scopes', []),
                'expires_at': connection['expires_at'],
                'is_expired': is_expired,
                'last_refresh': connection.get('last_refresh'),
                'created_at': connection.get('created_at')
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection status: {str(e)}")
            return {
                'connected': False,
                'provider': 'google',
                'status': 'error',
                'error': str(e)
            }
    
    def disconnect(self, user_id: str) -> bool:
        """
        Disconnect Google account and revoke tokens.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if disconnection was successful
        """
        try:
            # Get connection to revoke token
            response = self.connections_table.get_item(
                Key={'pk': f"{user_id}#google"}
            )
            
            if 'Item' in response:
                connection = response['Item']
                
                try:
                    # Revoke access token
                    access_token = decrypt_token(connection['access_token_encrypted'])
                    revoke_response = requests.post(
                        f'https://oauth2.googleapis.com/revoke?token={access_token}',
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    )
                    
                    if revoke_response.status_code not in [200, 400]:  # 400 means already revoked
                        logger.warning(f"Token revocation returned status {revoke_response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Failed to revoke token: {str(e)}")
                
                # Delete connection record
                self.connections_table.delete_item(
                    Key={'pk': f"{user_id}#google"}
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect Google account: {str(e)}")
            return False