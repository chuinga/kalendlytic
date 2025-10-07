"""
AI Agent handler for Bedrock Claude integration and AgentCore orchestration.
Manages agent reasoning, tool execution, and decision-making workflows.
"""

import json
import logging
from typing import Dict, Any

from ..services.agentcore_orchestrator import (
    AgentCoreOrchestrator, AgentCoreOrchestratorError
)
from ..services.agentcore_router import TaskType
from ..services.agentcore_planner import PlanningStrategy

logger = logging.getLogger(__name__)

# Initialize AgentCore orchestrator
orchestrator = AgentCoreOrchestrator()


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for AI agent operations with AgentCore integration.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with agent execution result
    """
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Route based on path and method
        if path == '/agent/schedule' and http_method == 'POST':
            return handle_intelligent_scheduling(body)
        elif path == '/agent/conflicts' and http_method == 'POST':
            return handle_conflict_resolution(body)
        elif path == '/agent/optimize' and http_method == 'POST':
            return handle_multi_step_optimization(body)
        elif path == '/agent/status' and http_method == 'GET':
            return handle_execution_status(event.get('queryStringParameters', {}))
        elif path == '/agent/stats' and http_method == 'GET':
            return handle_orchestrator_stats()
        else:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Not found',
                    'message': f'Path {path} with method {http_method} not supported'
                })
            }
        
    except Exception as e:
        logger.error(f"Agent handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
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
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': 'user_id is required'
                })
            }
        
        # Convert string parameters to enums
        try:
            task_type = TaskType(task_type_str)
            planning_strategy = PlanningStrategy(strategy_str)
        except ValueError as e:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': f'Invalid parameter: {str(e)}'
                })
            }
        
        # Execute intelligent scheduling
        result = orchestrator.execute_intelligent_scheduling(
            task_type=task_type,
            request_data=request_data,
            user_id=user_id,
            user_preferences=user_preferences,
            planning_strategy=planning_strategy
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(result)
        }
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"AgentCore orchestrator error: {e}")
        return {
            'statusCode': 422,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Processing error',
                'message': str(e)
            })
        }


def handle_conflict_resolution(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle complex conflict resolution requests."""
    try:
        context_id = body.get('context_id')
        conflicts = body.get('conflicts', [])
        alternatives = body.get('alternatives', [])
        
        if not context_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': 'context_id is required'
                })
            }
        
        # Handle complex conflicts
        result = orchestrator.handle_complex_conflicts(
            context_id=context_id,
            conflicts=conflicts,
            available_alternatives=alternatives
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(result)
        }
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"Conflict resolution error: {e}")
        return {
            'statusCode': 422,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Processing error',
                'message': str(e)
            })
        }


def handle_multi_step_optimization(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle multi-step operation optimization requests."""
    try:
        operations = body.get('operations', [])
        user_id = body.get('user_id')
        optimization_goals = body.get('optimization_goals', ['minimize_conflicts'])
        
        if not user_id or not operations:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Bad request',
                    'message': 'user_id and operations are required'
                })
            }
        
        # Optimize multi-step operation
        result = orchestrator.optimize_multi_step_operation(
            operations=operations,
            user_id=user_id,
            optimization_goals=optimization_goals
        )
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(result)
        }
        
    except AgentCoreOrchestratorError as e:
        logger.error(f"Multi-step optimization error: {e}")
        return {
            'statusCode': 422,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': 'Processing error',
                'message': str(e)
            })
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


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for responses."""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }