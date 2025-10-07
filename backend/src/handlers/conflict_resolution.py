"""
Conflict resolution handler for intelligent meeting scheduling.
Manages conflict detection, resolution option generation, and execution workflows.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.conflict_resolution_engine import ConflictResolutionEngine
from ..services.availability_aggregation import AvailabilityAggregationService
from ..services.priority_service import PriorityService
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for conflict resolution operations.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with conflict resolution result
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
        
        # Initialize conflict resolution engine
        conflict_engine = ConflictResolutionEngine()
        
        # Route requests based on path and method
        if path.startswith('/conflicts'):
            return handle_conflict_request(conflict_engine, user_id, path, method, event)
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
        logger.error(f"Conflict resolution error: {str(e)}")
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


def handle_conflict_request(conflict_engine: ConflictResolutionEngine, user_id: str,
                          path: str, method: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle conflict resolution specific requests."""
    try:
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        query_params = event.get('queryStringParameters') or {}
        
        # POST /conflicts/detect - Detect conflicts in a time range
        if path == '/conflicts/detect' and method == 'POST':
            start_date = datetime.fromisoformat(body.get('start_date'))
            end_date = datetime.fromisoformat(body.get('end_date'))
            connections = body.get('connections', [])
            preferences = body.get('preferences')
            proposed_meeting = body.get('proposed_meeting')
            
            conflicts = conflict_engine.detect_conflicts(
                user_id, start_date, end_date, connections, preferences, proposed_meeting
            )
            
            # Convert conflicts to serializable format
            conflicts_data = [
                {
                    'conflict_id': conflict.conflict_id,
                    'conflict_type': conflict.conflict_type.value,
                    'severity': conflict.severity.value,
                    'description': conflict.description,
                    'primary_meeting': {
                        'id': conflict.primary_meeting.sk,
                        'title': conflict.primary_meeting.title,
                        'start': conflict.primary_meeting.start.isoformat(),
                        'end': conflict.primary_meeting.end.isoformat()
                    },
                    'conflicting_meetings': [
                        {
                            'id': meeting.sk,
                            'title': meeting.title,
                            'start': meeting.start.isoformat(),
                            'end': meeting.end.isoformat()
                        }
                        for meeting in conflict.conflicting_meetings
                    ],
                    'affected_time_range': [
                        conflict.affected_time_range[0].isoformat(),
                        conflict.affected_time_range[1].isoformat()
                    ],
                    'suggested_strategy': conflict.suggested_strategy.value
                }
                for conflict in conflicts
            ]
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'conflicts': conflicts_data,
                    'count': len(conflicts_data),
                    'has_conflicts': len(conflicts_data) > 0
                })
            }
        
        # POST /conflicts/{conflict_id}/resolve - Generate resolution options
        elif path.startswith('/conflicts/') and path.endswith('/resolve') and method == 'POST':
            conflict_id = path.split('/')[-2]
            connections = body.get('connections', [])
            preferences = body.get('preferences')
            
            # This would typically retrieve the conflict from storage
            # For now, we'll expect the conflict details in the request body
            conflict_data = body.get('conflict')
            if not conflict_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Conflict details required'})
                }
            
            # Convert conflict data back to ConflictDetails object
            # This is a simplified implementation
            options = []  # Would generate actual options here
            
            # Create approval workflow
            workflow = conflict_engine.create_approval_workflow(
                None,  # Would pass actual conflict object
                options,
                user_id
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(workflow, default=str)
            }
        
        # POST /conflicts/workflows/{workflow_id}/approve - Process user approval
        elif path.startswith('/conflicts/workflows/') and path.endswith('/approve') and method == 'POST':
            workflow_id = path.split('/')[-2]
            selected_option_id = body.get('selected_option_id')
            user_feedback = body.get('user_feedback')
            
            if not selected_option_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Selected option ID required'})
                }
            
            resolution_result = conflict_engine.process_user_approval(
                workflow_id, selected_option_id, user_feedback
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'resolution_id': resolution_result.resolution_id,
                    'status': resolution_result.status,
                    'message': 'Resolution approved and ready for execution'
                })
            }
        
        # POST /conflicts/resolutions/{resolution_id}/execute - Execute approved resolution
        elif path.startswith('/conflicts/resolutions/') and path.endswith('/execute') and method == 'POST':
            resolution_id = path.split('/')[-2]
            connections = body.get('connections', [])
            
            # This would typically retrieve the resolution from storage
            # For now, we'll create a mock resolution result
            from ..services.conflict_resolution_engine import ConflictResolutionResult
            
            mock_resolution = ConflictResolutionResult(
                resolution_id=resolution_id,
                original_conflict=None,
                chosen_option=None,
                status="approved",
                created_at=datetime.utcnow()
            )
            
            execution_result = conflict_engine.execute_resolution(
                mock_resolution, user_id, connections
            )
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(execution_result, default=str)
            }
        
        # GET /conflicts/history - Get conflict resolution history
        elif path == '/conflicts/history' and method == 'GET':
            # This would retrieve historical conflict resolutions from storage
            # For now, return empty history
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'resolutions': [],
                    'count': 0,
                    'message': 'No conflict resolution history found'
                })
            }
        
        # GET /conflicts/stats - Get conflict resolution statistics
        elif path == '/conflicts/stats' and method == 'GET':
            # This would calculate statistics from stored data
            # For now, return mock statistics
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'total_conflicts_detected': 0,
                    'total_conflicts_resolved': 0,
                    'resolution_success_rate': 0.0,
                    'most_common_conflict_type': 'direct_overlap',
                    'most_used_resolution_strategy': 'reschedule_lower_priority',
                    'average_resolution_time_minutes': 0
                })
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
        logger.error(f"Conflict resolution request error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Conflict resolution operation failed',
                'message': str(e)
            })
        }