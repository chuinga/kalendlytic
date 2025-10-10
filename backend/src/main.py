"""
FastAPI main application for AWS Meeting Scheduling Agent
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import Dict, Any

# Import handlers
from handlers.auth import lambda_handler as auth_handler
from handlers.connections import lambda_handler as connections_handler
from handlers.agent import lambda_handler as agent_handler
from handlers.calendar import lambda_handler as calendar_handler
from handlers.preferences import lambda_handler as preferences_handler

app = FastAPI(
    title="AWS Meeting Scheduling Agent API",
    description="AI-powered meeting scheduling system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://d2plklx5a1wakf.cloudfront.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def lambda_to_fastapi_response(lambda_response: Dict[str, Any]):
    """Convert Lambda response format to FastAPI response"""
    status_code = lambda_response.get('statusCode', 200)
    body = lambda_response.get('body', '{}')
    
    if isinstance(body, str):
        import json
        try:
            body = json.loads(body)
        except:
            body = {"message": body}
    
    return JSONResponse(content=body, status_code=status_code)

def create_lambda_event(method: str, path: str, body: Any = None, query_params: Dict = None):
    """Create a Lambda event from FastAPI request"""
    return {
        'httpMethod': method,
        'path': path,
        'body': body,
        'queryStringParameters': query_params or {},
        'headers': {},
        'requestContext': {'requestId': 'local-dev'}
    }

# Auth routes
@app.get("/auth/health")
async def auth_health():
    event = create_lambda_event('GET', '/auth/health')
    response = auth_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.post("/auth/login")
async def auth_login(credentials: Dict[str, Any]):
    event = create_lambda_event('POST', '/auth/login', credentials)
    response = auth_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.post("/auth/register")
async def auth_register(user_data: Dict[str, Any]):
    event = create_lambda_event('POST', '/auth/register', user_data)
    response = auth_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/auth/profile")
async def auth_profile():
    event = create_lambda_event('GET', '/auth/profile')
    response = auth_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.put("/auth/profile")
async def auth_profile_update(profile_data: Dict[str, Any]):
    event = create_lambda_event('PUT', '/auth/profile', profile_data)
    response = auth_handler(event, {})
    return lambda_to_fastapi_response(response)

# Connections routes
@app.get("/connections/health")
async def connections_health():
    event = create_lambda_event('GET', '/connections/health')
    response = connections_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/connections")
async def get_connections():
    event = create_lambda_event('GET', '/connections')
    response = connections_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.post("/connections/{provider}")
async def create_connection(provider: str, connection_data: Dict[str, Any]):
    event = create_lambda_event('POST', f'/connections/{provider}', connection_data)
    response = connections_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.delete("/connections/{provider}")
async def delete_connection(provider: str):
    event = create_lambda_event('DELETE', f'/connections/{provider}')
    response = connections_handler(event, {})
    return lambda_to_fastapi_response(response)

# Agent routes
@app.get("/agent/health")
async def agent_health():
    event = create_lambda_event('GET', '/agent/health')
    response = agent_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.post("/agent/schedule")
async def agent_schedule(schedule_request: Dict[str, Any]):
    event = create_lambda_event('POST', '/agent/schedule', schedule_request)
    response = agent_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/agent/runs")
async def agent_runs():
    event = create_lambda_event('GET', '/agent/runs')
    response = agent_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/agent/runs/{run_id}")
async def agent_run_details(run_id: str):
    event = create_lambda_event('GET', f'/agent/runs/{run_id}')
    response = agent_handler(event, {})
    return lambda_to_fastapi_response(response)

# Calendar routes
@app.get("/calendar/health")
async def calendar_health():
    event = create_lambda_event('GET', '/calendar/health')
    response = calendar_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/calendar/availability")
async def calendar_availability():
    event = create_lambda_event('GET', '/calendar/availability')
    response = calendar_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/calendar/events")
async def calendar_events():
    event = create_lambda_event('GET', '/calendar/events')
    response = calendar_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.post("/calendar/events")
async def create_calendar_event(event_data: Dict[str, Any]):
    event = create_lambda_event('POST', '/calendar/events', event_data)
    response = calendar_handler(event, {})
    return lambda_to_fastapi_response(response)

# Preferences routes
@app.get("/preferences/health")
async def preferences_health():
    event = create_lambda_event('GET', '/preferences/health')
    response = preferences_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.get("/preferences")
async def get_preferences():
    event = create_lambda_event('GET', '/preferences')
    response = preferences_handler(event, {})
    return lambda_to_fastapi_response(response)

@app.put("/preferences")
async def update_preferences(preferences_data: Dict[str, Any]):
    event = create_lambda_event('PUT', '/preferences', preferences_data)
    response = preferences_handler(event, {})
    return lambda_to_fastapi_response(response)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AWS Meeting Scheduling Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/auth/*",
            "connections": "/connections/*", 
            "agent": "/agent/*",
            "calendar": "/calendar/*",
            "preferences": "/preferences/*"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)