"""
Health check utilities for Lambda functions.
Provides standardized health check functionality across all handlers.
"""

import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

from .logging import create_agent_logger

logger = create_agent_logger(__name__)


class HealthChecker:
    """Centralized health check functionality for Lambda functions."""
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.bedrock = boto3.client('bedrock')
        self.secrets_manager = boto3.client('secretsmanager')
        self.cloudwatch = boto3.client('cloudwatch')
        
    def perform_health_check(self, component_name: str, include_dependencies: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive health check for a Lambda function.
        
        Args:
            component_name: Name of the component being checked
            include_dependencies: Whether to check external dependencies
            
        Returns:
            Health check results
        """
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'component': component_name,
            'status': 'healthy',
            'checks': {},
            'version': '1.0.0'
        }
        
        try:
            # Basic function health
            health_status['checks']['function'] = self._check_function_health()
            
            if include_dependencies:
                # Check DynamoDB connectivity
                health_status['checks']['dynamodb'] = self._check_dynamodb()
                
                # Check Bedrock connectivity (for agent-related functions)
                if component_name in ['agent', 'calendar']:
                    health_status['checks']['bedrock'] = self._check_bedrock()
                
                # Check Secrets Manager connectivity
                health_status['checks']['secrets_manager'] = self._check_secrets_manager()
            
            # Determine overall health
            failed_checks = [
                name for name, check in health_status['checks'].items() 
                if not check.get('healthy', False)
            ]
            
            if failed_checks:
                health_status['status'] = 'unhealthy'
                health_status['failed_checks'] = failed_checks
            
            # Publish health metrics
            self._publish_health_metrics(component_name, health_status)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check error for {component_name}: {str(e)}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'component': component_name,
                'status': 'error',
                'error': str(e)
            }
    
    def _check_function_health(self) -> Dict[str, Any]:
        """Check basic Lambda function health."""
        try:
            # Basic memory and execution environment check
            import psutil
            import os
            
            memory_info = psutil.virtual_memory()
            
            return {
                'healthy': True,
                'memory_available_mb': round(memory_info.available / 1024 / 1024, 2),
                'memory_percent_used': memory_info.percent,
                'python_version': os.environ.get('AWS_EXECUTION_ENV', 'unknown'),
                'region': os.environ.get('AWS_REGION', 'unknown')
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_dynamodb(self) -> Dict[str, Any]:
        """Check DynamoDB connectivity and basic operations."""
        try:
            start_time = time.time()
            
            # Try to describe a table to test connectivity
            response = self.dynamodb.describe_table(TableName='meeting-agent-users')
            response_time = (time.time() - start_time) * 1000
            
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'table_status': response['Table']['TableStatus'],
                'item_count': response['Table'].get('ItemCount', 0)
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                'healthy': False,
                'error': f"DynamoDB error: {error_code}",
                'error_message': e.response['Error']['Message']
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_bedrock(self) -> Dict[str, Any]:
        """Check Bedrock connectivity."""
        try:
            start_time = time.time()
            
            # List foundation models to test connectivity
            response = self.bedrock.list_foundation_models(byProvider='anthropic')
            response_time = (time.time() - start_time) * 1000
            
            models = response.get('modelSummaries', [])
            claude_models = [
                model for model in models 
                if 'claude' in model.get('modelName', '').lower()
            ]
            
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'total_models_available': len(models),
                'claude_models_available': len(claude_models),
                'claude_models': [model['modelId'] for model in claude_models[:3]]  # First 3
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                'healthy': False,
                'error': f"Bedrock error: {error_code}",
                'error_message': e.response['Error']['Message']
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _check_secrets_manager(self) -> Dict[str, Any]:
        """Check Secrets Manager connectivity."""
        try:
            start_time = time.time()
            
            # List secrets to test connectivity (limited to 1 for performance)
            response = self.secrets_manager.list_secrets(MaxResults=1)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'secrets_accessible': len(response.get('SecretList', []))
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                'healthy': False,
                'error': f"Secrets Manager error: {error_code}",
                'error_message': e.response['Error']['Message']
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _publish_health_metrics(self, component_name: str, health_status: Dict[str, Any]) -> None:
        """Publish health check metrics to CloudWatch."""
        try:
            # Overall component health
            self.cloudwatch.put_metric_data(
                Namespace='MeetingAgent/Health',
                MetricData=[
                    {
                        'MetricName': f'{component_name.title()}Health',
                        'Value': 1 if health_status['status'] == 'healthy' else 0,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {
                                'Name': 'Component',
                                'Value': component_name
                            }
                        ]
                    }
                ]
            )
            
            # Individual check metrics
            for check_name, check_result in health_status.get('checks', {}).items():
                if isinstance(check_result, dict):
                    # Health status
                    self.cloudwatch.put_metric_data(
                        Namespace='MeetingAgent/Health',
                        MetricData=[
                            {
                                'MetricName': f'{check_name.title()}Health',
                                'Value': 1 if check_result.get('healthy', False) else 0,
                                'Unit': 'Count',
                                'Timestamp': datetime.utcnow(),
                                'Dimensions': [
                                    {
                                        'Name': 'Component',
                                        'Value': component_name
                                    },
                                    {
                                        'Name': 'CheckType',
                                        'Value': check_name
                                    }
                                ]
                            }
                        ]
                    )
                    
                    # Response time metrics
                    if 'response_time_ms' in check_result:
                        self.cloudwatch.put_metric_data(
                            Namespace='MeetingAgent/Performance',
                            MetricData=[
                                {
                                    'MetricName': f'{check_name.title()}ResponseTime',
                                    'Value': check_result['response_time_ms'],
                                    'Unit': 'Milliseconds',
                                    'Timestamp': datetime.utcnow(),
                                    'Dimensions': [
                                        {
                                            'Name': 'Component',
                                            'Value': component_name
                                        }
                                    ]
                                }
                            ]
                        )
        except Exception as e:
            logger.warning(f"Failed to publish health metrics for {component_name}: {str(e)}")


def create_health_check_response(component_name: str, include_dependencies: bool = True) -> Dict[str, Any]:
    """
    Create a standardized health check response for Lambda functions.
    
    Args:
        component_name: Name of the component being checked
        include_dependencies: Whether to check external dependencies
        
    Returns:
        API Gateway response with health check results
    """
    health_checker = HealthChecker()
    health_status = health_checker.perform_health_check(component_name, include_dependencies)
    
    status_code = 200
    if health_status['status'] == 'unhealthy':
        status_code = 503
    elif health_status['status'] == 'error':
        status_code = 500
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Health-Check-Version': '1.0.0'
        },
        'body': json.dumps(health_status, default=str)
    }


def publish_bedrock_usage_metrics(
    input_tokens: int,
    output_tokens: int,
    model_id: str,
    estimated_cost_usd: float,
    operation_type: str = 'inference'
) -> None:
    """
    Publish Bedrock usage and cost metrics to CloudWatch.
    
    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        model_id: Bedrock model identifier
        estimated_cost_usd: Estimated cost in USD
        operation_type: Type of operation (inference, agent, etc.)
    """
    try:
        cloudwatch = boto3.client('cloudwatch')
        timestamp = datetime.utcnow()
        
        # Token usage metrics
        cloudwatch.put_metric_data(
            Namespace='MeetingAgent/Bedrock',
            MetricData=[
                {
                    'MetricName': 'InputTokens',
                    'Value': input_tokens,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id},
                        {'Name': 'OperationType', 'Value': operation_type}
                    ]
                },
                {
                    'MetricName': 'OutputTokens',
                    'Value': output_tokens,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id},
                        {'Name': 'OperationType', 'Value': operation_type}
                    ]
                },
                {
                    'MetricName': 'TotalTokens',
                    'Value': input_tokens + output_tokens,
                    'Unit': 'Count',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id},
                        {'Name': 'OperationType', 'Value': operation_type}
                    ]
                }
            ]
        )
        
        # Cost metrics
        cloudwatch.put_metric_data(
            Namespace='MeetingAgent/Bedrock',
            MetricData=[
                {
                    'MetricName': 'EstimatedCostUSD',
                    'Value': estimated_cost_usd,
                    'Unit': 'None',
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'ModelId', 'Value': model_id},
                        {'Name': 'OperationType', 'Value': operation_type}
                    ]
                }
            ]
        )
        
        logger.info(
            f"Published Bedrock usage metrics: {input_tokens} input tokens, "
            f"{output_tokens} output tokens, ${estimated_cost_usd:.6f} estimated cost"
        )
        
    except Exception as e:
        logger.warning(f"Failed to publish Bedrock usage metrics: {str(e)}")