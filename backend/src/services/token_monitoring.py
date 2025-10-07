"""
Token monitoring and alerting service for proactive token health management.
Provides comprehensive monitoring, alerting, and reporting capabilities.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from ..utils.aws_clients import get_dynamodb_resource, get_secrets_client
from ..utils.logging import setup_logger, redact_pii
from ..utils.token_errors import TokenError, TokenErrorSeverity, TokenErrorCategory

logger = setup_logger(__name__)

class AlertType(Enum):
    """Types of token-related alerts."""
    CONSECUTIVE_FAILURES = "consecutive_failures"
    LOW_SUCCESS_RATE = "low_success_rate"
    HIGH_ERROR_RATE = "high_error_rate"
    EXPIRED_TOKENS = "expired_tokens"
    MISSING_REFRESH_TOKENS = "missing_refresh_tokens"
    PROVIDER_OUTAGE = "provider_outage"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    CONFIGURATION_ERROR = "configuration_error"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Token monitoring alert."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    user_id: Optional[str]
    provider: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]
    correlation_id: Optional[str] = None

@dataclass
class MonitoringMetrics:
    """Comprehensive monitoring metrics."""
    timestamp: str
    provider: str
    total_users: int
    active_connections: int
    expired_tokens: int
    failed_refreshes_24h: int
    success_rate_24h: float
    average_refresh_time: float
    error_distribution: Dict[str, int]
    health_score: float

class TokenMonitoringService:
    """Service for monitoring token health and generating alerts."""
    
    def __init__(self):
        self.dynamodb = get_dynamodb_resource()
        self.secrets_client = get_secrets_client()
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        
        self.connections_table = self.dynamodb.Table('Connections')
        self.metrics_table = self.dynamodb.Table('TokenMetrics')
        self.alerts_table = self.dynamodb.Table('TokenAlerts')
        
        # Alert thresholds
        self.thresholds = {
            'consecutive_failures': 3,
            'success_rate_warning': 80.0,
            'success_rate_critical': 60.0,
            'error_rate_warning': 20.0,
            'error_rate_critical': 40.0,
            'expired_tokens_warning': 10,
            'expired_tokens_critical': 25
        }
        
        # SNS topic ARNs (should be configurable via environment)
        self.alert_topics = {
            AlertSeverity.INFO: os.environ.get('SNS_INFO_TOPIC'),
            AlertSeverity.WARNING: os.environ.get('SNS_WARNING_TOPIC'),
            AlertSeverity.ERROR: os.environ.get('SNS_ERROR_TOPIC'),
            AlertSeverity.CRITICAL: os.environ.get('SNS_CRITICAL_TOPIC')
        }
    
    async def collect_metrics(self, provider: Optional[str] = None) -> List[MonitoringMetrics]:
        """
        Collect comprehensive monitoring metrics for all providers or specific provider.
        
        Args:
            provider: Optional provider filter
            
        Returns:
            List of monitoring metrics by provider
        """
        try:
            providers = [provider] if provider else ['google', 'microsoft']
            metrics_list = []
            
            for prov in providers:
                metrics = await self._collect_provider_metrics(prov)
                metrics_list.append(metrics)
            
            # Store metrics for historical tracking
            for metrics in metrics_list:
                await self._store_metrics(metrics)
            
            return metrics_list
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            return []
    
    async def _collect_provider_metrics(self, provider: str) -> MonitoringMetrics:
        """
        Collect metrics for a specific provider.
        
        Args:
            provider: OAuth provider
            
        Returns:
            MonitoringMetrics for the provider
        """
        try:
            current_time = datetime.utcnow()
            timestamp = current_time.isoformat()
            
            # Get all connections for provider
            response = self.connections_table.scan(
                FilterExpression='provider = :provider',
                ExpressionAttributeValues={':provider': provider}
            )
            connections = response['Items']
            
            total_users = len(connections)
            active_connections = len([c for c in connections if c.get('status') == 'active'])
            
            # Count expired tokens
            expired_tokens = 0
            for conn in connections:
                try:
                    expires_at = datetime.fromisoformat(conn['expires_at'])
                    if current_time >= expires_at:
                        expired_tokens += 1
                except:
                    pass
            
            # Get refresh metrics from last 24 hours
            window_start = current_time - timedelta(hours=24)
            
            refresh_response = self.metrics_table.query(
                IndexName='TimestampIndex',  # Assuming GSI on timestamp
                KeyConditionExpression='provider = :provider AND #ts BETWEEN :start AND :end',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':provider': provider,
                    ':start': window_start.isoformat(),
                    ':end': timestamp
                }
            )
            
            refresh_attempts = refresh_response.get('Items', [])
            
            # Calculate success rate and error distribution
            total_attempts = len(refresh_attempts)
            successful_attempts = len([a for a in refresh_attempts 
                                     if a.get('attempt_data', {}).get('status') == 'success'])
            
            success_rate_24h = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 100.0
            failed_refreshes_24h = total_attempts - successful_attempts
            
            # Calculate average refresh time
            refresh_times = [
                a.get('attempt_data', {}).get('refresh_time', 0) 
                for a in refresh_attempts 
                if a.get('attempt_data', {}).get('status') == 'success'
            ]
            average_refresh_time = sum(refresh_times) / len(refresh_times) if refresh_times else 0.0
            
            # Error distribution
            error_distribution = {}
            for attempt in refresh_attempts:
                error_type = attempt.get('attempt_data', {}).get('error_type')
                if error_type:
                    error_distribution[error_type] = error_distribution.get(error_type, 0) + 1
            
            # Calculate health score
            health_score = self._calculate_provider_health_score(
                success_rate_24h, expired_tokens, total_users, failed_refreshes_24h
            )
            
            return MonitoringMetrics(
                timestamp=timestamp,
                provider=provider,
                total_users=total_users,
                active_connections=active_connections,
                expired_tokens=expired_tokens,
                failed_refreshes_24h=failed_refreshes_24h,
                success_rate_24h=success_rate_24h,
                average_refresh_time=average_refresh_time,
                error_distribution=error_distribution,
                health_score=health_score
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics for provider {provider}: {str(e)}")
            # Return empty metrics on error
            return MonitoringMetrics(
                timestamp=datetime.utcnow().isoformat(),
                provider=provider,
                total_users=0,
                active_connections=0,
                expired_tokens=0,
                failed_refreshes_24h=0,
                success_rate_24h=0.0,
                average_refresh_time=0.0,
                error_distribution={},
                health_score=0.0
            )
    
    def _calculate_provider_health_score(self, success_rate: float, expired_tokens: int,
                                       total_users: int, failed_refreshes: int) -> float:
        """
        Calculate overall health score for a provider.
        
        Args:
            success_rate: Success rate percentage
            expired_tokens: Number of expired tokens
            total_users: Total number of users
            failed_refreshes: Number of failed refreshes in 24h
            
        Returns:
            Health score (0-100)
        """
        score = 100.0
        
        # Penalize low success rate
        if success_rate < 95:
            score -= (95 - success_rate) * 2
        
        # Penalize expired tokens
        if total_users > 0:
            expired_percentage = (expired_tokens / total_users) * 100
            if expired_percentage > 5:
                score -= (expired_percentage - 5) * 3
        
        # Penalize failed refreshes
        if failed_refreshes > 5:
            score -= (failed_refreshes - 5) * 2
        
        return max(0.0, min(100.0, score))
    
    async def _store_metrics(self, metrics: MonitoringMetrics) -> None:
        """
        Store metrics for historical tracking and analysis.
        
        Args:
            metrics: Monitoring metrics to store
        """
        try:
            self.metrics_table.put_item(
                Item={
                    'pk': f"provider_metrics#{metrics.provider}",
                    'sk': metrics.timestamp,
                    'provider': metrics.provider,
                    'metrics_data': asdict(metrics),
                    'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
                }
            )
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")
    
    async def check_alerts(self, metrics_list: List[MonitoringMetrics]) -> List[Alert]:
        """
        Check metrics against thresholds and generate alerts.
        
        Args:
            metrics_list: List of monitoring metrics
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        for metrics in metrics_list:
            provider_alerts = await self._check_provider_alerts(metrics)
            alerts.extend(provider_alerts)
        
        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)
        
        return alerts
    
    async def _check_provider_alerts(self, metrics: MonitoringMetrics) -> List[Alert]:
        """
        Check alerts for a specific provider.
        
        Args:
            metrics: Provider monitoring metrics
            
        Returns:
            List of alerts for the provider
        """
        alerts = []
        
        # Success rate alerts
        if metrics.success_rate_24h < self.thresholds['success_rate_critical']:
            alerts.append(Alert(
                alert_id=f"success_rate_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                alert_type=AlertType.LOW_SUCCESS_RATE,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical: Low Success Rate for {metrics.provider.title()}",
                message=f"Token refresh success rate is {metrics.success_rate_24h:.1f}% (threshold: {self.thresholds['success_rate_critical']}%)",
                user_id=None,
                provider=metrics.provider,
                timestamp=metrics.timestamp,
                metadata={
                    'success_rate': metrics.success_rate_24h,
                    'threshold': self.thresholds['success_rate_critical'],
                    'failed_refreshes': metrics.failed_refreshes_24h
                }
            ))
        elif metrics.success_rate_24h < self.thresholds['success_rate_warning']:
            alerts.append(Alert(
                alert_id=f"success_rate_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                alert_type=AlertType.LOW_SUCCESS_RATE,
                severity=AlertSeverity.WARNING,
                title=f"Warning: Low Success Rate for {metrics.provider.title()}",
                message=f"Token refresh success rate is {metrics.success_rate_24h:.1f}% (threshold: {self.thresholds['success_rate_warning']}%)",
                user_id=None,
                provider=metrics.provider,
                timestamp=metrics.timestamp,
                metadata={
                    'success_rate': metrics.success_rate_24h,
                    'threshold': self.thresholds['success_rate_warning'],
                    'failed_refreshes': metrics.failed_refreshes_24h
                }
            ))
        
        # Expired tokens alerts
        if metrics.total_users > 0:
            expired_percentage = (metrics.expired_tokens / metrics.total_users) * 100
            
            if expired_percentage > self.thresholds['expired_tokens_critical']:
                alerts.append(Alert(
                    alert_id=f"expired_tokens_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                    alert_type=AlertType.EXPIRED_TOKENS,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Critical: High Number of Expired Tokens for {metrics.provider.title()}",
                    message=f"{metrics.expired_tokens} tokens expired ({expired_percentage:.1f}% of users)",
                    user_id=None,
                    provider=metrics.provider,
                    timestamp=metrics.timestamp,
                    metadata={
                        'expired_tokens': metrics.expired_tokens,
                        'total_users': metrics.total_users,
                        'expired_percentage': expired_percentage
                    }
                ))
            elif expired_percentage > self.thresholds['expired_tokens_warning']:
                alerts.append(Alert(
                    alert_id=f"expired_tokens_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                    alert_type=AlertType.EXPIRED_TOKENS,
                    severity=AlertSeverity.WARNING,
                    title=f"Warning: Expired Tokens for {metrics.provider.title()}",
                    message=f"{metrics.expired_tokens} tokens expired ({expired_percentage:.1f}% of users)",
                    user_id=None,
                    provider=metrics.provider,
                    timestamp=metrics.timestamp,
                    metadata={
                        'expired_tokens': metrics.expired_tokens,
                        'total_users': metrics.total_users,
                        'expired_percentage': expired_percentage
                    }
                ))
        
        # High error rate alerts
        if metrics.total_users > 0:
            error_rate = (metrics.failed_refreshes_24h / metrics.total_users) * 100
            
            if error_rate > self.thresholds['error_rate_critical']:
                alerts.append(Alert(
                    alert_id=f"error_rate_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                    alert_type=AlertType.HIGH_ERROR_RATE,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Critical: High Error Rate for {metrics.provider.title()}",
                    message=f"Error rate is {error_rate:.1f}% ({metrics.failed_refreshes_24h} failures in 24h)",
                    user_id=None,
                    provider=metrics.provider,
                    timestamp=metrics.timestamp,
                    metadata={
                        'error_rate': error_rate,
                        'failed_refreshes': metrics.failed_refreshes_24h,
                        'error_distribution': metrics.error_distribution
                    }
                ))
            elif error_rate > self.thresholds['error_rate_warning']:
                alerts.append(Alert(
                    alert_id=f"error_rate_{metrics.provider}_{int(datetime.utcnow().timestamp())}",
                    alert_type=AlertType.HIGH_ERROR_RATE,
                    severity=AlertSeverity.WARNING,
                    title=f"Warning: High Error Rate for {metrics.provider.title()}",
                    message=f"Error rate is {error_rate:.1f}% ({metrics.failed_refreshes_24h} failures in 24h)",
                    user_id=None,
                    provider=metrics.provider,
                    timestamp=metrics.timestamp,
                    metadata={
                        'error_rate': error_rate,
                        'failed_refreshes': metrics.failed_refreshes_24h,
                        'error_distribution': metrics.error_distribution
                    }
                ))
        
        return alerts
    
    async def _send_alert(self, alert: Alert) -> None:
        """
        Send alert via multiple channels (CloudWatch, SNS, etc.).
        
        Args:
            alert: Alert to send
        """
        try:
            # Store alert in database
            await self._store_alert(alert)
            
            # Log structured alert
            logger.error(
                f"Token alert: {alert.title}",
                extra={
                    'alert_id': alert.alert_id,
                    'alert_type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'provider': alert.provider,
                    'user_id': alert.user_id,
                    'correlation_id': alert.correlation_id,
                    'metadata': redact_pii(alert.metadata)
                }
            )
            
            # Send CloudWatch metric
            await self._send_cloudwatch_metric(alert)
            
            # Send SNS notification
            await self._send_sns_notification(alert)
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    async def _store_alert(self, alert: Alert) -> None:
        """
        Store alert in database for tracking and analysis.
        
        Args:
            alert: Alert to store
        """
        try:
            self.alerts_table.put_item(
                Item={
                    'pk': f"alert#{alert.provider or 'system'}",
                    'sk': alert.timestamp,
                    'alert_id': alert.alert_id,
                    'alert_data': asdict(alert),
                    'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
                }
            )
        except Exception as e:
            logger.error(f"Failed to store alert: {str(e)}")
    
    async def _send_cloudwatch_metric(self, alert: Alert) -> None:
        """
        Send alert as CloudWatch custom metric.
        
        Args:
            alert: Alert to send
        """
        try:
            dimensions = [
                {'Name': 'AlertType', 'Value': alert.alert_type.value},
                {'Name': 'Severity', 'Value': alert.severity.value}
            ]
            
            if alert.provider:
                dimensions.append({'Name': 'Provider', 'Value': alert.provider})
            
            self.cloudwatch.put_metric_data(
                Namespace='MeetingScheduler/TokenAlerts',
                MetricData=[
                    {
                        'MetricName': 'AlertCount',
                        'Dimensions': dimensions,
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send CloudWatch metric: {str(e)}")
    
    async def _send_sns_notification(self, alert: Alert) -> None:
        """
        Send alert via SNS notification.
        
        Args:
            alert: Alert to send
        """
        try:
            topic_arn = self.alert_topics.get(alert.severity)
            if not topic_arn:
                logger.warning(f"No SNS topic configured for severity {alert.severity.value}")
                return
            
            message = {
                'alert_id': alert.alert_id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'provider': alert.provider,
                'timestamp': alert.timestamp,
                'metadata': redact_pii(alert.metadata)
            }
            
            self.sns.publish(
                TopicArn=topic_arn,
                Subject=alert.title,
                Message=json.dumps(message, indent=2)
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'NotFound':
                logger.error(f"Failed to send SNS notification: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to send SNS notification: {str(e)}")
    
    async def get_alert_history(self, provider: Optional[str] = None, 
                              hours: int = 24) -> List[Alert]:
        """
        Get alert history for analysis and reporting.
        
        Args:
            provider: Optional provider filter
            hours: Number of hours to look back
            
        Returns:
            List of historical alerts
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            if provider:
                response = self.alerts_table.query(
                    KeyConditionExpression='pk = :pk AND sk BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':pk': f"alert#{provider}",
                        ':start': start_time.isoformat(),
                        ':end': end_time.isoformat()
                    }
                )
            else:
                # Scan all alerts in time range
                response = self.alerts_table.scan(
                    FilterExpression='sk BETWEEN :start AND :end',
                    ExpressionAttributeValues={
                        ':start': start_time.isoformat(),
                        ':end': end_time.isoformat()
                    }
                )
            
            alerts = []
            for item in response.get('Items', []):
                alert_data = item['alert_data']
                alerts.append(Alert(**alert_data))
            
            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get alert history: {str(e)}")
            return []