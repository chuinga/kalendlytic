#!/usr/bin/env python3
"""
Example usage of the token refresh and error handling system.
Demonstrates how to use the new token refresh capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta

# Example: How to use the TokenRefreshService
async def example_token_refresh():
    """Example of using the token refresh service with error handling."""
    
    print("🔄 Token Refresh Service Example")
    print("=" * 40)
    
    # This would normally be initialized with real AWS resources
    # For this example, we'll show the interface
    
    print("1. Initialize TokenRefreshService")
    print("   service = TokenRefreshService()")
    
    print("\n2. Refresh token with exponential backoff")
    print("   result = await service.refresh_token_with_backoff('user123', 'google')")
    
    # Example result structure
    example_success_result = {
        'success': True,
        'status': 'success',
        'result': {
            'connection_id': 'user123#google',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'status': 'active'
        },
        'attempt_number': 1,
        'refresh_time': 1.23,
        'correlation_id': 'abc123-def456'
    }
    
    print(f"   Success Result: {json.dumps(example_success_result, indent=2)}")
    
    # Example failure result
    example_failure_result = {
        'success': False,
        'status': 'expired_refresh_token',
        'error_type': 'expired_refresh_token',
        'error_message': 'Refresh token has expired, re-authorization required',
        'attempt_number': 1,
        'correlation_id': 'abc123-def456',
        'requires_reauth': True
    }
    
    print(f"\n   Failure Result: {json.dumps(example_failure_result, indent=2)}")
    
    print("\n3. Get token health status")
    print("   health = await service.get_token_health_status('user123', 'google')")
    
    example_health_status = {
        'user_id': 'user123',
        'provider': 'google',
        'health_status': 'healthy',
        'health_score': 95.0,
        'metrics': {
            'consecutive_failures': 0,
            'total_refresh_attempts': 10,
            'success_rate': 95.0,
            'last_successful_refresh': datetime.utcnow().isoformat()
        },
        'recommendations': ['Token refresh health is good']
    }
    
    print(f"   Health Status: {json.dumps(example_health_status, indent=2)}")

async def example_monitoring_service():
    """Example of using the token monitoring service."""
    
    print("\n\n📊 Token Monitoring Service Example")
    print("=" * 40)
    
    print("1. Initialize TokenMonitoringService")
    print("   monitoring = TokenMonitoringService()")
    
    print("\n2. Collect metrics for all providers")
    print("   metrics = await monitoring.collect_metrics()")
    
    # Example metrics
    example_metrics = {
        'timestamp': datetime.utcnow().isoformat(),
        'provider': 'google',
        'total_users': 150,
        'active_connections': 145,
        'expired_tokens': 5,
        'failed_refreshes_24h': 8,
        'success_rate_24h': 94.7,
        'average_refresh_time': 1.8,
        'error_distribution': {
            'network_error': 3,
            'rate_limit_exceeded': 2,
            'provider_error': 3
        },
        'health_score': 92.5
    }
    
    print(f"   Example Metrics: {json.dumps(example_metrics, indent=2)}")
    
    print("\n3. Check for alerts")
    print("   alerts = await monitoring.check_alerts(metrics)")
    
    # Example alert
    example_alert = {
        'alert_id': 'success_rate_google_1234567890',
        'alert_type': 'low_success_rate',
        'severity': 'warning',
        'title': 'Warning: Low Success Rate for Google',
        'message': 'Token refresh success rate is 75.5% (threshold: 80.0%)',
        'provider': 'google',
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': {
            'success_rate': 75.5,
            'threshold': 80.0,
            'failed_refreshes': 15
        }
    }
    
    print(f"   Example Alert: {json.dumps(example_alert, indent=2)}")

def example_error_handling():
    """Example of using the enhanced error handling."""
    
    print("\n\n🚨 Error Handling Example")
    print("=" * 40)
    
    print("1. Token Error Classification")
    
    # Example error classifications
    error_examples = [
        {
            'scenario': 'HTTP 401 with invalid_grant',
            'classification': 'ExpiredRefreshTokenError',
            'retryable': False,
            'action': 'Require user re-authorization'
        },
        {
            'scenario': 'HTTP 429 rate limit',
            'classification': 'RateLimitExceededError',
            'retryable': True,
            'action': 'Wait and retry with exponential backoff'
        },
        {
            'scenario': 'Network timeout',
            'classification': 'NetworkError',
            'retryable': True,
            'action': 'Retry with exponential backoff'
        },
        {
            'scenario': 'HTTP 500 server error',
            'classification': 'ProviderError',
            'retryable': True,
            'action': 'Retry with exponential backoff'
        }
    ]
    
    for example in error_examples:
        print(f"\n   Scenario: {example['scenario']}")
        print(f"   Classification: {example['classification']}")
        print(f"   Retryable: {example['retryable']}")
        print(f"   Action: {example['action']}")
    
    print("\n2. Exponential Backoff Strategy")
    
    backoff_examples = [
        {'attempt': 1, 'delay': '1.0s', 'total_wait': '1.0s'},
        {'attempt': 2, 'delay': '2.1s', 'total_wait': '3.1s'},
        {'attempt': 3, 'delay': '4.3s', 'total_wait': '7.4s'},
        {'attempt': 4, 'delay': '8.7s', 'total_wait': '16.1s'},
        {'attempt': 5, 'delay': '17.2s', 'total_wait': '33.3s'}
    ]
    
    print("   Attempt | Delay  | Total Wait")
    print("   --------|--------|----------")
    for example in backoff_examples:
        print(f"   {example['attempt']:7} | {example['delay']:6} | {example['total_wait']:8}")

def example_maintenance_operations():
    """Example of maintenance operations."""
    
    print("\n\n🔧 Maintenance Operations Example")
    print("=" * 40)
    
    print("1. Scheduled Maintenance (via CloudWatch Events)")
    print("   - Runs every hour to check token health")
    print("   - Performs proactive token refresh for expiring tokens")
    print("   - Generates health reports and alerts")
    
    print("\n2. Manual Maintenance (via API)")
    print("   POST /api/maintenance")
    
    maintenance_request = {
        'operation': 'full_maintenance',  # or 'refresh_only', 'monitoring_only'
        'provider': 'google'  # optional, defaults to all providers
    }
    
    print(f"   Request: {json.dumps(maintenance_request, indent=2)}")
    
    maintenance_response = {
        'success': True,
        'correlation_id': 'maint_abc123',
        'operations_performed': [
            {
                'operation': 'collect_metrics',
                'success': True,
                'metrics_collected': 2,
                'providers': ['google', 'microsoft']
            },
            {
                'operation': 'check_alerts',
                'success': True,
                'alerts_generated': 1,
                'alert_types': ['low_success_rate']
            },
            {
                'operation': 'bulk_refresh',
                'success': True,
                'refresh_results': {
                    'total_connections': 25,
                    'successful_refreshes': 23,
                    'failed_refreshes': 2,
                    'skipped_connections': 0
                }
            }
        ],
        'health_report': {
            'overall_health': 'healthy',
            'overall_health_score': 89.5,
            'providers': {
                'google': {'health_score': 92.0, 'status': 'healthy'},
                'microsoft': {'health_score': 87.0, 'status': 'healthy'}
            }
        }
    }
    
    print(f"   Response: {json.dumps(maintenance_response, indent=2)}")

def example_integration_patterns():
    """Example integration patterns for the token refresh system."""
    
    print("\n\n🔗 Integration Patterns")
    print("=" * 40)
    
    print("1. Automatic Token Refresh in API Calls")
    print("""
   async def make_calendar_api_call(user_id, provider):
       try:
           # Get valid token (automatically refreshes if needed)
           token = oauth_manager.get_valid_access_token(provider, user_id)
           
           # Make API call
           response = await calendar_api.list_events(token)
           return response
           
       except ExpiredRefreshTokenError:
           # Refresh token expired, need re-auth
           return {'error': 'reauth_required'}
       except RateLimitExceededError as e:
           # Rate limited, retry after delay
           await asyncio.sleep(e.retry_after)
           return await make_calendar_api_call(user_id, provider)
       except NetworkError:
           # Network issue, retry with backoff
           return {'error': 'network_error', 'retryable': True}
    """)
    
    print("\n2. Proactive Health Monitoring")
    print("""
   # CloudWatch Event Rule (every hour)
   {
     "Rules": [{
       "Name": "TokenHealthCheck",
       "ScheduleExpression": "rate(1 hour)",
       "Targets": [{
         "Arn": "arn:aws:lambda:region:account:function:token-maintenance",
         "Input": "{\\"operation\\": \\"full_maintenance\\"}"
       }]
     }]
   }
    """)
    
    print("\n3. Alert Notifications")
    print("""
   # SNS Topic Configuration
   Critical Alerts -> PagerDuty/Slack
   Warning Alerts -> Email/Slack
   Info Alerts -> CloudWatch Dashboard
   
   # CloudWatch Dashboard Metrics
   - Token refresh success rate by provider
   - Average refresh time
   - Number of expired tokens
   - Health score trends
    """)

async def main():
    """Run all examples."""
    print("🚀 Token Refresh and Error Handling System")
    print("=" * 50)
    print("This system provides comprehensive token management with:")
    print("• Exponential backoff retry logic")
    print("• Advanced error classification and handling")
    print("• Proactive monitoring and alerting")
    print("• Health scoring and recommendations")
    print("• Bulk maintenance operations")
    
    await example_token_refresh()
    await example_monitoring_service()
    example_error_handling()
    example_maintenance_operations()
    example_integration_patterns()
    
    print("\n\n✅ Implementation Complete!")
    print("=" * 50)
    print("Key Features Implemented:")
    print("✓ Automatic token refresh with exponential backoff")
    print("✓ Comprehensive error handling for expired, invalid, and revoked tokens")
    print("✓ Monitoring and alerting for token refresh failures")
    print("✓ Health scoring and recommendations")
    print("✓ Rate limiting protection")
    print("✓ Bulk maintenance operations")
    print("✓ CloudWatch integration for metrics and alerts")
    print("✓ SNS notifications for critical issues")
    
    print("\nNext Steps:")
    print("1. Deploy the Lambda functions for maintenance operations")
    print("2. Configure CloudWatch Events for scheduled monitoring")
    print("3. Set up SNS topics for alert notifications")
    print("4. Update existing OAuth services to use new error handling")
    print("5. Test with real OAuth providers in development environment")

if __name__ == '__main__':
    asyncio.run(main())