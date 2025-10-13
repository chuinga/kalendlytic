#!/usr/bin/env python3
"""
Start backend server on an available port
"""

import socket
import subprocess
import sys
import os

def find_available_port(start_port=8000, max_port=8100):
    """Find an available port."""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def start_backend_server():
    """Start backend server on available port."""
    print("🔍 Finding available port...")
    
    port = find_available_port()
    if not port:
        print("❌ No available ports found")
        return None
    
    print(f"✅ Found available port: {port}")
    
    # Create a temporary server file with the correct port
    server_content = f'''#!/usr/bin/env python3
"""
Temporary backend server on port {port}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

app = FastAPI(
    title="AWS Meeting Scheduling Agent API",
    description="AI-powered meeting scheduling system with Nova Pro",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {{
        "message": "AWS Meeting Scheduling Agent API",
        "version": "1.0.0",
        "status": "running",
        "port": {port},
        "endpoints": {{
            "health": "/health",
            "docs": "/docs"
        }}
    }}

@app.get("/health")
async def health_check():
    return {{
        "status": "healthy",
        "port": {port},
        "message": "Backend API is running"
    }}

if __name__ == "__main__":
    print("🚀 Starting AWS Meeting Scheduling Agent API Server")
    print(f"📍 Server: http://localhost:{port}")
    print(f"📖 Docs: http://localhost:{port}/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port={port}, reload=False)
'''
    
    # Write temporary server file
    temp_server = "temp_backend_server.py"
    with open(temp_server, 'w') as f:
        f.write(server_content)
    
    print(f"🚀 Starting backend server on port {port}...")
    
    # Start the server
    try:
        process = subprocess.Popen(
            [sys.executable, temp_server],
            cwd="backend"
        )
        
        print(f"✅ Backend server started!")
        print(f"📍 URL: http://localhost:{port}")
        print(f"📖 API Docs: http://localhost:{port}/docs")
        
        return port, process
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None, None

if __name__ == "__main__":
    port, process = start_backend_server()
    
    if port:
        print(f"\\n🌐 Opening in Chrome...")
        print(f"Backend API: http://localhost:{port}")
        
        # Open in Chrome
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
        
        print("\\n⚠️ Server is running. Press Ctrl+C to stop.")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\\n🛑 Stopping server...")
            process.terminate()
    else:
        print("❌ Failed to start backend server")