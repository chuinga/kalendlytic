#!/usr/bin/env python3
"""
Simplified FastAPI server for testing Nova Pro integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
from typing import Dict, Any
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import Nova Pro client directly
try:
    import boto3
    from botocore.config import Config
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False

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

def call_nova_pro(prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
    """Call Nova Pro directly."""
    if not BEDROCK_AVAILABLE:
        return {
            "error": "Bedrock not available",
            "message": "boto3 not installed or configured"
        }
    
    try:
        # Configuration
        region = "eu-west-1"
        model_id = "eu.amazon.nova-pro-v1:0"
        
        # Create client
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=60
        )
        
        bedrock_client = boto3.client('bedrock-runtime', config=config)
        
        # Make request
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        response = bedrock_client.converse(
            modelId=model_id,
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )
        
        # Extract response
        output_message = response['output']['message']
        content = output_message['content'][0]['text']
        
        # Extract usage
        usage = response.get('usage', {})
        
        return {
            "success": True,
            "content": content,
            "model": model_id,
            "usage": {
                "input_tokens": usage.get('inputTokens', 0),
                "output_tokens": usage.get('outputTokens', 0),
                "total_tokens": usage.get('totalTokens', 0)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AWS Meeting Scheduling Agent API",
        "version": "1.0.0",
        "status": "running",
        "nova_pro": "available" if BEDROCK_AVAILABLE else "unavailable",
        "endpoints": {
            "health": "/health",
            "nova_test": "/nova/test",
            "schedule": "/agent/schedule",
            "docs": "/docs"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bedrock_available": BEDROCK_AVAILABLE,
        "region": "eu-west-1",
        "model": "eu.amazon.nova-pro-v1:0"
    }

# Nova Pro test endpoint
@app.get("/nova/test")
async def test_nova_pro():
    """Test Nova Pro integration."""
    prompt = "Hello! Please respond with 'Nova Pro is working correctly for meeting scheduling' if you can process this request."
    
    result = call_nova_pro(prompt, max_tokens=100)
    
    if result.get("success"):
        return {
            "status": "success",
            "message": "Nova Pro is working correctly!",
            "response": result["content"],
            "usage": result["usage"],
            "model": result["model"]
        }
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Nova Pro test failed",
                "error": result.get("error"),
                "error_type": result.get("error_type")
            }
        )

# Agent scheduling endpoint
@app.post("/agent/schedule")
async def schedule_meeting(request: Dict[str, Any]):
    """Schedule a meeting using Nova Pro AI."""
    
    # Extract request data
    title = request.get("title", "Untitled Meeting")
    duration = request.get("duration", 60)
    attendees = request.get("attendees", [])
    description = request.get("description", "")
    preferred_times = request.get("preferred_times", [])
    
    # Create AI prompt for meeting scheduling
    prompt = f"""
You are an AI meeting scheduling assistant. Help schedule the following meeting:

Title: {title}
Duration: {duration} minutes
Attendees: {', '.join(attendees)}
Description: {description}
Preferred times: {', '.join(preferred_times)}

Please provide:
1. A brief analysis of the meeting request
2. Suggested optimal scheduling approach
3. Any potential conflicts or considerations
4. A recommended meeting agenda if appropriate

Respond in a helpful, professional tone.
"""
    
    result = call_nova_pro(prompt, max_tokens=500)
    
    if result.get("success"):
        return {
            "status": "success",
            "message": "Meeting scheduling analysis completed",
            "meeting_details": {
                "title": title,
                "duration": duration,
                "attendees": attendees,
                "description": description,
                "preferred_times": preferred_times
            },
            "ai_analysis": result["content"],
            "usage": result["usage"],
            "model": result["model"]
        }
    else:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to process meeting scheduling request",
                "error": result.get("error"),
                "meeting_details": {
                    "title": title,
                    "duration": duration,
                    "attendees": attendees
                }
            }
        )

# Additional health endpoints for compatibility
@app.get("/auth/health")
async def auth_health():
    return {"status": "healthy", "service": "auth", "message": "Auth service placeholder"}

@app.get("/connections/health")
async def connections_health():
    return {"status": "healthy", "service": "connections", "message": "Connections service placeholder"}

@app.get("/agent/health")
async def agent_health():
    return {"status": "healthy", "service": "agent", "message": "Agent service with Nova Pro integration"}

@app.get("/calendar/health")
async def calendar_health():
    return {"status": "healthy", "service": "calendar", "message": "Calendar service placeholder"}

@app.get("/preferences/health")
async def preferences_health():
    return {"status": "healthy", "service": "preferences", "message": "Preferences service placeholder"}

if __name__ == "__main__":
    print("🚀 Starting AWS Meeting Scheduling Agent API Server")
    print("📍 Server: http://localhost:8002")
    print("📖 Docs: http://localhost:8002/docs")
    print("🧪 Nova Pro Test: http://localhost:8002/nova/test")
    print("🤖 Schedule Meeting: POST http://localhost:8002/agent/schedule")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=False)