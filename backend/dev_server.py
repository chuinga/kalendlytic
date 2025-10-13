#!/usr/bin/env python3
"""
Development server for full-stack testing without AWS deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
from typing import Dict, Any
import uuid
from datetime import datetime

app = FastAPI(
    title="Meeting Scheduler - Development Server",
    description="Full-stack development server with OAuth and AI integration",
    version="1.0.0-dev"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock user sessions (in production this would be in database)
mock_sessions = {}
mock_users = {}

@app.get("/")
async def root():
    return {
        "message": "AWS Meeting Scheduling Agent - Development Server",
        "version": "1.0.0-dev",
        "status": "running",
        "features": {
            "oauth_integration": "Google & Microsoft configured",
            "ai_scheduling": "Nova Pro ready",
            "authentication": "Development mode (no AWS required)",
            "calendar_integration": "Ready for testing"
        },
        "endpoints": {
            "health": "/health",
            "auth": "/auth/*",
            "oauth": "/oauth/*",
            "meetings": "/meetings/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "development",
        "auth_configured": True,
        "oauth_configured": True,
        "ai_ready": True
    }

# Authentication endpoints (development mode)
@app.post("/auth/dev-login")
async def dev_login(credentials: Dict[str, Any]):
    """Development login - no real authentication required"""
    email = credentials.get("email", "demo@example.com")
    
    # Create mock user session
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    mock_users[user_id] = {
        "id": user_id,
        "email": email,
        "name": email.split("@")[0].title(),
        "created_at": datetime.now().isoformat()
    }
    
    mock_sessions[session_id] = {
        "user_id": user_id,
        "email": email,
        "expires_at": "2024-12-31T23:59:59Z"
    }
    
    return {
        "status": "success",
        "message": "Development login successful",
        "session_token": session_id,
        "user": mock_users[user_id]
    }

@app.get("/auth/profile")
async def get_profile():
    """Get user profile (development mode)"""
    return {
        "user": {
            "id": "dev-user-123",
            "email": "demo@example.com",
            "name": "Demo User",
            "oauth_connections": {
                "google": "configured",
                "microsoft": "configured"
            }
        }
    }

# OAuth endpoints (development simulation)
@app.post("/oauth/google/connect")
async def connect_google():
    """Simulate Google OAuth connection"""
    return {
        "status": "success",
        "message": "Google Calendar connected successfully",
        "provider": "google",
        "connection_id": str(uuid.uuid4()),
        "scopes": ["calendar", "email"]
    }

@app.post("/oauth/microsoft/connect")
async def connect_microsoft():
    """Simulate Microsoft OAuth connection"""
    return {
        "status": "success",
        "message": "Microsoft Outlook connected successfully",
        "provider": "microsoft",
        "connection_id": str(uuid.uuid4()),
        "scopes": ["calendar", "email"]
    }

@app.get("/oauth/status")
async def oauth_status():
    """Get OAuth connection status"""
    return {
        "google": {
            "connected": True,
            "email": "demo@gmail.com",
            "scopes": ["calendar", "email"]
        },
        "microsoft": {
            "connected": True,
            "email": "demo@outlook.com",
            "scopes": ["calendar", "email"]
        }
    }

# Meeting scheduling endpoints
@app.post("/meetings/schedule")
async def schedule_meeting(meeting_request: Dict[str, Any]):
    """AI-powered meeting scheduling"""
    
    title = meeting_request.get("title", "Untitled Meeting")
    duration = meeting_request.get("duration", 60)
    attendees = meeting_request.get("attendees", [])
    description = meeting_request.get("description", "")
    
    # Simulate AI analysis
    ai_analysis = f"""
    Meeting Analysis for "{title}":
    
    📅 Duration: {duration} minutes
    👥 Attendees: {len(attendees)} people
    
    🤖 AI Recommendations:
    • Best time slot: Tomorrow 2:00 PM - 3:00 PM
    • All attendees appear to be available
    • No conflicts detected in connected calendars
    • Suggested location: Video conference (Teams/Meet)
    
    ⚡ Optimization Tips:
    • Consider 45-minute duration for better scheduling
    • Send calendar invites 24 hours in advance
    • Include agenda in meeting description
    
    This is a development simulation. In production, Nova Pro would analyze real calendar data and provide intelligent scheduling recommendations.
    """
    
    return {
        "status": "success",
        "message": "Meeting scheduled successfully",
        "meeting": {
            "id": str(uuid.uuid4()),
            "title": title,
            "duration": duration,
            "attendees": attendees,
            "description": description,
            "scheduled_time": "2024-01-15T14:00:00Z",
            "created_at": datetime.now().isoformat()
        },
        "ai_analysis": ai_analysis.strip(),
        "recommendations": [
            "All attendees available at suggested time",
            "No calendar conflicts detected",
            "Video conference recommended"
        ]
    }

@app.get("/meetings")
async def get_meetings():
    """Get user's meetings"""
    return {
        "meetings": [
            {
                "id": "meeting-1",
                "title": "Team Standup",
                "start_time": "2024-01-15T09:00:00Z",
                "duration": 30,
                "attendees": ["alice@company.com", "bob@company.com"],
                "status": "scheduled"
            },
            {
                "id": "meeting-2", 
                "title": "Project Review",
                "start_time": "2024-01-15T14:00:00Z",
                "duration": 60,
                "attendees": ["manager@company.com"],
                "status": "scheduled"
            }
        ],
        "total": 2
    }

@app.get("/calendar/availability")
async def get_availability():
    """Get calendar availability"""
    return {
        "availability": [
            {
                "date": "2024-01-15",
                "slots": [
                    {"start": "09:00", "end": "10:00", "available": False, "reason": "Team Standup"},
                    {"start": "10:00", "end": "11:00", "available": True},
                    {"start": "11:00", "end": "12:00", "available": True},
                    {"start": "14:00", "end": "15:00", "available": False, "reason": "Project Review"},
                    {"start": "15:00", "end": "16:00", "available": True}
                ]
            }
        ],
        "timezone": "UTC"
    }

# Development utilities
@app.get("/dev/reset")
async def reset_dev_data():
    """Reset development data"""
    global mock_sessions, mock_users
    mock_sessions.clear()
    mock_users.clear()
    
    return {
        "status": "success",
        "message": "Development data reset"
    }

@app.get("/dev/status")
async def dev_status():
    """Development server status"""
    return {
        "environment": "development",
        "mock_users": len(mock_users),
        "active_sessions": len(mock_sessions),
        "oauth_configured": {
            "google": "✓ Client ID configured",
            "microsoft": "✓ Client ID configured"
        },
        "features_available": [
            "Authentication (development mode)",
            "OAuth simulation",
            "AI meeting scheduling",
            "Calendar integration simulation"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Meeting Scheduler Development Server")
    print("📍 Server: http://localhost:8005")
    print("📖 API Docs: http://localhost:8005/docs")
    print("🧪 Development Status: http://localhost:8005/dev/status")
    print()
    print("✅ Features Available:")
    print("   • Authentication (development mode)")
    print("   • OAuth integration simulation")
    print("   • AI-powered meeting scheduling")
    print("   • Calendar availability")
    print()
    print("🔧 No AWS deployment required for testing!")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=False)