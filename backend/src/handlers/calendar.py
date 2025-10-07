"""
Calendar handler for unified calendar operations across Gmail and Outlook.
Manages availability aggregation, conflict detection, and event management.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.google_calendar import GoogleCalendarService
from ..utils.logging import setup_logger
from ..utils.health_check import create_health_check_response

logger = setup_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for calendar operations.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with calendar operation result
    """
    try:
        # Extract request information
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('user_id')
        
        if not user_id:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Initialize Google Calendar service
        google_calendar = GoogleCalendarService()
        
        # Handle health check endpoint
        if path == '/calendar/health' and method == 'GET':
            return handle_health_check()
        
        # Route requests based on path and method
        if path.startswith('/calendar/google'):
            return handle_google_calendar_request(google_calendar, user_id, path, method, event)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Endpoint not found'})
            }
        
    except Exception as e:
        logger.error(f"Calendar error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_google_calendar_request(google_calendar: GoogleCalendarService, user_id: str, 
                                 path: str, method: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google Calendar specific requests."""
    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        query_params = event.get('queryStringParameters') or {}
        
        # GET /calendar/google/events - Fetch calendar events
        if path == '/calendar/google/events' and method == 'GET':
            start_time = datetime.fromisoformat(query_params.get('start', 
                (datetime.utcnow() - timedelta(days=7)).isoformat()))
            end_time = datetime.fromisoformat(query_params.get('end', 
                (datetime.utcnow() + timedelta(days=30)).isoformat()))
            calendar_id = query_params.get('calendar_id', 'primary')
            
            events = google_calendar.fetch_calendar_events(user_id, start_time, end_time, calendar_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'events': events,
                    'count': len(events)
                }, default=str)
            }
        
        # POST /calendar/google/events - Create new event
        elif path == '/calendar/google/events' and method == 'POST':
            result = google_calendar.create_event(user_id, body)
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result, default=str)
            }
        
        # PUT /calendar/google/events/{event_id} - Update event
        elif path.startswith('/calendar/google/events/') and method == 'PUT':
            event_id = path.split('/')[-1]
            result = google_calendar.update_event(user_id, event_id, body)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result, default=str)
            }
        
        # DELETE /calendar/google/events/{event_id} - Delete event
        elif path.startswith('/calendar/google/events/') and method == 'DELETE':
            event_id = path.split('/')[-1]
            send_notifications = body.get('send_notifications', True)
            
            success = google_calendar.delete_event(user_id, event_id, 
                                                 send_notifications=send_notifications)
            
            return {
                'statusCode': 200 if success else 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': success})
            }
        
        # GET /calendar/google/availability - Calculate availability
        elif path == '/calendar/google/availability' and method == 'GET':
            start_date = datetime.fromisoformat(query_params.get('start', 
                datetime.utcnow().isoformat()))
            end_date = datetime.fromisoformat(query_params.get('end', 
                (datetime.utcnow() + timedelta(days=7)).isoformat()))
            
            working_hours = None
            if 'working_hours' in query_params:
                working_hours = json.loads(query_params['working_hours'])
            
            availability = google_calendar.calculate_availability(
                user_id, start_date, end_date, working_hours
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(availability.dict(), default=str)
            }
        
        # GET /calendar/google/calendars - List calendars
        elif path == '/calendar/google/calendars' and method == 'GET':
            calendars = google_calendar.get_calendar_list(user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'calendars': calendars})
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Google Calendar request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Google Calendar operation failed',
                'message': str(e)
            })
        }


def handle_health_check() -> Dict[str, Any]:
    """Handle health check requests for the calendar handler."""
    try:
        # Perform health check including Bedrock for AI-powered calendar features
        health_response = create_health_check_response('calendar', include_dependencies=True)
        
        # Add CORS headers
        health_response['headers'].update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        })
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Health check failed',
                'message': str(e)
            })
        }