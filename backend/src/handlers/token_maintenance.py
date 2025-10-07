"""
Lambda handler for scheduled token maintenance operations.
Performs proactive token refresh, monitoring, and alerting.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

from ..services.token_refresh_service import TokenRefreshService
from ..services.token_monitoring import TokenMonitoringService
from ..utils.logging import setup_logger, get_correlation_id

logger = setup_logger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for token maintenance operations.
    
    Args:
        event: Lambda event data
        context: Lambda context
        
    Returns:
        Response dictionary
    """
    correlation_id = get_correlation_id()
    
    logger.info(
        "Starting token maintenance operation",
        extra={
            'correlation_id': correlation_id,
            'event_source': event.get('source', 'unknown'),
            'function_name': context.function_name if context else 'local'
        }
    )
    
    try:
        # Run async maintenance operations
        result = asyncio.run(run_maintenance_operations(event, correlation_id))
        
        logger.info(
            "Token maintenance completed successfully",
            extra={
                'correlation_id': correlation_id,
                'result_summary': result
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'correlation_id': correlation_id,
                'result': result
            })
        }
        
    except Exception as e:
        logger.error(
            f"Token maintenance failed: {str(e)}",
            extra={
                'correlation_id': correlation_id,
                'error': str(e)
            },
            exc_info=True
        )
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'correlation_id': correlation_id,
                'error': str(e)
            })
        }

