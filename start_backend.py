#!/usr/bin/env python3
"""
Simple backend server startup script
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from src.main import app
    print("✅ Backend app imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Creating minimal FastAPI app...")
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="Meeting Scheduling Agent API")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    @app.get("/")
    async def root():
        return {"message": "Meeting Scheduling Agent API", "status": "running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    # Placeholder endpoints for frontend
    @app.get("/connections")
    async def get_connections():
        return {"connections": []}
    
    @app.get("/calendar/availability")
    async def get_availability():
        return {"availability": []}
    
    @app.get("/calendar/events")
    async def get_events():
        return {"events": []}
    
    @app.get("/agent/actions")
    async def get_agent_actions():
        return {"actions": []}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting backend server on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)