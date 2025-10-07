"""
Test cases for the preference management tool.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.tools.preference_management_tool import PreferenceManagementTool, PreferenceExtractionResult
from src.models.preferences import Preferences, WorkingHours, FocusBlock, MeetingType
from src.models.meeting import Meeting


class TestPreferenceManagementTool:
    """Test cases for preference management tool functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PreferenceManagementTool()
        self.user_id = "test_user_123"
        
        # Mock Bedrock client
        self.mock_bedrock_response = Mock()
        self.mock_bedrock_response.content = '''
        {
            "working_hours": {"monday": {"start": "09:00", "end": "17:00"}},
            "buffer_minutes": 15,
            "focus_blocks": [{"day": "monday", "start": "14:00", "end": "16:00", "title": "Deep work"}],
            "vip_contacts": ["boss@company.com"],
            "meeting_types": {"standup": {"duration": 30, "priority": "medium", "buffer_before": 0, "buffer_after": 5}},
            "confidence_score": 0.85
        }
        '''
    
    @patch('src.tools.preference_management_tool.BedrockClient')
    def test_extract_preferences_success(self, mock_bedrock_client):
        """Test successful preference extraction from natural language."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.invoke_model.return_value = self.mock_bedrock_response
        mock_bedrock_client.return_value = mock_client_instance
        
        # Create new tool instance with mocked client
        tool = PreferenceManagementTool()
        tool.bedrock_client = mock_client_instance
        
        # Test extraction
        natural_input = "I work Monday 9am to 5pm, need 15 minutes between meetings, and boss@company.com is VIP"
        result = tool.extract_preferences(natural_input, self.user_id)
        
        # Assertions
        assert isinstance(result, PreferenceExtractionResult)
        assert result.confidence_score == 0.85
        assert result.buffer_minutes == 15
        assert "boss@company.com" in result.vip_contacts
        assert "monday" in result.working_hours
        assert len(result.focus_blocks) == 1
        assert "standup" in result.meeting_types
    
    @patch('src.tools.preference_management_tool.get_dynamodb_resource')
    def test_store_preferences_success(self, mock_dynamodb):
        """Test successful preference storage."""
        # Setup mock
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_dynamodb.return_value = mock_resource
        
        # Create preferences
        preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={"monday": WorkingHours(start="09:00", end="17:00")},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=["boss@company.com"],
            meeting_types={}
        )
        
        # Create tool with mocked DynamoDB
        tool = PreferenceManagementTool()
        tool.preferences_table = mock_table
        
        # Test storage
        result = tool.store_preferences(self.user_id, preferences)
        
        # Assertions
        assert result is True
        mock_table.put_item.assert_called_once()
    
    @patch('src.tools.preference_management_tool.get_dynamodb_resource')
    def test_retrieve_preferences_success(self, mock_dynamodb):
        """Test successful preference retrieval."""
        # Setup mock
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'pk': f"user#{self.user_id}",
                'sk': 'preferences',
                'working_hours': {"monday": {"start": "09:00", "end": "17:00"}},
                'buffer_minutes': 15,
                'focus_blocks': [],
                'vip_contacts': ["boss@company.com"],
                'meeting_types': {}
            }
        }
        
        # Create tool with mocked DynamoDB
        tool = PreferenceManagementTool()
        tool.preferences_table = mock_table
        
        # Test retrieval
        result = tool.retrieve_preferences(self.user_id)
        
        # Assertions
        assert result is not None
        assert isinstance(result, Preferences)
        assert result.buffer_minutes == 15
        assert "boss@company.com" in result.vip_contacts
    
    def test_evaluate_meeting_priority_vip_meeting(self):
        """Test meeting priority evaluation for VIP meetings."""
        # Create preferences with VIP contacts
        preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=["boss@company.com"],
            meeting_types={}
        )
        
        # Create meeting with VIP attendee
        meeting = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#123",
            provider_event_id="event_123",
            provider="google",
            title="Important meeting with boss",
            start=datetime.utcnow() + timedelta(hours=1),
            end=datetime.utcnow() + timedelta(hours=2),
            attendees=["boss@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Test priority evaluation
        result = self.tool.evaluate_meeting_priority(meeting, preferences, self.user_id)
        
        # Assertions
        assert result.is_vip_meeting is True
        assert result.priority_score > 0.5  # Should be higher priority
        assert "vip_contacts" in result.priority_factors
        assert result.priority_factors["vip_contacts"] > 0.5
    
    def test_evaluate_meeting_priority_urgent_subject(self):
        """Test meeting priority evaluation for urgent meetings."""
        # Create basic preferences
        preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=[],
            meeting_types={}
        )
        
        # Create meeting with urgent subject
        meeting = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#456",
            provider_event_id="event_456",
            provider="google",
            title="URGENT: Critical system issue",
            start=datetime.utcnow() + timedelta(hours=1),
            end=datetime.utcnow() + timedelta(hours=2),
            attendees=["dev@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Test priority evaluation
        result = self.tool.evaluate_meeting_priority(meeting, preferences, self.user_id)
        
        # Assertions
        assert result.priority_score > 0.6  # Should be high priority due to urgent keyword
        assert "subject_analysis" in result.priority_factors
        assert result.priority_factors["subject_analysis"] > 0.7
    
    def test_identify_meeting_type(self):
        """Test meeting type identification."""
        # Create preferences with meeting types
        preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=[],
            meeting_types={
                "standup": MeetingType(duration=30, priority="medium", buffer_before=0, buffer_after=5)
            }
        )
        
        # Create meeting with standup in subject
        meeting = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#789",
            provider_event_id="event_789",
            provider="google",
            title="Daily standup meeting",
            start=datetime.utcnow() + timedelta(hours=1),
            end=datetime.utcnow() + timedelta(hours=2),
            attendees=[],
            last_modified=datetime.utcnow()
        )
        
        # Test meeting type identification
        meeting_type = self.tool._identify_meeting_type(meeting, preferences)
        
        # Assertions
        assert meeting_type == "standup"
    
    def test_calculate_vip_priority_no_vips(self):
        """Test VIP priority calculation when no VIPs are present."""
        # Create preferences without VIP contacts
        preferences = Preferences(
            pk=f"user#{self.user_id}",
            working_hours={},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=[],
            meeting_types={}
        )
        
        # Create meeting without VIP attendees
        meeting = Meeting(
            pk=f"user#{self.user_id}",
            sk="meeting#regular",
            provider_event_id="event_regular",
            provider="google",
            title="Regular team meeting",
            start=datetime.utcnow() + timedelta(hours=1),
            end=datetime.utcnow() + timedelta(hours=2),
            attendees=["colleague@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Test VIP priority calculation
        vip_score = self.tool._calculate_vip_priority(meeting, preferences)
        
        # Assertions
        assert vip_score == 0.0
    
    def test_update_preferences_from_feedback(self):
        """Test preference updates from user feedback."""
        # Test feedback processing
        result = self.tool.update_preferences_from_feedback(
            self.user_id, 
            "meeting_123", 
            "This meeting should have been higher priority"
        )
        
        # Assertions (currently just logs feedback)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])