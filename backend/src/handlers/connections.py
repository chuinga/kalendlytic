"""
OAuth connection handler for Google and Microsoft integration.
Manages OAuth flows, token storage, and connection health monitoring.
"""

import json
import logging
import os
from typing import Dict, Any
from urllib.parse import parse_qs

from ..services.google_oauth import GoogleOAuthService
from ..services.microsoft_oauth import MicrosoftOAuthService
from ..services.oauth_manager import UnifiedOAuthManager
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


def get_user_id_from_event(event: Dict[str, Any]) -> str:
    """Extract user ID from JWT token in Authorization header."""
    # TODO: Implement JWT token validation and user ID extraction
    # For now, return a placeholder - this will be implemented in auth handler
    auth_header = event.get('headers', {}).get('Authorization', '')
    if auth_header.startswith('Bearer '):
        # In production, decode and validate JWT token
        # For now, extract from test token or use placeholder
        return event.get('requestContext', {}).get('authorizer', {}).get('userId', 'test-user-123')
    
    raise Exception("Authorization header missing or invalid")


def handle_google_auth_start(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google OAuth authorization start."""
    try:
        user_id = get_user_id_from_event(event)
        body = json.loads(event.get('body', '{}'))
        
        redirect_uri = body.get('redirect_uri')
        if not redirect_uri:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'redirect_uri is required'})
            }
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.generate_authorization_url(
            user_id=user_id,
            redirect_uri=redirect_uri,
            state=body.get('state')
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Google auth start failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_google_auth_callback(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google OAuth authorization callback."""
    try:
        user_id = get_user_id_from_event(event)
        body = json.loads(event.get('body', '{}'))
        
        authorization_code = body.get('code')
        state = body.get('state')
        
        if not authorization_code or not state:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'code and state are required'})
            }
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.exchange_code_for_tokens(
            user_id=user_id,
            authorization_code=authorization_code,
            state=state
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Google auth callback failed: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }


