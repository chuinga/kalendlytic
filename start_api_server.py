#!/usr/bin/env python3
"""
Script to start the API server and test basic connectivity.
"""

import subprocess
import sys
import time
import requests
import threading
import os

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    print("📍 Server will run on: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print()
    print("To start the server manually, run:")
    print("  cd backend")
    print("  python src/main.py")
    print()
    print("Press Ctrl+C to stop the server when running.")

def test_server_connectivity():
    """Test if server is running and responsive."""
    print("🔍 Testing server connectivity...")
    
    base_url = "http://localhost:8000"
    
    # Wait a moment for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responsive!")
            print(f"📄 Response: {response.json()}")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 8000.")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def show_test_commands():
    """Show commands to test the API."""
    print("\n" + "="*60)
    print("🧪 **API Testing Commands**")
    print("="*60)
    
    commands = [
        ("Root endpoint", "curl http://localhost:8000/"),
        ("API documentation", "curl http://localhost:8000/docs"),
        ("Auth health check", "curl http://localhost:8000/auth/health"),
        ("Connections health", "curl http://localhost:8000/connections/health"),
        ("Agent health check", "curl http://localhost:8000/agent/health"),
        ("Calendar health", "curl http://localhost:8000/calendar/health"),
        ("Preferences health", "curl http://localhost:8000/preferences/health"),
        ("Get connections", "curl http://localhost:8000/connections"),
        ("Get agent runs", "curl http://localhost:8000/agent/runs"),
        ("Schedule meeting", '''curl -X POST http://localhost:8000/agent/schedule \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Test Meeting",
    "duration": 60,
    "attendees": ["test@example.com"],
    "preferred_times": ["2024-01-15T14:00:00Z"]
  }' '''),
    ]
    
    for i, (description, command) in enumerate(commands, 1):
        print(f"\n{i}. **{description}:**")
        print(f"   {command}")
    
    print(f"\n{'='*60}")
    print("💡 **Tips:**")
    print("- Use -v flag with curl for verbose output: curl -v ...")
    print("- Use jq for pretty JSON: curl ... | jq")
    print("- Check server logs in the terminal where you started it")

if __name__ == "__main__":
    print("AWS Meeting Scheduling Agent - API Server Setup")
    print("="*60)
    
    start_server()
    show_test_commands()
    
    print(f"\n🎯 **Next Steps:**")
    print("1. Open a new terminal")
    print("2. Run: cd backend && python src/main.py")
    print("3. Test the endpoints using the commands above")
    print("4. Visit http://localhost:8000/docs for interactive API documentation")