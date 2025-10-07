#!/usr/bin/env python3
"""
Simple test script to verify health check functionality.
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.health_check import create_health_check_response

def test_health_check():
    """Test the health check functionality."""
    print("Testing health check functionality...")
    
    try:
        # Test auth component health check
        print("\n1. Testing auth component health check...")
        auth_response = create_health_check_response('auth', include_dependencies=False)
        print(f"Status Code: {auth_response['statusCode']}")
        body = json.loads(auth_response['body'])
        print(f"Component: {body['component']}")
        print(f"Status: {body['status']}")
        
        # Test agent component health check
        print("\n2. Testing agent component health check...")
        agent_response = create_health_check_response('agent', include_dependencies=False)
        print(f"Status Code: {agent_response['statusCode']}")
        body = json.loads(agent_response['body'])
        print(f"Component: {body['component']}")
        print(f"Status: {body['status']}")
        
        print("\n✅ Health check tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Health check test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_health_check()
    sys.exit(0 if success else 1)