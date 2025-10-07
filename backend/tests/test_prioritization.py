"""
Tests for the meeting prioritization system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.tools.prioritization_tool import PrioritizationTool, PriorityScore, AttendeeAnalysis
from src.services.priority_service import PriorityService
from src.models.meeting import Meeting
from src.models.preferences import Preferences, MeetingType


class TestPrioritizationTool:
    """Test cases for the PrioritizationTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PrioritizationTool()
        
        # Mock external dependencies
        self.tool.bedrock_client = Mock()
        self.tool.dynamodb = Mock()
        self.tool.priority_table = Mock()
        self.tool.learning_table = Mock()
    
    def test_analyze_attendees_with_vips(self):
        """Test attendee analysis with VIP contacts."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Board Meeting",
            start=datetime.utcnow() + timedelta(hours=2),
            end=datetime.utcnow() + timedelta(hours=3),
            attendees=["user@company.com", "ceo@company.com", "external@client.com"],
            last_modified=datetime.utcnow()
        )
        
        preferences = Preferences(
            pk="user#123",
            working_hours={},
            vip_contacts=["ceo@company.com"],
            meeting_types={}
        )
        
        analysis = self.tool._analyze_attendees(meeting, preferences)
        
        assert analysis.total_attendees == 3
        assert "ceo@company.com" in analysis.vip_attendees
        assert analysis.vip_ratio == 1/3
        assert analysis.attendee_importance_score > 0.5
        assert "company.com" in analysis.domain_analysis
        assert "client.com" in analysis.domain_analysis
    
    def test_analyze_meeting_subject_high_priority(self):
        """Test subject analysis for high-priority keywords."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="URGENT: Board Meeting - Critical Decision Required",
            start=datetime.utcnow() + timedelta(hours=2),
            end=datetime.utcnow() + timedelta(hours=3),
            attendees=["user@company.com"],
            last_modified=datetime.utcnow()
        )
        
        score = self.tool._analyze_meeting_subject(meeting)
        
        assert score >= 0.8  # Should be high priority due to "URGENT" and "Critical"
    
    def test_analyze_meeting_subject_low_priority(self):
        """Test subject analysis for low-priority keywords."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Optional Coffee Chat - Social",
            start=datetime.utcnow() + timedelta(hours=2),
            end=datetime.utcnow() + timedelta(hours=3),
            attendees=["user@company.com"],
            last_modified=datetime.utcnow()
        )
        
        score = self.tool._analyze_meeting_subject(meeting)
        
        assert score <= 0.4  # Should be low priority due to "Optional" and "Social"
    
    def test_calculate_urgency_score_immediate(self):
        """Test urgency calculation for immediate meetings."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Test Meeting",
            start=datetime.utcnow() + timedelta(minutes=30),  # 30 minutes from now
            end=datetime.utcnow() + timedelta(hours=1),
            attendees=["user@company.com"],
            last_modified=datetime.utcnow()
        )
        
        score, level = self.tool._calculate_urgency_score(meeting)
        
        assert score >= 0.9
        assert level in ['immediate', 'very_urgent']
    
    def test_calculate_urgency_score_future(self):
        """Test urgency calculation for future meetings."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Test Meeting",
            start=datetime.utcnow() + timedelta(days=10),  # 10 days from now
            end=datetime.utcnow() + timedelta(days=10, hours=1),
            attendees=["user@company.com"],
            last_modified=datetime.utcnow()
        )
        
        score, level = self.tool._calculate_urgency_score(meeting)
        
        assert score <= 0.5
        assert level == 'future'
    
    def test_calculate_weighted_score(self):
        """Test weighted score calculation."""
        factors = {
            'vip_contacts': 0.8,
            'meeting_type': 0.6,
            'subject_analysis': 0.9,
            'attendee_importance': 0.5,
            'urgency': 0.7
        }
        
        weights = {
            'vip_contacts': 0.3,
            'meeting_type': 0.25,
            'subject_analysis': 0.2,
            'attendee_importance': 0.15,
            'urgency': 0.1
        }
        
        score = self.tool._calculate_weighted_score(factors, weights)
        
        # Expected: (0.8*0.3 + 0.6*0.25 + 0.9*0.2 + 0.5*0.15 + 0.7*0.1) / 1.0 = 0.715
        assert 0.71 <= score <= 0.72
    
    @patch('src.tools.prioritization_tool.PrioritizationTool._get_personalized_weights')
    @patch('src.tools.prioritization_tool.PrioritizationTool._store_priority_score')
    def test_prioritize_meeting_integration(self, mock_store, mock_weights):
        """Test full meeting prioritization integration."""
        mock_weights.return_value = self.tool.default_weights
        mock_store.return_value = True
        
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Important Client Meeting",
            start=datetime.utcnow() + timedelta(hours=2),
            end=datetime.utcnow() + timedelta(hours=3),
            attendees=["user@company.com", "client@external.com"],
            last_modified=datetime.utcnow()
        )
        
        preferences = Preferences(
            pk="user#123",
            working_hours={},
            vip_contacts=["client@external.com"],
            meeting_types={
                "client": MeetingType(duration=60, priority="high")
            }
        )
        
        result = self.tool.prioritize_meeting(meeting, preferences, "123")
        
        assert isinstance(result, PriorityScore)
        assert result.meeting_id == "meeting#456"
        assert 0.0 <= result.priority_score <= 1.0
        assert result.confidence_score > 0.0
        assert "client@external.com" in result.vip_attendees
        assert len(result.reasoning) > 0


class TestPriorityService:
    """Test cases for the PriorityService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PriorityService()
        
        # Mock the tools
        self.service.prioritization_tool = Mock()
        self.service.preference_tool = Mock()
    
    def test_prioritize_meetings_success(self):
        """Test successful meeting prioritization."""
        meetings = [
            Meeting(
                pk="user#123", sk="meeting#1", provider_event_id="1",
                provider="google", title="Low Priority", 
                start=datetime.utcnow(), end=datetime.utcnow() + timedelta(hours=1),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            ),
            Meeting(
                pk="user#123", sk="meeting#2", provider_event_id="2",
                provider="google", title="High Priority",
                start=datetime.utcnow(), end=datetime.utcnow() + timedelta(hours=1),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            )
        ]
        
        # Mock preferences
        self.service.preference_tool.retrieve_preferences.return_value = Preferences(
            pk="user#123", working_hours={}, vip_contacts=[], meeting_types={}
        )
        
        # Mock priority scores
        self.service.prioritization_tool.prioritize_meeting.side_effect = [
            PriorityScore(
                meeting_id="meeting#1", priority_score=0.3, priority_factors={},
                vip_attendees=[], meeting_type=None, urgency_level="low",
                confidence_score=0.8, reasoning="Low priority meeting"
            ),
            PriorityScore(
                meeting_id="meeting#2", priority_score=0.9, priority_factors={},
                vip_attendees=[], meeting_type=None, urgency_level="high",
                confidence_score=0.8, reasoning="High priority meeting"
            )
        ]
        
        result = self.service.prioritize_meetings(meetings, "123")
        
        assert len(result) == 2
        # Should be sorted by priority (highest first)
        assert result[0][1].priority_score == 0.9  # High priority first
        assert result[1][1].priority_score == 0.3  # Low priority second
    
    def test_resolve_conflicts_keep_highest_priority(self):
        """Test conflict resolution keeps highest priority meeting."""
        meetings = [
            Meeting(
                pk="user#123", sk="meeting#1", provider_event_id="1",
                provider="google", title="Low Priority",
                start=datetime.utcnow(), end=datetime.utcnow() + timedelta(hours=1),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            ),
            Meeting(
                pk="user#123", sk="meeting#2", provider_event_id="2",
                provider="google", title="High Priority",
                start=datetime.utcnow(), end=datetime.utcnow() + timedelta(hours=1),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            )
        ]
        
        # Mock the prioritize_meetings method
        self.service.prioritize_meetings = Mock(return_value=[
            (meetings[1], PriorityScore(
                meeting_id="meeting#2", priority_score=0.9, priority_factors={},
                vip_attendees=[], meeting_type=None, urgency_level="high",
                confidence_score=0.8, reasoning="High priority meeting"
            )),
            (meetings[0], PriorityScore(
                meeting_id="meeting#1", priority_score=0.3, priority_factors={},
                vip_attendees=[], meeting_type=None, urgency_level="low",
                confidence_score=0.8, reasoning="Low priority meeting"
            ))
        ])
        
        result = self.service.resolve_conflicts(meetings, "123")
        
        assert result['status'] == 'conflict_resolved'
        assert result['keep_meeting']['meeting_id'] == 'meeting#2'
        # Meeting with priority 0.3 should be in cancel_meetings (not > 0.3)
        assert len(result['cancel_meetings']) == 1
        assert result['cancel_meetings'][0]['meeting_id'] == 'meeting#1'


if __name__ == "__main__":
    pytest.main([__file__])