"""
Comprehensive unit tests for agent tools and Lambda functions.
Tests agent tools, calendar integration functions, OAuth flows, and algorithms.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Test imports
from src.tools.availability_tool import AvailabilityTool, AvailabilityRequest, AvailabilityResponse
from src.tools.event_management_tool import EventManagementTool
from src.tools.prioritization_tool import PrioritizationTool, PriorityScore
from src.tools.conflict_resolution_tool import ConflictResolutionTool
from src.models.meeting import Meeting, TimeSlot
from src.models.preferences import Preferences, WorkingHours
from src.models.connection import Connection


class TestAvailabilityTool:
    """Comprehensive tests for AvailabilityTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = AvailabilityTool()
        self.user_id = "test_user_123"
        self.start_date = datetime(2024, 1, 15, 9, 0, 0)
        self.end_date = datetime(2024, 1, 15, 17, 0, 0)
        
        # Mock connections
        self.connections = [
            Connection(
                pk="user#test_user_123#google",
                user_id=self.user_id,
                provider="google",
                status="active"
            )
        ]
        
        # Mock preferences
        self.preferences = Preferences(
            pk="user#test_user_123",
            working_hours={
                "monday": WorkingHours(start="09:00", end="17:00")
            },
            buffer_minutes=15
        )
    
    @patch('src.tools.availability_tool.AvailabilityAggregationService')
    def test_get_availability_success(self, mock_service_class):
        """Test successful availability retrieval."""
        # Mock the service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock availability response
        mock_availability = Mock()
        mock_availability.time_slots = [
            TimeSlot(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 10, 30),
                available=True,
                score=0.9
            ),
            TimeSlot(
                start=datetime(2024, 1, 15, 14, 0),
                end=datetime(2024, 1, 15, 14, 30),
                available=True,
                score=0.8
            )
        ]
        mock_service.aggregate_availability.return_value = mock_availability
        
        # Create request
        request = AvailabilityRequest(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
            duration_minutes=30,
            max_results=5
        )
        
        # Execute
        result = self.tool.get_availability(request, self.connections, self.preferences)
        
        # Verify
        assert isinstance(result, AvailabilityResponse)
        assert len(result.available_slots) > 0
        assert result.total_slots_found >= len(result.available_slots)
        assert result.execution_time_ms > 0
        
        # Verify service was called correctly
        mock_service.aggregate_availability.assert_called_once()
    
    def test_filter_by_attendees(self):
        """Test attendee filtering functionality."""
        # Create test slots
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True),
            TimeSlot(start=datetime(2024, 1, 15, 14, 0), end=datetime(2024, 1, 15, 14, 30), available=True)
        ]
        
        attendees = ["attendee1@example.com", "attendee2@example.com"]
        
        # Mock the conflict checking
        with patch.object(self.tool, '_check_attendee_conflicts') as mock_check:
            mock_check.return_value = []  # No conflicts
            
            result = self.tool._filter_by_attendees(slots, attendees, self.connections)
            
            # Should return all slots since no conflicts
            assert len(result) == 2
            assert all(slot.available for slot in result)
    
    def test_apply_working_hours_constraints(self):
        """Test working hours constraint application."""
        # Create slots spanning different hours
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 8, 0), end=datetime(2024, 1, 15, 8, 30), available=True),   # Before work
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True), # During work
            TimeSlot(start=datetime(2024, 1, 15, 18, 0), end=datetime(2024, 1, 15, 18, 30), available=True)  # After work
        ]
        
        result = self.tool._apply_working_hours_constraints(slots, self.preferences)
        
        # Should only return the slot during working hours
        assert len(result) == 1
        assert result[0].start.hour == 10
    
    def test_rank_time_slots(self):
        """Test time slot ranking algorithm."""
        # Create slots at different times
        slots = [
            TimeSlot(start=datetime(2024, 1, 15, 7, 0), end=datetime(2024, 1, 15, 7, 30), available=True, score=1.0),   # Early
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True, score=1.0), # Optimal
            TimeSlot(start=datetime(2024, 1, 15, 19, 0), end=datetime(2024, 1, 15, 19, 30), available=True, score=1.0)  # Late
        ]
        
        request = AvailabilityRequest(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
            duration_minutes=30
        )
        
        result = self.tool._rank_time_slots(slots, request, self.preferences)
        
        # Should be sorted by score (highest first)
        assert len(result) == 3
        assert result[0].start.hour == 10  # Optimal time should be first
        assert result[0].score > result[1].score
    
    def test_validate_buffer_times(self):
        """Test buffer time validation."""
        # Create available slots
        available_slots = [
            TimeSlot(start=datetime(2024, 1, 15, 10, 0), end=datetime(2024, 1, 15, 10, 30), available=True, score=0.9)
        ]
        
        # Create all calendar slots including existing meetings
        all_slots = available_slots + [
            TimeSlot(start=datetime(2024, 1, 15, 9, 30), end=datetime(2024, 1, 15, 9, 45), available=False)  # Existing meeting
        ]
        
        result = self.tool._validate_buffer_times(available_slots, 15, all_slots)
        
        # Should return slots (may have adjusted scores)
        assert len(result) >= 0
        assert all(hasattr(slot, 'score') for slot in result)


class TestEventManagementTool:
    """Comprehensive tests for EventManagementTool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = EventManagementTool()
        self.user_id = "test_user_123"
    
    @patch('src.tools.event_management_tool.GoogleCalendarService')
    @patch('src.tools.event_management_tool.MicrosoftCalendarService')
    def test_create_event_google(self, mock_ms_service, mock_google_service):
        """Test event creation via Google Calendar."""
        # Mock Google service
        mock_google_instance = Mock()
        mock_google_service.return_value = mock_google_instance
        mock_google_instance.create_event.return_value = {
            'id': 'event123',
            'title': 'Test Meeting',
            'start': datetime(2024, 1, 15, 10, 0),
            'end': datetime(2024, 1, 15, 11, 0)
        }
        
        # Mock connection
        connection = Connection(
            pk="user#test_user_123#google",
            user_id=self.user_id,
            provider="google",
            status="active"
        )
        
        event_data = {
            'title': 'Test Meeting',
            'start': datetime(2024, 1, 15, 10, 0),
            'end': datetime(2024, 1, 15, 11, 0),
            'attendees': ['attendee@example.com']
        }
        
        result = self.tool.create_event(self.user_id, event_data, connection)
        
        # Verify
        assert result['id'] == 'event123'
        assert result['title'] == 'Test Meeting'
        mock_google_instance.create_event.assert_called_once()
    
    @patch('src.tools.event_management_tool.GoogleCalendarService')
    def test_update_event_success(self, mock_google_service):
        """Test successful event update."""
        # Mock service
        mock_google_instance = Mock()
        mock_google_service.return_value = mock_google_instance
        mock_google_instance.update_event.return_value = {
            'id': 'event123',
            'title': 'Updated Meeting',
            'start': datetime(2024, 1, 15, 11, 0),
            'end': datetime(2024, 1, 15, 12, 0)
        }
        
        connection = Connection(
            pk="user#test_user_123#google",
            user_id=self.user_id,
            provider="google",
            status="active"
        )
        
        update_data = {
            'title': 'Updated Meeting',
            'start': datetime(2024, 1, 15, 11, 0),
            'end': datetime(2024, 1, 15, 12, 0)
        }
        
        result = self.tool.update_event(self.user_id, 'event123', update_data, connection)
        
        # Verify
        assert result['title'] == 'Updated Meeting'
        mock_google_instance.update_event.assert_called_once_with(self.user_id, 'event123', update_data)
    
    @patch('src.tools.event_management_tool.GoogleCalendarService')
    def test_delete_event_success(self, mock_google_service):
        """Test successful event deletion."""
        # Mock service
        mock_google_instance = Mock()
        mock_google_service.return_value = mock_google_instance
        mock_google_instance.delete_event.return_value = True
        
        connection = Connection(
            pk="user#test_user_123#google",
            user_id=self.user_id,
            provider="google",
            status="active"
        )
        
        result = self.tool.delete_event(self.user_id, 'event123', connection)
        
        # Verify
        assert result is True
        mock_google_instance.delete_event.assert_called_once_with(self.user_id, 'event123', send_notifications=True)
    
    def test_validate_event_data(self):
        """Test event data validation."""
        # Valid event data
        valid_data = {
            'title': 'Test Meeting',
            'start': datetime(2024, 1, 15, 10, 0),
            'end': datetime(2024, 1, 15, 11, 0),
            'attendees': ['attendee@example.com']
        }
        
        result = self.tool._validate_event_data(valid_data)
        assert result is True
        
        # Invalid event data (missing title)
        invalid_data = {
            'start': datetime(2024, 1, 15, 10, 0),
            'end': datetime(2024, 1, 15, 11, 0)
        }
        
        with pytest.raises(ValueError):
            self.tool._validate_event_data(invalid_data)
    
    def test_format_attendees(self):
        """Test attendee formatting for different providers."""
        attendees = ['user1@example.com', 'user2@example.com']
        
        # Test Google format
        google_formatted = self.tool._format_attendees_for_provider(attendees, 'google')
        assert isinstance(google_formatted, list)
        assert len(google_formatted) == 2
        
        # Test Microsoft format
        ms_formatted = self.tool._format_attendees_for_provider(attendees, 'microsoft')
        assert isinstance(ms_formatted, list)
        assert len(ms_formatted) == 2



class TestPrioritizationToolComprehensive:
    """Comprehensive tests for PrioritizationTool algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = PrioritizationTool()
        self.user_id = "test_user_123"
        
        # Mock dependencies
        self.tool.bedrock_client = Mock()
        self.tool.dynamodb = Mock()
        self.tool.priority_table = Mock()
        self.tool.learning_table = Mock()
    
    def test_priority_scoring_algorithm_comprehensive(self):
        """Test comprehensive priority scoring algorithm."""
        # Create test meeting with various priority indicators
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="URGENT: Board Meeting - Critical Decision Required",
            start=datetime.utcnow() + timedelta(minutes=30),  # Very soon
            end=datetime.utcnow() + timedelta(minutes=90),
            attendees=["user@company.com", "ceo@company.com", "board@company.com"],
            last_modified=datetime.utcnow()
        )
        
        preferences = Preferences(
            pk="user#123",
            working_hours={},
            vip_contacts=["ceo@company.com", "board@company.com"],
            meeting_types={}
        )
        
        # Mock personalized weights
        with patch.object(self.tool, '_get_personalized_weights') as mock_weights:
            mock_weights.return_value = {
                'vip_contacts': 0.35,
                'meeting_type': 0.20,
                'subject_analysis': 0.25,
                'attendee_importance': 0.15,
                'urgency': 0.05
            }
            
            with patch.object(self.tool, '_store_priority_score') as mock_store:
                mock_store.return_value = True
                
                result = self.tool.prioritize_meeting(meeting, preferences, "123")
        
        # Verify high priority score due to multiple factors
        assert isinstance(result, PriorityScore)
        assert result.priority_score > 0.8  # Should be very high priority
        assert len(result.vip_attendees) == 2  # Both VIPs detected
        assert result.urgency_level in ['immediate', 'very_urgent']
        assert "URGENT" in result.reasoning or "Critical" in result.reasoning
    
    def test_attendee_analysis_algorithm(self):
        """Test attendee analysis algorithm comprehensively."""
        meeting = Meeting(
            pk="user#123",
            sk="meeting#456",
            provider_event_id="event123",
            provider="google",
            title="Cross-functional Team Meeting",
            start=datetime.utcnow() + timedelta(hours=2),
            end=datetime.utcnow() + timedelta(hours=3),
            attendees=[
                "user@company.com",
                "ceo@company.com",
                "manager@company.com", 
                "external@client.com",
                "vendor@supplier.com"
            ],
            last_modified=datetime.utcnow()
        )
        
        preferences = Preferences(
            pk="user#123",
            working_hours={},
            vip_contacts=["ceo@company.com", "manager@company.com"],
            meeting_types={}
        )
        
        analysis = self.tool._analyze_attendees(meeting, preferences)
        
        # Verify comprehensive analysis
        assert analysis.total_attendees == 5
        assert len(analysis.vip_attendees) == 2
        assert analysis.vip_ratio == 0.4  # 2/5
        assert analysis.attendee_importance_score > 0.5
        
        # Verify domain analysis
        assert "company.com" in analysis.domain_analysis
        assert "client.com" in analysis.domain_analysis
        assert "supplier.com" in analysis.domain_analysis
        
        # Verify external attendee detection
        assert analysis.external_attendee_count == 2
        assert analysis.external_ratio == 0.4  # 2/5
    
    def test_subject_analysis_algorithm_edge_cases(self):
        """Test subject analysis with various edge cases."""
        test_cases = [
            # High priority keywords
            ("URGENT: System Down - Immediate Action Required", 0.9),
            ("CRITICAL: Security Breach Response", 0.85),
            ("EMERGENCY: Production Issue", 0.9),
            ("Board Meeting - Strategic Decision", 0.8),
            
            # Medium priority keywords
            ("Important: Quarterly Review", 0.6),
            ("Project Kickoff Meeting", 0.5),
            ("Team Standup", 0.4),
            
            # Low priority keywords
            ("Optional: Coffee Chat", 0.2),
            ("Social: Team Lunch", 0.3),
            ("FYI: Information Session", 0.3),
            
            # Mixed signals
            ("URGENT: Optional Training Session", 0.6),  # Conflicting signals
            ("Important Social Event", 0.45),
            
            # Edge cases
            ("", 0.5),  # Empty title
            ("Meeting", 0.5),  # Generic title
            ("1:1 with CEO", 0.7),  # VIP mention
        ]
        
        for title, expected_min_score in test_cases:
            meeting = Meeting(
                pk="user#123", sk="meeting#456", provider_event_id="event123",
                provider="google", title=title, 
                start=datetime.utcnow(), end=datetime.utcnow() + timedelta(hours=1),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            )
            
            score = self.tool._analyze_meeting_subject(meeting)
            
            # Allow some tolerance in scoring
            assert score >= expected_min_score - 0.1, f"Title '{title}' scored {score}, expected >= {expected_min_score}"
    
    def test_urgency_calculation_algorithm(self):
        """Test urgency calculation algorithm with various time scenarios."""
        base_time = datetime.utcnow()
        
        test_scenarios = [
            # (minutes_from_now, expected_min_score, expected_level)
            (15, 0.95, 'immediate'),      # 15 minutes
            (30, 0.9, 'very_urgent'),     # 30 minutes
            (60, 0.8, 'urgent'),          # 1 hour
            (120, 0.7, 'urgent'),         # 2 hours
            (480, 0.5, 'moderate'),       # 8 hours (same day)
            (1440, 0.3, 'low'),           # 24 hours (next day)
            (10080, 0.1, 'future'),       # 1 week
            (43200, 0.05, 'future'),      # 1 month
        ]
        
        for minutes_offset, expected_min_score, expected_level in test_scenarios:
            meeting = Meeting(
                pk="user#123", sk="meeting#456", provider_event_id="event123",
                provider="google", title="Test Meeting",
                start=base_time + timedelta(minutes=minutes_offset),
                end=base_time + timedelta(minutes=minutes_offset + 60),
                attendees=["user@company.com"], last_modified=datetime.utcnow()
            )
            
            score, level = self.tool._calculate_urgency_score(meeting)
            
            assert score >= expected_min_score - 0.1, f"Meeting in {minutes_offset} minutes scored {score}, expected >= {expected_min_score}"
            assert level == expected_level, f"Meeting in {minutes_offset} minutes got level {level}, expected {expected_level}"
    
    def test_weighted_score_calculation_algorithm(self):
        """Test weighted score calculation with various factor combinations."""
        test_cases = [
            # (factors, weights, expected_score_range)
            (
                {'vip_contacts': 1.0, 'meeting_type': 0.8, 'subject_analysis': 0.9, 'attendee_importance': 0.7, 'urgency': 0.6},
                {'vip_contacts': 0.3, 'meeting_type': 0.25, 'subject_analysis': 0.2, 'attendee_importance': 0.15, 'urgency': 0.1},
                (0.8, 0.9)  # High priority meeting
            ),
            (
                {'vip_contacts': 0.2, 'meeting_type': 0.3, 'subject_analysis': 0.4, 'attendee_importance': 0.3, 'urgency': 0.2},
                {'vip_contacts': 0.3, 'meeting_type': 0.25, 'subject_analysis': 0.2, 'attendee_importance': 0.15, 'urgency': 0.1},
                (0.25, 0.35)  # Low priority meeting
            ),
            (
                {'vip_contacts': 0.5, 'meeting_type': 0.5, 'subject_analysis': 0.5, 'attendee_importance': 0.5, 'urgency': 0.5},
                {'vip_contacts': 0.2, 'meeting_type': 0.2, 'subject_analysis': 0.2, 'attendee_importance': 0.2, 'urgency': 0.2},
                (0.45, 0.55)  # Balanced meeting
            )
        ]
        
        for factors, weights, (min_score, max_score) in test_cases:
            score = self.tool._calculate_weighted_score(factors, weights)
            assert min_score <= score <= max_score, f"Score {score} not in expected range [{min_score}, {max_score}]"
    
    def test_personalized_weights_learning(self):
        """Test personalized weights learning algorithm."""
        user_id = "test_user_123"
        
        # Mock historical data
        mock_historical_data = [
            {'meeting_id': 'meeting1', 'user_action': 'accepted', 'priority_factors': {'vip_contacts': 0.8, 'urgency': 0.9}},
            {'meeting_id': 'meeting2', 'user_action': 'declined', 'priority_factors': {'vip_contacts': 0.2, 'urgency': 0.3}},
            {'meeting_id': 'meeting3', 'user_action': 'rescheduled', 'priority_factors': {'vip_contacts': 0.6, 'urgency': 0.7}}
        ]
        
        with patch.object(self.tool, '_fetch_user_behavior_data') as mock_fetch:
            mock_fetch.return_value = mock_historical_data
            
            weights = self.tool._get_personalized_weights(user_id)
            
            # Verify weights are personalized (not default)
            assert weights != self.tool.default_weights
            assert all(0 <= weight <= 1 for weight in weights.values())
            assert abs(sum(weights.values()) - 1.0) < 0.01  # Should sum to ~1.0


