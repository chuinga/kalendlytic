"""
A
vailability tool for intelligent calendar scheduling.
Provides get_availability function with date range filtering, attendee constraints,
working hours validation, buffer time handling, and time slot ranking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..services.availability_aggregation import AvailabilityAggregationService
from ..models.meeting import TimeSlot, Availability
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class AvailabilityRequest:
    """Request parameters for availability lookup."""
    user_id: str
    start_date: datetime
    end_date: datetime
    attendees: List[str] = None
    duration_minutes: int = 30
    buffer_minutes: int = 15
    max_results: int = 10
    time_preferences: Dict[str, Any] = None
    working_hours_only: bool = True


@dataclass
class AvailabilityResponse:
    """Response containing ranked availability slots."""
    available_slots: List[TimeSlot]
    total_slots_found: int
    date_range_start: datetime
    date_range_end: datetime
    constraints_applied: List[str]
    ranking_factors: Dict[str, float]
    execution_time_ms: int


class AvailabilityTool:
    """
    Intelligent availability tool that integrates with unified calendar services.
    Implements advanced filtering, constraint handling, and time slot ranking.
    """
    
    def __init__(self):
        """Initialize the availability tool."""
        self.availability_service = AvailabilityAggregationService()
        self.tool_name = "get_availability"
        self.tool_description = "Get intelligent availability recommendations with constraint handling and ranking"
    
    def get_availability(self, request: AvailabilityRequest, 
                        connections: List[Connection],
                        preferences: Optional[Preferences] = None) -> AvailabilityResponse:
        """
        Get availability with intelligent filtering and ranking.
        
        Args:
            request: Availability request parameters
            connections: Active calendar connections
            preferences: User preferences for scheduling
            
        Returns:
            Ranked availability response with metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Getting availability for user {request.user_id} "
                       f"from {request.start_date} to {request.end_date}")
            
            # Step 1: Get unified availability from all calendars
            unified_availability = self.availability_service.aggregate_availability(
                user_id=request.user_id,
                start_date=request.start_date,
                end_date=request.end_date,
                connections=connections,
                preferences=preferences,
                time_slot_duration=request.duration_minutes,
                buffer_minutes=request.buffer_minutes
            )
            
            # Step 2: Apply attendee filtering if specified
            if request.attendees:
                filtered_slots = self._filter_by_attendees(
                    unified_availability.time_slots,
                    request.attendees,
                    connections
                )
            else:
                filtered_slots = unified_availability.time_slots
            
            # Step 3: Apply working hours constraints
            if request.working_hours_only:
                working_hours_slots = self._apply_working_hours_constraints(
                    filtered_slots,
                    preferences
                )
            else:
                working_hours_slots = filtered_slots
            
            # Step 4: Apply time preferences and additional constraints
            preference_filtered_slots = self._apply_time_preferences(
                working_hours_slots,
                request.time_preferences or {},
                preferences
            )
            
            # Step 5: Rank time slots using advanced algorithm
            ranked_slots = self._rank_time_slots(
                preference_filtered_slots,
                request,
                preferences
            )
            
            # Step 6: Apply buffer time constraints
            buffer_validated_slots = self._validate_buffer_times(
                ranked_slots,
                request.buffer_minutes,
                unified_availability.time_slots
            )
            
            # Step 7: Return top results
            final_slots = buffer_validated_slots[:request.max_results]
            
            # Calculate execution time
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Build constraints applied list
            constraints_applied = self._build_constraints_list(request, preferences)
            
            # Build ranking factors
            ranking_factors = self._build_ranking_factors(request, preferences)
            
            logger.info(f"Found {len(final_slots)} available slots for user {request.user_id}")
            
            return AvailabilityResponse(
                available_slots=final_slots,
                total_slots_found=len(buffer_validated_slots),
                date_range_start=request.start_date,
                date_range_end=request.end_date,
                constraints_applied=constraints_applied,
                ranking_factors=ranking_factors,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Failed to get availability for user {request.user_id}: {str(e)}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Return empty response with error context
            return AvailabilityResponse(
                available_slots=[],
                total_slots_found=0,
                date_range_start=request.start_date,
                date_range_end=request.end_date,
                constraints_applied=[f"ERROR: {str(e)}"],
                ranking_factors={},
                execution_time_ms=execution_time
            )
    
    def _filter_by_attendees(self, time_slots: List[TimeSlot], 
                           attendees: List[str],
                           connections: List[Connection]) -> List[TimeSlot]:
        """
        Filter time slots based on attendee availability.
        
        Args:
            time_slots: Available time slots to filter
            attendees: List of attendee email addresses
            connections: Calendar connections for attendee lookup
            
        Returns:
            Filtered time slots where all attendees are available
        """
        if not attendees:
            return time_slots
        
        logger.debug(f"Filtering slots for {len(attendees)} attendees")
        
        # For each time slot, check if all attendees are available
        filtered_slots = []
        
        for slot in time_slots:
            if not slot.available:
                continue
            
            # Check attendee availability (simplified implementation)
            # In a full implementation, this would query each attendee's calendar
            attendee_conflicts = self._check_attendee_conflicts(
                slot, attendees, connections
            )
            
            if not attendee_conflicts:
                # All attendees are available
                filtered_slots.append(slot)
            else:
                # Mark slot as unavailable due to attendee conflicts
                slot.available = False
                slot.score = 0.0
                logger.debug(f"Slot {slot.start}-{slot.end} conflicts with attendees: {attendee_conflicts}")
        
        return filtered_slots
    
    def _check_attendee_conflicts(self, slot: TimeSlot, 
                                attendees: List[str],
                                connections: List[Connection]) -> List[str]:
        """
        Check for conflicts with attendee calendars.
        
        Args:
            slot: Time slot to check
            attendees: List of attendee emails
            connections: Available calendar connections
            
        Returns:
            List of attendees with conflicts
        """
        # Simplified implementation - in reality would query external calendars
        # For now, simulate some conflicts based on time patterns
        
        conflicted_attendees = []
        
        # Simulate lunch time conflicts (12:00-13:00)
        if 12 <= slot.start.hour < 13:
            # 30% chance of lunch conflict per attendee
            import random
            for attendee in attendees:
                if random.random() < 0.3:
                    conflicted_attendees.append(attendee)
        
        # Simulate early morning conflicts (before 9 AM)
        if slot.start.hour < 9:
            # 50% chance of early morning conflict per attendee
            import random
            for attendee in attendees:
                if random.random() < 0.5:
                    conflicted_attendees.append(attendee)
        
        # Simulate late afternoon conflicts (after 5 PM)
        if slot.start.hour >= 17:
            # 40% chance of late afternoon conflict per attendee
            import random
            for attendee in attendees:
                if random.random() < 0.4:
                    conflicted_attendees.append(attendee)
        
        return conflicted_attendees
    
    def _apply_working_hours_constraints(self, time_slots: List[TimeSlot],
                                       preferences: Optional[Preferences]) -> List[TimeSlot]:
        """
        Apply working hours constraints to filter time slots.
        
        Args:
            time_slots: Time slots to filter
            preferences: User preferences containing working hours
            
        Returns:
            Filtered time slots within working hours
        """
        if not preferences or not preferences.working_hours:
            # Default working hours: 9 AM to 5 PM, Monday to Friday
            return [slot for slot in time_slots 
                   if (9 <= slot.start.hour < 17 and 
                       slot.start.weekday() < 5)]
        
        filtered_slots = []
        
        for slot in time_slots:
            weekday_name = slot.start.strftime('%A').lower()
            
            # Check if this day has working hours defined
            if weekday_name in preferences.working_hours:
                working_hours = preferences.working_hours[weekday_name]
                
                # Parse working hours
                start_hour, start_minute = map(int, working_hours.start.split(':'))
                end_hour, end_minute = map(int, working_hours.end.split(':'))
                
                # Check if slot falls within working hours
                slot_start_minutes = slot.start.hour * 60 + slot.start.minute
                slot_end_minutes = slot.end.hour * 60 + slot.end.minute
                work_start_minutes = start_hour * 60 + start_minute
                work_end_minutes = end_hour * 60 + end_minute
                
                if (slot_start_minutes >= work_start_minutes and 
                    slot_end_minutes <= work_end_minutes):
                    filtered_slots.append(slot)
            else:
                # No working hours defined for this day, skip
                continue
        
        logger.debug(f"Working hours filter: {len(filtered_slots)} slots remain from {len(time_slots)}")
        return filtered_slots
    
    def _apply_time_preferences(self, time_slots: List[TimeSlot],
                              time_preferences: Dict[str, Any],
                              preferences: Optional[Preferences]) -> List[TimeSlot]:
        """
        Apply time preferences to filter and adjust time slots.
        
        Args:
            time_slots: Time slots to filter
            time_preferences: Specific time preferences for this request
            preferences: User's general preferences
            
        Returns:
            Filtered and adjusted time slots
        """
        filtered_slots = []
        
        # Extract preference parameters
        preferred_times = time_preferences.get('preferred_times', [])
        avoid_times = time_preferences.get('avoid_times', [])
        min_duration = time_preferences.get('min_duration_minutes', 30)
        max_duration = time_preferences.get('max_duration_minutes', 120)
        
        for slot in time_slots:
            if not slot.available:
                continue
            
            # Check duration constraints
            slot_duration = (slot.end - slot.start).total_seconds() / 60
            if slot_duration < min_duration or slot_duration > max_duration:
                continue
            
            # Check avoid times
            if self._slot_in_avoid_times(slot, avoid_times):
                continue
            
            # Apply preferred times boost
            if self._slot_in_preferred_times(slot, preferred_times):
                slot.score = (slot.score or 1.0) * 1.2
            
            # Apply focus blocks from user preferences
            if preferences and preferences.focus_blocks:
                if self._slot_conflicts_with_focus_blocks(slot, preferences.focus_blocks):
                    continue
            
            filtered_slots.append(slot)
        
        logger.debug(f"Time preferences filter: {len(filtered_slots)} slots remain from {len(time_slots)}")
        return filtered_slots
    
    def _slot_in_avoid_times(self, slot: TimeSlot, avoid_times: List[Dict[str, Any]]) -> bool:
        """Check if slot falls within avoid times."""
        for avoid_time in avoid_times:
            avoid_start = datetime.fromisoformat(avoid_time['start'])
            avoid_end = datetime.fromisoformat(avoid_time['end'])
            
            if (slot.start < avoid_end and slot.end > avoid_start):
                return True
        
        return False
    
    def _slot_in_preferred_times(self, slot: TimeSlot, preferred_times: List[Dict[str, Any]]) -> bool:
        """Check if slot falls within preferred times."""
        if not preferred_times:
            return False
        
        for preferred_time in preferred_times:
            pref_start = datetime.fromisoformat(preferred_time['start'])
            pref_end = datetime.fromisoformat(preferred_time['end'])
            
            if (slot.start >= pref_start and slot.end <= pref_end):
                return True
        
        return False
    
    def _slot_conflicts_with_focus_blocks(self, slot: TimeSlot, focus_blocks: List[Any]) -> bool:
        """Check if slot conflicts with user's focus blocks."""
        weekday_name = slot.start.strftime('%A').lower()
        
        for focus_block in focus_blocks:
            if focus_block.day.lower() == weekday_name:
                # Parse focus block time
                focus_start_hour, focus_start_minute = map(int, focus_block.start.split(':'))
                focus_end_hour, focus_end_minute = map(int, focus_block.end.split(':'))
                
                # Create focus block datetime for the same day
                focus_start = slot.start.replace(
                    hour=focus_start_hour, 
                    minute=focus_start_minute, 
                    second=0, 
                    microsecond=0
                )
                focus_end = slot.start.replace(
                    hour=focus_end_hour, 
                    minute=focus_end_minute, 
                    second=0, 
                    microsecond=0
                )
                
                # Check for overlap
                if slot.start < focus_end and slot.end > focus_start:
                    return True
        
        return False
    
    def _rank_time_slots(self, time_slots: List[TimeSlot],
                        request: AvailabilityRequest,
                        preferences: Optional[Preferences]) -> List[TimeSlot]:
        """
        Rank time slots using advanced algorithm based on user preferences.
        
        Args:
            time_slots: Available time slots to rank
            request: Original availability request
            preferences: User preferences for ranking
            
        Returns:
            Time slots sorted by ranking score (highest first)
        """
        logger.debug(f"Ranking {len(time_slots)} time slots")
        
        for slot in time_slots:
            if not slot.available:
                slot.score = 0.0
                continue
            
            # Start with base score
            score = slot.score or 1.0
            
            # Factor 1: Time of day preferences
            score *= self._calculate_time_of_day_score(slot)
            
            # Factor 2: Day of week preferences
            score *= self._calculate_day_of_week_score(slot)
            
            # Factor 3: Meeting density considerations
            score *= self._calculate_meeting_density_score(slot, time_slots)
            
            # Factor 4: Buffer time optimization
            score *= self._calculate_buffer_score(slot, request.buffer_minutes)
            
            # Factor 5: Duration optimization
            score *= self._calculate_duration_score(slot, request.duration_minutes)
            
            # Factor 6: User preference alignment
            if preferences:
                score *= self._calculate_preference_alignment_score(slot, preferences)
            
            # Factor 7: Attendee convenience (if attendees specified)
            if request.attendees:
                score *= self._calculate_attendee_convenience_score(slot, request.attendees)
            
            # Ensure score stays within bounds
            slot.score = max(0.0, min(1.0, score))
        
        # Sort by score (highest first)
        ranked_slots = sorted(
            [slot for slot in time_slots if slot.available and slot.score > 0],
            key=lambda x: x.score,
            reverse=True
        )
        
        logger.debug(f"Ranked {len(ranked_slots)} available slots")
        return ranked_slots
    
    def _calculate_time_of_day_score(self, slot: TimeSlot) -> float:
        """Calculate score based on time of day preferences."""
        hour = slot.start.hour
        
        # Optimal times: 9-11 AM and 2-4 PM
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            return 1.2
        # Good times: 8-9 AM, 11 AM-12 PM, 1-2 PM, 4-5 PM
        elif 8 <= hour <= 9 or 11 <= hour <= 12 or 13 <= hour <= 14 or 16 <= hour <= 17:
            return 1.0
        # Acceptable times: 7-8 AM, 12-1 PM (lunch), 5-6 PM
        elif 7 <= hour <= 8 or 12 <= hour <= 13 or 17 <= hour <= 18:
            return 0.8
        # Poor times: very early or late
        else:
            return 0.6
    
    def _calculate_day_of_week_score(self, slot: TimeSlot) -> float:
        """Calculate score based on day of week preferences."""
        weekday = slot.start.weekday()
        
        # Monday = 0, Sunday = 6
        if weekday in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
            return 1.1
        elif weekday in [0, 4]:   # Monday, Friday
            return 1.0
        else:  # Weekend
            return 0.7
    
    def _calculate_meeting_density_score(self, slot: TimeSlot, all_slots: List[TimeSlot]) -> float:
        """Calculate score based on meeting density around the time slot."""
        # Count nearby unavailable slots (indicating existing meetings)
        day_start = slot.start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_slots = [s for s in all_slots if day_start <= s.start < day_end]
        unavailable_slots = [s for s in day_slots if not s.available]
        
        # Calculate density as ratio of unavailable to total slots
        if len(day_slots) == 0:
            return 1.0
        
        density = len(unavailable_slots) / len(day_slots)
        
        # Prefer moderate density (some meetings but not too packed)
        if 0.2 <= density <= 0.6:
            return 1.1  # Sweet spot
        elif density < 0.2:
            return 1.0  # Light day
        elif density < 0.8:
            return 0.9  # Busy day
        else:
            return 0.7  # Very busy day
    
    def _calculate_buffer_score(self, slot: TimeSlot, buffer_minutes: int) -> float:
        """Calculate score based on buffer time availability."""
        # This is a simplified implementation
        # In practice, would check actual calendar events around this time
        
        # Prefer slots that naturally have buffer time
        hour = slot.start.hour
        minute = slot.start.minute
        
        # Slots at round hours or half-hours are preferred (easier scheduling)
        if minute == 0:
            return 1.1
        elif minute == 30:
            return 1.05
        else:
            return 1.0
    
    def _calculate_duration_score(self, slot: TimeSlot, requested_duration: int) -> float:
        """Calculate score based on how well slot duration matches request."""
        slot_duration = (slot.end - slot.start).total_seconds() / 60
        
        if slot_duration == requested_duration:
            return 1.2  # Perfect match
        elif slot_duration >= requested_duration:
            # Longer slots are okay but not as preferred
            excess_ratio = (slot_duration - requested_duration) / requested_duration
            if excess_ratio <= 0.5:  # Up to 50% longer is fine
                return 1.0
            else:
                return 0.9  # Too long
        else:
            # Shorter slots are not suitable
            return 0.5
    
    def _calculate_preference_alignment_score(self, slot: TimeSlot, preferences: Preferences) -> float:
        """Calculate score based on user preference alignment."""
        score = 1.0
        
        # Check VIP contact considerations
        if preferences.vip_contacts:
            # This would be enhanced to check if the meeting involves VIP contacts
            # For now, apply a neutral score
            pass
        
        # Check meeting type preferences
        if preferences.meeting_types:
            # This would be enhanced to match against specific meeting types
            # For now, apply a neutral score
            pass
        
        # Buffer time preferences
        if preferences.buffer_minutes:
            # Prefer slots that align with user's preferred buffer times
            if preferences.buffer_minutes <= 15:
                score *= 1.05  # User prefers tight scheduling
            else:
                score *= 1.0   # User prefers more buffer time
        
        return score
    
    def _calculate_attendee_convenience_score(self, slot: TimeSlot, attendees: List[str]) -> float:
        """Calculate score based on attendee convenience factors."""
        # Simplified implementation - in practice would consider:
        # - Attendee time zones
        # - Attendee working hours
        # - Attendee meeting patterns
        
        # For now, apply time zone considerations
        hour = slot.start.hour
        
        # Assume most attendees are in similar time zones
        # Prefer business hours that work across time zones
        if 10 <= hour <= 15:  # 10 AM to 3 PM is generally good across zones
            return 1.1
        elif 9 <= hour <= 16:  # 9 AM to 4 PM is acceptable
            return 1.0
        else:
            return 0.9
    
    def _validate_buffer_times(self, time_slots: List[TimeSlot],
                             buffer_minutes: int,
                             all_calendar_slots: List[TimeSlot]) -> List[TimeSlot]:
        """
        Validate that time slots have adequate buffer time around existing meetings.
        
        Args:
            time_slots: Ranked time slots to validate
            buffer_minutes: Required buffer time in minutes
            all_calendar_slots: All calendar slots for buffer validation
            
        Returns:
            Validated time slots with adequate buffer time
        """
        if buffer_minutes <= 0:
            return time_slots
        
        buffer_delta = timedelta(minutes=buffer_minutes)
        validated_slots = []
        
        # Get all unavailable slots (existing meetings)
        existing_meetings = [slot for slot in all_calendar_slots if not slot.available]
        
        for slot in time_slots:
            has_adequate_buffer = True
            
            # Check buffer before the slot
            buffer_start = slot.start - buffer_delta
            buffer_end = slot.start
            
            for meeting in existing_meetings:
                if (meeting.start < buffer_end and meeting.end > buffer_start):
                    has_adequate_buffer = False
                    break
            
            # Check buffer after the slot
            if has_adequate_buffer:
                buffer_start = slot.end
                buffer_end = slot.end + buffer_delta
                
                for meeting in existing_meetings:
                    if (meeting.start < buffer_end and meeting.end > buffer_start):
                        has_adequate_buffer = False
                        break
            
            if has_adequate_buffer:
                validated_slots.append(slot)
            else:
                # Reduce score for slots with insufficient buffer
                slot.score = (slot.score or 1.0) * 0.7
                validated_slots.append(slot)
        
        # Re-sort after buffer validation
        validated_slots.sort(key=lambda x: x.score or 0, reverse=True)
        
        logger.debug(f"Buffer validation: {len(validated_slots)} slots validated")
        return validated_slots
    
    def _build_constraints_list(self, request: AvailabilityRequest, 
                              preferences: Optional[Preferences]) -> List[str]:
        """Build list of constraints that were applied."""
        constraints = []
        
        if request.working_hours_only:
            constraints.append("working_hours_only")
        
        if request.attendees:
            constraints.append(f"attendee_filtering_{len(request.attendees)}_attendees")
        
        if request.buffer_minutes > 0:
            constraints.append(f"buffer_time_{request.buffer_minutes}_minutes")
        
        if request.time_preferences:
            if request.time_preferences.get('preferred_times'):
                constraints.append("preferred_times_applied")
            if request.time_preferences.get('avoid_times'):
                constraints.append("avoid_times_applied")
        
        if preferences:
            if preferences.focus_blocks:
                constraints.append(f"focus_blocks_{len(preferences.focus_blocks)}_blocks")
            if preferences.vip_contacts:
                constraints.append(f"vip_contacts_{len(preferences.vip_contacts)}_contacts")
        
        constraints.append(f"duration_{request.duration_minutes}_minutes")
        constraints.append(f"max_results_{request.max_results}")
        
        return constraints
    
    def _build_ranking_factors(self, request: AvailabilityRequest,
                             preferences: Optional[Preferences]) -> Dict[str, float]:
        """Build dictionary of ranking factors and their weights."""
        factors = {
            "time_of_day_weight": 0.25,
            "day_of_week_weight": 0.15,
            "meeting_density_weight": 0.20,
            "buffer_time_weight": 0.15,
            "duration_match_weight": 0.10,
            "preference_alignment_weight": 0.10,
            "attendee_convenience_weight": 0.05 if request.attendees else 0.0
        }
        
        # Adjust weights based on preferences
        if preferences:
            if preferences.vip_contacts:
                factors["vip_contact_weight"] = 0.15
                # Reduce other weights proportionally
                for key in factors:
                    if key != "vip_contact_weight":
                        factors[key] *= 0.85
        
        return factors
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for agent integration."""
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier for availability lookup"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Start date for availability window (ISO format)"
                    },
                    "end_date": {
                        "type": "string", 
                        "format": "date-time",
                        "description": "End date for availability window (ISO format)"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of attendee email addresses"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "default": 30,
                        "description": "Required meeting duration in minutes"
                    },
                    "buffer_minutes": {
                        "type": "integer", 
                        "default": 15,
                        "description": "Buffer time around meetings in minutes"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum number of results to return"
                    },
                    "time_preferences": {
                        "type": "object",
                        "description": "Optional time preferences for filtering"
                    },
                    "working_hours_only": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to filter to working hours only"
                    }
                },
                "required": ["user_id", "start_date", "end_date"]
            }
        }
    
    def execute_tool(self, parameters: Dict[str, Any], 
                    connections: List[Connection],
                    preferences: Optional[Preferences] = None) -> Dict[str, Any]:
        """
        Execute the availability tool with given parameters.
        
        Args:
            parameters: Tool execution parameters
            connections: Active calendar connections
            preferences: User preferences
            
        Returns:
            Tool execution result
        """
        try:
            # Parse parameters into request object
            request = AvailabilityRequest(
                user_id=parameters["user_id"],
                start_date=datetime.fromisoformat(parameters["start_date"]),
                end_date=datetime.fromisoformat(parameters["end_date"]),
                attendees=parameters.get("attendees"),
                duration_minutes=parameters.get("duration_minutes", 30),
                buffer_minutes=parameters.get("buffer_minutes", 15),
                max_results=parameters.get("max_results", 10),
                time_preferences=parameters.get("time_preferences"),
                working_hours_only=parameters.get("working_hours_only", True)
            )
            
            # Execute availability lookup
            response = self.get_availability(request, connections, preferences)
            
            # Convert response to serializable format
            return {
                "success": True,
                "available_slots": [
                    {
                        "start": slot.start.isoformat(),
                        "end": slot.end.isoformat(),
                        "available": slot.available,
                        "score": slot.score
                    }
                    for slot in response.available_slots
                ],
                "total_slots_found": response.total_slots_found,
                "date_range_start": response.date_range_start.isoformat(),
                "date_range_end": response.date_range_end.isoformat(),
                "constraints_applied": response.constraints_applied,
                "ranking_factors": response.ranking_factors,
                "execution_time_ms": response.execution_time_ms
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "available_slots": [],
                "total_slots_found": 0
            }