async def run_maintenance_operations(event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """
    Run all token maintenance operations.
    
    Args:
        event: Lambda event data
        correlation_id: Correlation ID for tracking
        
    Returns:
        Summary of maintenance operations
    """
    refresh_service = TokenRefreshService()
    monitoring_service = TokenMonitoringService()
    
    operation_type = event.get('operation', 'full_maintenance')
    provider_filter = event.get('provider')
    
    results = {
        'operation_type': operation_type,
        'correlation_id': correlation_id,
        'timestamp': datetime.utcnow().isoformat(),
        'operations_performed': []
    }
    
    try:
        # 1. Collect monitoring metrics
        if operation_type in ['full_maintenance', 'monitoring_only']:
            logger.info("Collecting monitoring metrics")
            
            metrics = await monitoring_service.collect_metrics(provider_filter)
            
            results['operations_performed'].append({
                'operation': 'collect_metrics',
                'success': True,
                'metrics_collected': len(metrics),
                'providers': [m.provider for m in metrics]
            })
            
            # 2. Check for alerts
            logger.info("Checking for alerts")
            
            alerts = await monitoring_service.check_alerts(metrics)
            
            results['operations_performed'].append({
                'operation': 'check_alerts',
                'success': True,
                'alerts_generated': len(alerts),
                'alert_types': [a.alert_type.value for a in alerts]
            })
            
            # Store metrics summary in results
            results['metrics_summary'] = [
                {
                    'provider': m.provider,
                    'total_users': m.total_users,
                    'active_connections': m.active_connections,
                    'expired_tokens': m.expired_tokens,
                    'success_rate_24h': m.success_rate_24h,
                    'health_score': m.health_score
                }
                for m in metrics
            ]
            
            results['alerts_summary'] = [
                {
                    'alert_type': a.alert_type.value,
                    'severity': a.severity.value,
                    'provider': a.provider,
                    'title': a.title
                }
                for a in alerts
            ]
        
        # 3. Perform bulk token refresh (if requested or if high number of expired tokens)
        if operation_type in ['full_maintenance', 'refresh_only']:
            should_refresh = True
            
            # Check if refresh is needed based on metrics
            if operation_type == 'full_maintenance' and 'metrics_summary' in results:
                total_expired = sum(m['expired_tokens'] for m in results['metrics_summary'])
                total_users = sum(m['total_users'] for m in results['metrics_summary'])
                
                if total_users > 0:
                    expired_percentage = (total_expired / total_users) * 100
                    should_refresh = expired_percentage > 5  # Only refresh if >5% tokens expired
                else:
                    should_refresh = False
            
            if should_refresh:
                logger.info("Performing bulk token refresh")
                
                refresh_results = await refresh_service.bulk_refresh_tokens(provider_filter)
                
                results['operations_performed'].append({
                    'operation': 'bulk_refresh',
                    'success': True,
                    'refresh_results': refresh_results
                })
            else:
                logger.info("Skipping bulk refresh - not needed")
                results['operations_performed'].append({
                    'operation': 'bulk_refresh',
                    'success': True,
                    'skipped': True,
                    'reason': 'Low number of expired tokens'
                })
        
        # 4. Generate health report
        if operation_type in ['full_maintenance', 'health_report']:
            logger.info("Generating health report")
            
            health_report = await generate_health_report(monitoring_service, provider_filter)
            
            results['operations_performed'].append({
                'operation': 'health_report',
                'success': True,
                'report_generated': True
            })
            
            results['health_report'] = health_report
        
        results['success'] = True
        return results
        
    except Exception as e:
        logger.error(f"Maintenance operation failed: {str(e)}")
        results['success'] = False
        results['error'] = str(e)
        return results

async def generate_health_report(monitoring_service: TokenMonitoringService, 
                               provider_filter: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive health report for token operations.
    
    Args:
        monitoring_service: Token monitoring service instance
        provider_filter: Optional provider filter
        
    Returns:
        Health report dictionary
    """
    try:
        providers = [provider_filter] if provider_filter else ['google', 'microsoft']
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'providers': {},
            'overall_health': 'unknown',
            'recommendations': []
        }
        
        total_health_score = 0
        provider_count = 0
        
        for provider in providers:
            try:
                # Get recent metrics
                metrics = await monitoring_service._collect_provider_metrics(provider)
                
                # Get recent alerts
                alerts = await monitoring_service.get_alert_history(provider, hours=24)
                
                provider_report = {
                    'health_score': metrics.health_score,
                    'total_users': metrics.total_users,
                    'active_connections': metrics.active_connections,
                    'expired_tokens': metrics.expired_tokens,
                    'success_rate_24h': metrics.success_rate_24h,
                    'failed_refreshes_24h': metrics.failed_refreshes_24h,
                    'average_refresh_time': metrics.average_refresh_time,
                    'error_distribution': metrics.error_distribution,
                    'recent_alerts': len(alerts),
                    'critical_alerts': len([a for a in alerts if a.severity.value == 'critical']),
                    'status': 'healthy' if metrics.health_score >= 80 else 
                             'warning' if metrics.health_score >= 60 else 
                             'degraded' if metrics.health_score >= 40 else 'critical'
                }
                
                report['providers'][provider] = provider_report
                total_health_score += metrics.health_score
                provider_count += 1
                
                # Generate provider-specific recommendations
                if metrics.health_score < 70:
                    report['recommendations'].append(
                        f"Review {provider} OAuth configuration and connection health"
                    )
                
                if metrics.expired_tokens > 5:
                    report['recommendations'].append(
                        f"Consider proactive token refresh for {provider} users"
                    )
                
                if metrics.success_rate_24h < 90:
                    report['recommendations'].append(
                        f"Investigate {provider} token refresh failures"
                    )
                
            except Exception as e:
                logger.error(f"Failed to generate report for provider {provider}: {str(e)}")
                report['providers'][provider] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate overall health
        if provider_count > 0:
            overall_score = total_health_score / provider_count
            if overall_score >= 80:
                report['overall_health'] = 'healthy'
            elif overall_score >= 60:
                report['overall_health'] = 'warning'
            elif overall_score >= 40:
                report['overall_health'] = 'degraded'
            else:
                report['overall_health'] = 'critical'
            
            report['overall_health_score'] = overall_score
        
        # Add general recommendations
        if not report['recommendations']:
            report['recommendations'].append("Token health is good across all providers")
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate health report: {str(e)}")
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'error': str(e),
            'overall_health': 'error'
        }

# Handler for CloudWatch Events (EventBridge)
def scheduled_maintenance_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler specifically for scheduled maintenance via CloudWatch Events.
    
    Args:
        event: CloudWatch Events event
        context: Lambda context
        
    Returns:
        Response dictionary
    """
    # Add scheduled maintenance specific logic
    maintenance_event = {
        'operation': 'full_maintenance',
        'source': 'cloudwatch_events',
        'scheduled': True
    }
    
    return lambda_handler(maintenance_event, context)

# Handler for manual operations via API Gateway
def manual_maintenance_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler for manual maintenance operations via API Gateway.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        maintenance_event = {
            'operation': body.get('operation', 'full_maintenance'),
            'provider': body.get('provider'),
            'source': 'api_gateway',
            'manual': True
        }
        
        result = lambda_handler(maintenance_event, context)
        
        return {
            'statusCode': result['statusCode'],
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': result['body']
        }
        
    except Exception as e:
        logger.error(f"Manual maintenance handler failed: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }