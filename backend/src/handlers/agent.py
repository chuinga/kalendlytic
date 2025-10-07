"""
AI Agent handler for Bedrock Claude integration and AgentCore orchestration.
Manages agent reasoning, tool execution, and decision-making workflows.
"""

import json
import os
from typing import Dict, Any

from ..utils.logging import create_agent_logger, AgentDecisionType, get_correlation_id
from ..utils.health_check import create_health_check_response, publish_bedrock_usage_metrics
from ..config.logging_config import LoggingConfig, apply_environment_config
from ..services.agentcore_orchestrator import (
    AgentCoreOrchestrator, AgentCoreOrchestratorError
)
from ..services.agentcore_router import TaskType
from ..services.agentcore_planner import PlanningStrategy

# Apply environment-specific logging configuration
apply_environment_config()

# Create enhanced agent logger
logger = create_agent_logger(__name__)

# Initialize AgentCore orchestrator
orchestrator = AgentCoreOrchestrator()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for AI agent operations with AgentCore integration.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with agent operation results
    """
    # Set up logging context
    correlation_id = get_correlation_id()
    user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    
    # Update logger with context
    logger.set_user_context(user_id or 'anonymous')
    logger.start_performance_tracking()
    
    # Set AWS context in logger
    if hasattr(context, 'aws_request_id'):
        os.environ['AWS_REQUEST_ID'] = context.aws_request_id
    
    logger.info(
        "Agent handler invoked",
        extra={
            'event_type': event.get('httpMethod'),
            'path': event.get('path'),
            'user_agent': event.get('headers', {}).get('User-Agent'),
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        }
    )
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        action = body.get('action', 'unknown')
        
        # Generate agent run ID for tracking
        import uuid
        agent_run_id = str(uuid.uuid4())
        logger.set_agent_run_id(agent_run_id)
        
        logger.info(f"Starting agent operation: {action}")
        
        # Process the request based on action type
        if action == 'schedule_meeting':
            result = handle_schedule_meeting(body, logger)
        elif action == 'resolve_conflict':
            result = handle_resolve_conflict(body, logger)
        elif action == 'daily_learning':
            result = handle_daily_learning(body, logger)
        elif action == 'intelligent_scheduling':
            result = handle_intelligent_scheduling(body)
        elif action == 'conflict_resolution':
            result = handle_conflict_resolution(body)
        elif action == 'availability_lookup':
            result = handle_availability_lookup(body)
        elif action == 'multi_step_optimization':
            result = handle_multi_step_optimization(body)
        else:
            logger.warning(f"Unknown action requested: {action}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
        
        # Log successful completion
        logger.log_performance_metrics(
            operation=action,
            metrics={
                'agent_run_id': agent_run_id,
                'success': True,
                'result_size': len(str(result))
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id,
                'X-Agent-Run-ID': agent_run_id
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(
            f"Agent handler error: {str(e)}",
            extra={'error_type': type(e).__name__},
            exc_info=True
        )
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'X-Correlation-ID': correlation_id
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'correlation_id': correlation_id
            })
        }


def handle_schedule_meeting(body: Dict[str, Any], logger) -> Dict[str, Any]:
    """Handle meeting scheduling request with enhanced logging."""
    logger.info("Processing meeting scheduling request")
    
    # Extract request parameters
    attendees = body.get('attendees', [])
    duration = body.get('duration', 30)
    subject = body.get('subject', 'Meeting')
    
    # Log agent decision
    logger.log_agent_decision(
        decision_type=AgentDecisionType.SCHEDULING,
        rationale=f"Scheduling meeting '{subject}' for {len(attendees)} attendees with {duration} minute duration",
        inputs={
            'attendees': attendees,
            'duration': duration,
            'subject': subject
        },
        outputs={'status': 'processing'},
        confidence_score=0.8,
        alternatives_count=3
    )
    
    # Placeholder implementation
    return {
        'action': 'schedule_meeting',
        'status': 'completed',
        'meeting_id': 'placeholder_meeting_123',
        'message': 'Meeting scheduling request processed'
    }


def handle_resolve_conflict(body: Dict[str, Any], logger) -> Dict[str, Any]:
    """Handle conflict resolution request with enhanced logging."""
    logger.info("Processing conflict resolution request")
    
    conflict_id = body.get('conflict_id')
    resolution_strategy = body.get('strategy', 'reschedule')
    
    # Log agent decision
    logger.log_agent_decision(
        decision_type=AgentDecisionType.CONFLICT_RESOLUTION,
        rationale=f"Resolving conflict {conflict_id} using {resolution_strategy} strategy",
        inputs={
            'conflict_id': conflict_id,
            'strategy': resolution_strategy
        },
        outputs={'status': 'processing'},
        confidence_score=0.9,
        alternatives_count=2
    )
    
    # Placeholder implementation
    return {
        'action': 'resolve_conflict',
        'status': 'completed',
        'conflict_id': conflict_id,
        'resolution': resolution_strategy,
        'message': 'Conflict resolution completed'
    }


def handle_daily_learning(body: Dict[str, Any], logger) -> Dict[str, Any]:
    """Handle daily learning and optimization with enhanced logging."""
    logger.info("Processing daily learning request")
    
    # Log agent decision
    logger.log_agent_decision(
        decision_type=AgentDecisionType.PREFERENCE_EXTRACTION,
        rationale="Analyzing user behavior patterns for preference optimization",
        inputs={'timestamp': body.get('timestamp')},
        outputs={'status': 'processing'},
        confidence_score=0.7
    )
    
    # Placeholder implementation
    return {
        'action': 'daily_learning',
        'status': 'completed',
        'insights_generated': 5,
        'preferences_updated': 3,
        'message': 'Daily learning completed'
    }


def handle_intelligent_scheduling(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle intelligent scheduling requests."""
    try:
        # Extract required parameters
        task_type_str = body.get('task_type', 'schedule_meeting')
        request_data = body.get('request_data', {})
        user_id = body.get('user_id')
        user_preferences = body.get('user_preferences', {})
        strategy_str = body.get('planning_strategy', 'balanced')
        
        if not user_id:
            return {
                'error': 'Bad request',
                'message': 'user_id is required'
            }
        
        # Convert string parameters to enums
        try:
            task_type = TaskType(task_type_str)
            planning_strategy = PlanningStrategy(strategy_str)
        except ValueError as e:
            return {
                'error': 'Bad request',
                'message': f'Invalid parameter: {str(e)}'
            }
        
        # Execute intelligent scheduling
        result = orchestrator.execute_intelligent_scheduling(
            task_type=task_type,
            request_data=request_data,
            user_id=user_id,
            user_preferences=user_preferences,
            planning_strategy=planning_strategy
        )
        
        return result
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"AgentCore orchestrator error: {e}")
        return {
            'error': 'Processing error',
            'message': str(e)
        }


