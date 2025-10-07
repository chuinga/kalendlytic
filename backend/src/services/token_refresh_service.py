"""
Advanced token refresh service with exponential backoff and comprehensive error handling.
Provides automatic token refresh, monitoring, and alerting capabilities.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

import boto3
from botocore.exceptions import ClientError

from .oauth_manager import UnifiedOAuthManager, OAuthProvider
from ..utils.aws_clients import get_dynamodb_resource, get_secrets_client
from ..utils.logging import setup_logger, get_correlation_id, redact_pii

logger = setup_logger(__name__)

class TokenRefreshStatus(Enum):
    """Token refresh operation status."""
    SUCCESS = "success"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"
    EXPIRED_REFRESH_TOKEN = "expired_refresh_token"
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMITED = "rate_limited"

class TokenErrorType(Enum):
    """Types of token-related errors."""
    EXPIRED_ACCESS_TOKEN = "expired_access_token"
    EXPIRED_REFRESH_TOKEN = "expired_refresh_token"
    INVALID_TOKEN = "invalid_token"
    REVOKED_TOKEN = "revoked_token"
    INSUFFICIENT_SCOPE = "insufficient_scope"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    NETWORK_ERROR = "network_error"
    PROVIDER_ERROR = "provider_error"

@dataclass
class RefreshAttempt:
    """Record of a token refresh attempt."""
    timestamp: str
    attempt_number: int
    status: TokenRefreshStatus
    error_type: Optional[TokenErrorType]
    error_message: Optional[str]
    backoff_delay: float
    correlation_id: str

@dataclass
class TokenHealthMetrics:
    """Token health and performance metrics."""
    user_id: str
    provider: str
    last_successful_refresh: Optional[str]
    consecutive_failures: int
    total_refresh_attempts: int
    success_rate: float
    average_refresh_time: float
    last_error: Optional[str]
    health_score: float  # 0-100 scale

class TokenRefreshService:
    """Advanced token refresh service with exponential backoff and monitoring."""
    
    def __init__(self):
        self.oauth_manager = UnifiedOAuthManager()
        self.dynamodb = get_dynamodb_resource()
        self.secrets_client = get_secrets_client()
        self.connections_table = self.dynamodb.Table('Connections')
        self.metrics_table = self.dynamodb.Table('TokenMetrics')
        
        # Exponential backoff configuration
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 300.0  # Maximum delay (5 minutes)
        self.max_retries = 5
        self.backoff_multiplier = 2.0
        self.jitter_factor = 0.1
        
        # Rate limiting configuration
        self.rate_limit_window = 3600  # 1 hour in seconds
        self.max_refresh_attempts_per_hour = 10
        
    def _calculate_backoff_delay(self, attempt: int, base_delay: float = None) -> float:
        """
        Calculate exponential backoff delay with jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay override
            
        Returns:
            Delay in seconds
        """
        if base_delay is None:
            base_delay = self.base_delay
            
        # Exponential backoff: base_delay * (multiplier ^ attempt)
        delay = base_delay * (self.backoff_multiplier ** attempt)
        
        # Cap at maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * (0.5 - hash(str(time.time())) % 100 / 100)
        delay += jitter
        
        return max(0, delay)
    
    def _is_rate_limited(self, user_id: str, provider: str) -> bool:
        """
        Check if user/provider combination is rate limited.
        
        Args:
            user_id: User identifier
            provider: OAuth provider
            
        Returns:
            True if rate limited
        """
        try:
            # Get recent refresh attempts
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=self.rate_limit_window)
            
            response = self.metrics_table.query(
                KeyConditionExpression='pk = :pk AND sk BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':pk': f"refresh_attempts#{user_id}#{provider}",
                    ':start': window_start.isoformat(),
                    ':end': current_time.isoformat()
                }
            )
            
            attempt_count = response['Count']
            
            if attempt_count >= self.max_refresh_attempts_per_hour:
                logger.warning(
                    f"Rate limit exceeded for user {user_id}, provider {provider}",
                    extra={
                        'user_id': user_id,
                        'provider': provider,
                        'attempt_count': attempt_count,
                        'rate_limit': self.max_refresh_attempts_per_hour
                    }
                )
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {str(e)}")
            return False
    
    def _record_refresh_attempt(self, user_id: str, provider: str, 
                              attempt: RefreshAttempt) -> None:
        """
        Record a token refresh attempt for monitoring and rate limiting.
        
        Args:
            user_id: User identifier
            provider: OAuth provider
            attempt: Refresh attempt details
        """
        try:
            self.metrics_table.put_item(
                Item={
                    'pk': f"refresh_attempts#{user_id}#{provider}",
                    'sk': attempt.timestamp,
                    'user_id': user_id,
                    'provider': provider,
                    'attempt_data': asdict(attempt),
                    'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())
                }
            )
        except Exception as e:
            logger.error(f"Failed to record refresh attempt: {str(e)}")
    
    def _classify_error(self, error: Exception, provider: str) -> Tuple[TokenErrorType, bool]:
        """
        Classify token refresh error and determine if it's retryable.
        
        Args:
            error: Exception that occurred
            provider: OAuth provider
            
        Returns:
            Tuple of (error_type, is_retryable)
        """
        error_str = str(error).lower()
        
        # Check for specific error patterns
        if 'invalid_grant' in error_str or 'refresh token' in error_str:
            return TokenErrorType.EXPIRED_REFRESH_TOKEN, False
        elif 'invalid_token' in error_str or 'unauthorized' in error_str:
            return TokenErrorType.INVALID_TOKEN, False
        elif 'revoked' in error_str:
            return TokenErrorType.REVOKED_TOKEN, False
        elif 'insufficient_scope' in error_str or 'scope' in error_str:
            return TokenErrorType.INSUFFICIENT_SCOPE, False
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            return TokenErrorType.RATE_LIMIT_EXCEEDED, True
        elif 'network' in error_str or 'timeout' in error_str or 'connection' in error_str:
            return TokenErrorType.NETWORK_ERROR, True
        else:
            return TokenErrorType.PROVIDER_ERROR, True
    
    async def refresh_token_with_backoff(self, user_id: str, provider: str,
                                       correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh token with exponential backoff and comprehensive error handling.
        
        Args:
            user_id: User identifier
            provider: OAuth provider
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Dictionary containing refresh result and metadata
        """
        if correlation_id is None:
            correlation_id = get_correlation_id()
            
        logger.info(
            f"Starting token refresh for user {user_id}, provider {provider}",
            extra={'user_id': user_id, 'provider': provider, 'correlation_id': correlation_id}
        )
        
        # Check rate limiting
        if self._is_rate_limited(user_id, provider):
            error_result = {
                'success': False,
                'status': TokenRefreshStatus.RATE_LIMITED,
                'error_type': TokenErrorType.RATE_LIMIT_EXCEEDED,
                'error_message': 'Rate limit exceeded for token refresh',
                'correlation_id': correlation_id,
                'retry_after': self.rate_limit_window
            }
            
            # Record rate limit hit
            attempt = RefreshAttempt(
                timestamp=datetime.utcnow().isoformat(),
                attempt_number=0,
                status=TokenRefreshStatus.RATE_LIMITED,
                error_type=TokenErrorType.RATE_LIMIT_EXCEEDED,
                error_message='Rate limit exceeded',
                backoff_delay=0,
                correlation_id=correlation_id
            )
            self._record_refresh_attempt(user_id, provider, attempt)
            
            return error_result
        
        last_error = None
        
        for attempt_num in range(self.max_retries):
            start_time = time.time()
            
            try:
                # Attempt token refresh
                result = self.oauth_manager.refresh_access_token(provider, user_id)
                
                # Success - record metrics and return
                refresh_time = time.time() - start_time
                
                attempt = RefreshAttempt(
                    timestamp=datetime.utcnow().isoformat(),
                    attempt_number=attempt_num + 1,
                    status=TokenRefreshStatus.SUCCESS,
                    error_type=None,
                    error_message=None,
                    backoff_delay=0,
                    correlation_id=correlation_id
                )
                self._record_refresh_attempt(user_id, provider, attempt)
                
                # Update health metrics
                await self._update_health_metrics(user_id, provider, True, refresh_time)
                
                logger.info(
                    f"Token refresh successful for user {user_id}, provider {provider}",
                    extra={
                        'user_id': user_id,
                        'provider': provider,
                        'correlation_id': correlation_id,
                        'attempt_number': attempt_num + 1,
                        'refresh_time': refresh_time
                    }
                )
                
                return {
                    'success': True,
                    'status': TokenRefreshStatus.SUCCESS,
                    'result': result,
                    'attempt_number': attempt_num + 1,
                    'refresh_time': refresh_time,
                    'correlation_id': correlation_id
                }
                
            except Exception as e:
                last_error = e
                error_type, is_retryable = self._classify_error(e, provider)
                
                logger.warning(
                    f"Token refresh attempt {attempt_num + 1} failed: {str(e)}",
                    extra={
                        'user_id': user_id,
                        'provider': provider,
                        'correlation_id': correlation_id,
                        'attempt_number': attempt_num + 1,
                        'error_type': error_type.value,
                        'is_retryable': is_retryable
                    }
                )
                
                # If error is not retryable, fail immediately
                if not is_retryable:
                    status = TokenRefreshStatus.FAILED_PERMANENT
                    if error_type == TokenErrorType.EXPIRED_REFRESH_TOKEN:
                        status = TokenRefreshStatus.EXPIRED_REFRESH_TOKEN
                    elif error_type == TokenErrorType.INVALID_TOKEN:
                        status = TokenRefreshStatus.INVALID_CREDENTIALS
                    
                    attempt = RefreshAttempt(
                        timestamp=datetime.utcnow().isoformat(),
                        attempt_number=attempt_num + 1,
                        status=status,
                        error_type=error_type,
                        error_message=str(e),
                        backoff_delay=0,
                        correlation_id=correlation_id
                    )
                    self._record_refresh_attempt(user_id, provider, attempt)
                    
                    # Update health metrics
                    await self._update_health_metrics(user_id, provider, False, 0)
                    
                    return {
                        'success': False,
                        'status': status,
                        'error_type': error_type,
                        'error_message': str(e),
                        'attempt_number': attempt_num + 1,
                        'correlation_id': correlation_id,
                        'requires_reauth': error_type in [
                            TokenErrorType.EXPIRED_REFRESH_TOKEN,
                            TokenErrorType.REVOKED_TOKEN,
                            TokenErrorType.INVALID_TOKEN
                        ]
                    }
                
                # Calculate backoff delay for retryable errors
                if attempt_num < self.max_retries - 1:  # Don't delay after last attempt
                    delay = self._calculate_backoff_delay(attempt_num)
                    
                    attempt = RefreshAttempt(
                        timestamp=datetime.utcnow().isoformat(),
                        attempt_number=attempt_num + 1,
                        status=TokenRefreshStatus.FAILED_RETRYABLE,
                        error_type=error_type,
                        error_message=str(e),
                        backoff_delay=delay,
                        correlation_id=correlation_id
                    )
                    self._record_refresh_attempt(user_id, provider, attempt)
                    
                    logger.info(
                        f"Retrying token refresh in {delay:.2f} seconds",
                        extra={
                            'user_id': user_id,
                            'provider': provider,
                            'correlation_id': correlation_id,
                            'delay': delay,
                            'next_attempt': attempt_num + 2
                        }
                    )
                    
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        attempt = RefreshAttempt(
            timestamp=datetime.utcnow().isoformat(),
            attempt_number=self.max_retries,
            status=TokenRefreshStatus.FAILED_RETRYABLE,
            error_type=self._classify_error(last_error, provider)[0],
            error_message=str(last_error),
            backoff_delay=0,
            correlation_id=correlation_id
        )
        self._record_refresh_attempt(user_id, provider, attempt)
        
        # Update health metrics
        await self._update_health_metrics(user_id, provider, False, 0)
        
        logger.error(
            f"Token refresh failed after {self.max_retries} attempts",
            extra={
                'user_id': user_id,
                'provider': provider,
                'correlation_id': correlation_id,
                'final_error': str(last_error)
            }
        )
        
        return {
            'success': False,
            'status': TokenRefreshStatus.FAILED_RETRYABLE,
            'error_type': self._classify_error(last_error, provider)[0],
            'error_message': str(last_error),
            'attempt_number': self.max_retries,
            'correlation_id': correlation_id
        }
    
    async def _update_health_metrics(self, user_id: str, provider: str, 
                                   success: bool, refresh_time: float) -> None:
        """
        Update token health metrics for monitoring and alerting.
        
        Args:
            user_id: User identifier
            provider: OAuth provider
            success: Whether the refresh was successful
            refresh_time: Time taken for refresh operation
        """
        try:
            metrics_key = f"health#{user_id}#{provider}"
            current_time = datetime.utcnow().isoformat()
            
            # Get existing metrics
            try:
                response = self.metrics_table.get_item(Key={'pk': metrics_key, 'sk': 'current'})
                existing_metrics = response.get('Item', {}).get('metrics', {})
            except:
                existing_metrics = {}
            
            # Calculate new metrics
            total_attempts = existing_metrics.get('total_refresh_attempts', 0) + 1
            
            if success:
                consecutive_failures = 0
                last_successful_refresh = current_time
                # Update running average of refresh time
                current_avg = existing_metrics.get('average_refresh_time', 0)
                new_avg = ((current_avg * (total_attempts - 1)) + refresh_time) / total_attempts
            else:
                consecutive_failures = existing_metrics.get('consecutive_failures', 0) + 1
                last_successful_refresh = existing_metrics.get('last_successful_refresh')
                new_avg = existing_metrics.get('average_refresh_time', 0)
            
            # Calculate success rate
            successful_attempts = existing_metrics.get('successful_attempts', 0)
            if success:
                successful_attempts += 1
            success_rate = (successful_attempts / total_attempts) * 100
            
            # Calculate health score (0-100)
            health_score = self._calculate_health_score(
                success_rate, consecutive_failures, last_successful_refresh
            )
            
            # Create updated metrics
            updated_metrics = TokenHealthMetrics(
                user_id=user_id,
                provider=provider,
                last_successful_refresh=last_successful_refresh,
                consecutive_failures=consecutive_failures,
                total_refresh_attempts=total_attempts,
                success_rate=success_rate,
                average_refresh_time=new_avg,
                last_error=None if success else existing_metrics.get('last_error'),
                health_score=health_score
            )
            
            # Store updated metrics
            self.metrics_table.put_item(
                Item={
                    'pk': metrics_key,
                    'sk': 'current',
                    'user_id': user_id,
                    'provider': provider,
                    'metrics': asdict(updated_metrics),
                    'successful_attempts': successful_attempts,
                    'updated_at': current_time
                }
            )
            
            # Check if alerting is needed
            await self._check_health_alerts(updated_metrics)
            
        except Exception as e:
            logger.error(f"Failed to update health metrics: {str(e)}")
    
    def _calculate_health_score(self, success_rate: float, consecutive_failures: int,
                              last_successful_refresh: Optional[str]) -> float:
        """
        Calculate overall health score for token refresh operations.
        
        Args:
            success_rate: Success rate percentage (0-100)
            consecutive_failures: Number of consecutive failures
            last_successful_refresh: Timestamp of last successful refresh
            
        Returns:
            Health score (0-100)
        """
        score = success_rate
        
        # Penalize consecutive failures
        failure_penalty = min(consecutive_failures * 10, 50)
        score -= failure_penalty
        
        # Penalize stale successful refreshes
        if last_successful_refresh:
            try:
                last_success = datetime.fromisoformat(last_successful_refresh)
                hours_since_success = (datetime.utcnow() - last_success).total_seconds() / 3600
                
                if hours_since_success > 24:  # More than 24 hours
                    staleness_penalty = min((hours_since_success - 24) * 2, 30)
                    score -= staleness_penalty
            except:
                pass
        else:
            score -= 20  # No successful refresh recorded
        
        return max(0, min(100, score))
    
    async def _check_health_alerts(self, metrics: TokenHealthMetrics) -> None:
        """
        Check if health metrics warrant alerting and send notifications.
        
        Args:
            metrics: Current health metrics
        """
        try:
            alerts = []
            
            # Critical: Multiple consecutive failures
            if metrics.consecutive_failures >= 3:
                alerts.append({
                    'severity': 'CRITICAL',
                    'type': 'consecutive_failures',
                    'message': f"Token refresh has failed {metrics.consecutive_failures} consecutive times",
                    'user_id': metrics.user_id,
                    'provider': metrics.provider
                })
            
            # Warning: Low success rate
            if metrics.success_rate < 80 and metrics.total_refresh_attempts >= 5:
                alerts.append({
                    'severity': 'WARNING',
                    'type': 'low_success_rate',
                    'message': f"Token refresh success rate is {metrics.success_rate:.1f}%",
                    'user_id': metrics.user_id,
                    'provider': metrics.provider
                })
            
            # Warning: Low health score
            if metrics.health_score < 50:
                alerts.append({
                    'severity': 'WARNING',
                    'type': 'low_health_score',
                    'message': f"Token health score is {metrics.health_score:.1f}",
                    'user_id': metrics.user_id,
                    'provider': metrics.provider
                })
            
            # Send alerts if any
            for alert in alerts:
                await self._send_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to check health alerts: {str(e)}")
    
    async def _send_alert(self, alert: Dict[str, Any]) -> None:
        """
        Send alert notification via CloudWatch and SNS.
        
        Args:
            alert: Alert details
        """
        try:
            # Log structured alert for CloudWatch
            logger.error(
                f"Token refresh alert: {alert['message']}",
                extra={
                    'alert_type': alert['type'],
                    'severity': alert['severity'],
                    'user_id': alert['user_id'],
                    'provider': alert['provider'],
                    'alert_data': redact_pii(alert)
                }
            )
            
            # Send CloudWatch custom metric
            cloudwatch = boto3.client('cloudwatch')
            cloudwatch.put_metric_data(
                Namespace='MeetingScheduler/TokenHealth',
                MetricData=[
                    {
                        'MetricName': f"TokenRefresh{alert['type'].title()}",
                        'Dimensions': [
                            {'Name': 'Provider', 'Value': alert['provider']},
                            {'Name': 'Severity', 'Value': alert['severity']}
                        ],
                        'Value': 1,
                        'Unit': 'Count'
                    }
                ]
            )
            
            # Send SNS notification for critical alerts
            if alert['severity'] == 'CRITICAL':
                sns = boto3.client('sns')
                topic_arn = f"arn:aws:sns:us-east-1:123456789012:token-refresh-alerts"  # TODO: Make configurable
                
                try:
                    sns.publish(
                        TopicArn=topic_arn,
                        Subject=f"Critical Token Refresh Alert - {alert['provider']}",
                        Message=json.dumps(redact_pii(alert), indent=2)
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NotFound':
                        raise
                    logger.warning(f"SNS topic not found: {topic_arn}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    async def get_token_health_status(self, user_id: str, provider: str) -> Dict[str, Any]:
        """
        Get comprehensive token health status for a user/provider combination.
        
        Args:
            user_id: User identifier
            provider: OAuth provider
            
        Returns:
            Dictionary containing health status and metrics
        """
        try:
            metrics_key = f"health#{user_id}#{provider}"
            
            # Get current health metrics
            response = self.metrics_table.get_item(Key={'pk': metrics_key, 'sk': 'current'})
            
            if 'Item' not in response:
                return {
                    'user_id': user_id,
                    'provider': provider,
                    'health_status': 'unknown',
                    'health_score': 0,
                    'message': 'No refresh history available'
                }
            
            metrics_data = response['Item']['metrics']
            
            # Determine health status
            health_score = metrics_data['health_score']
            if health_score >= 80:
                health_status = 'healthy'
            elif health_score >= 60:
                health_status = 'warning'
            elif health_score >= 40:
                health_status = 'degraded'
            else:
                health_status = 'critical'
            
            # Get recent refresh attempts
            attempts_response = self.metrics_table.query(
                KeyConditionExpression='pk = :pk',
                ExpressionAttributeValues={
                    ':pk': f"refresh_attempts#{user_id}#{provider}"
                },
                ScanIndexForward=False,  # Most recent first
                Limit=10
            )
            
            recent_attempts = [item['attempt_data'] for item in attempts_response.get('Items', [])]
            
            return {
                'user_id': user_id,
                'provider': provider,
                'health_status': health_status,
                'health_score': health_score,
                'metrics': metrics_data,
                'recent_attempts': recent_attempts,
                'recommendations': self._generate_health_recommendations(metrics_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get token health status: {str(e)}")
            return {
                'user_id': user_id,
                'provider': provider,
                'health_status': 'error',
                'health_score': 0,
                'error': str(e)
            }
    
    def _generate_health_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations based on health metrics.
        
        Args:
            metrics: Health metrics data
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if metrics['consecutive_failures'] >= 2:
            recommendations.append("Consider re-authorizing the OAuth connection")
        
        if metrics['success_rate'] < 90 and metrics['total_refresh_attempts'] >= 5:
            recommendations.append("Monitor for provider API issues or network connectivity problems")
        
        if metrics['health_score'] < 70:
            recommendations.append("Review OAuth scopes and ensure they haven't been revoked")
        
        if not metrics['last_successful_refresh']:
            recommendations.append("Initial token refresh required - connection may need setup")
        else:
            try:
                last_success = datetime.fromisoformat(metrics['last_successful_refresh'])
                hours_since = (datetime.utcnow() - last_success).total_seconds() / 3600
                
                if hours_since > 48:
                    recommendations.append("Long time since last successful refresh - check connection status")
            except:
                pass
        
        if not recommendations:
            recommendations.append("Token refresh health is good")
        
        return recommendations
    
    async def bulk_refresh_tokens(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform bulk token refresh for all users or specific provider.
        Useful for maintenance operations and proactive refresh.
        
        Args:
            provider: Optional provider filter
            
        Returns:
            Summary of bulk refresh operation
        """
        try:
            correlation_id = get_correlation_id()
            
            logger.info(
                f"Starting bulk token refresh",
                extra={'provider_filter': provider, 'correlation_id': correlation_id}
            )
            
            # Query all active connections
            scan_kwargs = {
                'FilterExpression': 'attribute_exists(provider) AND #status = :status',
                'ExpressionAttributeNames': {'#status': 'status'},
                'ExpressionAttributeValues': {':status': 'active'}
            }
            
            if provider:
                scan_kwargs['FilterExpression'] += ' AND provider = :provider'
                scan_kwargs['ExpressionAttributeValues'][':provider'] = provider
            
            response = self.connections_table.scan(**scan_kwargs)
            connections = response['Items']
            
            # Process connections in batches
            batch_size = 10
            results = {
                'total_connections': len(connections),
                'successful_refreshes': 0,
                'failed_refreshes': 0,
                'skipped_connections': 0,
                'errors': []
            }
            
            for i in range(0, len(connections), batch_size):
                batch = connections[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for connection in batch:
                    user_id = connection['user_id']
                    conn_provider = connection['provider']
                    
                    # Check if token needs refresh (expires within 1 hour)
                    try:
                        expires_at = datetime.fromisoformat(connection['expires_at'])
                        if datetime.utcnow() >= expires_at - timedelta(hours=1):
                            task = self.refresh_token_with_backoff(
                                user_id, conn_provider, correlation_id
                            )
                            tasks.append((user_id, conn_provider, task))
                        else:
                            results['skipped_connections'] += 1
                    except Exception as e:
                        results['errors'].append(f"Failed to parse expiry for {user_id}#{conn_provider}: {str(e)}")
                        results['failed_refreshes'] += 1
                
                # Wait for batch completion
                if tasks:
                    batch_results = await asyncio.gather(
                        *[task for _, _, task in tasks],
                        return_exceptions=True
                    )
                    
                    for (user_id, conn_provider, _), result in zip(tasks, batch_results):
                        if isinstance(result, Exception):
                            results['errors'].append(f"Exception for {user_id}#{conn_provider}: {str(result)}")
                            results['failed_refreshes'] += 1
                        elif result.get('success'):
                            results['successful_refreshes'] += 1
                        else:
                            results['failed_refreshes'] += 1
                            results['errors'].append(f"Failed refresh for {user_id}#{conn_provider}: {result.get('error_message', 'Unknown error')}")
                
                # Small delay between batches to avoid overwhelming providers
                if i + batch_size < len(connections):
                    await asyncio.sleep(1)
            
            logger.info(
                f"Bulk token refresh completed",
                extra={
                    'correlation_id': correlation_id,
                    'results': results
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk token refresh failed: {str(e)}")
            return {
                'total_connections': 0,
                'successful_refreshes': 0,
                'failed_refreshes': 0,
                'skipped_connections': 0,
                'errors': [str(e)]
            }