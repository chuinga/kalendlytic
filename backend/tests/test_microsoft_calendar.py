"""
Tests for Microsoft Graph Calendar service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests

from src.services.microsoft_calendar import MicrosoftCalendarService
from src.models.meeting import TimeSlot, Availability


class TestMicrosoftCalendarService:
    """Test cases for Microsoft Calendar service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = MicrosoftCalendarService()
        self.user_id = "test_user_123"
        self.mock_token = "mock_access_token"
    
    @patch('src.services.microsoft_calendar.MicrosoftOAuthService')
    def test_get_auth_headers(self, mock_oauth_service):
        """Test authentication header generation."""
        # Setup mock
        mock_oauth_instance = Mock()
        mock_oauth_instance.get_valid_access_token.return_value = self.mock_token
        mock_oauth_service.return_value = mock_oauth_instance
        
        service = MicrosoftCalendarService()
        headers = service._get_auth_headers(self.user_id)
        
        assert headers['Authorization'] == f'Bearer {self.mock_token}'
        assert headers['Content-Type'] == 'application/json'
        mock_oauth_instance.get_valid_access_token.assert_called_once_with(self.user_id)
    
    def test_normalize_timezone_utc(self):
        """Test timezone normalization for UTC datetime."""
        dt_str = "2023-12-01T10:00:00Z"
        result = self.service._normalize_timezone(dt_str)
        
        expected = datetime(2023, 12, 1, 10, 0, 0)
        assert result == expected
    
    def test_normalize_timezone_with_offset(self):
        """Test timezone normalization with timezone offset."""
        dt_str = "2023-12-01T10:00:00-05:00"
        result = self.service._normalize_timezone(dt_str)
        
        # Should convert to UTC (10:00 EST = 15:00 UTC)
        expected = datetime(2023, 12, 1, 15, 0, 0)
        assert result == expected
    
    def test_format_graph_datetime(self):
        """Test formatting datetime for Graph API."""
        dt = datetime(2023, 12, 1, 10, 0, 0)
        result = self.service._format_graph_datetime(dt, 'UTC')
        
        assert result['timeZone'] == 'UTC'
        assert '2023-12-01T10:00:00' in result['dateTime']
    
    @patch('src.services.microsoft_calendar.requests.get')
    @patch.object(MicrosoftCalendarService, '_get_auth_headers')
    def test_fetch_calendar_events_success(self, mock_auth_headers, mock_requests_get):
        """Test successful calendar events fetch."""
        # Setup mocks
        mock_auth_headers.return_value = {'Authorization': f'Bearer {self.mock_token}'}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {
                    'id': 'event_1',
                    'subject': 'Test Meeting',
                    'start': {'dateTime': '2023-12-01T10:00:00Z', 'timeZone': 'UTC'},
                    'end': {'dateTime': '2023-12-01T11:00:00Z', 'timeZone': 'UTC'},
                    'attendees': [],
                    'organizer': {'emailAddress': {'address': 'test@example.com'}},
                    'isAllDay': False,
                    'showAs': 'busy'
                }
            ]
        }
        mock_requests_get.return_value = mock_response
        
        # Test
        start_time = datetime(2023, 12, 1, 9, 0, 0)
        end_time = datetime(2023, 12, 1, 17, 0, 0)
        
        events = self.service.fetch_calendar_events(self.user_id, start_time, end_time)
        
        assert len(events) == 1
        assert events[0]['id'] == 'event_1'
        assert events[0]['title'] == 'Test Meeting'
        assert events[0]['provider'] == 'microsoft'
        
        # Verify API call
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        assert 'me/events' in call_args[0][0]
    
    @patch('src.services.microsoft_calendar.requests.get')
    @patch.object(MicrosoftCalendarService, '_get_auth_headers')
    def test_fetch_calendar_events_auth_error(self, mock_auth_headers, mock_requests_get):
        """Test calendar events fetch with authentication error."""
        # Setup mocks
        mock_auth_headers.return_value = {'Authorization': f'Bearer {self.mock_token}'}
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests_get.return_value = mock_response
        
        # Test
        start_time = datetime(2023, 12, 1, 9, 0, 0)
        end_time = datetime(2023, 12, 1, 17, 0, 0)
        
        with pytest.raises(Exception) as exc_info:
            self.service.fetch_calendar_events(self.user_id, start_time, end_time)
        
        assert "Authentication failed" in str(exc_info.value)
    
    def test_normalize_event_basic(self):
        """Test basic event normalization."""
        raw_event = {
            'id': 'event_123',
            'subject': 'Team Meeting',
            'body': {'content': 'Weekly team sync'},
            'start': {'dateTime': '2023-12-01T10:00:00Z', 'timeZone': 'UTC'},
            'end': {'dateTime': '2023-12-01T11:00:00Z', 'timeZone': 'UTC'},
            'attendees': [
                {
                    'emailAddress': {'address': 'user1@example.com', 'name': 'User One'},
                    'status': {'response': 'accepted'},
                    'type': 'required'
                }
            ],
            'organizer': {'emailAddress': {'address': 'organizer@example.com'}},
            'location': {'displayName': 'Conference Room A'},
            'isAllDay': False,
            'showAs': 'busy',
            'sensitivity': 'normal',
            'categories': ['Work'],
            'webLink': 'https://outlook.com/event/123',
            'createdDateTime': '2023-11-30T09:00:00Z',
            'lastModifiedDateTime': '2023-11-30T09:30:00Z'
        }
        
        normalized = self.service._normalize_event(raw_event)
        
        assert normalized is not None
        assert normalized['id'] == 'event_123'
        assert normalized['title'] == 'Team Meeting'
        assert normalized['description'] == 'Weekly team sync'
        assert normalized['provider'] == 'microsoft'
        assert normalized['transparency'] == 'opaque'
        assert len(normalized['attendees']) == 1
        assert normalized['attendees'][0]['email'] == 'user1@example.com'
        assert normalized['location'] == 'Conference Room A'
        assert normalized['categories'] == ['Work']
    
    def test_normalize_event_free_time(self):
        """Test event normalization for free time events."""
        raw_event = {
            'id': 'event_free',
            'subject': 'Lunch Break',
            'start': {'dateTime': '2023-12-01T12:00:00Z', 'timeZone': 'UTC'},
            'end': {'dateTime': '2023-12-01T13:00:00Z', 'timeZone': 'UTC'},
            'showAs': 'free',
            'organizer': {'emailAddress': {'address': 'user@example.com'}},
            'attendees': [],
            'isAllDay': False
        }
        
        normalized = self.service._normalize_event(raw_event)
        
        assert normalized is not None
        assert normalized['transparency'] == 'transparent'
        assert normalized['show_as'] == 'free'
    
    @patch('src.services.microsoft_calendar.requests.post')
    @patch.object(MicrosoftCalendarService, '_get_auth_headers')
    def test_create_event_success(self, mock_auth_headers, mock_requests_post):
        """Test successful event creation."""
        # Setup mocks
        mock_auth_headers.return_value = {'Authorization': f'Bearer {self.mock_token}'}
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'new_event_123',
            'subject': 'New Meeting',
            'webLink': 'https://outlook.com/event/new_event_123',
            'start': {'dateTime': '2023-12-01T14:00:00Z', 'timeZone': 'UTC'},
            'end': {'dateTime': '2023-12-01T15:00:00Z', 'timeZone': 'UTC'},
            'organizer': {'emailAddress': {'address': 'user@example.com'}},
            'attendees': [],
            'isAllDay': False,
            'showAs': 'busy'
        }
        mock_requests_post.return_value = mock_response
        
        # Test data
        event_data = {
            'title': 'New Meeting',
            'description': 'Test meeting description',
            'start': datetime(2023, 12, 1, 14, 0, 0),
            'end': datetime(2023, 12, 1, 15, 0, 0),
            'attendees': ['attendee@example.com'],
            'location': 'Meeting Room B'
        }
        
        result = self.service.create_event(self.user_id, event_data)
        
        assert result['event_id'] == 'new_event_123'
        assert result['html_link'] == 'https://outlook.com/event/new_event_123'
        assert result['event_data']['title'] == 'New Meeting'
        
        # Verify API call
        mock_requests_post.assert_called_once()
        call_args = mock_requests_post.call_args
        assert 'me/events' in call_args[0][0]
        
        # Check request payload
        payload = call_args[1]['json']
        assert payload['subject'] == 'New Meeting'
        assert len(payload['attendees']) == 1
        assert payload['attendees'][0]['emailAddress']['address'] == 'attendee@example.com'
    
    def test_slots_overlap(self):
        """Test time slot overlap detection."""
        # Overlapping slots
        assert self.service._slots_overlap(
            datetime(2023, 12, 1, 10, 0, 0),  # slot: 10:00-10:30
            datetime(2023, 12, 1, 10, 30, 0),
            datetime(2023, 12, 1, 10, 15, 0),  # event: 10:15-10:45
            datetime(2023, 12, 1, 10, 45, 0)
        ) == True
        
        # Non-overlapping slots
        assert self.service._slots_overlap(
            datetime(2023, 12, 1, 10, 0, 0),  # slot: 10:00-10:30
            datetime(2023, 12, 1, 10, 30, 0),
            datetime(2023, 12, 1, 11, 0, 0),   # event: 11:00-11:30
            datetime(2023, 12, 1, 11, 30, 0)
        ) == False
        
        # Adjacent slots (no overlap)
        assert self.service._slots_overlap(
            datetime(2023, 12, 1, 10, 0, 0),  # slot: 10:00-10:30
            datetime(2023, 12, 1, 10, 30, 0),
            datetime(2023, 12, 1, 10, 30, 0),  # event: 10:30-11:00
            datetime(2023, 12, 1, 11, 0, 0)
        ) == False
    
    @patch.object(MicrosoftCalendarService, 'fetch_calendar_events')
    def test_calculate_availability(self, mock_fetch_events):
        """Test availability calculation."""
        # Mock events
        mock_fetch_events.return_value = [
            {
                'start': datetime(2023, 12, 1, 10, 0, 0),
                'end': datetime(2023, 12, 1, 11, 0, 0),
                'transparency': 'opaque',
                'show_as': 'busy'
            }
        ]
        
        # Test
        start_date = datetime(2023, 12, 1, 9, 0, 0)
        end_date = datetime(2023, 12, 1, 17, 0, 0)
        
        availability = self.service.calculate_availability(self.user_id, start_date, end_date)
        
        assert isinstance(availability, Availability)
        assert availability.user_id == self.user_id
        assert len(availability.time_slots) > 0
        
        # Check that some slots are marked as unavailable due to the busy event
        busy_slots = [slot for slot in availability.time_slots if not slot.available]
        assert len(busy_slots) > 0


if __name__ == '__main__':
    pytest.main([__file__])