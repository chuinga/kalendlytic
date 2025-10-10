#!/usr/bin/env python3
"""
Test if both backend and frontend servers are running
"""

import requests
import time

def test_backend():
    """Test if backend API is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running on http://localhost:8000")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend API not responding on http://localhost:8000")
        print("   Start with: cd backend && python simple_api_server.py")
        return False
    except Exception as e:
        print(f"❌ Backend test error: {e}")
        return False

def test_frontend():
    """Test if frontend is running."""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running on http://localhost:3000")
            return True
        else:
            print(f"⚠️ Frontend responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not responding on http://localhost:3000")
        print("   Start with: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False

def main():
    print("🧪 Testing Meeting Scheduler Servers")
    print("="*40)
    
    backend_ok = test_backend()
    time.sleep(1)
    frontend_ok = test_frontend()
    
    print("\n" + "="*40)
    if backend_ok and frontend_ok:
        print("🎉 Both servers are running!")
        print("\n🌐 Access Points:")
        print("   • Frontend: http://localhost:3000")
        print("   • Backend API: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/docs")
        
        print("\n🧪 Test OAuth Integration:")
        print("   1. Visit http://localhost:3000")
        print("   2. Look for 'Connect Calendar' buttons")
        print("   3. Test Google and Microsoft OAuth flows")
        print("   4. Try scheduling a meeting with AI")
        
    else:
        print("⚠️ Some servers are not running")
        print("\n🔧 To start servers:")
        if not backend_ok:
            print("   Backend: cd backend && python simple_api_server.py")
        if not frontend_ok:
            print("   Frontend: cd frontend && npm run dev")

if __name__ == "__main__":
    main()