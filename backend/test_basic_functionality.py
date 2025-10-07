#!/usr/bin/env python3
"""
Basic functionality test for Google Calendar integration.
"""

from datetime import datetime, timedelta
from src.services.google_calendar import GoogleCalendarService

def test_timezone_normalization():
    """Test timezone normalization functionality."""
    service = GoogleCalendarService()
    
    # Test UTC datetime
    utc_dt = "2024-01-15T10:00:00Z"
    result = service._normalize_timezone(utc_dt)
    expected = datetime(2024, 1, 15, 10, 0, 0)
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ UTC timezone normalization works")
    
    # Test datetime with offset
    offset_dt = "2024-01-15T10:00:00-05:00"
    result = service._normalize_timezone(offset_dt)
    expected = datetime(2024, 1, 15, 15, 0, 0)  # Should convert to UTC
    assert result == expected, f"Expected {expected}, got {result}"
    print("✓ Offset timezone normalization works")
    
    # Test date-only string
    date_only = "2024-01-15"
    result = service._normalize_timezone(date_only)
    assert result.date() == datetime(2024, 1, 15).date()
    print("✓ Date-only normalization works")

def test_iso8601_formatting():
    """Test ISO 8601 formatting."""
    service = GoogleCalendarService()
    
    dt = datetime(2024, 1, 15, 10, 0, 0)
    result = service._format_iso8601(dt)
    assert result.startswith("2024-01-15T10:00:00")
    print("✓ ISO 8601 formatting works")

def test_event_normalization():
    """Test event normalization."""
    service = GoogleCalendarService()
    
    # Valid event
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
    
    result = service._normalize_event(event)
    assert result is not None
    assert result['id'] == 'event123'
    assert result['title'] == 'Test Meeting'
    assert result['provider'] == 'google'
    assert len(result['attendees']) == 1
    print("✓ Event normalization works")
    
    # Invalid event (missing start/end)
    invalid_event = {
        'id': 'event123',
        'summary': 'Test Meeting'
    }
    
    result = service._normalize_event(invalid_event)
    assert result is None
    print("✓ Invalid event handling works")

def test_slot_overlap():
    """Test slot overlap detection."""
    service = GoogleCalendarService()
    
    # Overlapping slots
    overlap = service._slots_overlap(
        datetime(2024, 1, 15, 10, 0),
        datetime(2024, 1, 15, 11, 0),
        datetime(2024, 1, 15, 10, 30),
        datetime(2024, 1, 15, 11, 30)
    )
    assert overlap is True
    print("✓ Overlap detection works")
    
    # Non-overlapping slots
    no_overlap = service._slots_overlap(
        datetime(2024, 1, 15, 10, 0),
        datetime(2024, 1, 15, 11, 0),
        datetime(2024, 1, 15, 11, 0),
        datetime(2024, 1, 15, 12, 0)
    )
    assert no_overlap is False
    print("✓ Non-overlap detection works")

def test_time_slot_generation():
    """Test time slot generation."""
    service = GoogleCalendarService()
    
    start_date = datetime(2024, 1, 15, 0, 0, 0)  # Monday
    end_date = datetime(2024, 1, 16, 0, 0, 0)    # Tuesday
    
    working_hours = {
        'start_time': '09:00',
        'end_time': '17:00',
        'timezone': 'UTC',
        'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
    }
    
    slots = service._generate_time_slots(start_date, end_date, working_hours, 60)
    
    # Should have 8 one-hour slots for Monday (9 AM to 5 PM)
    assert len(slots) == 8
    assert all(slot.available for slot in slots)
    assert slots[0].start.hour == 9
    assert slots[-1].end.hour == 17
    print("✓ Time slot generation works")

if __name__ == "__main__":
    print("Testing Google Calendar integration...")
    
    try:
        test_timezone_normalization()
        test_iso8601_formatting()
        test_event_normalization()
        test_slot_overlap()
        test_time_slot_generation()
        
        print("\n🎉 All tests passed! Google Calendar integration is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise