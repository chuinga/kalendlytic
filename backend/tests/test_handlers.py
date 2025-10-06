"""
Basic tests for Lambda handlers to ensure they can be imported and have basic structure.
"""

import pytest
from src.handlers import auth, connections, agent, calendar, preferences


def test_auth_handler_exists():
    """Test that auth handler exists and is callable."""
    assert hasattr(auth, 'lambda_handler')
    assert callable(auth.lambda_handler)


def test_connections_handler_exists():
    """Test that connections handler exists and is callable."""
    assert hasattr(connections, 'lambda_handler')
    assert callable(connections.lambda_handler)


def test_agent_handler_exists():
    """Test that agent handler exists and is callable."""
    assert hasattr(agent, 'lambda_handler')
    assert callable(agent.lambda_handler)


def test_calendar_handler_exists():
    """Test that calendar handler exists and is callable."""
    assert hasattr(calendar, 'lambda_handler')
    assert callable(calendar.lambda_handler)


def test_preferences_handler_exists():
    """Test that preferences handler exists and is callable."""
    assert hasattr(preferences, 'lambda_handler')
    assert callable(preferences.lambda_handler)


def test_auth_handler_basic_response():
    """Test that auth handler returns proper response structure."""
    event = {'path': '/auth', 'httpMethod': 'GET'}
    context = {}
    
    response = auth.lambda_handler(event, context)
    
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    assert response['statusCode'] == 200