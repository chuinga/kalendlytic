"""
Unified availability aggregation service.
Merges availability data from multiple calendar providers and implements
conflict detection with configurable buffer times and scoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from .google_calendar import GoogleCalendarService
from .microsoft_calendar import MicrosoftCalendarService
from ..models.meeting import TimeSlot, Availability
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class AvailabilityAggregationService:
    """Service for aggregating availability across multiple calendar providers."""
    
    def __init__(self):
        self.google_service = GoogleCalendarService()
        self.microsoft_service = MicrosoftCalendarService()
    
    def aggregate_availability(self, user_id: str, start_date: datetime, end_date: datetime,
                             connections: List[Connection], preferences: Optional[Preferences] = None,
                             time_slot_duration: int = 30, buffer_minutes: int = 15) -> Availability:
        """
        Aggregate availability from all connected calendar providers.
        
        Args:
            user_id: User identifier
            start_date: Start of availability window (UTC)
            end_date: End of availability window (UTC)
            connections: List of active calendar connections
            preferences: User preferences for working hours and scheduling
            time_slot_duration: Duration of time slots in minutes
            buffer_minutes: Buffer time around meetings in minutes
            
        Returns:
            Unified availability with conflict detection and scoring
        """
        try:
            logger.info(f"Aggregating availability for user {user_id} from {start_date} to {end_date}")
            
            # Extract working hours from preferences
            working_hours = self._extract_working_hours(preferences)
            
            # Collect events from all connected providers
            all_events = []
            provider_availabilities = {}
            
            for connection in connections:
                try:
                    if connection.get('provider') == 'google' and connection.get('status') == 'active':
                        events = self.google_service.fetch_calendar_events(
                            user_id, start_date, end_date
                        )
                        all_events.extend(events)
                        
                        # Get provider-specific availability for comparison
                        provider_availability = self.google_service.calculate_availability(
                            user_id, start_date, end_date, working_hours, time_slot_duration
                        )
                        provider_availabilities['google'] = provider_availability
                        
                    elif connection.get('provider') == 'microsoft' and connection.get('status') == 'active':
                        events = self.microsoft_service.fetch_calendar_events(
                            user_id, start_date, end_date
                        )
                        all_events.extend(events)
                        
                        # Get provider-specific availability for comparison
                        provider_availability = self.microsoft_service.calculate_availability(
                            user_id, start_date, end_date, working_hours, time_slot_duration
                        )
                        provider_availabilities['microsoft'] = provider_availability
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch events from {connection.get('provider', 'unknown')}: {str(e)}")
                    continue
            
            # Generate unified time slots
            unified_slots = self._generate_unified_time_slots(
                start_date, end_date, working_hours, time_slot_duration
            )
            
            # Apply conflict detection across all events
            conflicted_slots = self._detect_conflicts(unified_slots, all_events, buffer_minutes)
            
            # Apply focus blocks and preferences
            preference_adjusted_slots = self._apply_preferences(
                conflicted_slots, preferences, all_events
            )
            
            # Calculate availability scores
            scored_slots = self._calculate_unified_scores(
                preference_adjusted_slots, all_events, preferences
            )
            
            logger.info(f"Generated {len(scored_slots)} unified availability slots for user {user_id}")
            
            return Availability(
                user_id=user_id,
                date_range_start=start_date,
                date_range_end=end_date,
                time_slots=scored_slots,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to aggregate availability for user {user_id}: {str(e)}")
            raise Exception(f"Failed to aggregate availability: {str(e)}")
    
    def _extract_working_hours(self, preferences: Optional[Preferences]) -> Dict[str, Any]:
        """Extract working hours configuration from user preferences."""
        if not preferences or not preferences.working_hours:
            # Default working hours (9 AM to 5 PM UTC, Monday to Friday)
            return {
                'start_time': '09:00',
                'end_time': '17:00',
                'timezone': 'UTC',
                'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
            }
        
        # Convert preferences working hours to the expected format
        # Assume preferences use day names as keys
        working_days = []
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        # Use the first working day's hours as default
        default_start = '09:00'
        default_end = '17:00'
        
        for day_name, hours in preferences.working_hours.items():
            if day_name.lower() in day_mapping:
                working_days.append(day_mapping[day_name.lower()])
                default_start = hours.start
                default_end = hours.end
        
        return {
            'start_time': default_start,
            'end_time': default_end,
            'timezone': 'UTC',  # Assume UTC for now, could be enhanced
            'working_days': working_days if working_days else [0, 1, 2, 3, 4]
        }
    
    def _generate_unified_time_slots(self, start_date: datetime, end_date: datetime,
                                   working_hours: Dict[str, Any], slot_duration: int) -> List[TimeSlot]:
        """Generate unified time slots across the date range."""
        slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # Parse working hours
        start_time_str = working_hours.get('start_time', '09:00')
        end_time_str = working_hours.get('end_time', '17:00')
        working_days = working_hours.get('working_days', [0, 1, 2, 3, 4])
        
        while current_date <= end_date_only:
            # Check if it's a working day (0 = Monday, 6 = Sunday)
            if current_date.weekday() in working_days:
                # Parse start and end times for this day
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                
                # Create datetime objects for the day (assume UTC)
                day_start = datetime.combine(current_date, datetime.min.time().replace(
                    hour=start_hour, minute=start_minute
                ))
                day_end = datetime.combine(current_date, datetime.min.time().replace(
                    hour=end_hour, minute=end_minute
                ))
                
                # Generate slots for this day
                current_slot_start = day_start
                while current_slot_start < day_end:
                    slot_end = current_slot_start + timedelta(minutes=slot_duration)
                    
                    # Ensure slot doesn't exceed day end
                    if slot_end > day_end:
                        slot_end = day_end
                    
                    # Only add slot if it's within the requested range
                    if (current_slot_start >= start_date and 
                        slot_end <= end_date and 
                        slot_end > current_slot_start):
                        
                        slots.append(TimeSlot(
                            start=current_slot_start,
                            end=slot_end,
                            available=True,
                            score=1.0
                        ))
                    
                    current_slot_start = slot_end
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _detect_conflicts(self, time_slots: List[TimeSlot], events: List[Dict[str, Any]], 
                         buffer_minutes: int) -> List[TimeSlot]:
        """
        Detect conflicts across all calendar events with configurable buffer times.
        
        Args:
            time_slots: List of time slots to check
            events: All events from all connected calendars
            buffer_minutes: Buffer time around meetings
            
        Returns:
            Time slots with conflicts marked
        """
        buffer_delta = timedelta(minutes=buffer_minutes)
        
        for event in events:
            # Skip transparent events (marked as free time)
            if event.get('transparency') == 'transparent':
                continue
            
            # Skip declined or cancelled events
            if event.get('status') in ['cancelled', 'declined']:
                continue
            
            event_start = event['start']
            event_end = event['end']
            
            # Apply buffer times
            buffered_start = event_start - buffer_delta
            buffered_end = event_end + buffer_delta
            
            # Mark overlapping slots as unavailable
            for slot in time_slots:
                if self._slots_overlap(slot.start, slot.end, buffered_start, buffered_end):
                    slot.available = False
                    slot.score = 0.0
                    
                    # Log conflict for debugging
                    logger.debug(f"Conflict detected: slot {slot.start}-{slot.end} "
                               f"conflicts with event {event.get('title', 'Unknown')} "
                               f"({event_start}-{event_end}) from {event.get('provider', 'unknown')}")
        
        return time_slots
    
    def _slots_overlap(self, slot_start: datetime, slot_end: datetime,
                      event_start: datetime, event_end: datetime) -> bool:
        """Check if a time slot overlaps with an event."""
        return (slot_start < event_end and slot_end > event_start)
    
    def _apply_preferences(self, time_slots: List[TimeSlot], preferences: Optional[Preferences],
                          events: List[Dict[str, Any]]) -> List[TimeSlot]:
        """Apply user preferences like focus blocks to time slots."""
        if not preferences:
            return time_slots
        
        # Apply focus blocks
        for focus_block in preferences.focus_blocks:
            try:
                # Parse focus block time
                start_hour, start_minute = map(int, focus_block.start.split(':'))
                end_hour, end_minute = map(int, focus_block.end.split(':'))
                
                # Map day name to weekday number
                day_mapping = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                
                focus_weekday = day_mapping.get(focus_block.day.lower())
                if focus_weekday is None:
                    continue
                
                # Mark slots during focus blocks as unavailable
                for slot in time_slots:
                    if slot.start.weekday() == focus_weekday:
                        # Create focus block start and end times for the same day
                        focus_start = slot.start.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                        focus_end = slot.start.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                        
                        # Check if slot overlaps with focus block
                        if self._slots_overlap(slot.start, slot.end, focus_start, focus_end):
                            slot.available = False
                            slot.score = 0.0
                        
            except Exception as e:
                logger.warning(f"Failed to apply focus block {focus_block.title}: {str(e)}")
                continue
        
        return time_slots
    
    def _calculate_unified_scores(self, time_slots: List[TimeSlot], events: List[Dict[str, Any]],
                                preferences: Optional[Preferences]) -> List[TimeSlot]:
        """
        Calculate availability scores for optimal time slot ranking.
        
        Scoring factors:
        - Time of day preferences (mid-morning and early afternoon preferred)
        - Proximity to existing meetings (buffer considerations)
        - Meeting density in surrounding time periods
        - VIP contact considerations
        - Meeting type priorities
        """
        buffer_minutes = preferences.buffer_minutes if preferences else 15
        buffer_delta = timedelta(minutes=buffer_minutes)
        
        for slot in time_slots:
            if not slot.available:
                continue
            
            score = 1.0
            
            # Time of day scoring
            hour = slot.start.hour
            if 9 <= hour <= 11 or 13 <= hour <= 15:
                score *= 1.2  # Prefer mid-morning and early afternoon
            elif 8 <= hour <= 9 or 15 <= hour <= 16:
                score *= 1.0  # Neutral for early morning and late afternoon
            elif hour < 8 or hour > 17:
                score *= 0.6  # Penalize very early or late slots
            elif 11 <= hour <= 13:
                score *= 0.8  # Slight penalty for lunch time
            
            # Proximity to existing meetings
            adjacent_meetings = 0
            nearby_meetings = 0
            
            for event in events:
                if event.get('transparency') == 'transparent':
                    continue
                    
                event_start = event['start']
                event_end = event['end']
                
                # Check for adjacent meetings (within buffer time)
                if (abs((slot.start - event_end).total_seconds()) <= buffer_delta.total_seconds() or
                    abs((event_start - slot.end).total_seconds()) <= buffer_delta.total_seconds()):
                    adjacent_meetings += 1
                
                # Check for nearby meetings (within 1 hour)
                elif (abs((slot.start - event_end).total_seconds()) <= 3600 or
                      abs((event_start - slot.end).total_seconds()) <= 3600):
                    nearby_meetings += 1
            
            # Penalize slots with too many adjacent meetings
            if adjacent_meetings > 0:
                score *= (0.7 ** adjacent_meetings)
            
            # Slight penalty for nearby meetings
            if nearby_meetings > 0:
                score *= (0.9 ** nearby_meetings)
            
            # Meeting density scoring (prefer slots with some buffer)
            day_start = slot.start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_events = [e for e in events if day_start <= e['start'] < day_end]
            meeting_density = len(day_events) / 8  # Normalize by 8-hour workday
            
            if meeting_density > 0.75:  # Very busy day
                score *= 0.8
            elif meeting_density < 0.25:  # Light day
                score *= 1.1
            
            # VIP contact considerations
            if preferences and preferences.vip_contacts:
                # This would need to be enhanced to check if the slot is for a VIP meeting
                # For now, we'll just apply a neutral score
                pass
            
            # Day of week preferences
            weekday = slot.start.weekday()
            if weekday in [0, 1, 2]:  # Monday, Tuesday, Wednesday
                score *= 1.05  # Slight preference for early week
            elif weekday == 4:  # Friday
                score *= 0.95  # Slight penalty for Friday
            
            # Ensure score doesn't exceed 1.0
            slot.score = min(score, 1.0)
        
        # Sort slots by score (highest first) for easier consumption
        time_slots.sort(key=lambda x: x.score if x.score is not None else 0, reverse=True)
        
        return time_slots
    
    def find_optimal_time_slots(self, availability: Availability, duration_minutes: int,
                              count: int = 5) -> List[TimeSlot]:
        """
        Find optimal time slots for a meeting of specified duration.
        
        Args:
            availability: Unified availability data
            duration_minutes: Required meeting duration in minutes
            count: Number of optimal slots to return
            
        Returns:
            List of optimal time slots sorted by score
        """
        try:
            optimal_slots = []
            
            # Group consecutive available slots
            consecutive_groups = self._group_consecutive_slots(availability.time_slots)
            
            for group in consecutive_groups:
                # Check if group can accommodate the required duration
                group_duration = (group[-1].end - group[0].start).total_seconds() / 60
                
                if group_duration >= duration_minutes:
                    # Calculate average score for the group
                    avg_score = sum(slot.score or 0 for slot in group) / len(group)
                    
                    # Create a time slot for the required duration
                    optimal_slot = TimeSlot(
                        start=group[0].start,
                        end=group[0].start + timedelta(minutes=duration_minutes),
                        available=True,
                        score=avg_score
                    )
                    
                    optimal_slots.append(optimal_slot)
            
            # Sort by score and return top results
            optimal_slots.sort(key=lambda x: x.score or 0, reverse=True)
            return optimal_slots[:count]
            
        except Exception as e:
            logger.error(f"Failed to find optimal time slots: {str(e)}")
            return []
    
    def _group_consecutive_slots(self, time_slots: List[TimeSlot]) -> List[List[TimeSlot]]:
        """Group consecutive available time slots."""
        if not time_slots:
            return []
        
        # Filter only available slots and sort by start time
        available_slots = [slot for slot in time_slots if slot.available]
        available_slots.sort(key=lambda x: x.start)
        
        groups = []
        current_group = []
        
        for slot in available_slots:
            if not current_group:
                current_group = [slot]
            elif slot.start == current_group[-1].end:
                # Consecutive slot
                current_group.append(slot)
            else:
                # Gap found, start new group
                if current_group:
                    groups.append(current_group)
                current_group = [slot]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def detect_scheduling_conflicts(self, proposed_start: datetime, proposed_end: datetime,
                                  user_id: str, connections: List[Connection]) -> Dict[str, Any]:
        """
        Detect potential scheduling conflicts for a proposed meeting time.
        
        Args:
            proposed_start: Proposed meeting start time
            proposed_end: Proposed meeting end time
            user_id: User identifier
            connections: List of active calendar connections
            
        Returns:
            Conflict detection results with details
        """
        try:
            conflicts = []
            
            # Extend time range to check for buffer conflicts
            buffer_start = proposed_start - timedelta(minutes=30)
            buffer_end = proposed_end + timedelta(minutes=30)
            
            for connection in connections:
                try:
                    events = []
                    
                    if connection.get('provider') == 'google' and connection.get('status') == 'active':
                        events = self.google_service.fetch_calendar_events(
                            user_id, buffer_start, buffer_end
                        )
                    elif connection.get('provider') == 'microsoft' and connection.get('status') == 'active':
                        events = self.microsoft_service.fetch_calendar_events(
                            user_id, buffer_start, buffer_end
                        )
                    
                    # Check for conflicts
                    for event in events:
                        if (event.get('transparency') != 'transparent' and
                            event.get('status') not in ['cancelled', 'declined'] and
                            self._slots_overlap(proposed_start, proposed_end, 
                                              event['start'], event['end'])):
                            
                            conflicts.append({
                                'provider': connection.get('provider'),
                                'event_id': event.get('id'),
                                'title': event.get('title', 'Unknown'),
                                'start': event['start'],
                                'end': event['end'],
                                'conflict_type': 'direct_overlap'
                            })
                
                except Exception as e:
                    logger.warning(f"Failed to check conflicts for {connection.get('provider', 'unknown')}: {str(e)}")
                    continue
            
            return {
                'has_conflicts': len(conflicts) > 0,
                'conflict_count': len(conflicts),
                'conflicts': conflicts,
                'proposed_start': proposed_start,
                'proposed_end': proposed_end
            }
            
        except Exception as e:
            logger.error(f"Failed to detect scheduling conflicts: {str(e)}")
            return {
                'has_conflicts': False,
                'conflict_count': 0,
                'conflicts': [],
                'error': str(e)
            }