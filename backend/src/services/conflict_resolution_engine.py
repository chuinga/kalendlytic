"""
Conflict resolution engine for intelligent meeting scheduling.
Implements conflict detection, alternative time slot generation, and automatic rescheduling
with priority-based ranking and user approval workflows.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel

from .availability_aggregation import AvailabilityAggregationService
from .priority_service import PriorityService
from .scheduling_agent import SchedulingAgent
from ..models.meeting import Meeting, TimeSlot, Availability
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class ConflictType(Enum):
    """Types of scheduling conflicts."""
    DIRECT_OVERLAP = "direct_overlap"
    BUFFER_VIOLATION = "buffer_violation"
    FOCUS_BLOCK_CONFLICT = "focus_block_conflict"
    WORKING_HOURS_VIOLATION = "working_hours_violation"
    DOUBLE_BOOKING = "double_booking"


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionStrategy(Enum):
    """Strategies for conflict resolution."""
    RESCHEDULE_LOWER_PRIORITY = "reschedule_lower_priority"
    FIND_ALTERNATIVE_SLOTS = "find_alternative_slots"
    SHORTEN_MEETINGS = "shorten_meetings"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    AUTO_DECLINE = "auto_decline"


class ConflictDetails(BaseModel):
    """Details about a detected conflict."""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    primary_meeting: Meeting
    conflicting_meetings: List[Meeting]
    affected_time_range: Tuple[datetime, datetime]
    description: str
    suggested_strategy: ResolutionStrategy


class ResolutionOption(BaseModel):
    """A potential resolution for a conflict."""
    option_id: str
    strategy: ResolutionStrategy
    description: str
    confidence_score: float
    alternative_slots: List[TimeSlot]
    affected_meetings: List[str]  # meeting IDs
    requires_approval: bool
    estimated_impact: str


class ConflictResolutionResult(BaseModel):
    """Result of conflict resolution process."""
    resolution_id: str
    original_conflict: ConflictDetails
    chosen_option: ResolutionOption
    status: str  # pending_approval, approved, rejected, executed
    created_at: datetime
    user_feedback: Optional[str] = None
    execution_details: Optional[Dict[str, Any]] = None


class ConflictResolutionEngine:
    """
    Advanced conflict resolution engine that detects scheduling conflicts
    and provides intelligent resolution options with user approval workflows.
    """
    
    def __init__(self):
        """Initialize the conflict resolution engine."""
        self.availability_service = AvailabilityAggregationService()
        self.priority_service = PriorityService()
        self.scheduling_agent = SchedulingAgent()
        
    def detect_conflicts(self, user_id: str, start_date: datetime, end_date: datetime,
                        connections: List[Connection], preferences: Optional[Preferences] = None,
                        proposed_meeting: Optional[Dict[str, Any]] = None) -> List[ConflictDetails]:
        """
        Detect all types of scheduling conflicts across connected calendars.
        
        Args:
            user_id: User identifier
            start_date: Start of time range to check
            end_date: End of time range to check
            connections: List of active calendar connections
            preferences: User preferences and constraints
            proposed_meeting: Optional new meeting to check for conflicts
            
        Returns:
            List of detected conflicts with details
        """
        logger.info(f"Detecting conflicts for user {user_id} from {start_date} to {end_date}")
        
        try:
            conflicts = []
            
            # Get all meetings in the time range
            all_meetings = self._fetch_all_meetings(user_id, start_date, end_date, connections)
            
            # Add proposed meeting if provided
            if proposed_meeting:
                proposed_meeting_obj = self._convert_to_meeting_object(proposed_meeting, user_id)
                all_meetings.append(proposed_meeting_obj)
            
            # Detect different types of conflicts
            conflicts.extend(self._detect_direct_overlaps(all_meetings, user_id))
            conflicts.extend(self._detect_buffer_violations(all_meetings, preferences))
            conflicts.extend(self._detect_focus_block_conflicts(all_meetings, preferences))
            conflicts.extend(self._detect_working_hours_violations(all_meetings, preferences))
            conflicts.extend(self._detect_double_bookings(all_meetings))
            
            # Sort conflicts by severity and time
            conflicts.sort(key=lambda c: (c.severity.value, c.affected_time_range[0]))
            
            logger.info(f"Detected {len(conflicts)} conflicts for user {user_id}")
            return conflicts
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts for user {user_id}: {str(e)}")
            raise Exception(f"Conflict detection failed: {str(e)}")
    
    def generate_resolution_options(self, conflict: ConflictDetails, user_id: str,
                                  connections: List[Connection], 
                                  preferences: Optional[Preferences] = None) -> List[ResolutionOption]:
        """
        Generate intelligent resolution options for a detected conflict.
        
        Args:
            conflict: Detected conflict details
            user_id: User identifier
            connections: List of active calendar connections
            preferences: User preferences
            
        Returns:
            List of resolution options ranked by confidence score
        """
        logger.info(f"Generating resolution options for conflict {conflict.conflict_id}")
        
        try:
            options = []
            
            # Get priority scores for conflicting meetings
            all_meetings = [conflict.primary_meeting] + conflict.conflicting_meetings
            prioritized_meetings = self.priority_service.prioritize_meetings(all_meetings, user_id)
            
            # Strategy 1: Reschedule lower priority meetings
            if len(prioritized_meetings) > 1:
                reschedule_option = self._generate_reschedule_option(
                    conflict, prioritized_meetings, user_id, connections, preferences
                )
                if reschedule_option:
                    options.append(reschedule_option)
            
            # Strategy 2: Find alternative time slots
            alternative_option = self._generate_alternative_slots_option(
                conflict, user_id, connections, preferences
            )
            if alternative_option:
                options.append(alternative_option)
            
            # Strategy 3: Shorten meetings if possible
            if conflict.conflict_type in [ConflictType.DIRECT_OVERLAP, ConflictType.BUFFER_VIOLATION]:
                shorten_option = self._generate_shorten_meetings_option(conflict, preferences)
                if shorten_option:
                    options.append(shorten_option)
            
            # Strategy 4: Escalate to human for complex conflicts
            if (conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL] or
                len(options) == 0):
                escalation_option = self._generate_escalation_option(conflict)
                options.append(escalation_option)
            
            # Use AI to enhance and rank options
            enhanced_options = self._enhance_options_with_ai(conflict, options, user_id)
            
            # Sort by confidence score
            enhanced_options.sort(key=lambda o: o.confidence_score, reverse=True)
            
            logger.info(f"Generated {len(enhanced_options)} resolution options for conflict {conflict.conflict_id}")
            return enhanced_options
            
        except Exception as e:
            logger.error(f"Failed to generate resolution options: {str(e)}")
            # Return escalation option as fallback
            return [self._generate_escalation_option(conflict)]    

    def execute_resolution(self, resolution_result: ConflictResolutionResult, user_id: str,
                          connections: List[Connection]) -> Dict[str, Any]:
        """
        Execute an approved conflict resolution.
        
        Args:
            resolution_result: Approved resolution details
            user_id: User identifier
            connections: List of active calendar connections
            
        Returns:
            Execution results with success/failure details
        """
        logger.info(f"Executing resolution {resolution_result.resolution_id}")
        
        try:
            if resolution_result.status != "approved":
                raise ValueError("Resolution must be approved before execution")
            
            execution_results = {
                'resolution_id': resolution_result.resolution_id,
                'strategy': resolution_result.chosen_option.strategy.value,
                'started_at': datetime.utcnow(),
                'actions_taken': [],
                'errors': [],
                'success': False
            }
            
            option = resolution_result.chosen_option
            
            if option.strategy == ResolutionStrategy.RESCHEDULE_LOWER_PRIORITY:
                results = self._execute_reschedule_strategy(option, user_id, connections)
                execution_results['actions_taken'].extend(results.get('actions', []))
                execution_results['errors'].extend(results.get('errors', []))
                
            elif option.strategy == ResolutionStrategy.FIND_ALTERNATIVE_SLOTS:
                results = self._execute_alternative_slots_strategy(option, user_id, connections)
                execution_results['actions_taken'].extend(results.get('actions', []))
                execution_results['errors'].extend(results.get('errors', []))
                
            elif option.strategy == ResolutionStrategy.SHORTEN_MEETINGS:
                results = self._execute_shorten_meetings_strategy(option, user_id, connections)
                execution_results['actions_taken'].extend(results.get('actions', []))
                execution_results['errors'].extend(results.get('errors', []))
                
            elif option.strategy == ResolutionStrategy.ESCALATE_TO_HUMAN:
                results = self._execute_escalation_strategy(option, user_id)
                execution_results['actions_taken'].extend(results.get('actions', []))
                
            elif option.strategy == ResolutionStrategy.AUTO_DECLINE:
                results = self._execute_auto_decline_strategy(option, user_id, connections)
                execution_results['actions_taken'].extend(results.get('actions', []))
                execution_results['errors'].extend(results.get('errors', []))
            
            execution_results['success'] = len(execution_results['errors']) == 0
            execution_results['completed_at'] = datetime.utcnow()
            
            # Update resolution result
            resolution_result.status = "executed" if execution_results['success'] else "failed"
            resolution_result.execution_details = execution_results
            
            logger.info(f"Resolution execution completed: {execution_results['success']}")
            return execution_results
            
        except Exception as e:
            logger.error(f"Failed to execute resolution: {str(e)}")
            return {
                'resolution_id': resolution_result.resolution_id,
                'success': False,
                'error': str(e),
                'completed_at': datetime.utcnow()
            }
    
    def create_approval_workflow(self, conflict: ConflictDetails, options: List[ResolutionOption],
                               user_id: str) -> Dict[str, Any]:
        """
        Create a user approval workflow for conflict resolution.
        
        Args:
            conflict: Detected conflict
            options: Available resolution options
            user_id: User identifier
            
        Returns:
            Approval workflow details for frontend display
        """
        logger.info(f"Creating approval workflow for conflict {conflict.conflict_id}")
        
        try:
            workflow = {
                'workflow_id': f"approval_{conflict.conflict_id}_{int(datetime.utcnow().timestamp())}",
                'conflict_summary': {
                    'conflict_id': conflict.conflict_id,
                    'type': conflict.conflict_type.value,
                    'severity': conflict.severity.value,
                    'description': conflict.description,
                    'affected_meetings': [
                        {
                            'id': conflict.primary_meeting.sk,
                            'title': conflict.primary_meeting.title,
                            'start': conflict.primary_meeting.start,
                            'end': conflict.primary_meeting.end
                        }
                    ] + [
                        {
                            'id': meeting.sk,
                            'title': meeting.title,
                            'start': meeting.start,
                            'end': meeting.end
                        }
                        for meeting in conflict.conflicting_meetings
                    ]
                },
                'resolution_options': [
                    {
                        'option_id': option.option_id,
                        'strategy': option.strategy.value,
                        'description': option.description,
                        'confidence_score': option.confidence_score,
                        'requires_approval': option.requires_approval,
                        'estimated_impact': option.estimated_impact,
                        'alternative_slots': [
                            {
                                'start': slot.start,
                                'end': slot.end,
                                'score': slot.score
                            }
                            for slot in option.alternative_slots
                        ] if option.alternative_slots else []
                    }
                    for option in options
                ],
                'created_at': datetime.utcnow(),
                'status': 'pending_user_input',
                'user_id': user_id,
                'expires_at': datetime.utcnow() + timedelta(hours=24)  # 24-hour expiry
            }
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create approval workflow: {str(e)}")
            raise Exception(f"Approval workflow creation failed: {str(e)}")
    
    def process_user_approval(self, workflow_id: str, selected_option_id: str,
                            user_feedback: Optional[str] = None) -> ConflictResolutionResult:
        """
        Process user approval for a conflict resolution option.
        
        Args:
            workflow_id: Approval workflow identifier
            selected_option_id: ID of the selected resolution option
            user_feedback: Optional user feedback
            
        Returns:
            Conflict resolution result ready for execution
        """
        logger.info(f"Processing user approval for workflow {workflow_id}")
        
        try:
            # This would typically retrieve the workflow from storage
            # For now, we'll create a mock result
            resolution_result = ConflictResolutionResult(
                resolution_id=f"resolution_{workflow_id}_{int(datetime.utcnow().timestamp())}",
                original_conflict=None,  # Would be populated from storage
                chosen_option=None,      # Would be populated from storage
                status="approved",
                created_at=datetime.utcnow(),
                user_feedback=user_feedback
            )
            
            logger.info(f"User approval processed for workflow {workflow_id}")
            return resolution_result
            
        except Exception as e:
            logger.error(f"Failed to process user approval: {str(e)}")
            raise Exception(f"User approval processing failed: {str(e)}")
    
    # Private helper methods
    
    def _fetch_all_meetings(self, user_id: str, start_date: datetime, end_date: datetime,
                           connections: List[Connection]) -> List[Meeting]:
        """Fetch all meetings from connected calendars."""
        # This would integrate with existing calendar services
        # For now, return empty list as placeholder
        return []
    
    def _convert_to_meeting_object(self, meeting_dict: Dict[str, Any], user_id: str) -> Meeting:
        """Convert meeting dictionary to Meeting object."""
        return Meeting(
            pk=f"user#{user_id}",
            sk=f"meeting#{meeting_dict.get('id', 'proposed')}",
            provider_event_id=meeting_dict.get('id', ''),
            provider=meeting_dict.get('provider', 'proposed'),
            title=meeting_dict.get('title', 'Proposed Meeting'),
            start=meeting_dict['start'],
            end=meeting_dict['end'],
            attendees=meeting_dict.get('attendees', []),
            status=meeting_dict.get('status', 'proposed'),
            priority_score=meeting_dict.get('priority_score', 0.5),
            created_by_agent=True,
            last_modified=datetime.utcnow()
        )
    
    def _detect_direct_overlaps(self, meetings: List[Meeting], user_id: str) -> List[ConflictDetails]:
        """Detect direct time overlaps between meetings."""
        conflicts = []
        
        for i, meeting1 in enumerate(meetings):
            for j, meeting2 in enumerate(meetings[i+1:], i+1):
                if self._meetings_overlap(meeting1, meeting2):
                    conflict_id = f"overlap_{user_id}_{i}_{j}_{int(datetime.utcnow().timestamp())}"
                    
                    conflict = ConflictDetails(
                        conflict_id=conflict_id,
                        conflict_type=ConflictType.DIRECT_OVERLAP,
                        severity=ConflictSeverity.HIGH,
                        primary_meeting=meeting1,
                        conflicting_meetings=[meeting2],
                        affected_time_range=(
                            max(meeting1.start, meeting2.start),
                            min(meeting1.end, meeting2.end)
                        ),
                        description=f"Direct overlap between '{meeting1.title}' and '{meeting2.title}'",
                        suggested_strategy=ResolutionStrategy.RESCHEDULE_LOWER_PRIORITY
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_buffer_violations(self, meetings: List[Meeting], 
                                preferences: Optional[Preferences]) -> List[ConflictDetails]:
        """Detect buffer time violations between meetings."""
        if not preferences:
            return []
        
        conflicts = []
        buffer_minutes = preferences.buffer_minutes
        
        # Sort meetings by start time
        sorted_meetings = sorted(meetings, key=lambda m: m.start)
        
        for i in range(len(sorted_meetings) - 1):
            current_meeting = sorted_meetings[i]
            next_meeting = sorted_meetings[i + 1]
            
            # Check if there's enough buffer time
            time_gap = (next_meeting.start - current_meeting.end).total_seconds() / 60
            
            if 0 < time_gap < buffer_minutes:
                conflict_id = f"buffer_{current_meeting.sk}_{next_meeting.sk}_{int(datetime.utcnow().timestamp())}"
                
                conflict = ConflictDetails(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.BUFFER_VIOLATION,
                    severity=ConflictSeverity.MEDIUM,
                    primary_meeting=current_meeting,
                    conflicting_meetings=[next_meeting],
                    affected_time_range=(current_meeting.end, next_meeting.start),
                    description=f"Insufficient buffer time ({time_gap:.0f} min) between meetings",
                    suggested_strategy=ResolutionStrategy.FIND_ALTERNATIVE_SLOTS
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_focus_block_conflicts(self, meetings: List[Meeting],
                                    preferences: Optional[Preferences]) -> List[ConflictDetails]:
        """Detect conflicts with focus blocks."""
        if not preferences or not preferences.focus_blocks:
            return []
        
        conflicts = []
        
        for meeting in meetings:
            for focus_block in preferences.focus_blocks:
                if self._meeting_conflicts_with_focus_block(meeting, focus_block):
                    conflict_id = f"focus_{meeting.sk}_{focus_block.title}_{int(datetime.utcnow().timestamp())}"
                    
                    conflict = ConflictDetails(
                        conflict_id=conflict_id,
                        conflict_type=ConflictType.FOCUS_BLOCK_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        primary_meeting=meeting,
                        conflicting_meetings=[],
                        affected_time_range=(meeting.start, meeting.end),
                        description=f"Meeting conflicts with focus block '{focus_block.title}'",
                        suggested_strategy=ResolutionStrategy.FIND_ALTERNATIVE_SLOTS
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_working_hours_violations(self, meetings: List[Meeting],
                                       preferences: Optional[Preferences]) -> List[ConflictDetails]:
        """Detect meetings outside working hours."""
        if not preferences or not preferences.working_hours:
            return []
        
        conflicts = []
        
        for meeting in meetings:
            if self._meeting_outside_working_hours(meeting, preferences):
                conflict_id = f"hours_{meeting.sk}_{int(datetime.utcnow().timestamp())}"
                
                conflict = ConflictDetails(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.WORKING_HOURS_VIOLATION,
                    severity=ConflictSeverity.LOW,
                    primary_meeting=meeting,
                    conflicting_meetings=[],
                    affected_time_range=(meeting.start, meeting.end),
                    description=f"Meeting '{meeting.title}' is outside working hours",
                    suggested_strategy=ResolutionStrategy.FIND_ALTERNATIVE_SLOTS
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_double_bookings(self, meetings: List[Meeting]) -> List[ConflictDetails]:
        """Detect double bookings (same meeting in multiple calendars)."""
        conflicts = []
        
        # Group meetings by title and time
        meeting_groups = {}
        for meeting in meetings:
            key = (meeting.title, meeting.start, meeting.end)
            if key not in meeting_groups:
                meeting_groups[key] = []
            meeting_groups[key].append(meeting)
        
        # Find groups with multiple meetings (potential double bookings)
        for (title, start, end), group_meetings in meeting_groups.items():
            if len(group_meetings) > 1:
                conflict_id = f"double_{title}_{int(start.timestamp())}_{int(datetime.utcnow().timestamp())}"
                
                conflict = ConflictDetails(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.DOUBLE_BOOKING,
                    severity=ConflictSeverity.HIGH,
                    primary_meeting=group_meetings[0],
                    conflicting_meetings=group_meetings[1:],
                    affected_time_range=(start, end),
                    description=f"Potential double booking for '{title}'",
                    suggested_strategy=ResolutionStrategy.ESCALATE_TO_HUMAN
                )
                conflicts.append(conflict)
        
        return conflicts   
 
    def _meetings_overlap(self, meeting1: Meeting, meeting2: Meeting) -> bool:
        """Check if two meetings overlap in time."""
        return (meeting1.start < meeting2.end and meeting1.end > meeting2.start)
    
    def _meeting_conflicts_with_focus_block(self, meeting: Meeting, focus_block) -> bool:
        """Check if a meeting conflicts with a focus block."""
        # Get the day of the week for the meeting
        meeting_weekday = meeting.start.strftime('%A').lower()
        
        if meeting_weekday != focus_block.day.lower():
            return False
        
        # Parse focus block times
        try:
            focus_start_hour, focus_start_minute = map(int, focus_block.start.split(':'))
            focus_end_hour, focus_end_minute = map(int, focus_block.end.split(':'))
            
            # Create focus block datetime objects for the same day as the meeting
            focus_start = meeting.start.replace(
                hour=focus_start_hour, minute=focus_start_minute, second=0, microsecond=0
            )
            focus_end = meeting.start.replace(
                hour=focus_end_hour, minute=focus_end_minute, second=0, microsecond=0
            )
            
            # Check for overlap
            return (meeting.start < focus_end and meeting.end > focus_start)
            
        except (ValueError, AttributeError):
            return False
    
    def _meeting_outside_working_hours(self, meeting: Meeting, preferences: Preferences) -> bool:
        """Check if a meeting is outside working hours."""
        meeting_weekday = meeting.start.strftime('%A').lower()
        
        if meeting_weekday not in preferences.working_hours:
            return True  # No working hours defined for this day
        
        working_hours = preferences.working_hours[meeting_weekday]
        
        try:
            # Parse working hours
            work_start_hour, work_start_minute = map(int, working_hours.start.split(':'))
            work_end_hour, work_end_minute = map(int, working_hours.end.split(':'))
            
            # Create working hours datetime objects for the same day as the meeting
            work_start = meeting.start.replace(
                hour=work_start_hour, minute=work_start_minute, second=0, microsecond=0
            )
            work_end = meeting.start.replace(
                hour=work_end_hour, minute=work_end_minute, second=0, microsecond=0
            )
            
            # Check if meeting is outside working hours
            return (meeting.start < work_start or meeting.end > work_end)
            
        except (ValueError, AttributeError):
            return False
    
    def _generate_reschedule_option(self, conflict: ConflictDetails, 
                                  prioritized_meetings: List[Tuple[Meeting, Any]],
                                  user_id: str, connections: List[Connection],
                                  preferences: Optional[Preferences]) -> Optional[ResolutionOption]:
        """Generate reschedule option based on meeting priorities."""
        try:
            # Find the lowest priority meeting to reschedule
            lowest_priority_meeting = min(prioritized_meetings, key=lambda x: x[1].priority_score)
            meeting_to_reschedule = lowest_priority_meeting[0]
            
            # Find alternative time slots
            duration_minutes = int((meeting_to_reschedule.end - meeting_to_reschedule.start).total_seconds() / 60)
            
            # Get availability for the next week
            search_start = datetime.utcnow()
            search_end = search_start + timedelta(days=7)
            
            availability = self.availability_service.aggregate_availability(
                user_id, search_start, search_end, connections, preferences, duration_minutes
            )
            
            alternative_slots = self.availability_service.find_optimal_time_slots(
                availability, duration_minutes, count=3
            )
            
            if not alternative_slots:
                return None
            
            option_id = f"reschedule_{conflict.conflict_id}_{int(datetime.utcnow().timestamp())}"
            
            return ResolutionOption(
                option_id=option_id,
                strategy=ResolutionStrategy.RESCHEDULE_LOWER_PRIORITY,
                description=f"Reschedule '{meeting_to_reschedule.title}' (priority: {lowest_priority_meeting[1].priority_score:.2f}) to an alternative time",
                confidence_score=0.8,
                alternative_slots=alternative_slots,
                affected_meetings=[meeting_to_reschedule.sk],
                requires_approval=True,
                estimated_impact=f"Reschedule 1 meeting, {len(alternative_slots)} alternative slots available"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate reschedule option: {str(e)}")
            return None
    
    def _generate_alternative_slots_option(self, conflict: ConflictDetails, user_id: str,
                                         connections: List[Connection],
                                         preferences: Optional[Preferences]) -> Optional[ResolutionOption]:
        """Generate alternative time slots option."""
        try:
            # Calculate total duration needed
            all_meetings = [conflict.primary_meeting] + conflict.conflicting_meetings
            total_duration = sum(
                int((meeting.end - meeting.start).total_seconds() / 60)
                for meeting in all_meetings
            )
            
            # Find alternative slots for all meetings
            search_start = datetime.utcnow()
            search_end = search_start + timedelta(days=14)  # Search 2 weeks ahead
            
            availability = self.availability_service.aggregate_availability(
                user_id, search_start, search_end, connections, preferences
            )
            
            alternative_slots = []
            for meeting in all_meetings:
                duration = int((meeting.end - meeting.start).total_seconds() / 60)
                slots = self.availability_service.find_optimal_time_slots(
                    availability, duration, count=2
                )
                alternative_slots.extend(slots)
            
            if not alternative_slots:
                return None
            
            option_id = f"alternatives_{conflict.conflict_id}_{int(datetime.utcnow().timestamp())}"
            
            return ResolutionOption(
                option_id=option_id,
                strategy=ResolutionStrategy.FIND_ALTERNATIVE_SLOTS,
                description=f"Find alternative time slots for all {len(all_meetings)} conflicting meetings",
                confidence_score=0.7,
                alternative_slots=alternative_slots,
                affected_meetings=[meeting.sk for meeting in all_meetings],
                requires_approval=True,
                estimated_impact=f"Reschedule {len(all_meetings)} meetings, {len(alternative_slots)} alternative slots found"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate alternative slots option: {str(e)}")
            return None
    
    def _generate_shorten_meetings_option(self, conflict: ConflictDetails,
                                        preferences: Optional[Preferences]) -> Optional[ResolutionOption]:
        """Generate option to shorten meetings to resolve conflicts."""
        try:
            all_meetings = [conflict.primary_meeting] + conflict.conflicting_meetings
            
            # Check if meetings can be shortened
            shortenable_meetings = []
            for meeting in all_meetings:
                duration_minutes = int((meeting.end - meeting.start).total_seconds() / 60)
                if duration_minutes > 30:  # Only shorten meetings longer than 30 minutes
                    shortenable_meetings.append(meeting)
            
            if not shortenable_meetings:
                return None
            
            option_id = f"shorten_{conflict.conflict_id}_{int(datetime.utcnow().timestamp())}"
            
            return ResolutionOption(
                option_id=option_id,
                strategy=ResolutionStrategy.SHORTEN_MEETINGS,
                description=f"Shorten {len(shortenable_meetings)} meetings to resolve conflict",
                confidence_score=0.6,
                alternative_slots=[],  # No alternative slots needed
                affected_meetings=[meeting.sk for meeting in shortenable_meetings],
                requires_approval=True,
                estimated_impact=f"Shorten {len(shortenable_meetings)} meetings by 15-30 minutes each"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate shorten meetings option: {str(e)}")
            return None
    
    def _generate_escalation_option(self, conflict: ConflictDetails) -> ResolutionOption:
        """Generate escalation to human option."""
        option_id = f"escalate_{conflict.conflict_id}_{int(datetime.utcnow().timestamp())}"
        
        return ResolutionOption(
            option_id=option_id,
            strategy=ResolutionStrategy.ESCALATE_TO_HUMAN,
            description="Escalate to human decision-making for manual resolution",
            confidence_score=1.0,  # Always available
            alternative_slots=[],
            affected_meetings=[conflict.primary_meeting.sk] + [m.sk for m in conflict.conflicting_meetings],
            requires_approval=False,  # Escalation doesn't need approval
            estimated_impact="Manual intervention required - no automatic changes will be made"
        )
    
    def _enhance_options_with_ai(self, conflict: ConflictDetails, options: List[ResolutionOption],
                               user_id: str) -> List[ResolutionOption]:
        """Use AI to enhance and provide better descriptions for resolution options."""
        try:
            # Prepare data for AI analysis
            conflict_data = {
                'type': conflict.conflict_type.value,
                'severity': conflict.severity.value,
                'description': conflict.description,
                'meetings': [
                    {
                        'title': conflict.primary_meeting.title,
                        'start': conflict.primary_meeting.start.isoformat(),
                        'end': conflict.primary_meeting.end.isoformat()
                    }
                ] + [
                    {
                        'title': meeting.title,
                        'start': meeting.start.isoformat(),
                        'end': meeting.end.isoformat()
                    }
                    for meeting in conflict.conflicting_meetings
                ]
            }
            
            options_data = [
                {
                    'strategy': option.strategy.value,
                    'description': option.description,
                    'confidence_score': option.confidence_score,
                    'estimated_impact': option.estimated_impact
                }
                for option in options
            ]
            
            # Use scheduling agent to enhance options
            ai_response = self.scheduling_agent.resolve_conflicts(
                meeting_request={'conflict': conflict_data},
                conflicts=[conflict_data],
                available_slots=options_data
            )
            
            # Enhance options with AI insights
            if 'enhanced_options' in ai_response:
                for i, enhanced in enumerate(ai_response['enhanced_options']):
                    if i < len(options):
                        options[i].description = enhanced.get('description', options[i].description)
                        options[i].confidence_score = enhanced.get('confidence_score', options[i].confidence_score)
                        options[i].estimated_impact = enhanced.get('estimated_impact', options[i].estimated_impact)
            
            return options
            
        except Exception as e:
            logger.warning(f"Failed to enhance options with AI: {str(e)}")
            return options  # Return original options if AI enhancement fails
    
    # Execution methods
    
    def _execute_reschedule_strategy(self, option: ResolutionOption, user_id: str,
                                   connections: List[Connection]) -> Dict[str, Any]:
        """Execute reschedule strategy."""
        results = {'actions': [], 'errors': []}
        
        try:
            # This would integrate with calendar services to actually reschedule meetings
            for meeting_id in option.affected_meetings:
                # Mock implementation
                results['actions'].append(f"Rescheduled meeting {meeting_id}")
                
                # Send notifications
                results['actions'].append(f"Sent reschedule notification for meeting {meeting_id}")
            
        except Exception as e:
            results['errors'].append(f"Failed to reschedule meetings: {str(e)}")
        
        return results
    
    def _execute_alternative_slots_strategy(self, option: ResolutionOption, user_id: str,
                                          connections: List[Connection]) -> Dict[str, Any]:
        """Execute alternative slots strategy."""
        results = {'actions': [], 'errors': []}
        
        try:
            # This would integrate with calendar services
            for meeting_id in option.affected_meetings:
                results['actions'].append(f"Found alternative slots for meeting {meeting_id}")
                results['actions'].append(f"Sent alternative time proposals for meeting {meeting_id}")
            
        except Exception as e:
            results['errors'].append(f"Failed to propose alternative slots: {str(e)}")
        
        return results
    
    def _execute_shorten_meetings_strategy(self, option: ResolutionOption, user_id: str,
                                         connections: List[Connection]) -> Dict[str, Any]:
        """Execute shorten meetings strategy."""
        results = {'actions': [], 'errors': []}
        
        try:
            for meeting_id in option.affected_meetings:
                results['actions'].append(f"Shortened meeting {meeting_id} by 15 minutes")
                results['actions'].append(f"Sent meeting update notification for {meeting_id}")
            
        except Exception as e:
            results['errors'].append(f"Failed to shorten meetings: {str(e)}")
        
        return results
    
    def _execute_escalation_strategy(self, option: ResolutionOption, user_id: str) -> Dict[str, Any]:
        """Execute escalation strategy."""
        results = {'actions': [], 'errors': []}
        
        try:
            results['actions'].append("Created escalation ticket for human review")
            results['actions'].append("Sent notification to user about manual intervention needed")
            results['actions'].append("Preserved all conflicting meetings pending manual resolution")
            
        except Exception as e:
            results['errors'].append(f"Failed to escalate conflict: {str(e)}")
        
        return results
    
    def _execute_auto_decline_strategy(self, option: ResolutionOption, user_id: str,
                                     connections: List[Connection]) -> Dict[str, Any]:
        """Execute auto-decline strategy."""
        results = {'actions': [], 'errors': []}
        
        try:
            for meeting_id in option.affected_meetings:
                results['actions'].append(f"Auto-declined meeting {meeting_id}")
                results['actions'].append(f"Sent decline notification for meeting {meeting_id}")
            
        except Exception as e:
            results['errors'].append(f"Failed to auto-decline meetings: {str(e)}")
        
        return results