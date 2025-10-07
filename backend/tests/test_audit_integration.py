"""
Integration tests for audit trail and agent decision logging.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.audit_service import AuditService, UserActionType, ApprovalStatus
from src.services.scheduling_agent import SchedulingAgent
from src.models.agent import CostEstimate
from src.utils.logging import AgentDecisionType


class TestAuditIntegration:
    """Test audit trail integration with agent services."""
    
    @pytest.fixture
    def audit_service(self):
        """Create audit service for testing."""
        with patch('boto3.resource'):
            return AuditService(table_name="test-audit-table")
    
    @pytest.fixture
    def mock_dynamodb_table(self):
        """Mock DynamoDB table for testing."""
        table = Mock()
        table.put_item.return_value = {}
        table.query.return_value = {'Items': []}
        return table
    
    def test_agent_decision_logging(self, audit_service, mock_dynamodb_table):
        """Test logging of agent decisions."""
        audit_service.table = mock_dynamodb_table
        
        # Test data
        user_id = "test-user-123"
        run_id = "test-run-456"
        
        inputs = {
            'meeting_request': {
                'title': 'Team Meeting',
                'duration': 60,
                'attendees': ['user1@example.com', 'user2@example.com']
            }
        }
        
        outputs = {
            'recommended_time': '2024-01-15T14:00:00Z',
            'confidence': 0.85,
            'alternatives': []
        }
        
        cost_estimate = CostEstimate(
            bedrock_tokens=1500,
            estimated_cost_usd=0.0045
        )
        
        # Log agent decision
        audit_id = audit_service.log_agent_decision(
            user_id=user_id,
            run_id=run_id,
            decision_type=AgentDecisionType.SCHEDULING,
            inputs=inputs,
            outputs=outputs,
            rationale="Selected optimal time based on attendee availability",
            confidence_score=0.85,
            alternatives_considered=[],
            cost_estimate=cost_estimate,
            requires_approval=False
        )
        
        # Verify audit entry was created
        assert audit_id is not None
        mock_dynamodb_table.put_item.assert_called_once()
        
        # Verify the logged data structure
        call_args = mock_dynamodb_table.put_item.call_args[1]['Item']
        assert call_args['pk'] == f"user#{user_id}"
        assert call_args['run_id'] == run_id
        assert call_args['decision_type'] == AgentDecisionType.SCHEDULING.value
        assert call_args['confidence_score'] == 0.85
        assert call_args['requires_approval'] == False
    
    def test_user_action_logging(self, audit_service, mock_dynamodb_table):
        """Test logging of user actions."""
        audit_service.table = mock_dynamodb_table
        
        user_id = "test-user-123"
        
        # Log user action
        audit_id = audit_service.log_user_action(
            user_id=user_id,
            action_type=UserActionType.APPROVE_MEETING,
            context={'meeting_id': 'meeting-123'},
            related_decision_id='decision-456',
            feedback='Looks good, approved!'
        )
        
        # Verify audit entry was created
        assert audit_id is not None
        mock_dynamodb_table.put_item.assert_called_once()
        
        # Verify the logged data structure
        call_args = mock_dynamodb_table.put_item.call_args[1]['Item']
        assert call_args['pk'] == f"user#{user_id}"
        assert call_args['action_type'] == UserActionType.APPROVE_MEETING.value
        assert call_args['feedback'] == 'Looks good, approved!'
    
    def test_tool_invocation_logging(self, audit_service, mock_dynamodb_table):
        """Test logging of tool invocations."""
        audit_service.table = mock_dynamodb_table
        
        user_id = "test-user-123"
        run_id = "test-run-456"
        
        # Log tool invocation
        audit_id = audit_service.log_tool_invocation(
            user_id=user_id,
            run_id=run_id,
            tool_name="availability_check",
            inputs={'attendees': ['user1@example.com']},
            outputs={'available_slots': ['2024-01-15T14:00:00Z']},
            execution_time_ms=250,
            success=True
        )
        
        # Verify audit entry was created
        assert audit_id is not None
        mock_dynamodb_table.put_item.assert_called_once()
        
        # Verify the logged data structure
        call_args = mock_dynamodb_table.put_item.call_args[1]['Item']
        assert call_args['pk'] == f"user#{user_id}"
        assert call_args['tool_name'] == "availability_check"
        assert call_args['success'] == True
        assert call_args['execution_time_ms'] == 250
    
    def test_audit_trail_query(self, audit_service, mock_dynamodb_table):
        """Test querying audit trail entries."""
        # Mock query response
        mock_entries = [
            {
                'pk': 'user#test-user-123',
                'sk': 'decision#2024-01-15T10:00:00#abc123',
                'audit_id': 'abc123',
                'event_type': 'agent_decision',
                'decision_type': 'scheduling',
                'timestamp': '2024-01-15T10:00:00Z',
                'rationale': 'Test decision',
                'confidence_score': 0.8
            }
        ]
        
        mock_dynamodb_table.query.return_value = {'Items': mock_entries}
        audit_service.table = mock_dynamodb_table
        
        # Query audit trail
        entries = audit_service.get_audit_trail(
            user_id="test-user-123",
            limit=10
        )
        
        # Verify query was made
        mock_dynamodb_table.query.assert_called_once()
        assert len(entries) == 1
        assert entries[0]['audit_id'] == 'abc123'
    
    def test_decision_analytics(self, audit_service, mock_dynamodb_table):
        """Test decision analytics calculation."""
        # Mock query response with decision entries
        mock_entries = [
            {
                'event_type': 'agent_decision',
                'decision_type': 'scheduling',
                'confidence_score': 0.8,
                'cost_estimate': {'estimated_cost_usd': 0.005},
                'approval_status': 'approved'
            },
            {
                'event_type': 'agent_decision',
                'decision_type': 'conflict_resolution',
                'confidence_score': 0.9,
                'cost_estimate': {'estimated_cost_usd': 0.003},
                'approval_status': 'approved'
            }
        ]
        
        mock_dynamodb_table.query.return_value = {'Items': mock_entries}
        audit_service.table = mock_dynamodb_table
        
        # Get analytics
        analytics = audit_service.get_decision_analytics(
            user_id="test-user-123",
            days=30
        )
        
        # Verify analytics calculation
        assert analytics['total_decisions'] == 2
        assert analytics['decision_types']['scheduling'] == 1
        assert analytics['decision_types']['conflict_resolution'] == 1
        assert analytics['average_confidence'] == 0.85
        assert analytics['approval_rate'] == 1.0
        assert analytics['cost_summary']['total_cost_usd'] == 0.008
    
    @patch('src.services.audit_service.AuditService')
    def test_scheduling_agent_audit_integration(self, mock_audit_service):
        """Test that scheduling agent integrates with audit logging."""
        # Mock Bedrock client
        mock_bedrock_client = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps({
            'recommended_action': 'schedule',
            'optimal_time': '2024-01-15T14:00:00Z',
            'confidence': 0.85
        })
        mock_response.token_usage.total_tokens = 1500
        mock_response.token_usage.estimated_cost_usd = 0.0045
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        # Create scheduling agent with audit logging
        agent = SchedulingAgent(
            bedrock_client=mock_bedrock_client,
            user_id="test-user-123"
        )
        
        # Mock audit service
        mock_audit_instance = Mock()
        mock_audit_service.return_value = mock_audit_instance
        agent.audit_service = mock_audit_instance
        
        # Test conflict resolution with audit logging
        meeting_request = {'title': 'Test Meeting'}
        conflicts = [{'id': 'conflict1'}]
        available_slots = [{'start_time': '2024-01-15T14:00:00Z'}]
        
        result = agent.resolve_conflicts(meeting_request, conflicts, available_slots)
        
        # Verify audit logging was called
        mock_audit_instance.log_agent_decision.assert_called_once()
        
        # Verify the audit call parameters
        call_args = mock_audit_instance.log_agent_decision.call_args[1]
        assert call_args['user_id'] == "test-user-123"
        assert call_args['decision_type'] == AgentDecisionType.CONFLICT_RESOLUTION
        assert 'rationale' in call_args
        assert 'confidence_score' in call_args


if __name__ == '__main__':
    pytest.main([__file__])