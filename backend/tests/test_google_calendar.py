"""
Tests for Google Calendar API integration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytz

from src.services.google_calendar import GoogleCalendarService
from src.models.meeting import TimeSlot, Availability


class TestGoogleCalendarService:
    """Test cases for Google Calendar service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = GoogleCalendarService()
        self.user_id = "test_user_123"
        self.mock_credentials = Mock()
    
    @patch('src.services.google_calendar.build')
    def test_get_calendar_service(self, mock_build):
        """Test getting authenticated calendar service."""
        with patch.object(self.service.oauth_service, 'get_valid_credentials', 
                         return_value=self.mock_credentials):
            
            result = self.service._get_calendar_service(self.user_id)
            
            mock_build.assert_called_once_with('calendar', 'v3', credentials=self.mock_credentials)
    
    def test_normalize_timezone_utc(self):
        """Test timezone normalization for UTC datetime."""
        dt_str = "2024-01-15T10:00:00Z"
        result = self.service._normalize_timezone(dt_str)
        
        expected = datetime(2024, 1, 15, 10, 0, 0)
        assert result == expected
    
    def test_normalize_timezone_with_offset(self):
        """Test timezone normalization with offset."""
        dt_str = "2024-01-15T10:00:00-05:00"
        result = self.service._normalize_timezone(dt_str)
        
        # Should convert to UTC (add 5 hours)
        expected = datetime(2024, 1, 15, 15, 0, 0)
        assert result == expected
    
    def test_normalize_timezone_date_only(self):
        """Test timezone normalization for date-only string."""
        dt_str = "2024-01-15"
        result = self.service._normalize_timezone(dt_str, "America/New_York")
        
        # Should be start of day in specified timezone, converted to UTC
        assert result.date() == datetime(2024, 1, 15).date()
    
    def test_format_iso8601_utc(self):
        """Test ISO 8601 formatting for UTC."""
        dt = datetime(2024, 1, 15, 10, 0, 0)
        result = self.service._format_iso8601(dt)
        
        assert result.startswith("2024-01-15T10:00:00")
    
    @patch('src.services.google_calendar.build')
    def test_fetch_calendar_events_success(self, mock_build):
        """Test successful calendar events fetch."""
        # Mock the calendar service
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock API response
        mock_events = {
            'items': [
                {
                    'id': 'event1',
                    'summary': 'Test Meeting',
                    'start': {'dateTime': '2024-01-15T10:00:00Z'},
                    'end': {'dateTime': '2024-01-15T11:00:00Z'},
                    'status': 'confirmed'
                }
            ]
        }
        mock_service.events().list().execute.return_value = mock_events
        
        with patch.object(self.service.oauth_service, 'get_valid_credentials', 
                         return_value=self.mock_credentials):
            
            start_time = datetime(2024, 1, 15, 9, 0, 0)
            end_time = datetime(2024, 1, 15, 17, 0, 0)
            
            result = self.service.fetch_calendar_events(self.user_id, start_time, end_time)
            
            assert len(result) == 1
            assert result[0]['title'] == 'Test Meeting'
            assert result[0]['provider'] == 'google'
    
    def test_normalize_event_valid(self):
        """Test event normalization with valid data."""
        event = {
            'id': 'event123',
            'summary': 'Test Meeting',
            'start': {'dateTime': '2024-01-15T10:00:00Z'},
            'end': {'dateTime': '2024-01-15T11:00:00Z'},
            'status': 'confirmed',
            'attendees': [
                {'email': 'test@example.com', 'displayName': 'Test User'}
            ]
        }
        
        result = self.service._normalize_event(event)
        
        assert result is not None
        assert result['id'] == 'event123'
        assert result['title'] == 'Test Meeting'
        assert result['provider'] == 'google'
        assert len(result['attendees']) == 1
        assert result['attendees'][0]['email'] == 'test@example.com'
    
    def test_normalize_event_invalid(self):
        """Test event normalization with invalid data."""
        event = {
            'id': 'event123',
            'summary': 'Test Meeting'
            # Missing start/end times
        }
        
        result = self.service._normalize_event(event)
        assert result is None
    
    def test_generate_time_slots(self):
        """Test time slot generation."""
        start_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday
        end_date = datetime(2024, 1, 16, 0, 0, 0)    # Tuesday
        
        working_hours = {
            'start_time': '09:00',
            'end_time': '17:00',
            'timezone': 'UTC',
            'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
        }
        
        slots = self.service._generate_time_slots(start_date, end_date, working_hours, 60)
        
        # Should have 8 one-hour slots for Monday (9 AM to 5 PM)
        assert len(slots) == 8
        assert all(slot.available for slot in slots)
        assert slots[0].start.hour == 9
        assert slots[-1].end.hour == 17
    
    def test_slots_overlap(self):
        """Test slot overlap detection."""
        # Overlapping slots
        assert self.service._slots_overlap(
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 10, 30),
            datetime(2024, 1, 15, 11, 30)
        )
        
        # Non-overlapping slots
        assert not self.service._slots_overlap(
            datetime(2024, 1, 15, 10, 0),
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 12, 0)
        )
    
    def test_mark_busy_slots(self):
        """Test marking slots as busy based on events."""
        slots = [
            TimeSlot(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 11, 0),
                available=True
            ),
            TimeSlot(
                start=datetime(2024, 1, 15, 11, 0),
                end=datetime(2024, 1, 15, 12, 0),
                available=True
            )
        ]
        
        events = [
            {
                'start': datetime(2024, 1, 15, 10, 30),
                'end': datetime(2024, 1, 15, 11, 30),
                'transparency': 'opaque',
                'status': 'confirmed'
            }
        ]
        
        result = self.service._mark_busy_slots(slots, events)
        
        # Both slots should be marked as unavailable due to overlap
        assert not result[0].available
        assert not result[1].available
    
    @patch('src.services.google_calendar.build')
    def test_create_event_success(self, mock_build):
        """Test successful event creation."""
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock API response
        created_event = {
            'id': 'new_event_123',
            'summary': 'New Meeting',
            'start': {'dateTime': '2024-01-15T10:00:00Z'},
            'end': {'dateTime': '2024-01-15T11:00:00Z'},
            'htmlLink': 'https://calendar.google.com/event?eid=123'
        }
        mock_service.events().insert().execute.return_value = created_event
        
        with patch.object(self.service.oauth_service, 'get_valid_credentials', 
                         return_value=self.mock_credentials):
            
            event_data = {
                'title': 'New Meeting',
                'start': datetime(2024, 1, 15, 10, 0),
                'end': datetime(2024, 1, 15, 11, 0),
                'attendees': ['test@example.com']
            }
            
            result = self.service.create_event(self.user_id, event_data)
            
            assert result['event_id'] == 'new_event_123'
            assert 'html_link' in result
            mock_service.events().insert.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])