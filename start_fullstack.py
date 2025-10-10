#!/usr/bin/env python3
"""
Start both backend and frontend servers for testing
"""

import subprocess
import sys
import time
import os

def start_backend():
    """Start the backend API server."""
    print("🚀 Starting Backend API Server...")
    
    try:
        # Start backend server
        backend_process = subprocess.Popen(
            [sys.executable, "simple_api_server.py"],
            cwd="backend",
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"✅ Backend started with PID: {backend_process.pid}")
        print("📍 Backend running on: http://localhost:8000")
        return backend_process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the frontend development server."""
    print("\n🌐 Starting Frontend Development Server...")
    
    try:
        # Start frontend server
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd="frontend",
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"✅ Frontend started with PID: {frontend_process.pid}")
        print("📍 Frontend running on: http://localhost:3000")
        return frontend_process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Start both servers."""
    print("🚀 Starting Full-Stack Meeting Scheduler")
    print("="*50)
    
    # Start backend
    backend_process = start_backend()
    
    # Wait a moment
    time.sleep(2)
    
    # Start frontend
    frontend_process = start_frontend()
    
    # Wait for servers to initialize
    print("\n⏳ Waiting for servers to initialize...")
    time.sleep(5)
    
    print("\n" + "="*50)
    print("🎉 Full-Stack Application Started!")
    print("\n🌐 Access Points:")
    print("   • Frontend App: http://localhost:3000")
    print("   • Backend API: http://localhost:8000")
    print("   • API Documentation: http://localhost:8000/docs")
    
    print("\n🧪 Testing Features:")
    print("   1. OAuth Integration (Google & Microsoft)")
    print("   2. AI-Powered Meeting Scheduling")
    print("   3. Calendar Conflict Resolution")
    print("   4. Nova Pro Integration")
    
    print("\n💡 Manual Testing:")
    print("   • Open Chrome and visit http://localhost:3000")
    print("   • Test OAuth flows with your configured credentials")
    print("   • Try scheduling meetings with AI assistance")
    
    print(f"\n🔧 Process IDs:")
    if backend_process:
        print(f"   Backend PID: {backend_process.pid}")
    if frontend_process:
        print(f"   Frontend PID: {frontend_process.pid}")
    
    print("\n⚠️ To stop servers:")
    print("   • Close the console windows that opened")
    print("   • Or use Task Manager to end the processes")

if __name__ == "__main__":
    main()