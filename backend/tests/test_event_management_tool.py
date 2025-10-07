"""
Tests for the Event Management Tool.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.tools.event_management_tool import (
    EventManagementTool, 
    EventRequest, 
    RescheduleRequest,
    ConferenceProvider,
    ConflictResolutionStrategy
)
from src.models.connection import Connection
from src.models.preferences import Preferences


class TestEventManagementTool:
    """Test cases for EventManagementTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = EventManagementTool()
        self.user_id = "test_user_123"
        
        # Mock connections
        self.google_connection = Mock()
        self.google_connection.provider = "google"
        self.google_connection.is_active = True
        self.google_connection.calendar_id = "primary"
        
        self.microsoft_connection = Mock()
        self.microsoft_connection.provider = "microsoft"
        self.microsoft_connection.is_active = True
        self.microsoft_connection.calendar_id = "default"
        
        self.connections = [self.google_connection, self.microsoft_connection]
        
        # Mock preferences
        self.preferences = Mock()
        self.preferences.conflict_detection_enabled = True
        self.preferences.buffer_minutes = 15
    
    def test_validate_event_request_valid(self):
        """Test event request validation with valid data."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time,
            attendees=["test@example.com"]
        )
        
        result = self.tool._validate_event_request(request)
        assert result["valid"] is True
    
    def test_validate_event_request_invalid_title(self):
        """Test event request validation with empty title."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        request = EventRequest(
            user_id=self.user_id,
            title="",
            start=start_time,
            end=end_time
        )
        
        result = self.tool._validate_event_request(request)
        assert result["valid"] is False
        assert "title is required" in result["error"]
    
    def test_validate_event_request_invalid_time_order(self):
        """Test event request validation with end time before start time."""
        start_time = datetime.utcnow() + timedelta(hours=2)
        end_time = start_time - timedelta(hours=1)  # End before start
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time
        )
        
        result = self.tool._validate_event_request(request)
        assert result["valid"] is False
        assert "End time must be after start time" in result["error"]
    
    def test_validate_event_request_too_long_duration(self):
        """Test event request validation with duration exceeding 24 hours."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=25)  # 25 hours duration
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time
        )
        
        result = self.tool._validate_event_request(request)
        assert result["valid"] is False
        assert "cannot exceed 24 hours" in result["error"]
    
    def test_prepare_event_data_basic(self):
        """Test preparing event data with basic information."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time,
            description="Test description",
            location="Conference Room A",
            attendees=["test@example.com"],
            conference_provider=ConferenceProvider.GOOGLE_MEET
        )
        
        event_data = self.tool._prepare_event_data(request, self.preferences)
        
        assert event_data["title"] == "Test Meeting"
        assert event_data["description"] == "Test description"
        assert event_data["location"] == "Conference Room A"
        assert event_data["attendees"] == ["test@example.com"]
        assert event_data["add_conference"] is True
        assert event_data["start"] == start_time
        assert event_data["end"] == end_time
    
    def test_prepare_event_data_no_conference(self):
        """Test preparing event data without conference integration."""
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time,
            conference_provider=ConferenceProvider.NONE
        )
        
        event_data = self.tool._prepare_event_data(request, self.preferences)
        
        assert "add_conference" not in event_data
    
    @patch('src.tools.event_management_tool.EventManagementTool._detect_conflicts')
    @patch('src.services.google_calendar.GoogleCalendarService.create_event')
    @patch('src.services.microsoft_calendar.MicrosoftCalendarService.create_event')
    def test_create_event_success(self, mock_ms_create, mock_google_create, mock_detect_conflicts):
        """Test successful event creation."""
        # Mock responses
        mock_detect_conflicts.return_value = []
        mock_google_create.return_value = {
            "event_id": "google_event_123",
            "html_link": "https://calendar.google.com/event/123",
            "hangout_link": "https://meet.google.com/abc-def-ghi",
            "event_data": {"title": "Test Meeting"}
        }
        mock_ms_create.return_value = {
            "event_id": "ms_event_456", 
            "html_link": "https://outlook.com/event/456",
            "event_data": {"title": "Test Meeting"}
        }
        
        start_time = datetime.utcnow() + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        request = EventRequest(
            user_id=self.user_id,
            title="Test Meeting",
            start=start_time,
            end=end_time,
            conference_provider=ConferenceProvider.GOOGLE_MEET
        )
        
        response = self.tool.create_event(request, self.connections, self.preferences)
        
        assert response.success is True
        assert response.event_id == "google_event_123"
        assert response.conference_url == "https://meet.google.com/abc-def-ghi"
        assert mock_google_create.called
        assert mock_ms_create.called
    
    def test_get_tool_schema(self):
        """Test getting the tool schema."""
        schema = self.tool.get_tool_schema()
        
        assert schema["name"] == "manage_events"
        assert "description" in schema
        assert "parameters" in schema
        assert "action" in schema["parameters"]["properties"]
        assert "user_id" in schema["parameters"]["properties"]
        
        # Check action enum values
        action_enum = schema["parameters"]["properties"]["action"]["enum"]
        assert "create" in action_enum
        assert "reschedule" in action_enum
        assert "modify" in action_enum
        assert "cancel" in action_enum


if __name__ == "__main__":
    pytest.main([__file__])