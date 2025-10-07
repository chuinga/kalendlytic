"""
Comprehensive audit service for tracking agent actions and decisions.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from enum import Enum

import boto3
from botocore.exceptions import ClientError

from ..utils.logging import AgentLogger, AgentDecisionType, create_agent_logger
from ..models.agent import AuditLog, AgentRun, ToolCall, CostEstimate
from ..config.logging_config import LoggingConfig


class AuditEventType(Enum):
    """Types of audit events to track."""
    AGENT_DECISION = "agent_decision"
    TOOL_INVOCATION = "tool_invocation"
    USER_ACTION = "user_action"
    APPROVAL_WORKFLOW = "approval_workflow"
    ERROR_HANDLING = "error_handling"
    SYSTEM_EVENT = "system_event"


class UserActionType(Enum):
    """Types of user actions to track."""
    APPROVE_MEETING = "approve_meeting"
    REJECT_MEETING = "reject_meeting"
    MODIFY_PREFERENCES = "modify_preferences"
    OVERRIDE_DECISION = "override_decision"
    CANCEL_REQUEST = "cancel_request"
    PROVIDE_FEEDBACK = "provide_feedback"


class ApprovalStatus(Enum):
    """Status of approval workflows."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AuditService:
    """Service for comprehensive audit logging and trail management."""
    
    def __init__(self, table_name: str = "meeting-agent-audit"):
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.logger = create_agent_logger('audit_service')
        
    def log_agent_decision(
        self,
        user_id: str,
        run_id: str,
        decision_type: AgentDecisionType,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        rationale: str,
        confidence_score: float,
        alternatives_considered: List[Dict[str, Any]] = None,
        tool_calls: List[str] = None,
        cost_estimate: Optional[CostEstimate] = None,
        requires_approval: bool = False
    ) -> str:
        """
        Log comprehensive agent decision with natural language rationale.
        
        Args:
            user_id: ID of the user for whom the decision was made
            run_id: Agent run identifier
            decision_type: Type of decision made
            inputs: Input parameters that led to the decision
            outputs: Results of the decision
            rationale: Natural language explanation of the decision
            confidence_score: Confidence level (0.0 to 1.0)
            alternatives_considered: List of alternative options considered
            tool_calls: List of tools used in making the decision
            cost_estimate: Estimated cost breakdown
            requires_approval: Whether this decision requires user approval
            
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        
        # Generate enhanced rationale with context
        enhanced_rationale = self._generate_enhanced_rationale(
            decision_type, inputs, outputs, rationale, 
            alternatives_considered, confidence_score
        )
        
        audit_entry = {
            'pk': f"user#{user_id}",
            'sk': f"decision#{timestamp.isoformat()}#{audit_id}",
            'audit_id': audit_id,
            'run_id': run_id,
            'event_type': AuditEventType.AGENT_DECISION.value,
            'decision_type': decision_type.value,
            'timestamp': timestamp.isoformat(),
            'inputs': inputs,
            'outputs': outputs,
            'rationale': rationale,
            'enhanced_rationale': enhanced_rationale,
            'confidence_score': confidence_score,
            'alternatives_considered': alternatives_considered or [],
            'alternatives_count': len(alternatives_considered) if alternatives_considered else 0,
            'tool_calls': tool_calls or [],
            'cost_estimate': cost_estimate.dict() if cost_estimate else None,
            'requires_approval': requires_approval,
            'approval_status': ApprovalStatus.PENDING.value if requires_approval else None,
            'created_at': timestamp.isoformat(),
            'ttl': int((timestamp + timedelta(days=LoggingConfig.AGENT_DECISION_RETENTION_DAYS)).timestamp())
        }
        
        try:
            self.table.put_item(Item=audit_entry)
            
            # Log to CloudWatch for real-time monitoring
            self.logger.log_agent_decision(
                decision_type=decision_type,
                rationale=enhanced_rationale,
                inputs=inputs,
                outputs=outputs,
                confidence_score=confidence_score,
                alternatives_count=len(alternatives_considered) if alternatives_considered else 0,
                cost_estimate=cost_estimate.dict() if cost_estimate else None
            )
            
            return audit_id
            
        except ClientError as e:
            self.logger.error(f"Failed to log agent decision: {e}")
            raise
    
    def log_tool_invocation(
        self,
        user_id: str,
        run_id: str,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> str:
        """
        Log tool invocation for audit trail.
        
        Args:
            user_id: ID of the user
            run_id: Agent run identifier
            tool_name: Name of the invoked tool
            inputs: Tool input parameters
            outputs: Tool outputs
            execution_time_ms: Execution time in milliseconds
            success: Whether the tool execution was successful
            error_message: Error message if execution failed
            
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        
        audit_entry = {
            'pk': f"user#{user_id}",
            'sk': f"tool#{timestamp.isoformat()}#{audit_id}",
            'audit_id': audit_id,
            'run_id': run_id,
            'event_type': AuditEventType.TOOL_INVOCATION.value,
            'tool_name': tool_name,
            'timestamp': timestamp.isoformat(),
            'inputs': inputs,
            'outputs': outputs,
            'execution_time_ms': execution_time_ms,
            'success': success,
            'error_message': error_message,
            'created_at': timestamp.isoformat(),
            'ttl': int((timestamp + timedelta(days=LoggingConfig.AGENT_DECISION_RETENTION_DAYS)).timestamp())
        }
        
        try:
            self.table.put_item(Item=audit_entry)
            
            # Log to CloudWatch
            self.logger.log_tool_invocation(
                tool_name=tool_name,
                inputs=inputs,
                outputs=outputs,
                success=success,
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )
            
            return audit_id
            
        except ClientError as e:
            self.logger.error(f"Failed to log tool invocation: {e}")
            raise
    
    def log_user_action(
        self,
        user_id: str,
        action_type: UserActionType,
        context: Dict[str, Any],
        related_decision_id: Optional[str] = None,
        feedback: Optional[str] = None
    ) -> str:
        """
        Log user actions for approval workflow tracking.
        
        Args:
            user_id: ID of the user performing the action
            action_type: Type of user action
            context: Context information about the action
            related_decision_id: ID of related agent decision
            feedback: Optional user feedback
            
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        
        audit_entry = {
            'pk': f"user#{user_id}",
            'sk': f"action#{timestamp.isoformat()}#{audit_id}",
            'audit_id': audit_id,
            'event_type': AuditEventType.USER_ACTION.value,
            'action_type': action_type.value,
            'timestamp': timestamp.isoformat(),
            'context': context,
            'related_decision_id': related_decision_id,
            'feedback': feedback,
            'created_at': timestamp.isoformat(),
            'ttl': int((timestamp + timedelta(days=LoggingConfig.AGENT_DECISION_RETENTION_DAYS)).timestamp())
        }
        
        try:
            self.table.put_item(Item=audit_entry)
            
            # Update related decision if applicable
            if related_decision_id and action_type in [UserActionType.APPROVE_MEETING, UserActionType.REJECT_MEETING]:
                self._update_approval_status(user_id, related_decision_id, action_type)
            
            self.logger.info(
                f"User action logged: {action_type.value}",
                extra={
                    'user_id': user_id,
                    'action_type': action_type.value,
                    'related_decision_id': related_decision_id
                }
            )
            
            return audit_id
            
        except ClientError as e:
            self.logger.error(f"Failed to log user action: {e}")
            raise
    
    def log_approval_workflow(
        self,
        user_id: str,
        decision_id: str,
        status: ApprovalStatus,
        approver_id: Optional[str] = None,
        approval_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log approval workflow events.
        
        Args:
            user_id: ID of the user
            decision_id: ID of the decision requiring approval
            status: Approval status
            approver_id: ID of the user who approved/rejected
            approval_context: Additional context about the approval
            
        Returns:
            Audit log entry ID
        """
        timestamp = datetime.utcnow()
        audit_id = str(uuid.uuid4())
        
        audit_entry = {
            'pk': f"user#{user_id}",
            'sk': f"approval#{timestamp.isoformat()}#{audit_id}",
            'audit_id': audit_id,
            'event_type': AuditEventType.APPROVAL_WORKFLOW.value,
            'decision_id': decision_id,
            'approval_status': status.value,
            'approver_id': approver_id,
            'approval_context': approval_context,
            'timestamp': timestamp.isoformat(),
            'created_at': timestamp.isoformat(),
            'ttl': int((timestamp + timedelta(days=LoggingConfig.AGENT_DECISION_RETENTION_DAYS)).timestamp())
        }
        
        try:
            self.table.put_item(Item=audit_entry)
            
            self.logger.info(
                f"Approval workflow logged: {status.value}",
                extra={
                    'user_id': user_id,
                    'decision_id': decision_id,
                    'approval_status': status.value,
                    'approver_id': approver_id
                }
            )
            
            return audit_id
            
        except ClientError as e:
            self.logger.error(f"Failed to log approval workflow: {e}")
            raise
    
    def get_audit_trail(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit trail for a user with filtering options.
        
        Args:
            user_id: ID of the user
            start_date: Start date for filtering
            end_date: End date for filtering
            event_types: List of event types to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of audit trail entries
        """
        try:
            # Build query parameters
            key_condition = boto3.dynamodb.conditions.Key('pk').eq(f"user#{user_id}")
            
            if start_date:
                if end_date:
                    key_condition = key_condition & boto3.dynamodb.conditions.Key('sk').between(
                        f"action#{start_date.isoformat()}",
                        f"tool#{end_date.isoformat()}#zzz"
                    )
                else:
                    key_condition = key_condition & boto3.dynamodb.conditions.Key('sk').gte(
                        f"action#{start_date.isoformat()}"
                    )
            
            # Query DynamoDB
            response = self.table.query(
                KeyConditionExpression=key_condition,
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            entries = response.get('Items', [])
            
            # Filter by event types if specified
            if event_types:
                event_type_values = [et.value for et in event_types]
                entries = [
                    entry for entry in entries 
                    if entry.get('event_type') in event_type_values
                ]
            
            return entries
            
        except ClientError as e:
            self.logger.error(f"Failed to query audit trail: {e}")
            raise
    
    def get_decision_analytics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics on agent decisions for a user.
        
        Args:
            user_id: ID of the user
            days: Number of days to analyze
            
        Returns:
            Analytics summary
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get decision entries
        decisions = self.get_audit_trail(
            user_id=user_id,
            start_date=start_date,
            event_types=[AuditEventType.AGENT_DECISION]
        )
        
        if not decisions:
            return {
                'total_decisions': 0,
                'period_days': days,
                'decision_types': {},
                'average_confidence': 0,
                'approval_rate': 0,
                'cost_summary': {'total_cost_usd': 0}
            }
        
        # Analyze decisions
        decision_types = {}
        confidence_scores = []
        total_cost = 0.0
        approved_count = 0
        
        for decision in decisions:
            # Count decision types
            decision_type = decision.get('decision_type', 'unknown')
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
            
            # Collect confidence scores
            confidence = decision.get('confidence_score')
            if confidence is not None:
                confidence_scores.append(confidence)
            
            # Calculate costs
            cost_estimate = decision.get('cost_estimate', {})
            if isinstance(cost_estimate, dict) and 'estimated_cost_usd' in cost_estimate:
                total_cost += float(cost_estimate['estimated_cost_usd'])
            
            # Count approvals
            if decision.get('approval_status') == ApprovalStatus.APPROVED.value:
                approved_count += 1
        
        return {
            'total_decisions': len(decisions),
            'period_days': days,
            'decision_types': decision_types,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'approval_rate': approved_count / len(decisions) if decisions else 0,
            'cost_summary': {
                'total_cost_usd': total_cost,
                'average_cost_per_decision_usd': total_cost / len(decisions) if decisions else 0
            }
        }
    
    def _generate_enhanced_rationale(
        self,
        decision_type: AgentDecisionType,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        base_rationale: str,
        alternatives: Optional[List[Dict[str, Any]]],
        confidence_score: float
    ) -> str:
        """
        Generate enhanced natural language rationale for agent decisions.
        
        Args:
            decision_type: Type of decision made
            inputs: Input parameters
            outputs: Decision outputs
            base_rationale: Base rationale provided
            alternatives: Alternative options considered
            confidence_score: Confidence level
            
        Returns:
            Enhanced rationale with additional context
        """
        enhanced_parts = [base_rationale]
        
        # Add confidence context
        if confidence_score < 0.5:
            enhanced_parts.append(f"This decision has low confidence ({confidence_score:.2f}) and may require review.")
        elif confidence_score > 0.9:
            enhanced_parts.append(f"This decision has high confidence ({confidence_score:.2f}).")
        
        # Add alternatives context
        if alternatives and len(alternatives) > 0:
            enhanced_parts.append(f"Considered {len(alternatives)} alternative options before making this decision.")
            
            # Summarize top alternatives
            for i, alt in enumerate(alternatives[:2]):  # Show top 2 alternatives
                alt_summary = alt.get('summary', 'Alternative option')
                alt_score = alt.get('score', 0)
                enhanced_parts.append(f"Alternative {i+1}: {alt_summary} (score: {alt_score:.2f})")
        
        # Add decision type specific context
        if decision_type == AgentDecisionType.SCHEDULING:
            meeting_count = len(outputs.get('scheduled_meetings', []))
            if meeting_count > 0:
                enhanced_parts.append(f"Successfully scheduled {meeting_count} meeting(s).")
        
        elif decision_type == AgentDecisionType.CONFLICT_RESOLUTION:
            conflicts_resolved = outputs.get('conflicts_resolved', 0)
            if conflicts_resolved > 0:
                enhanced_parts.append(f"Resolved {conflicts_resolved} scheduling conflict(s).")
        
        return " ".join(enhanced_parts)
    
    def _update_approval_status(
        self,
        user_id: str,
        decision_id: str,
        action_type: UserActionType
    ) -> None:
        """
        Update approval status for a decision based on user action.
        
        Args:
            user_id: ID of the user
            decision_id: ID of the decision
            action_type: Type of user action
        """
        try:
            # Map action to approval status
            status_mapping = {
                UserActionType.APPROVE_MEETING: ApprovalStatus.APPROVED,
                UserActionType.REJECT_MEETING: ApprovalStatus.REJECTED
            }
            
            new_status = status_mapping.get(action_type)
            if not new_status:
                return
            
            # Find and update the decision entry
            # This is a simplified approach - in production, you'd want to use GSI for efficient lookups
            response = self.table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('pk').eq(f"user#{user_id}"),
                FilterExpression=boto3.dynamodb.conditions.Attr('audit_id').eq(decision_id)
            )
            
            items = response.get('Items', [])
            if items:
                item = items[0]
                self.table.update_item(
                    Key={'pk': item['pk'], 'sk': item['sk']},
                    UpdateExpression='SET approval_status = :status, updated_at = :timestamp',
                    ExpressionAttributeValues={
                        ':status': new_status.value,
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                
        except ClientError as e:
            self.logger.error(f"Failed to update approval status: {e}")