def handle_google_refresh(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google token refresh."""
    try:
        user_id = get_user_id_from_event(event)
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.refresh_access_token(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Google token refresh failed: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }


def handle_google_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google connection status check."""
    try:
        user_id = get_user_id_from_event(event)
        
        google_oauth = GoogleOAuthService()
        result = google_oauth.get_connection_status(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Google status check failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_google_disconnect(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google account disconnection."""
    try:
        user_id = get_user_id_from_event(event)
        
        google_oauth = GoogleOAuthService()
        success = google_oauth.disconnect(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': success})
        }
        
    except Exception as e:
        logger.error(f"Google disconnect failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_microsoft_auth_start(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft OAuth authorization start."""
    try:
        user_id = get_user_id_from_event(event)
        body = json.loads(event.get('body', '{}'))
        
        redirect_uri = body.get('redirect_uri')
        if not redirect_uri:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'redirect_uri is required'})
            }
        
        microsoft_oauth = MicrosoftOAuthService()
        result = microsoft_oauth.generate_authorization_url(
            user_id=user_id,
            redirect_uri=redirect_uri,
            state=body.get('state')
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Microsoft auth start failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_microsoft_auth_callback(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft OAuth authorization callback."""
    try:
        user_id = get_user_id_from_event(event)
        body = json.loads(event.get('body', '{}'))
        
        authorization_code = body.get('code')
        state = body.get('state')
        
        if not authorization_code or not state:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'code and state are required'})
            }
        
        microsoft_oauth = MicrosoftOAuthService()
        result = microsoft_oauth.exchange_code_for_tokens(
            user_id=user_id,
            authorization_code=authorization_code,
            state=state
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Microsoft auth callback failed: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }


def handle_microsoft_refresh(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft token refresh."""
    try:
        user_id = get_user_id_from_event(event)
        
        microsoft_oauth = MicrosoftOAuthService()
        result = microsoft_oauth.refresh_access_token(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Microsoft token refresh failed: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }


def handle_microsoft_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft connection status check."""
    try:
        user_id = get_user_id_from_event(event)
        
        microsoft_oauth = MicrosoftOAuthService()
        result = microsoft_oauth.get_connection_status(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Microsoft status check failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_microsoft_disconnect(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft account disconnection."""
    try:
        user_id = get_user_id_from_event(event)
        
        microsoft_oauth = MicrosoftOAuthService()
        success = microsoft_oauth.disconnect(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': success})
        }
        
    except Exception as e:
        logger.error(f"Microsoft disconnect failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_unified_connections_status(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified connection status for all providers."""
    try:
        user_id = get_user_id_from_event(event)
        
        oauth_manager = UnifiedOAuthManager()
        connections = oauth_manager.get_all_connections(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'connections': connections,
                'supported_providers': oauth_manager.get_supported_providers()
            })
        }
        
    except Exception as e:
        logger.error(f"Unified connections status failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_unified_disconnect_all(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle disconnection of all provider accounts."""
    try:
        user_id = get_user_id_from_event(event)
        
        oauth_manager = UnifiedOAuthManager()
        results = oauth_manager.disconnect_all(user_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'results': results})
        }
        
    except Exception as e:
        logger.error(f"Unified disconnect all failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for OAuth connection operations.
    
    Routes:
    Google OAuth:
    - POST /connections/google/auth/start - Start Google OAuth flow
    - POST /connections/google/auth/callback - Handle OAuth callback
    - POST /connections/google/refresh - Refresh Google tokens
    - GET /connections/google/status - Get Google connection status
    - DELETE /connections/google - Disconnect Google account
    
    Microsoft OAuth:
    - POST /connections/microsoft/auth/start - Start Microsoft OAuth flow
    - POST /connections/microsoft/auth/callback - Handle OAuth callback
    - POST /connections/microsoft/refresh - Refresh Microsoft tokens
    - GET /connections/microsoft/status - Get Microsoft connection status
    - DELETE /connections/microsoft - Disconnect Microsoft account
    
    Unified:
    - GET /connections/status - Get all connection statuses
    - DELETE /connections/all - Disconnect all accounts
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with connection result
    """
    
    # CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Route Google OAuth requests
        if '/connections/google' in path:
            if path.endswith('/auth/start') and http_method == 'POST':
                response = handle_google_auth_start(event)
            elif path.endswith('/auth/callback') and http_method == 'POST':
                response = handle_google_auth_callback(event)
            elif path.endswith('/refresh') and http_method == 'POST':
                response = handle_google_refresh(event)
            elif path.endswith('/status') and http_method == 'GET':
                response = handle_google_status(event)
            elif path.endswith('/google') and http_method == 'DELETE':
                response = handle_google_disconnect(event)
            else:
                response = {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Endpoint not found'})
                }
        # Route Microsoft OAuth requests
        elif '/connections/microsoft' in path:
            if path.endswith('/auth/start') and http_method == 'POST':
                response = handle_microsoft_auth_start(event)
            elif path.endswith('/auth/callback') and http_method == 'POST':
                response = handle_microsoft_auth_callback(event)
            elif path.endswith('/refresh') and http_method == 'POST':
                response = handle_microsoft_refresh(event)
            elif path.endswith('/status') and http_method == 'GET':
                response = handle_microsoft_status(event)
            elif path.endswith('/microsoft') and http_method == 'DELETE':
                response = handle_microsoft_disconnect(event)
            else:
                response = {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Endpoint not found'})
                }
        # Route unified connection requests
        elif path == '/connections/status' and http_method == 'GET':
            response = handle_unified_connections_status(event)
        elif path == '/connections/all' and http_method == 'DELETE':
            response = handle_unified_disconnect_all(event)
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
        
        # Add CORS headers to response
        response['headers'] = {**cors_headers, **response.get('headers', {})}
        return response
        
    except Exception as e:
        logger.error(f"Connection handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }