#!/usr/bin/env python3
"""
Direct test of Lambda handlers without running the server.
"""

import sys
import os
sys.path.append('src')

import json
from handlers.auth import lambda_handler as auth_handler
from handlers.connections import lambda_handler as connections_handler
from handlers.agent import lambda_handler as agent_handler
from handlers.calendar import lambda_handler as calendar_handler
from handlers.preferences import lambda_handler as preferences_handler

def create_test_event(method: str, path: str, body: dict = None):
    """Create a test Lambda event."""
    return {
        'httpMethod': method,
        'path': path,
        'body': json.dumps(body) if body else None,
        'queryStringParameters': {},
        'headers': {
            'Authorization': 'Bearer test-token'
        },
        'requestContext': {
            'requestId': 'test-request',
            'authorizer': {
                'userId': 'test-user-123'
            }
        }
    }

def test_handler(handler_name: str, handler_func, test_cases):
    """Test a specific handler with multiple test cases."""
    print(f"\n=== Testing {handler_name} Handler ===")
    
    results = []
    
    for description, method, path, body in test_cases:
        print(f"Testing: {description}")
        print(f"  {method} {path}")
        
        try:
            event = create_test_event(method, path, body)
            response = handler_func(event, {})
            
            status_code = response.get('statusCode', 500)
            response_body = response.get('body', '{}')
            
            if isinstance(response_body, str):
                try:
                    response_body = json.loads(response_body)
                except:
                    pass
            
            success = 200 <= status_code < 300
            results.append(success)
            
            if success:
                print(f"  ✅ Success ({status_code})")
                if isinstance(response_body, dict):
                    message = response_body.get('message', str(response_body)[:100])
                    print(f"  📄 Response: {message}")
                else:
                    print(f"  📄 Response: {str(response_body)[:100]}")
            else:
                print(f"  ❌ Failed ({status_code})")
                print(f"  💥 Error: {response_body}")
                
        except Exception as e:
            print(f"  💥 Exception: {e}")
            results.append(False)
        
        print()
    
    successful = sum(results)
    total = len(results)
    print(f"{handler_name} Results: {successful}/{total} passed")
    
    return successful, total

def test_all_handlers():
    """Test all Lambda handlers."""
    print("=== Testing AWS Meeting Scheduling Agent Handlers ===")
    
    # Test cases for each handler
    test_cases = {
        'Auth': [
            ("Health check", "GET", "/auth/health", None),
            ("Login placeholder", "POST", "/auth/login", {"email": "test@example.com", "password": "test123"}),
            ("Profile placeholder", "GET", "/auth/profile", None),
        ],
        
        'Connections': [
            ("Health check", "GET", "/connections/health", None),
            ("Get connections", "GET", "/connections", None),
            ("Google OAuth start", "POST", "/connections/google/auth", {"redirect_uri": "http://localhost:3000/callback"}),
        ],
        
        'Agent': [
            ("Health check", "GET", "/agent/health", None),
            ("Schedule meeting", "POST", "/agent/schedule", {
                "title": "Test Meeting",
                "duration": 60,
                "attendees": ["test@example.com"]
            }),
            ("Get agent runs", "GET", "/agent/runs", None),
        ],
        
        'Calendar': [
            ("Health check", "GET", "/calendar/health", None),
            ("Get availability", "GET", "/calendar/availability", None),
            ("Get events", "GET", "/calendar/events", None),
        ],
        
        'Preferences': [
            ("Health check", "GET", "/preferences/health", None),
            ("Get preferences", "GET", "/preferences", None),
            ("Update preferences", "PUT", "/preferences", {"timezone": "UTC", "working_hours": "9-17"}),
        ]
    }
    
    handlers = {
        'Auth': auth_handler,
        'Connections': connections_handler,
        'Agent': agent_handler,
        'Calendar': calendar_handler,
        'Preferences': preferences_handler
    }
    
    total_successful = 0
    total_tests = 0
    
    for handler_name, handler_func in handlers.items():
        cases = test_cases.get(handler_name, [])
        successful, count = test_handler(handler_name, handler_func, cases)
        total_successful += successful
        total_tests += count
    
    # Summary
    print("\n" + "="*50)
    print("=== Overall Test Summary ===")
    print(f"Total tests: {total_tests}")
    print(f"Successful: {total_successful}")
    print(f"Failed: {total_tests - total_successful}")
    print(f"Success rate: {(total_successful/total_tests)*100:.1f}%")
    
    if total_successful == total_tests:
        print("\n🎉 All handler tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_tests - total_successful} tests failed.")
        return False

if __name__ == "__main__":
    success = test_all_handlers()
    
    if success:
        print("\n✅ All handlers are working correctly!")
        print("You can now:")
        print("1. Start the API server: python src/main.py")
        print("2. Test with the frontend application")
        print("3. Use the API endpoints for meeting scheduling")
    else:
        print("\n❌ Some handlers have issues. Check the implementation.")
    
    sys.exit(0 if success else 1)