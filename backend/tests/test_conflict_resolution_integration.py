"""
Integration tests for the conflict resolution engine.
Tests the complete workflow from conflict detection to resolution execution.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.conflict_resolution_engine import (
    ConflictResolutionEngine,
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy
)
from src.tools.conflict_resolution_tool import ConflictResolutionTool
from src.models.meeting import Meeting
from src.models.preferences import Preferences, WorkingHours, FocusBlock
from src.models.connection import Connection


class TestConflictResolutionIntegration:
    """Integration tests for conflict resolution functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ConflictResolutionEngine()
        self.tool = ConflictResolutionTool()
        self.user_id = "test_user_123"
        
        # Create test meetings
        self.meeting1 = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#1",
            provider_event_id="event_1",
            provider="google",
            title="Team Standup",
            start=datetime(2024, 1, 15, 9, 0),
            end=datetime(2024, 1, 15, 9, 30),
            attendees=["alice@example.com", "bob@example.com"],
            status="confirmed",
            priority_score=0.7,
            created_by_agent=False,
            last_modified=datetime.utcnow()
        )
        
        self.meeting2 = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#2",
            provider_event_id="event_2",
            provider="microsoft",
            title="Client Call",
            start=datetime(2024, 1, 15, 9, 15),  # Overlaps with meeting1
            end=datetime(2024, 1, 15, 10, 0),
            attendees=["client@example.com"],
            status="confirmed",
            priority_score=0.9,
            created_by_agent=False,
            last_modified=datetime.utcnow()
        )
        
        # Create test preferences
        self.preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={
                "monday": WorkingHours(start="09:00", end="17:00"),
                "tuesday": WorkingHours(start="09:00", end="17:00"),
                "wednesday": WorkingHours(start="09:00", end="17:00"),
                "thursday": WorkingHours(start="09:00", end="17:00"),
                "friday": WorkingHours(start="09:00", end="17:00")
            },
            buffer_minutes=15,
            focus_blocks=[
                FocusBlock(
                    day="monday",
                    start="14:00",
                    end="16:00",
                    title="Deep Work"
                )
            ],
            vip_contacts=["client@example.com"],
            meeting_types={}
        )
        
        # Create test connections
        self.connections = [
            Connection(
                pk=f"user#{self.user_id}#google",
                provider="google",
                access_token_encrypted="encrypted_mock_token",
                refresh_token_encrypted="encrypted_mock_refresh",
                scopes=["calendar.readonly", "calendar.events"],
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow()
            ),
            Connection(
                pk=f"user#{self.user_id}#microsoft",
                provider="microsoft",
                access_token_encrypted="encrypted_mock_token",
                refresh_token_encrypted="encrypted_mock_refresh",
                scopes=["calendars.read", "calendars.readwrite"],
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow()
            )
        ]
    
    @patch('src.services.conflict_resolution_engine.ConflictResolutionEngine._fetch_all_meetings')
    def test_detect_direct_overlap_conflict(self, mock_fetch_meetings):
        """Test detection of direct overlap conflicts."""
        # Mock the meeting fetch to return our test meetings
        mock_fetch_meetings.return_value = [self.meeting1, self.meeting2]
        
        # Detect conflicts
        conflicts = self.engine.detect_conflicts(
            user_id=self.user_id,
            start_date=datetime(2024, 1, 15, 0, 0),
            end_date=datetime(2024, 1, 15, 23, 59),
            connections=self.connections,
            preferences=self.preferences
        )
        
        # Verify conflict detection
        assert len(conflicts) > 0
        
        # Find the direct overlap conflict
        overlap_conflict = next(
            (c for c in conflicts if c.conflict_type == ConflictType.DIRECT_OVERLAP),
            None
        )
        
        assert overlap_conflict is not None
        assert overlap_conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        assert overlap_conflict.suggested_strategy == ResolutionStrategy.RESCHEDULE_LOWER_PRIORITY
        assert len(overlap_conflict.conflicting_meetings) == 1
    
    @patch('src.services.conflict_resolution_engine.ConflictResolutionEngine._fetch_all_meetings')
    def test_buffer_violation_detection(self, mock_fetch_meetings):
        """Test detection of buffer time violations."""
        # Create meetings with insufficient buffer time
        meeting_a = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#a",
            provider_event_id="event_a",
            provider="google",
            title="Meeting A",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 10, 30),
            attendees=["test@example.com"],
            status="confirmed",
            priority_score=0.5,
            created_by_agent=False,
            last_modified=datetime.utcnow()
        )
        
        meeting_b = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#b",
            provider_event_id="event_b",
            provider="google",
            title="Meeting B",
            start=datetime(2024, 1, 15, 10, 35),  # Only 5 minutes after meeting_a
            end=datetime(2024, 1, 15, 11, 0),
            attendees=["test@example.com"],
            status="confirmed",
            priority_score=0.5,
            created_by_agent=False,
            last_modified=datetime.utcnow()
        )
        
        mock_fetch_meetings.return_value = [meeting_a, meeting_b]
        
        # Detect conflicts
        conflicts = self.engine.detect_conflicts(
            user_id=self.user_id,
            start_date=datetime(2024, 1, 15, 0, 0),
            end_date=datetime(2024, 1, 15, 23, 59),
            connections=self.connections,
            preferences=self.preferences
        )
        
        # Find buffer violation conflict
        buffer_conflict = next(
            (c for c in conflicts if c.conflict_type == ConflictType.BUFFER_VIOLATION),
            None
        )
        
        assert buffer_conflict is not None
        assert buffer_conflict.severity == ConflictSeverity.MEDIUM
        assert buffer_conflict.suggested_strategy == ResolutionStrategy.FIND_ALTERNATIVE_SLOTS
    
    @patch('src.services.conflict_resolution_engine.ConflictResolutionEngine._fetch_all_meetings')
    def test_focus_block_conflict_detection(self, mock_fetch_meetings):
        """Test detection of focus block conflicts."""
        # Create a meeting that conflicts with focus block (Monday 2-4 PM)
        focus_conflict_meeting = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#focus",
            provider_event_id="event_focus",
            provider="google",
            title="Conflicting Meeting",
            start=datetime(2024, 1, 15, 14, 30),  # Monday 2:30 PM (in focus block)
            end=datetime(2024, 1, 15, 15, 0),
            attendees=["test@example.com"],
            status="confirmed",
            priority_score=0.5,
            created_by_agent=False,
            last_modified=datetime.utcnow()
        )
        
        mock_fetch_meetings.return_value = [focus_conflict_meeting]
        
        # Detect conflicts
        conflicts = self.engine.detect_conflicts(
            user_id=self.user_id,
            start_date=datetime(2024, 1, 15, 0, 0),
            end_date=datetime(2024, 1, 15, 23, 59),
            connections=self.connections,
            preferences=self.preferences
        )
        
        # Find focus block conflict
        focus_conflict = next(
            (c for c in conflicts if c.conflict_type == ConflictType.FOCUS_BLOCK_CONFLICT),
            None
        )
        
        assert focus_conflict is not None
        assert focus_conflict.severity == ConflictSeverity.MEDIUM
        assert focus_conflict.suggested_strategy == ResolutionStrategy.FIND_ALTERNATIVE_SLOTS
    
    def test_conflict_resolution_tool_integration(self):
        """Test the conflict resolution tool integration."""
        # Test tool schema
        schema = self.tool.get_tool_schema()
        assert schema["name"] == "resolve_scheduling_conflicts"
        assert "parameters" in schema
        assert "action" in schema["parameters"]["properties"]
        
        # Test tool invocation with detect_conflicts action
        parameters = {
            "action": "detect_conflicts",
            "user_id": self.user_id,
            "start_date": "2024-01-15T00:00:00",
            "end_date": "2024-01-15T23:59:59",
            "connections": [conn.dict() for conn in self.connections]
        }
        
        with patch.object(self.tool.conflict_engine, 'detect_conflicts') as mock_detect:
            mock_detect.return_value = []
            
            result = self.tool.invoke(parameters)
            
            assert result["success"] is True
            assert result["action"] == "detect_conflicts"
            assert "data" in result
            mock_detect.assert_called_once()
    
    def test_conflict_summary_generation(self):
        """Test conflict summary generation."""
        # Create mock conflicts for summary testing
        from src.services.conflict_resolution_engine import ConflictDetails
        
        mock_conflicts = [
            Mock(
                conflict_type=ConflictType.DIRECT_OVERLAP,
                severity=ConflictSeverity.HIGH
            ),
            Mock(
                conflict_type=ConflictType.BUFFER_VIOLATION,
                severity=ConflictSeverity.MEDIUM
            ),
            Mock(
                conflict_type=ConflictType.DIRECT_OVERLAP,
                severity=ConflictSeverity.CRITICAL
            )
        ]
        
        summary = self.tool._generate_conflict_summary(mock_conflicts)
        
        assert summary["total_conflicts"] == 3
        assert summary["severity_breakdown"]["high"] == 1
        assert summary["severity_breakdown"]["medium"] == 1
        assert summary["severity_breakdown"]["critical"] == 1
        assert summary["type_breakdown"]["direct_overlap"] == 2
        assert summary["type_breakdown"]["buffer_violation"] == 1
        assert len(summary["recommendations"]) > 0
    
    def test_empty_conflict_detection(self):
        """Test conflict detection with no conflicts."""
        with patch.object(self.engine, '_fetch_all_meetings') as mock_fetch:
            mock_fetch.return_value = []
            
            conflicts = self.engine.detect_conflicts(
                user_id=self.user_id,
                start_date=datetime(2024, 1, 15, 0, 0),
                end_date=datetime(2024, 1, 15, 23, 59),
                connections=self.connections,
                preferences=self.preferences
            )
            
            assert len(conflicts) == 0
    
    def test_conflict_resolution_workflow_creation(self):
        """Test creation of approval workflow."""
        # Create a mock conflict
        from src.services.conflict_resolution_engine import ConflictDetails
        
        mock_conflict = Mock()
        mock_conflict.conflict_id = "test_conflict_123"
        mock_conflict.conflict_type = ConflictType.DIRECT_OVERLAP
        mock_conflict.severity = ConflictSeverity.HIGH
        mock_conflict.description = "Test conflict"
        mock_conflict.primary_meeting = self.meeting1
        mock_conflict.conflicting_meetings = [self.meeting2]
        
        workflow = self.engine.create_approval_workflow(
            conflict=mock_conflict,
            options=[],
            user_id=self.user_id
        )
        
        assert "workflow_id" in workflow
        assert workflow["conflict_summary"]["conflict_id"] == "test_conflict_123"
        assert workflow["status"] == "pending_user_input"
        assert workflow["user_id"] == self.user_id
        assert "expires_at" in workflow
    
    def test_error_handling_in_conflict_detection(self):
        """Test error handling in conflict detection."""
        with patch.object(self.engine, '_fetch_all_meetings') as mock_fetch:
            mock_fetch.side_effect = Exception("Database error")
            
            with pytest.raises(Exception, match="Conflict detection failed"):
                self.engine.detect_conflicts(
                    user_id=self.user_id,
                    start_date=datetime(2024, 1, 15, 0, 0),
                    end_date=datetime(2024, 1, 15, 23, 59),
                    connections=self.connections,
                    preferences=self.preferences
                )
    
    def test_tool_error_handling(self):
        """Test error handling in the conflict resolution tool."""
        # Test with invalid action
        parameters = {
            "action": "invalid_action",
            "user_id": self.user_id
        }
        
        result = self.tool.invoke(parameters)
        
        assert result["success"] is False
        assert "Unknown action" in result["error"]
        
        # Test with missing required parameters
        parameters = {
            "action": "detect_conflicts"
            # Missing user_id
        }
        
        result = self.tool.invoke(parameters)
        
        assert result["success"] is False
        assert "Missing required parameters" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__])