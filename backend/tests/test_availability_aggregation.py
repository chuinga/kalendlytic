"""
Tests for unified availability aggregation service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List

from src.services.availability_aggregation import AvailabilityAggregationService
from src.models.meeting import TimeSlot, Availability
from src.models.preferences import Preferences, WorkingHours, FocusBlock
from src.models.connection import Connection


class TestAvailabilityAggregationService:
    """Test cases for availability aggregation service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = AvailabilityAggregationService()
        self.user_id = "test_user_123"
        self.start_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday
        self.end_date = datetime(2024, 1, 19, 23, 59, 59)  # Friday
        
        # Mock connections (using dict for simplicity in tests)
        self.google_connection = {
            'provider': 'google',
            'status': 'active'
        }
        
        self.microsoft_connection = {
            'provider': 'microsoft',
            'status': 'active'
        }
        
        # Mock preferences
        self.preferences = Preferences(
            pk="user#test_user_123",
            working_hours={
                "monday": WorkingHours(start="09:00", end="17:00"),
                "tuesday": WorkingHours(start="09:00", end="17:00"),
                "wednesday": WorkingHours(start="09:00", end="17:00"),
                "thursday": WorkingHours(start="09:00", end="17:00"),
                "friday": WorkingHours(start="09:00", end="17:00")
            },
            buffer_minutes=15,
            focus_blocks=[
                FocusBlock(day="wednesday", start="14:00", end="16:00", title="Deep Work")
            ]
        )
    
    def test_extract_working_hours_with_preferences(self):
        """Test extracting working hours from user preferences."""
        result = self.service._extract_working_hours(self.preferences)
        
        assert result['start_time'] == '09:00'
        assert result['end_time'] == '17:00'
        assert result['timezone'] == 'UTC'
        assert result['working_days'] == [0, 1, 2, 3, 4]  # Monday to Friday
    
    def test_extract_working_hours_default(self):
        """Test extracting default working hours when no preferences."""
        result = self.service._extract_working_hours(None)
        
        assert result['start_time'] == '09:00'
        assert result['end_time'] == '17:00'
        assert result['timezone'] == 'UTC'
        assert result['working_days'] == [0, 1, 2, 3, 4]
    
    def test_generate_unified_time_slots(self):
        """Test generating unified time slots."""
        working_hours = {
            'start_time': '09:00',
            'end_time': '17:00',
            'timezone': 'UTC',
            'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
        }
        
        # Test for one day
        start = datetime(2024, 1, 15, 0, 0, 0)  # Monday
        end = datetime(2024, 1, 15, 23, 59, 59)
        
        slots = self.service._generate_unified_time_slots(start, end, working_hours, 30)
        
        # Should have 16 slots (8 hours * 2 slots per hour)
        assert len(slots) == 16
        
        # First slot should start at 9:00 AM
        assert slots[0].start.hour == 9
        assert slots[0].start.minute == 0
        
        # Last slot should end at 5:00 PM
        assert slots[-1].end.hour == 17
        assert slots[-1].end.minute == 0
        
        # All slots should be initially available
        assert all(slot.available for slot in slots)
    
    def test_detect_conflicts_with_buffer(self):
        """Test conflict detection with buffer times."""
        # Create test slots
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 10, 30), end=datetime(2024, 1, 15, 11, 0), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 11, 0), end=datetime(2024, 1, 15, 11, 30), available=True)
        ]
        
        # Create conflicting event
        events = [{
            'start': datetime(2024, 1, 15, 10, 15),
            'end': datetime(2024, 1, 15, 10, 45),
            'title': 'Test Meeting',
            'transparency': 'opaque',
            'status': 'confirmed',
            'provider': 'google'
        }]
        
        result_slots = self.service._detect_conflicts(slots, events, 15)
        
        # First two slots should be unavailable due to conflict and buffer
        assert not result_slots[0].available
        assert not result_slots[1].available
        # Third slot should still be available
        assert result_slots[2].available
    
    def test_apply_focus_blocks(self):
        """Test applying focus blocks to time slots."""
        # Create slots for Wednesday 2-4 PM
        slots = [
            TimeSlot(start=datetime(2024, 1, 17, 14, 0), end=datetime(2024, 1, 17, 14, 30), available=True),
            TimeSlot(start=datetime(2024, 1, 17, 14, 30), end=datetime(2024, 1, 17, 15, 0), available=True),
            TimeSlot(start=datetime(2024, 1, 17, 15, 0), end=datetime(2024, 1, 17, 15, 30), available=True),
            TimeSlot(start=datetime(2024, 1, 17, 15, 30), end=datetime(2024, 1, 17, 16, 0), available=True)
        ]
        
        result_slots = self.service._apply_preferences(slots, self.preferences, [])
        
        # All slots should be unavailable due to focus block
        assert all(not slot.available for slot in result_slots)
    
    def test_calculate_unified_scores(self):
        """Test unified scoring algorithm."""
        # Create slots at different times of day
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True),  # Mid-morning
            TimeSlot(start=datetime(2024, 1, 15, 14, 0), end=datetime(2024, 1, 15, 14, 30), available=True),  # Early afternoon
            TimeSlot(start=datetime(2024, 1, 15, 7, 0), end=datetime(2024, 1, 15, 7, 30), available=True),   # Very early
            TimeSlot(start=datetime(2024, 1, 15, 18, 0), end=datetime(2024, 1, 15, 18, 30), available=True)  # Late
        ]
        
        events = []  # No events for this test
        
        result_slots = self.service._calculate_unified_scores(slots, events, self.preferences)
        
        # Mid-morning and early afternoon should have higher scores
        assert result_slots[0].score > result_slots[2].score  # Mid-morning > very early
        assert result_slots[1].score > result_slots[3].score  # Early afternoon > late
    
    def test_slots_overlap(self):
        """Test slot overlap detection."""
        # Test overlapping slots
        assert self.service._slots_overlap(
            datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 10, 30), datetime(2024, 1, 15, 11, 30)
        )
        
        # Test non-overlapping slots
        assert not self.service._slots_overlap(
            datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 11, 0),
            datetime(2024, 1, 15, 11, 0), datetime(2024, 1, 15, 12, 0)
        )
        
        # Test adjacent slots (should not overlap)
        assert not self.service._slots_overlap(
            datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 10, 30),
            datetime(2024, 1, 15, 10, 30), datetime(2024, 1, 15, 11, 0)
        )
    
    def test_group_consecutive_slots(self):
        """Test grouping consecutive available slots."""
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 10, 30), end=datetime(2024, 1, 15, 11, 0), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 11, 0), end=datetime(2024, 1, 15, 11, 30), available=False),  # Gap
            TimeSlot(start=datetime(2024, 1, 15, 11, 30), end=datetime(2024, 1, 15, 12, 0), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 12, 0), end=datetime(2024, 1, 15, 12, 30), available=True)
        ]
        
        groups = self.service._group_consecutive_slots(slots)
        
        # Should have 2 groups
        assert len(groups) == 2
        
        # First group should have 2 slots
        assert len(groups[0]) == 2
        
        # Second group should have 2 slots
        assert len(groups[1]) == 2
    
    def test_find_optimal_time_slots(self):
        """Test finding optimal time slots for a meeting duration."""
        # Create availability with consecutive slots
        time_slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True, score=0.9),
            TimeSlot(start=datetime(2024, 1, 15, 10, 30), end=datetime(2024, 1, 15, 11, 0), available=True, score=0.8),
            TimeSlot(start=datetime(2024, 1, 15, 11, 0), end=datetime(2024, 1, 15, 11, 30), available=True, score=0.7),
            TimeSlot(start=datetime(2024, 1, 15, 14, 0), end=datetime(2024, 1, 15, 14, 30), available=True, score=0.6),
            TimeSlot(start=datetime(2024, 1, 15, 14, 30), end=datetime(2024, 1, 15, 15, 0), available=True, score=0.5)
        ]
        
        availability = Availability(
            user_id=self.user_id,
            date_range_start=self.start_date,
            date_range_end=self.end_date,
            time_slots=time_slots,
            last_updated=datetime.utcnow()
        )
        
        # Find slots for 60-minute meeting
        optimal_slots = self.service.find_optimal_time_slots(availability, 60, count=3)
        
        # Should find slots
        assert len(optimal_slots) > 0
        
        # First slot should start at 10:00 (highest scoring consecutive group)
        assert optimal_slots[0].start == datetime(2024, 1, 15, 10, 0)
        assert optimal_slots[0].end == datetime(2024, 1, 15, 11, 0)
    
    @patch('src.services.availability_aggregation.GoogleCalendarService')
    @patch('src.services.availability_aggregation.MicrosoftCalendarService')
    def test_aggregate_availability_multiple_providers(self, mock_microsoft_service, mock_google_service):
        """Test aggregating availability from multiple providers."""
        # Mock Google service
        mock_google_instance = Mock()
        mock_google_service.return_value = mock_google_instance
        mock_google_instance.fetch_calendar_events.return_value = [
            {
                'start': datetime(2024, 1, 15, 10, 0),
                'end': datetime(2024, 1, 15, 11, 0),
                'title': 'Google Meeting',
                'transparency': 'opaque',
                'status': 'confirmed',
                'provider': 'google'
            }
        ]
        mock_google_instance.calculate_availability.return_value = Mock()
        
        # Mock Microsoft service
        mock_microsoft_instance = Mock()
        mock_microsoft_service.return_value = mock_microsoft_instance
        mock_microsoft_instance.fetch_calendar_events.return_value = [
            {
                'start': datetime(2024, 1, 15, 14, 0),
                'end': datetime(2024, 1, 15, 15, 0),
                'title': 'Outlook Meeting',
                'transparency': 'opaque',
                'status': 'confirmed',
                'provider': 'microsoft'
            }
        ]
        mock_microsoft_instance.calculate_availability.return_value = Mock()
        
        # Create new service instance to use mocked services
        service = AvailabilityAggregationService()
        
        connections = [self.google_connection, self.microsoft_connection]
        
        result = service.aggregate_availability(
            self.user_id, self.start_date, self.end_date, connections, self.preferences
        )
        
        # Should return availability object
        assert isinstance(result, Availability)
        assert result.user_id == self.user_id
        
        # Should have called both services
        mock_google_instance.fetch_calendar_events.assert_called_once()
        mock_microsoft_instance.fetch_calendar_events.assert_called_once()
    
    def test_detect_scheduling_conflicts(self):
        """Test detecting scheduling conflicts for proposed meeting time."""
        # Mock the calendar services
        with patch.object(self.service.google_service, 'fetch_calendar_events') as mock_google_fetch:
            mock_google_fetch.return_value = [
                {
                    'start': datetime(2024, 1, 15, 10, 0),
                    'end': datetime(2024, 1, 15, 11, 0),
                    'title': 'Existing Meeting',
                    'transparency': 'opaque',
                    'status': 'confirmed',
                    'provider': 'google',
                    'id': 'event123'
                }
            ]
            
            # Test conflicting time
            result = self.service.detect_scheduling_conflicts(
                datetime(2024, 1, 15, 10, 30),  # Overlaps with existing meeting
                datetime(2024, 1, 15, 11, 30),
                self.user_id,
                [self.google_connection]
            )
            
            assert result['has_conflicts'] is True
            assert result['conflict_count'] == 1
            assert len(result['conflicts']) == 1
            assert result['conflicts'][0]['title'] == 'Existing Meeting'
    
    def test_detect_no_scheduling_conflicts(self):
        """Test detecting no conflicts for proposed meeting time."""
        with patch.object(self.service.google_service, 'fetch_calendar_events') as mock_google_fetch:
            mock_google_fetch.return_value = [
                {
                    'start': datetime(2024, 1, 15, 10, 0),
                    'end': datetime(2024, 1, 15, 11, 0),
                    'title': 'Existing Meeting',
                    'transparency': 'opaque',
                    'status': 'confirmed',
                    'provider': 'google',
                    'id': 'event123'
                }
            ]
            
            # Test non-conflicting time
            result = self.service.detect_scheduling_conflicts(
                datetime(2024, 1, 15, 14, 0),  # No overlap
                datetime(2024, 1, 15, 15, 0),
                self.user_id,
                [self.google_connection]
            )
            
            assert result['has_conflicts'] is False
            assert result['conflict_count'] == 0
            assert len(result['conflicts']) == 0


if __name__ == '__main__':
    pytest.main([__file__])