"""
Event Management Tool for intelligent calendar event operations.
Provides create_event, reschedule_event, modify_event, and cancel_event functions
with video conferencing integration and cross-platform synchronization.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..services.google_calendar import GoogleCalendarService
from ..services.microsoft_calendar import MicrosoftCalendarService
from ..services.availability_aggregation import AvailabilityAggregationService
from ..models.meeting import TimeSlot, Meeting
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class ConferenceProvider(Enum):
    """Supported video conferencing providers."""
    GOOGLE_MEET = "google_meet"
    MICROSOFT_TEAMS = "microsoft_teams"
    ZOOM = "zoom"
    NONE = "none"


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving scheduling conflicts."""
    FIND_ALTERNATIVE = "find_alternative"
    NOTIFY_CONFLICTS = "notify_conflicts"
    FORCE_SCHEDULE = "force_schedule"
    CANCEL_CONFLICTING = "cancel_conflicting"


@dataclass
class EventRequest:
    """Request parameters for event operations."""
    user_id: str
    title: str
    start: datetime
    end: datetime
    attendees: List[str] = None
    description: str = ""
    location: str = ""
    conference_provider: ConferenceProvider = ConferenceProvider.NONE
    timezone: str = "UTC"
    send_notifications: bool = True
    calendar_id: str = None
    categories: List[str] = None
    sensitivity: str = "normal"


@dataclass
class RescheduleRequest:
    """Request parameters for rescheduling events."""
    user_id: str
    event_id: str
    new_start: datetime
    new_end: datetime
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.FIND_ALTERNATIVE
    max_alternatives: int = 5
    buffer_minutes: int = 15
    preserve_attendees: bool = True
    send_notifications: bool = True


@dataclass
class EventResponse:
    """Response containing event operation results."""
    success: bool
    event_id: str = None
    event_data: Dict[str, Any] = None
    conflicts: List[Dict[str, Any]] = None
    alternatives: List[TimeSlot] = None
    conference_url: str = None
    html_link: str = None
    error_message: str = None
    execution_time_ms: int = 0


