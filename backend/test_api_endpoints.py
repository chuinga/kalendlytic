#!/usr/bin/env python3
"""
Test script for API endpoints using the FastAPI development server.
"""

import requests
import json
import time
import sys
import subprocess
import threading
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return the response."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": 200 <= response.status_code < 300
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def test_api_endpoints():
    """Test various API endpoints."""
    print("=== Testing AWS Meeting Scheduling Agent API ===")
    print(f"Base URL: {API_BASE_URL}")
    print()
    
    # Test cases
    test_cases = [
        # Root endpoint
        ("GET", "/", None, "Root endpoint"),
        
        # Health checks
        ("GET", "/auth/health", None, "Auth health check"),
        ("GET", "/connections/health", None, "Connections health check"),
        ("GET", "/agent/health", None, "Agent health check"),
        ("GET", "/calendar/health", None, "Calendar health check"),
        ("GET", "/preferences/health", None, "Preferences health check"),
        
        # Auth endpoints (placeholders)
        ("GET", "/auth/profile", None, "Get user profile"),
        
        # Connections endpoints
        ("GET", "/connections", None, "Get connections status"),
        
        # Agent endpoints
        ("GET", "/agent/runs", None, "Get agent runs"),
        ("POST", "/agent/schedule", {
            "title": "Test Meeting",
            "duration": 60,
            "attendees": ["test@example.com"],
            "preferred_times": ["2024-01-15T14:00:00Z"]
        }, "Schedule meeting with agent"),
        
        # Calendar endpoints
        ("GET", "/calendar/availability", None, "Get calendar availability"),
        ("GET", "/calendar/events", None, "Get calendar events"),
        
        # Preferences endpoints
        ("GET", "/preferences", None, "Get user preferences"),
    ]
    
    results = []
    
    for method, endpoint, data, description in test_cases:
        print(f"Testing: {description}")
        print(f"  {method} {endpoint}")
        
        result = test_endpoint(method, endpoint, data)
        results.append((description, result))
        
        if result.get("success"):
            print(f"  ✅ Success ({result['status_code']})")
            if isinstance(result.get("response"), dict):
                # Pretty print first few keys
                response_preview = str(result["response"])[:200]
                if len(str(result["response"])) > 200:
                    response_preview += "..."
                print(f"  📄 Response: {response_preview}")
            else:
                print(f"  📄 Response: {result.get('response', 'No response')}")
        else:
            print(f"  ❌ Failed ({result.get('status_code', 'N/A')})")
            print(f"  💥 Error: {result.get('error', result.get('response', 'Unknown error'))}")
        
        print()
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("=== Test Summary ===")
    successful = sum(1 for _, result in results if result.get("success"))
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Success rate: {(successful/total)*100:.1f}%")
    
    if successful == total:
        print("\n🎉 All API endpoint tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - successful} tests failed. Check the API server and handlers.")
        return False

def check_server_running():
    """Check if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("Checking if API server is running...")
    
    if not check_server_running():
        print("❌ API server is not running!")
        print("Please start the server first:")
        print("  cd backend")
        print("  python src/main.py")
        print("\nOr run it in the background and then run this test.")
        sys.exit(1)
    
    print("✅ API server is running!")
    print()
    
    success = test_api_endpoints()
    sys.exit(0 if success else 1)