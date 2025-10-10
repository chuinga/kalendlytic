#!/usr/bin/env python3
"""
Full-stack demo startup script
"""

import subprocess
import sys
import time
import webbrowser
import requests
import threading
import os

def test_backend_health():
    """Test if backend is responding."""
    print("🔍 Testing backend health...")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is healthy!")
                print(f"📄 Response: {response.json()}")
                return True
        except:
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
            else:
                print("❌ Backend health check failed")
                return False
    
    return False

def test_oauth_endpoints():
    """Test OAuth endpoints."""
    print("\n🔐 Testing OAuth endpoints...")
    
    # Test Google OAuth
    try:
        response = requests.post("http://localhost:8001/connections/google/auth", 
                               json={"redirect_uri": "http://localhost:3000/auth/google/callback"},
                               timeout=5)
        if response.status_code in [200, 400]:  # 400 is expected without proper auth
            print("✅ Google OAuth endpoint responding")
        else:
            print(f"⚠️ Google OAuth endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Google OAuth test failed: {e}")
    
    # Test Microsoft OAuth
    try:
        response = requests.post("http://localhost:8001/connections/microsoft/auth",
                               json={"redirect_uri": "http://localhost:3000/auth/microsoft/callback"},
                               timeout=5)
        if response.status_code in [200, 400]:  # 400 is expected without proper auth
            print("✅ Microsoft OAuth endpoint responding")
        else:
            print(f"⚠️ Microsoft OAuth endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Microsoft OAuth test failed: {e}")

def test_nova_pro():
    """Test Nova Pro integration."""
    print("\n🤖 Testing Nova Pro integration...")
    
    try:
        response = requests.get("http://localhost:8001/nova/test", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ Nova Pro integration working!")
            print(f"📄 AI Response: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"⚠️ Nova Pro test returned: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Nova Pro test failed: {e}")

def test_meeting_scheduling():
    """Test AI meeting scheduling."""
    print("\n📅 Testing AI meeting scheduling...")
    
    meeting_request = {
        "title": "Demo Meeting",
        "duration": 30,
        "attendees": ["demo@example.com"],
        "description": "Testing the AI meeting scheduler",
        "preferred_times": ["2024-01-15T14:00:00Z"]
    }
    
    try:
        response = requests.post("http://localhost:8001/agent/schedule",
                               json=meeting_request,
                               timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("✅ AI meeting scheduling working!")
            print(f"📄 AI Analysis: {result.get('ai_analysis', 'No analysis')[:150]}...")
        else:
            print(f"⚠️ Meeting scheduling returned: {response.status_code}")
            print(f"📄 Response: {response.text}")
    except Exception as e:
        print(f"❌ Meeting scheduling test failed: {e}")

def show_demo_instructions():
    """Show demo instructions."""
    print("\n" + "="*60)
    print("🎉 **FULL-STACK DEMO READY**")
    print("="*60)
    
    print("\n🌐 **Access Points:**")
    print("• Backend API: http://localhost:8001")
    print("• API Documentation: http://localhost:8001/docs")
    print("• Frontend App: http://localhost:3000 (when started)")
    
    print("\n🧪 **Test Endpoints:**")
    print("• Health Check: http://localhost:8001/health")
    print("• Nova Pro Test: http://localhost:8001/nova/test")
    print("• API Docs: http://localhost:8001/docs")
    
    print("\n🔐 **OAuth Testing:**")
    print("1. Visit http://localhost:3000 (when frontend is running)")
    print("2. Try connecting Google Calendar")
    print("3. Try connecting Microsoft Outlook")
    print("4. Test meeting scheduling with AI")
    
    print("\n🚀 **Next Steps:**")
    print("1. Keep this backend running")
    print("2. In another terminal: cd frontend && npm run dev")
    print("3. Visit http://localhost:3000 to test the full application")
    
    print("\n💡 **Demo Features to Test:**")
    print("• User authentication")
    print("• Calendar connections (Google/Microsoft)")
    print("• AI-powered meeting scheduling")
    print("• Conflict resolution")
    print("• Meeting preferences")

def main():
    """Main demo function."""
    print("AWS Meeting Scheduling Agent - Full-Stack Demo")
    print("="*60)
    
    print("🚀 Starting backend server on port 8001...")
    print("📍 Backend will run at: http://localhost:8001")
    print()
    
    # Start backend server in background
    backend_process = subprocess.Popen([
        sys.executable, "backend/simple_api_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for backend to start
        time.sleep(3)
        
        # Test backend health
        if test_backend_health():
            # Run all tests
            test_oauth_endpoints()
            test_nova_pro()
            test_meeting_scheduling()
            
            # Show instructions
            show_demo_instructions()
            
            # Open browser to API docs
            print("\n🌐 Opening API documentation in browser...")
            webbrowser.open("http://localhost:8001/docs")
            
            print("\n⏸️ Press Ctrl+C to stop the demo")
            
            # Keep running
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping demo...")
        else:
            print("❌ Backend failed to start properly")
            
    finally:
        # Clean up
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

if __name__ == "__main__":
    main()