def handle_conflict_resolution(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle complex conflict resolution requests."""
    try:
        context_id = body.get('context_id')
        conflicts = body.get('conflicts', [])
        alternatives = body.get('alternatives', [])
        
        if not context_id:
            return {
                'error': 'Bad request',
                'message': 'context_id is required'
            }
        
        # Handle complex conflicts
        result = orchestrator.handle_complex_conflicts(
            context_id=context_id,
            conflicts=conflicts,
            available_alternatives=alternatives
        )
        
        return result
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"Conflict resolution error: {e}")
        return {
            'error': 'Processing error',
            'message': str(e)
        }


def handle_multi_step_optimization(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle multi-step operation optimization requests."""
    try:
        operations = body.get('operations', [])
        user_id = body.get('user_id')
        optimization_goals = body.get('optimization_goals', ['minimize_conflicts'])
        
        if not user_id or not operations:
            return {
                'error': 'Bad request',
                'message': 'user_id and operations are required'
            }
        
        # Optimize multi-step operation
        result = orchestrator.optimize_multi_step_operation(
            operations=operations,
            user_id=user_id,
            optimization_goals=optimization_goals
        )
        
        return result
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"Multi-step optimization error: {e}")
        return {
            'error': 'Processing error',
            'message': str(e)
        }


def handle_execution_status(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle execution status requests."""
    try:
        execution_id = query_params.get('execution_id')
        
        if not execution_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': 'execution_id query parameter is required'
                })
            }
        
        # Get execution status
        status = orchestrator.get_execution_status(execution_id)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(status)
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_availability_lookup(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle availability lookup requests."""
    try:
        from datetime import datetime
        
        # Extract required parameters
        user_id = body.get('user_id')
        start_date_str = body.get('start_date')
        end_date_str = body.get('end_date')
        connections = body.get('connections', [])
        preferences = body.get('preferences')
        
        if not all([user_id, start_date_str, end_date_str]):
            return {
                'error': 'Bad request',
                'message': 'user_id, start_date, and end_date are required'
            }
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError as e:
            return {
                'error': 'Bad request',
                'message': f'Invalid date format: {str(e)}'
            }
        
        # Extract optional parameters
        attendees = body.get('attendees')
        duration_minutes = body.get('duration_minutes', 30)
        buffer_minutes = body.get('buffer_minutes', 15)
        max_results = body.get('max_results', 10)
        time_preferences = body.get('time_preferences')
        working_hours_only = body.get('working_hours_only', True)
        
        # Execute availability lookup
        result = orchestrator.execute_availability_lookup(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            connections=connections,
            preferences=preferences,
            attendees=attendees,
            duration_minutes=duration_minutes,
            buffer_minutes=buffer_minutes,
            max_results=max_results,
            time_preferences=time_preferences,
            working_hours_only=working_hours_only
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Availability lookup error: {e}")
        return {
            'error': 'Internal server error',
            'message': str(e)
        }


def handle_orchestrator_stats() -> Dict[str, Any]:
    """Handle orchestrator statistics requests."""
    try:
        stats = orchestrator.get_orchestrator_stats()
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(stats)
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_health_check() -> Dict[str, Any]:
    """Handle health check requests for the agent handler."""
    try:
        # Perform comprehensive health check including Bedrock
        health_response = create_health_check_response('agent', include_dependencies=True)
        
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
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Health check failed',
                'message': str(e)
            })
        }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }