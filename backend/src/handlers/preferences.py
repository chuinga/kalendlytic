"""
Preferences handler for user preference management and scheduling rules.
Manages working hours, VIP contacts, meeting types, and constraint enforcement.
"""

import json
import logging
from typing import Dict, Any

from ..tools.preference_management_tool import PreferenceManagementTool
from ..models.preferences import Preferences
from ..models.meeting import Meeting
from ..utils.health_check import create_health_check_response

logger = logging.getLogger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for preference operations.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with preference operation result
    """
    try:
        # Initialize preference management tool
        preference_tool = PreferenceManagementTool()
        
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Handle health check endpoint
        if path == '/preferences/health' and http_method == 'GET':
            return handle_health_check()
        
        # Extract user ID from path or body
        user_id = body.get('user_id') or event.get('pathParameters', {}).get('user_id')
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'user_id is required'})
            }
        
        # Handle different HTTP methods and operations
        if http_method == 'GET':
            # Retrieve preferences
            preferences = preference_tool.retrieve_preferences(user_id)
            if preferences:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'preferences': preferences.dict(),
                        'user_id': user_id
                    })
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'No preferences found for user'})
                }
        
        elif http_method == 'POST':
            # Handle different POST operations based on action
            action = body.get('action', 'extract_preferences')
            
            if action == 'extract_preferences':
                # Extract preferences from natural language
                natural_language_input = body.get('natural_language_input', '')
                if not natural_language_input:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'natural_language_input is required'})
                    }
                
                extraction_result = preference_tool.extract_preferences(natural_language_input, user_id)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'extraction_result': {
                            'working_hours': {day: {'start': wh.start, 'end': wh.end} 
                                            for day, wh in extraction_result.working_hours.items()},
                            'buffer_minutes': extraction_result.buffer_minutes,
                            'focus_blocks': [
                                {
                                    'day': fb.day,
                                    'start': fb.start,
                                    'end': fb.end,
                                    'title': fb.title
                                } for fb in extraction_result.focus_blocks
                            ],
                            'vip_contacts': extraction_result.vip_contacts,
                            'meeting_types': {name: {
                                'duration': mt.duration,
                                'priority': mt.priority,
                                'buffer_before': mt.buffer_before,
                                'buffer_after': mt.buffer_after
                            } for name, mt in extraction_result.meeting_types.items()},
                            'confidence_score': extraction_result.confidence_score
                        }
                    })
                }
            
            elif action == 'evaluate_priority':
                # Evaluate meeting priority
                meeting_data = body.get('meeting_data', {})
                if not meeting_data:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'meeting_data is required'})
                    }
                
                # Get user preferences
                preferences = preference_tool.retrieve_preferences(user_id)
                if not preferences:
                    return {
                        'statusCode': 404,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({'error': 'User preferences not found'})
                    }
                
                # Create meeting object from data
                meeting = Meeting(**meeting_data)
                
                # Evaluate priority
                priority_score = preference_tool.evaluate_meeting_priority(meeting, preferences, user_id)
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'priority_score': {
                            'meeting_id': priority_score.meeting_id,
                            'priority_score': priority_score.priority_score,
                            'priority_factors': priority_score.priority_factors,
                            'is_vip_meeting': priority_score.is_vip_meeting,
                            'meeting_type': priority_score.meeting_type,
                            'reasoning': priority_score.reasoning
                        }
                    })
                }
        
        elif http_method == 'PUT':
            # Store/update preferences
            preferences_data = body.get('preferences', {})
            if not preferences_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'preferences data is required'})
                }
            
            # Create preferences object
            preferences = Preferences(pk=f"user#{user_id}", **preferences_data)
            
            # Store preferences
            success = preference_tool.store_preferences(user_id, preferences)
            
            if success:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'message': 'Preferences updated successfully'})
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Failed to update preferences'})
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
        logger.error(f"Preferences error: {str(e)}")
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


def handle_health_check() -> Dict[str, Any]:
    """Handle health check requests for the preferences handler."""
    try:
        # Perform health check without Bedrock dependency
        health_response = create_health_check_response('preferences', include_dependencies=True)
        
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