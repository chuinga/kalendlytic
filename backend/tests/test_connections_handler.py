"""
Tests for connections handler integration with Google OAuth service.
"""

import json
import pytest
from unittest.mock import Mock, patch
from src.handlers.connections import lambda_handler


class TestConnectionsHandler:
    """Test cases for connections handler."""
    
    def test_cors_preflight(self):
        """Test CORS preflight request handling."""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/connections/google/auth/start',
            'headers': {}
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert response['body'] == ''
    
    @patch('src.handlers.connections.GoogleOAuthService')
    def test_google_auth_start_success(self, mock_oauth_service):
        """Test successful Google OAuth start."""
        # Mock the OAuth service
        mock_service_instance = Mock()
        mock_oauth_service.return_value = mock_service_instance
        mock_service_instance.generate_authorization_url.return_value = {
            'authorization_url': 'https://accounts.google.com/oauth2/auth?...',
            'state': 'test-state-123',
            'expires_at': '2024-01-01T01:00:00Z'
        }
        
        event = {
            'httpMethod': 'POST',
            'path': '/connections/google/auth/start',
            'headers': {'Authorization': 'Bearer test-token'},
            'body': json.dumps({
                'redirect_uri': 'https://example.com/callback'
            }),
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'authorization_url' in body
        assert 'state' in body
        assert 'expires_at' in body
        
        # Verify service was called correctly
        mock_service_instance.generate_authorization_url.assert_called_once_with(
            user_id='test-user-123',
            redirect_uri='https://example.com/callback',
            state=None
        )
    
    def test_google_auth_start_missing_redirect_uri(self):
        """Test Google OAuth start with missing redirect_uri."""
        event = {
            'httpMethod': 'POST',
            'path': '/connections/google/auth/start',
            'headers': {'Authorization': 'Bearer test-token'},
            'body': json.dumps({}),
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'redirect_uri is required' in body['error']
    
    @patch('src.handlers.connections.GoogleOAuthService')
    def test_google_auth_callback_success(self, mock_oauth_service):
        """Test successful Google OAuth callback."""
        # Mock the OAuth service
        mock_service_instance = Mock()
        mock_oauth_service.return_value = mock_service_instance
        mock_service_instance.exchange_code_for_tokens.return_value = {
            'connection_id': 'test-user-123#google',
            'provider': 'google',
            'profile': {
                'email': 'test@example.com',
                'name': 'Test User'
            },
            'scopes': ['calendar', 'gmail.send'],
            'expires_at': '2024-01-01T01:00:00Z',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        event = {
            'httpMethod': 'POST',
            'path': '/connections/google/auth/callback',
            'headers': {'Authorization': 'Bearer test-token'},
            'body': json.dumps({
                'code': 'test-auth-code',
                'state': 'test-state-123'
            }),
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['connection_id'] == 'test-user-123#google'
        assert body['provider'] == 'google'
        assert body['profile']['email'] == 'test@example.com'
        
        # Verify service was called correctly
        mock_service_instance.exchange_code_for_tokens.assert_called_once_with(
            user_id='test-user-123',
            authorization_code='test-auth-code',
            state='test-state-123'
        )
    
    def test_google_auth_callback_missing_params(self):
        """Test Google OAuth callback with missing parameters."""
        event = {
            'httpMethod': 'POST',
            'path': '/connections/google/auth/callback',
            'headers': {'Authorization': 'Bearer test-token'},
            'body': json.dumps({'code': 'test-code'}),  # Missing state
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'code and state are required' in body['error']
    
    @patch('src.handlers.connections.GoogleOAuthService')
    def test_google_status_check(self, mock_oauth_service):
        """Test Google connection status check."""
        # Mock the OAuth service
        mock_service_instance = Mock()
        mock_oauth_service.return_value = mock_service_instance
        mock_service_instance.get_connection_status.return_value = {
            'connected': True,
            'provider': 'google',
            'status': 'active',
            'profile': {
                'email': 'test@example.com',
                'name': 'Test User'
            },
            'is_expired': False
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/connections/google/status',
            'headers': {'Authorization': 'Bearer test-token'},
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['connected'] is True
        assert body['provider'] == 'google'
        assert body['status'] == 'active'
        
        # Verify service was called correctly
        mock_service_instance.get_connection_status.assert_called_once_with('test-user-123')
    
    def test_endpoint_not_found(self):
        """Test handling of unknown endpoints."""
        event = {
            'httpMethod': 'GET',
            'path': '/connections/unknown',
            'headers': {'Authorization': 'Bearer test-token'},
            'requestContext': {
                'authorizer': {'userId': 'test-user-123'}
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Endpoint not found' in body['error']
    
    def test_missing_authorization(self):
        """Test handling of missing authorization header."""
        event = {
            'httpMethod': 'POST',
            'path': '/connections/google/auth/start',
            'headers': {},
            'body': json.dumps({
                'redirect_uri': 'https://example.com/callback'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body