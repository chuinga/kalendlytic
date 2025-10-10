"""
Log aggregation utilities for agent decision tracking and analysis.
"""

import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AggregationPeriod(Enum):
    """Time periods for log aggregation."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class DecisionMetrics:
    """Metrics for agent decision analysis."""
    total_decisions: int
    decision_types: Dict[str, int]
    success_rate: float
    average_execution_time_ms: float
    total_cost_usd: float
    average_cost_per_decision_usd: float
    confidence_scores: List[float]
    timestamp: str


@dataclass
class ToolMetrics:
    """Metrics for tool invocation analysis."""
    total_invocations: int
    tool_usage: Dict[str, int]
    success_rate: float
    average_execution_time_ms: float
    error_types: Dict[str, int]
    timestamp: str


class LogAggregator:
    """Utility for aggregating and analyzing agent logs."""
    
    def __init__(self, region: str = 'eu-west-1'):
        self.logs_client = boto3.client('logs', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region
    
    def aggregate_agent_decisions(
        self,
        log_group: str,
        start_time: datetime,
        end_time: datetime,
        filter_pattern: str = '{ $.decision_type = * }'
    ) -> DecisionMetrics:
        """
        Aggregate agent decision logs for analysis.
        
        Args:
            log_group: CloudWatch log group name
            start_time: Start time for log aggregation
            end_time: End time for log aggregation
            filter_pattern: CloudWatch filter pattern
            
        Returns:
            DecisionMetrics with aggregated data
        """
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern=filter_pattern
            )
            
            decisions = []
            for event in response.get('events', []):
                try:
                    log_data = json.loads(event['message'])
                    if 'decision_type' in log_data:
                        decisions.append(log_data)
                except json.JSONDecodeError:
                    continue
            
            return self._calculate_decision_metrics(decisions)
            
        except Exception as e:
            print(f"Error aggregating agent decisions: {str(e)}")
            return DecisionMetrics(
                total_decisions=0,
                decision_types={},
                success_rate=0.0,
                average_execution_time_ms=0.0,
                total_cost_usd=0.0,
                average_cost_per_decision_usd=0.0,
                confidence_scores=[],
                timestamp=datetime.utcnow().isoformat()
            )    

    def aggregate_tool_invocations(
        self,
        log_group: str,
        start_time: datetime,
        end_time: datetime,
        filter_pattern: str = '{ $.tool_name = * }'
    ) -> ToolMetrics:
        """
        Aggregate tool invocation logs for analysis.
        
        Args:
            log_group: CloudWatch log group name
            start_time: Start time for log aggregation
            end_time: End time for log aggregation
            filter_pattern: CloudWatch filter pattern
            
        Returns:
            ToolMetrics with aggregated data
        """
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern=filter_pattern
            )
            
            invocations = []
            for event in response.get('events', []):
                try:
                    log_data = json.loads(event['message'])
                    if 'tool_name' in log_data:
                        invocations.append(log_data)
                except json.JSONDecodeError:
                    continue
            
            return self._calculate_tool_metrics(invocations)
            
        except Exception as e:
            print(f"Error aggregating tool invocations: {str(e)}")
            return ToolMetrics(
                total_invocations=0,
                tool_usage={},
                success_rate=0.0,
                average_execution_time_ms=0.0,
                error_types={},
                timestamp=datetime.utcnow().isoformat()
            )
    
    def store_aggregated_metrics(
        self,
        bucket: str,
        metrics: Dict[str, Any],
        period: AggregationPeriod,
        timestamp: datetime
    ) -> str:
        """
        Store aggregated metrics in S3 for long-term analysis.
        
        Args:
            bucket: S3 bucket name
            metrics: Aggregated metrics data
            period: Aggregation period
            timestamp: Timestamp for the metrics
            
        Returns:
            S3 key where metrics were stored
        """
        try:
            key = self._generate_s3_key(period, timestamp, 'metrics')
            
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(metrics, default=str, indent=2),
                ContentType='application/json',
                Metadata={
                    'aggregation_period': period.value,
                    'timestamp': timestamp.isoformat(),
                    'service': 'meeting-scheduling-agent'
                }
            )
            
            return key
            
        except Exception as e:
            print(f"Error storing aggregated metrics: {str(e)}")
            raise
    
    def get_aggregated_metrics(
        self,
        bucket: str,
        period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieve aggregated metrics from S3 for a date range.
        
        Args:
            bucket: S3 bucket name
            period: Aggregation period
            start_date: Start date for retrieval
            end_date: End date for retrieval
            
        Returns:
            List of aggregated metrics
        """
        try:
            prefix = f"aggregated-logs/{period.value}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                StartAfter=f"{prefix}{start_date.strftime('%Y/%m/%d')}",
                EndBefore=f"{prefix}{end_date.strftime('%Y/%m/%d')}"
            )
            
            metrics = []
            for obj in response.get('Contents', []):
                try:
                    obj_response = self.s3_client.get_object(
                        Bucket=bucket,
                        Key=obj['Key']
                    )
                    data = json.loads(obj_response['Body'].read())
                    metrics.append(data)
                except Exception as e:
                    print(f"Error reading metrics from {obj['Key']}: {str(e)}")
                    continue
            
            return metrics
            
        except Exception as e:
            print(f"Error retrieving aggregated metrics: {str(e)}")
            return []
    
    def _calculate_decision_metrics(self, decisions: List[Dict[str, Any]]) -> DecisionMetrics:
        """Calculate metrics from decision log entries."""
        if not decisions:
            return DecisionMetrics(
                total_decisions=0,
                decision_types={},
                success_rate=0.0,
                average_execution_time_ms=0.0,
                total_cost_usd=0.0,
                average_cost_per_decision_usd=0.0,
                confidence_scores=[],
                timestamp=datetime.utcnow().isoformat()
            )
        
        decision_types = {}
        total_execution_time = 0
        successful_decisions = 0
        total_cost = 0.0
        confidence_scores = []
        
        for decision in decisions:
            # Count decision types
            decision_type = decision.get('decision_type', 'unknown')
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
            
            # Aggregate execution time
            exec_time = decision.get('execution_time_ms', 0)
            if exec_time:
                total_execution_time += exec_time
            
            # Count successful decisions
            if decision.get('success', True):
                successful_decisions += 1
            
            # Aggregate costs
            cost_estimate = decision.get('cost_estimate', {})
            if isinstance(cost_estimate, dict) and 'estimated_cost_usd' in cost_estimate:
                total_cost += float(cost_estimate['estimated_cost_usd'])
            
            # Collect confidence scores
            confidence = decision.get('confidence_score')
            if confidence is not None:
                confidence_scores.append(float(confidence))
        
        return DecisionMetrics(
            total_decisions=len(decisions),
            decision_types=decision_types,
            success_rate=successful_decisions / len(decisions),
            average_execution_time_ms=total_execution_time / len(decisions),
            total_cost_usd=total_cost,
            average_cost_per_decision_usd=total_cost / len(decisions),
            confidence_scores=confidence_scores,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _calculate_tool_metrics(self, invocations: List[Dict[str, Any]]) -> ToolMetrics:
        """Calculate metrics from tool invocation log entries."""
        if not invocations:
            return ToolMetrics(
                total_invocations=0,
                tool_usage={},
                success_rate=0.0,
                average_execution_time_ms=0.0,
                error_types={},
                timestamp=datetime.utcnow().isoformat()
            )
        
        tool_usage = {}
        total_execution_time = 0
        successful_invocations = 0
        error_types = {}
        
        for invocation in invocations:
            # Count tool usage
            tool_name = invocation.get('tool_name', 'unknown')
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
            
            # Aggregate execution time
            exec_time = invocation.get('execution_time_ms', 0)
            if exec_time:
                total_execution_time += exec_time
            
            # Count successful invocations
            if invocation.get('success', True):
                successful_invocations += 1
            else:
                # Count error types
                error_msg = invocation.get('error_message', 'unknown_error')
                error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return ToolMetrics(
            total_invocations=len(invocations),
            tool_usage=tool_usage,
            success_rate=successful_invocations / len(invocations),
            average_execution_time_ms=total_execution_time / len(invocations),
            error_types=error_types,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _generate_s3_key(self, period: AggregationPeriod, timestamp: datetime, data_type: str) -> str:
        """Generate S3 key for storing aggregated data."""
        if period == AggregationPeriod.HOURLY:
            return f"aggregated-logs/{period.value}/{timestamp.strftime('%Y/%m/%d/%H')}/{data_type}.json"
        elif period == AggregationPeriod.DAILY:
            return f"aggregated-logs/{period.value}/{timestamp.strftime('%Y/%m/%d')}/{data_type}.json"
        elif period == AggregationPeriod.WEEKLY:
            week_num = timestamp.isocalendar()[1]
            return f"aggregated-logs/{period.value}/{timestamp.strftime('%Y')}/week-{week_num:02d}/{data_type}.json"
        elif period == AggregationPeriod.MONTHLY:
            return f"aggregated-logs/{period.value}/{timestamp.strftime('%Y/%m')}/{data_type}.json"
        else:
            return f"aggregated-logs/unknown/{timestamp.strftime('%Y/%m/%d')}/{data_type}.json"


def create_log_aggregator(region: str = 'eu-west-1') -> LogAggregator:
    """Create a log aggregator instance."""
    return LogAggregator(region)