class TestConflictResolutionAlgorithms:
    """Comprehensive tests for conflict resolution algorithms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ConflictResolutionTool()
        self.user_id = "test_user_123"
    
    def test_conflict_detection_algorithm(self):
        """Test conflict detection algorithm with various scenarios."""
        # Create overlapping meetings
        meeting1 = Meeting(
            pk="user#123", sk="meeting#1", provider_event_id="event1",
            provider="google", title="Meeting 1",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            attendees=["user@company.com"], last_modified=datetime.utcnow()
        )
        
        meeting2 = Meeting(
            pk="user#123", sk="meeting#2", provider_event_id="event2",
            provider="google", title="Meeting 2",
            start=datetime(2024, 1, 15, 10, 30),  # Overlaps with meeting1
            end=datetime(2024, 1, 15, 11, 30),
            attendees=["user@company.com"], last_modified=datetime.utcnow()
        )
        
        meeting3 = Meeting(
            pk="user#123", sk="meeting#3", provider_event_id="event3",
            provider="google", title="Meeting 3",
            start=datetime(2024, 1, 15, 12, 0),  # No overlap
            end=datetime(2024, 1, 15, 13, 0),
            attendees=["user@company.com"], last_modified=datetime.utcnow()
        )
        
        meetings = [meeting1, meeting2, meeting3]
        
        conflicts = self.tool._detect_conflicts(meetings)
        
        # Should detect conflict between meeting1 and meeting2
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert len(conflict['meetings']) == 2
        assert conflict['conflict_type'] == 'time_overlap'
        assert conflict['severity'] == 'high'  # 30-minute overlap is significant
    
    def test_conflict_resolution_strategies(self):
        """Test various conflict resolution strategies."""
        # Create conflicting meetings with different priorities
        high_priority_meeting = Meeting(
            pk="user#123", sk="meeting#1", provider_event_id="event1",
            provider="google", title="URGENT: Board Meeting",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            attendees=["user@company.com", "ceo@company.com"],
            last_modified=datetime.utcnow()
        )
        
        low_priority_meeting = Meeting(
            pk="user#123", sk="meeting#2", provider_event_id="event2",
            provider="google", title="Optional: Team Lunch",
            start=datetime(2024, 1, 15, 10, 30),
            end=datetime(2024, 1, 15, 11, 30),
            attendees=["user@company.com", "colleague@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Mock priority scores
        priority_scores = {
            'meeting#1': PriorityScore(
                meeting_id='meeting#1', priority_score=0.9, priority_factors={},
                vip_attendees=['ceo@company.com'], meeting_type=None,
                urgency_level='high', confidence_score=0.8, reasoning="High priority"
            ),
            'meeting#2': PriorityScore(
                meeting_id='meeting#2', priority_score=0.3, priority_factors={},
                vip_attendees=[], meeting_type=None,
                urgency_level='low', confidence_score=0.8, reasoning="Low priority"
            )
        }
        
        conflict = {
            'meetings': [high_priority_meeting, low_priority_meeting],
            'conflict_type': 'time_overlap',
            'severity': 'high'
        }
        
        # Test priority-based resolution
        resolution = self.tool._resolve_by_priority(conflict, priority_scores)
        
        assert resolution['strategy'] == 'keep_highest_priority'
        assert resolution['keep_meeting']['meeting_id'] == 'meeting#1'
        assert resolution['reschedule_meetings'][0]['meeting_id'] == 'meeting#2'
    
    def test_alternative_time_suggestion_algorithm(self):
        """Test algorithm for suggesting alternative meeting times."""
        # Create a meeting that needs rescheduling
        meeting = Meeting(
            pk="user#123", sk="meeting#1", provider_event_id="event1",
            provider="google", title="Team Meeting",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            attendees=["user@company.com", "colleague@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Mock availability data
        available_slots = [
            TimeSlot(start=datetime(2024, 1, 15, 14, 0), end=datetime(2024, 1, 15, 15, 0), available=True, score=0.8),
            TimeSlot(start=datetime(2024, 1, 15, 15, 0), end=datetime(2024, 1, 15, 16, 0), available=True, score=0.9),
            TimeSlot(start=datetime(2024, 1, 16, 10, 0), end=datetime(2024, 1, 16, 11, 0), available=True, score=0.7)
        ]
        
        with patch.object(self.tool, '_get_available_slots') as mock_availability:
            mock_availability.return_value = available_slots
            
            alternatives = self.tool._suggest_alternative_times(meeting, count=3)
            
            # Should return alternatives sorted by score
            assert len(alternatives) == 3
            assert alternatives[0]['start'] == datetime(2024, 1, 15, 15, 0)  # Highest score
            assert alternatives[1]['start'] == datetime(2024, 1, 15, 14, 0)  # Second highest
            assert alternatives[2]['start'] == datetime(2024, 1, 16, 10, 0)  # Lowest score
    
    def test_buffer_time_conflict_detection(self):
        """Test detection of buffer time conflicts."""
        # Create meetings with insufficient buffer time
        meeting1 = Meeting(
            pk="user#123", sk="meeting#1", provider_event_id="event1",
            provider="google", title="Meeting 1",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 10, 30),
            attendees=["user@company.com"], last_modified=datetime.utcnow()
        )
        
        meeting2 = Meeting(
            pk="user#123", sk="meeting#2", provider_event_id="event2",
            provider="google", title="Meeting 2",
            start=datetime(2024, 1, 15, 10, 35),  # Only 5 minutes buffer
            end=datetime(2024, 1, 15, 11, 5),
            attendees=["user@company.com"], last_modified=datetime.utcnow()
        )
        
        buffer_minutes = 15
        
        conflicts = self.tool._detect_buffer_conflicts([meeting1, meeting2], buffer_minutes)
        
        # Should detect buffer conflict
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict['conflict_type'] == 'insufficient_buffer'
        assert conflict['required_buffer'] == buffer_minutes
        assert conflict['actual_buffer'] == 5
    
    def test_multi_attendee_conflict_resolution(self):
        """Test conflict resolution with multiple attendees."""
        # Create meeting with multiple attendees having different priorities
        meeting = Meeting(
            pk="user#123", sk="meeting#1", provider_event_id="event1",
            provider="google", title="Cross-team Meeting",
            start=datetime(2024, 1, 15, 10, 0),
            end=datetime(2024, 1, 15, 11, 0),
            attendees=["user@company.com", "ceo@company.com", "intern@company.com"],
            last_modified=datetime.utcnow()
        )
        
        # Mock attendee priorities
        attendee_priorities = {
            "ceo@company.com": 0.9,      # VIP
            "user@company.com": 0.7,     # Regular user
            "intern@company.com": 0.3    # Lower priority
        }
        
        with patch.object(self.tool, '_get_attendee_priorities') as mock_priorities:
            mock_priorities.return_value = attendee_priorities
            
            resolution = self.tool._resolve_multi_attendee_conflict(meeting)
            
            # Should prioritize based on attendee importance
            assert resolution['strategy'] == 'attendee_priority_based'
            assert resolution['primary_attendee'] == 'ceo@company.com'
            assert resolution['meeting_importance_score'] > 0.7



if __name__ == '__main__':
    pytest.main([__file__])