class EventManagementTool:
    """
    Intelligent event management tool with cross-platform support.
    Handles event creation, modification, rescheduling, and cancellation.
    """
    
    def __init__(self):
        """Initialize the event management tool."""
        self.google_service = GoogleCalendarService()
        self.microsoft_service = MicrosoftCalendarService()
        self.availability_service = AvailabilityAggregationService()
        self.tool_name = "manage_events"
        self.tool_description = "Comprehensive event management with conflict resolution and video conferencing"
    
    def create_event(self, request: EventRequest, 
                    connections: List[Connection],
                    preferences: Optional[Preferences] = None) -> EventResponse:
        """
        Create a new calendar event with video conferencing integration.
        
        Args:
            request: Event creation request parameters
            connections: Active calendar connections
            preferences: User preferences for event creation
            
        Returns:
            Event creation response with metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Creating event '{request.title}' for user {request.user_id}")
            
            # Step 1: Validate event parameters
            validation_result = self._validate_event_request(request)
            if not validation_result["valid"]:
                return EventResponse(
                    success=False,
                    error_message=validation_result["error"],
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 2: Check for conflicts if requested
            conflicts = []
            if preferences and preferences.conflict_detection_enabled:
                conflicts = self._detect_conflicts(request, connections)
                
                if conflicts and request.user_id not in [c.get("organizer", "") for c in conflicts]:
                    logger.warning(f"Conflicts detected for event creation: {len(conflicts)} conflicts")
            
            # Step 3: Prepare event data with conference integration
            event_data = self._prepare_event_data(request, preferences)
            
            # Step 4: Create event on all connected platforms
            created_events = {}
            conference_url = None
            html_link = None
            
            for connection in connections:
                if not connection.is_active:
                    continue
                
                try:
                    if connection.provider == "google":
                        result = self.google_service.create_event(
                            user_id=request.user_id,
                            event_data=event_data,
                            calendar_id=request.calendar_id or "primary"
                        )
                        created_events["google"] = result
                        
                        # Extract conference URL from Google Meet
                        if request.conference_provider == ConferenceProvider.GOOGLE_MEET:
                            conference_url = result.get("hangout_link")
                        html_link = html_link or result.get("html_link")
                        
                    elif connection.provider == "microsoft":
                        result = self.microsoft_service.create_event(
                            user_id=request.user_id,
                            event_data=event_data,
                            calendar_id=request.calendar_id
                        )
                        created_events["microsoft"] = result
                        
                        # Extract conference URL from Teams
                        if request.conference_provider == ConferenceProvider.MICROSOFT_TEAMS:
                            conference_url = result.get("online_meeting_url")
                        html_link = html_link or result.get("html_link")
                
                except Exception as e:
                    logger.error(f"Failed to create event on {connection.provider}: {str(e)}")
                    # Continue with other providers
            
            if not created_events:
                return EventResponse(
                    success=False,
                    error_message="Failed to create event on any connected calendar",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 5: Store meeting record for tracking
            primary_event = list(created_events.values())[0]
            meeting_record = self._create_meeting_record(request, primary_event, created_events)
            
            logger.info(f"Successfully created event {primary_event.get('event_id')} for user {request.user_id}")
            
            return EventResponse(
                success=True,
                event_id=primary_event.get("event_id"),
                event_data=primary_event.get("event_data"),
                conflicts=conflicts,
                conference_url=conference_url,
                html_link=html_link,
                execution_time_ms=self._calculate_execution_time(start_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to create event for user {request.user_id}: {str(e)}")
            return EventResponse(
                success=False,
                error_message=f"Event creation failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            ) 
   
    def reschedule_event(self, request: RescheduleRequest,
                        connections: List[Connection],
                        preferences: Optional[Preferences] = None) -> EventResponse:
        """
        Reschedule an existing event with conflict resolution logic.
        
        Args:
            request: Reschedule request parameters
            connections: Active calendar connections
            preferences: User preferences for rescheduling
            
        Returns:
            Reschedule response with alternatives if needed
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Rescheduling event {request.event_id} for user {request.user_id}")
            
            # Step 1: Get existing event details
            existing_event = self._get_event_details(request.event_id, request.user_id, connections)
            if not existing_event:
                return EventResponse(
                    success=False,
                    error_message="Event not found or access denied",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 2: Check for conflicts at new time
            conflicts = self._detect_conflicts_for_reschedule(request, connections, existing_event)
            
            # Step 3: Apply conflict resolution strategy
            if conflicts:
                resolution_result = self._resolve_conflicts(
                    request, conflicts, connections, preferences
                )
                
                if not resolution_result["can_proceed"]:
                    return EventResponse(
                        success=False,
                        conflicts=conflicts,
                        alternatives=resolution_result.get("alternatives", []),
                        error_message="Cannot reschedule due to conflicts",
                        execution_time_ms=self._calculate_execution_time(start_time)
                    )
                
                # Update request with resolved time if alternative was selected
                if resolution_result.get("alternative_time"):
                    request.new_start = resolution_result["alternative_time"]["start"]
                    request.new_end = resolution_result["alternative_time"]["end"]
            
            # Step 4: Update event on all platforms
            updated_events = {}
            
            for connection in connections:
                if not connection.is_active:
                    continue
                
                try:
                    update_data = {
                        "start": request.new_start,
                        "end": request.new_end,
                        "send_notifications": request.send_notifications
                    }
                    
                    if connection.provider == "google":
                        result = self.google_service.update_event(
                            user_id=request.user_id,
                            event_id=request.event_id,
                            event_data=update_data
                        )
                        updated_events["google"] = result
                        
                    elif connection.provider == "microsoft":
                        result = self.microsoft_service.update_event(
                            user_id=request.user_id,
                            event_id=request.event_id,
                            event_data=update_data
                        )
                        updated_events["microsoft"] = result
                
                except Exception as e:
                    logger.error(f"Failed to update event on {connection.provider}: {str(e)}")
            
            if not updated_events:
                return EventResponse(
                    success=False,
                    error_message="Failed to update event on any connected calendar",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            primary_event = list(updated_events.values())[0]
            
            logger.info(f"Successfully rescheduled event {request.event_id} for user {request.user_id}")
            
            return EventResponse(
                success=True,
                event_id=request.event_id,
                event_data=primary_event.get("event_data"),
                conflicts=conflicts if conflicts else None,
                execution_time_ms=self._calculate_execution_time(start_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to reschedule event for user {request.user_id}: {str(e)}")
            return EventResponse(
                success=False,
                error_message=f"Reschedule failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            )
    
    def modify_event(self, user_id: str, event_id: str, modifications: Dict[str, Any],
                    connections: List[Connection],
                    preferences: Optional[Preferences] = None) -> EventResponse:
        """
        Modify an existing event (title, description, attendees, etc.).
        
        Args:
            user_id: User identifier
            event_id: Event ID to modify
            modifications: Dictionary of fields to modify
            connections: Active calendar connections
            preferences: User preferences
            
        Returns:
            Modification response
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Modifying event {event_id} for user {user_id}")
            
            # Step 1: Validate modifications
            if not modifications:
                return EventResponse(
                    success=False,
                    error_message="No modifications specified",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 2: Get existing event details
            existing_event = self._get_event_details(event_id, user_id, connections)
            if not existing_event:
                return EventResponse(
                    success=False,
                    error_message="Event not found or access denied",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 3: Check if time changes require conflict detection
            time_changed = 'start' in modifications or 'end' in modifications
            conflicts = []
            
            if time_changed and preferences and preferences.conflict_detection_enabled:
                # Create temporary request for conflict detection
                temp_request = EventRequest(
                    user_id=user_id,
                    title=existing_event.get('title', ''),
                    start=modifications.get('start', existing_event['start']),
                    end=modifications.get('end', existing_event['end'])
                )
                conflicts = self._detect_conflicts(temp_request, connections)
            
            # Step 4: Update event on all platforms
            updated_events = {}
            
            for connection in connections:
                if not connection.is_active:
                    continue
                
                try:
                    if connection.provider == "google":
                        result = self.google_service.update_event(
                            user_id=user_id,
                            event_id=event_id,
                            event_data=modifications
                        )
                        updated_events["google"] = result
                        
                    elif connection.provider == "microsoft":
                        result = self.microsoft_service.update_event(
                            user_id=user_id,
                            event_id=event_id,
                            event_data=modifications
                        )
                        updated_events["microsoft"] = result
                
                except Exception as e:
                    logger.error(f"Failed to modify event on {connection.provider}: {str(e)}")
            
            if not updated_events:
                return EventResponse(
                    success=False,
                    error_message="Failed to modify event on any connected calendar",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            primary_event = list(updated_events.values())[0]
            
            logger.info(f"Successfully modified event {event_id} for user {user_id}")
            
            return EventResponse(
                success=True,
                event_id=event_id,
                event_data=primary_event.get("event_data"),
                conflicts=conflicts if conflicts else None,
                execution_time_ms=self._calculate_execution_time(start_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to modify event for user {user_id}: {str(e)}")
            return EventResponse(
                success=False,
                error_message=f"Event modification failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            )
    
    def cancel_event(self, user_id: str, event_id: str,
                    connections: List[Connection],
                    send_notifications: bool = True,
                    cancellation_reason: str = "") -> EventResponse:
        """
        Cancel an existing event across all platforms.
        
        Args:
            user_id: User identifier
            event_id: Event ID to cancel
            connections: Active calendar connections
            send_notifications: Whether to send cancellation notifications
            cancellation_reason: Optional reason for cancellation
            
        Returns:
            Cancellation response
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Cancelling event {event_id} for user {user_id}")
            
            # Step 1: Get existing event details for logging
            existing_event = self._get_event_details(event_id, user_id, connections)
            
            # Step 2: Delete event from all platforms
            deletion_results = {}
            
            for connection in connections:
                if not connection.is_active:
                    continue
                
                try:
                    if connection.provider == "google":
                        success = self.google_service.delete_event(
                            user_id=user_id,
                            event_id=event_id,
                            send_notifications=send_notifications
                        )
                        deletion_results["google"] = success
                        
                    elif connection.provider == "microsoft":
                        success = self.microsoft_service.delete_event(
                            user_id=user_id,
                            event_id=event_id
                        )
                        deletion_results["microsoft"] = success
                
                except Exception as e:
                    logger.error(f"Failed to cancel event on {connection.provider}: {str(e)}")
                    deletion_results[connection.provider] = False
            
            # Check if at least one deletion succeeded
            any_success = any(deletion_results.values()) if deletion_results else False
            
            if not any_success:
                return EventResponse(
                    success=False,
                    error_message="Failed to cancel event on any connected calendar",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            logger.info(f"Successfully cancelled event {event_id} for user {user_id}")
            
            return EventResponse(
                success=True,
                event_id=event_id,
                event_data=existing_event,
                execution_time_ms=self._calculate_execution_time(start_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to cancel event for user {user_id}: {str(e)}")
            return EventResponse(
                success=False,
                error_message=f"Event cancellation failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            )    

    def _validate_event_request(self, request: EventRequest) -> Dict[str, Any]:
        """Validate event request parameters."""
        try:
            # Check required fields
            if not request.title.strip():
                return {"valid": False, "error": "Event title is required"}
            
            if not request.start or not request.end:
                return {"valid": False, "error": "Start and end times are required"}
            
            # Check time logic
            if request.start >= request.end:
                return {"valid": False, "error": "End time must be after start time"}
            
            # Check duration (max 24 hours)
            duration = request.end - request.start
            if duration.total_seconds() > 24 * 3600:
                return {"valid": False, "error": "Event duration cannot exceed 24 hours"}
            
            # Validate attendees format
            if request.attendees:
                for attendee in request.attendees:
                    if isinstance(attendee, str) and '@' not in attendee:
                        return {"valid": False, "error": f"Invalid email format: {attendee}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _prepare_event_data(self, request: EventRequest, preferences: Optional[Preferences]) -> Dict[str, Any]:
        """Prepare event data for calendar service calls."""
        event_data = {
            "title": request.title,
            "description": request.description,
            "start": request.start,
            "end": request.end,
            "timezone": request.timezone,
            "send_notifications": request.send_notifications
        }
        
        if request.location:
            event_data["location"] = request.location
        
        if request.attendees:
            event_data["attendees"] = request.attendees
        
        if request.categories:
            event_data["categories"] = request.categories
        
        if request.sensitivity != "normal":
            event_data["sensitivity"] = request.sensitivity
        
        # Add conference integration
        if request.conference_provider != ConferenceProvider.NONE:
            event_data["add_conference"] = True
        
        return event_data
    
    def _detect_conflicts(self, request: EventRequest, connections: List[Connection]) -> List[Dict[str, Any]]:
        """Detect scheduling conflicts for the requested time slot."""
        try:
            conflicts = []
            
            # Get availability for the requested time period
            availability = self.availability_service.aggregate_availability(
                user_id=request.user_id,
                start_date=request.start,
                end_date=request.end,
                connections=connections,
                time_slot_duration=30  # Check in 30-minute increments
            )
            
            # Find overlapping unavailable slots
            for slot in availability.time_slots:
                if not slot.available:
                    # Check if this slot overlaps with our requested time
                    if (slot.start < request.end and slot.end > request.start):
                        conflicts.append({
                            "start": slot.start,
                            "end": slot.end,
                            "type": "existing_event",
                            "severity": "high"
                        })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {str(e)}")
            return []
    
    def _detect_conflicts_for_reschedule(self, request: RescheduleRequest, 
                                       connections: List[Connection],
                                       existing_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts for rescheduling, excluding the event being moved."""
        try:
            # Create temporary event request for conflict detection
            temp_request = EventRequest(
                user_id=request.user_id,
                title=existing_event.get('title', ''),
                start=request.new_start,
                end=request.new_end
            )
            
            conflicts = self._detect_conflicts(temp_request, connections)
            
            # Filter out the event being rescheduled itself
            filtered_conflicts = []
            for conflict in conflicts:
                # Skip if this is the same event (approximate time match)
                if not self._is_same_event_time(conflict, existing_event):
                    filtered_conflicts.append(conflict)
            
            return filtered_conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect reschedule conflicts: {str(e)}")
            return []
    
    def _resolve_conflicts(self, request: RescheduleRequest, conflicts: List[Dict[str, Any]],
                          connections: List[Connection], preferences: Optional[Preferences]) -> Dict[str, Any]:
        """Resolve scheduling conflicts based on strategy."""
        try:
            if request.conflict_resolution == ConflictResolutionStrategy.FORCE_SCHEDULE:
                return {"can_proceed": True}
            
            elif request.conflict_resolution == ConflictResolutionStrategy.NOTIFY_CONFLICTS:
                return {"can_proceed": False, "conflicts": conflicts}
            
            elif request.conflict_resolution == ConflictResolutionStrategy.FIND_ALTERNATIVE:
                # Find alternative time slots
                alternatives = self._find_alternative_times(request, connections, preferences)
                
                if alternatives:
                    # Return the best alternative
                    best_alternative = alternatives[0]
                    return {
                        "can_proceed": True,
                        "alternative_time": {
                            "start": best_alternative.start,
                            "end": best_alternative.end
                        },
                        "alternatives": alternatives
                    }
                else:
                    return {"can_proceed": False, "alternatives": []}
            
            else:
                return {"can_proceed": False}
                
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {str(e)}")
            return {"can_proceed": False}
    
    def _find_alternative_times(self, request: RescheduleRequest, 
                               connections: List[Connection],
                               preferences: Optional[Preferences]) -> List[TimeSlot]:
        """Find alternative time slots for rescheduling."""
        try:
            # Calculate duration
            duration = request.new_end - request.new_start
            duration_minutes = int(duration.total_seconds() / 60)
            
            # Search for alternatives in the next 7 days
            search_start = request.new_start.replace(hour=9, minute=0, second=0, microsecond=0)
            search_end = search_start + timedelta(days=7)
            
            # Get availability for the search period
            availability = self.availability_service.aggregate_availability(
                user_id=request.user_id,
                start_date=search_start,
                end_date=search_end,
                connections=connections,
                time_slot_duration=duration_minutes,
                buffer_minutes=request.buffer_minutes
            )
            
            # Filter available slots and limit results
            alternatives = [slot for slot in availability.time_slots if slot.available]
            alternatives = alternatives[:request.max_alternatives]
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Failed to find alternative times: {str(e)}")
            return []
    
    def _get_event_details(self, event_id: str, user_id: str, connections: List[Connection]) -> Optional[Dict[str, Any]]:
        """Get event details from connected calendars."""
        try:
            for connection in connections:
                if not connection.is_active:
                    continue
                
                try:
                    if connection.provider == "google":
                        # This would need to be implemented in GoogleCalendarService
                        # For now, return a placeholder
                        return {"id": event_id, "title": "Event", "start": datetime.utcnow(), "end": datetime.utcnow()}
                    
                    elif connection.provider == "microsoft":
                        # This would need to be implemented in MicrosoftCalendarService
                        # For now, return a placeholder
                        return {"id": event_id, "title": "Event", "start": datetime.utcnow(), "end": datetime.utcnow()}
                
                except Exception as e:
                    logger.error(f"Failed to get event from {connection.provider}: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get event details: {str(e)}")
            return None
    
    def _create_meeting_record(self, request: EventRequest, primary_event: Dict[str, Any], 
                              all_events: Dict[str, Any]) -> Meeting:
        """Create a meeting record for tracking."""
        try:
            meeting = Meeting(
                pk=f"user#{request.user_id}",
                sk=f"meeting#{primary_event.get('event_id')}",
                provider_event_id=primary_event.get('event_id'),
                provider=list(all_events.keys())[0],  # Primary provider
                title=request.title,
                start=request.start,
                end=request.end,
                attendees=request.attendees or [],
                status="confirmed",
                priority_score=0.5,
                created_by_agent=True,
                last_modified=datetime.utcnow()
            )
            
            # In a real implementation, this would be saved to DynamoDB
            logger.info(f"Created meeting record for event {primary_event.get('event_id')}")
            
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to create meeting record: {str(e)}")
            return None
    
    def _is_same_event_time(self, conflict: Dict[str, Any], existing_event: Dict[str, Any]) -> bool:
        """Check if conflict represents the same event being rescheduled."""
        try:
            # Compare times with some tolerance (5 minutes)
            tolerance = timedelta(minutes=5)
            
            conflict_start = conflict.get('start')
            conflict_end = conflict.get('end')
            event_start = existing_event.get('start')
            event_end = existing_event.get('end')
            
            if not all([conflict_start, conflict_end, event_start, event_end]):
                return False
            
            start_match = abs(conflict_start - event_start) <= tolerance
            end_match = abs(conflict_end - event_end) <= tolerance
            
            return start_match and end_match
            
        except Exception as e:
            logger.error(f"Failed to compare event times: {str(e)}")
            return False
    
    def _calculate_execution_time(self, start_time: datetime) -> int:
        """Calculate execution time in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for agent integration."""
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "reschedule", "modify", "cancel"],
                        "description": "Event management action to perform"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier for event management"
                    },
                    "event_data": {
                        "type": "object",
                        "description": "Event data for creation or modification"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Event ID for reschedule, modify, or cancel operations"
                    },
                    "conflict_resolution": {
                        "type": "string",
                        "enum": ["find_alternative", "notify_conflicts", "force_schedule"],
                        "description": "Strategy for resolving scheduling conflicts"
                    }
                },
                "required": ["action", "user_id"]
            }
        }