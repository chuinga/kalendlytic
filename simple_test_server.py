#!/usr/bin/env python3
"""
Simple test server for demonstration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Meeting Scheduler API Test")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "AWS Meeting Scheduling Agent API",
        "status": "running",
        "features": [
            "OAuth Integration (Google & Microsoft)",
            "AI-Powered Meeting Scheduling",
            "Nova Pro Integration",
            "Calendar Conflict Resolution"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "meeting-scheduler"}

@app.get("/oauth/status")
async def oauth_status():
    return {
        "google_oauth": "configured",
        "microsoft_oauth": "configured",
        "ready_for_calendar_integration": True
    }

@app.post("/demo/schedule")
async def demo_schedule(meeting_data: dict):
    return {
        "status": "success",
        "message": "Meeting scheduling demo",
        "ai_analysis": "This is a demo response. In production, Nova Pro would analyze the meeting request and provide intelligent scheduling recommendations.",
        "meeting_data": meeting_data
    }

if __name__ == "__main__":
    print("Starting Meeting Scheduler API Demo...")
    print("Server: http://localhost:8004")
    print("Docs: http://localhost:8004/docs")
    uvicorn.run(app, host="0.0.0.0", port=8004)