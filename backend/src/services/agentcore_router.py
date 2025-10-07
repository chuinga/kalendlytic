"""
AgentCore Router/Planner primitive for intelligent tool execution sequencing.
Manages complex scheduling scenarios with decision trees and context management.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of scheduling tasks the agent can handle."""
    SCHEDULE_MEETING = "schedule_meeting"
    RESOLVE_CONFLICT = "resolve_conflict"
    FIND_AVAILABILITY = "find_availability"
    RESCHEDULE_MEETING = "reschedule_meeting"
    CANCEL_MEETING = "cancel_meeting"
    UPDATE_PREFERENCES = "update_preferences"
    GENERATE_COMMUNICATION = "generate_communication"


class Priority(Enum):
    """Priority levels for task execution."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ToolType(Enum):
    """Available tools for the agent."""
    CALENDAR_SERVICE = "calendar_service"
    AVAILABILITY_AGGREGATOR = "availability_aggregator"
    SCHEDULING_AGENT = "scheduling_agent"
    OAUTH_MANAGER = "oauth_manager"
    PREFERENCE_SERVICE = "preference_service"
    COMMUNICATION_GENERATOR = "communication_generator"


@dataclass
class ExecutionStep:
    """Individual step in the execution plan."""
    step_id: str
    tool_type: ToolType
    action: str
    inputs: Dict[str, Any]
    dependencies: List[str]
    priority: Priority
    estimated_duration_ms: int
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionContext:
    """Context for multi-step agent operations."""
    session_id: str
    user_id: str
    task_type: TaskType
    original_request: Dict[str, Any]
    current_step: int
    total_steps: int
    accumulated_data: Dict[str, Any]
    conflict_resolution_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class AgentCoreRouterError(Exception):
    """Custom exception for AgentCore router errors."""
    pass


class AgentCoreRouter:
    """
    AgentCore Router/Planner for determining optimal tool execution sequences.
    Handles complex scheduling scenarios with intelligent decision-making.
    """
    
    def __init__(self):
        """Initialize the AgentCore router."""
        self.active_contexts: Dict[str, ExecutionContext] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Decision tree mappings for different scenarios
        self.task_workflows = {
            TaskType.SCHEDULE_MEETING: self._build_schedule_meeting_workflow,
            TaskType.RESOLVE_CONFLICT: self._build_conflict_resolution_workflow,
            TaskType.FIND_AVAILABILITY: self._build_availability_workflow,
            TaskType.RESCHEDULE_MEETING: self._build_reschedule_workflow,
            TaskType.CANCEL_MEETING: self._build_cancel_workflow,
            TaskType.UPDATE_PREFERENCES: self._build_preferences_workflow,
            TaskType.GENERATE_COMMUNICATION: self._build_communication_workflow
        }
    
    def plan_execution(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any],
        user_id: str,
        session_id: Optional[str] = None
    ) -> Tuple[str, List[ExecutionStep]]:
        """
        Plan optimal execution sequence for a given task.
        
        Args:
            task_type: Type of task to execute
            request_data: Input data for the task
            user_id: User identifier
            session_id: Optional session identifier for context continuity
            
        Returns:
            Tuple of (context_id, execution_steps)
        """
        try:
            # Generate or use existing session ID
            context_id = session_id or f"{user_id}_{task_type}_{int(datetime.utcnow().timestamp())}"
            
            # Analyze request complexity and conflicts
            complexity_analysis = self._analyze_request_complexity(task_type, request_data)
            
            # Build execution workflow based on task type
            if task_type not in self.task_workflows:
                raise AgentCoreRouterError(f"Unsupported task type: {task_type}")
            
            workflow_builder = self.task_workflows[task_type]
            execution_steps = workflow_builder(request_data, complexity_analysis)
            
            # Create execution context
            context = ExecutionContext(
                session_id=context_id,
                user_id=user_id,
                task_type=task_type,
                original_request=request_data,
                current_step=0,
                total_steps=len(execution_steps),
                accumulated_data={},
                conflict_resolution_history=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.active_contexts[context_id] = context
            
            logger.info(f"Execution plan created: {len(execution_steps)} steps for {task_type}")
            return context_id, execution_steps
            
        except Exception as e:
            logger.error(f"Failed to plan execution: {e}")
            raise AgentCoreRouterError(f"Execution planning failed: {e}")
    
    def handle_conflicts(
        self,
        context_id: str,
        conflicts: List[Dict[str, Any]],
        available_alternatives: List[Dict[str, Any]]
    ) -> List[ExecutionStep]:
        """
        Handle scheduling conflicts with intelligent prioritization.
        
        Args:
            context_id: Execution context identifier
            conflicts: List of detected conflicts
            available_alternatives: Alternative options available
            
        Returns:
            Updated execution steps for conflict resolution
        """
        try:
            if context_id not in self.active_contexts:
                raise AgentCoreRouterError(f"Context not found: {context_id}")
            
            context = self.active_contexts[context_id]
            
            # Analyze conflict severity and impact
            conflict_analysis = self._analyze_conflicts(conflicts, context.original_request)
            
            # Determine resolution strategy based on conflict type and priority
            resolution_strategy = self._determine_resolution_strategy(
                conflict_analysis, available_alternatives, context
            )
            
            # Generate conflict resolution steps
            resolution_steps = self._build_conflict_resolution_steps(
                resolution_strategy, conflicts, available_alternatives
            )
            
            # Update context with conflict resolution history
            context.conflict_resolution_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'conflicts': conflicts,
                'strategy': resolution_strategy,
                'steps_generated': len(resolution_steps),
                'rationale': f"Selected {resolution_strategy} strategy based on {len(conflicts)} conflicts with {conflict_analysis['resolution_complexity']} complexity. This approach balances efficiency with thoroughness.",
                'natural_language_explanation': self._generate_conflict_explanation(conflicts, resolution_strategy, available_alternatives)
            })
            context.updated_at = datetime.utcnow()
            
            logger.info(f"Conflict resolution planned: {len(resolution_steps)} steps")
            return resolution_steps
            
        except Exception as e:
            logger.error(f"Failed to handle conflicts: {e}")
            raise AgentCoreRouterError(f"Conflict handling failed: {e}")
    
    def update_context(
        self,
        context_id: str,
        step_result: Dict[str, Any],
        next_step_index: int
    ) -> None:
        """
        Update execution context with step results.
        
        Args:
            context_id: Execution context identifier
            step_result: Result data from completed step
            next_step_index: Index of the next step to execute
        """
        try:
            if context_id not in self.active_contexts:
                raise AgentCoreRouterError(f"Context not found: {context_id}")
            
            context = self.active_contexts[context_id]
            
            # Update accumulated data
            step_key = f"step_{context.current_step}"
            context.accumulated_data[step_key] = step_result
            
            # Update current step
            context.current_step = next_step_index
            context.updated_at = datetime.utcnow()
            
            logger.debug(f"Context updated: step {next_step_index}/{context.total_steps}")
            
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            raise AgentCoreRouterError(f"Context update failed: {e}")
    
    def get_context(self, context_id: str) -> Optional[ExecutionContext]:
        """Get execution context by ID."""
        return self.active_contexts.get(context_id)
    
    def cleanup_context(self, context_id: str) -> None:
        """Clean up completed execution context."""
        if context_id in self.active_contexts:
            context = self.active_contexts.pop(context_id)
            
            # Archive to execution history
            self.execution_history.append({
                'context_id': context_id,
                'task_type': context.task_type,
                'user_id': context.user_id,
                'total_steps': context.total_steps,
                'completed_at': datetime.utcnow().isoformat(),
                'conflicts_resolved': len(context.conflict_resolution_history)
            })
            
            logger.info(f"Context cleaned up: {context_id}")
    
    def _analyze_request_complexity(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze request complexity to determine execution strategy."""
        complexity = {
            'attendee_count': len(request_data.get('attendees', [])),
            'duration_hours': request_data.get('duration_minutes', 60) / 60,
            'has_constraints': bool(request_data.get('constraints')),
            'has_preferences': bool(request_data.get('preferences')),
            'requires_external_calendars': len(request_data.get('external_calendars', [])) > 0,
            'complexity_score': 0
        }
        
        # Calculate complexity score
        score = 0
        score += min(complexity['attendee_count'] * 2, 20)  # Max 20 points for attendees
        score += min(complexity['duration_hours'] * 5, 15)  # Max 15 points for duration
        score += 10 if complexity['has_constraints'] else 0
        score += 5 if complexity['has_preferences'] else 0
        score += 15 if complexity['requires_external_calendars'] else 0
        
        complexity['complexity_score'] = score
        complexity['complexity_level'] = (
            'simple' if score < 20 else
            'moderate' if score < 40 else
            'complex' if score < 60 else
            'very_complex'
        )
        
        return complexity
    
    def _analyze_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        original_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze conflicts to determine resolution approach."""
        analysis = {
            'total_conflicts': len(conflicts),
            'conflict_types': {},
            'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'affected_attendees': set(),
            'time_overlap_minutes': 0,
            'resolution_complexity': 'simple'
        }
        
        for conflict in conflicts:
            # Analyze conflict type
            conflict_type = conflict.get('type', 'unknown')
            analysis['conflict_types'][conflict_type] = analysis['conflict_types'].get(conflict_type, 0) + 1
            
            # Analyze severity
            severity = conflict.get('severity', 'medium')
            analysis['severity_distribution'][severity] += 1
            
            # Track affected attendees
            if 'attendees' in conflict:
                analysis['affected_attendees'].update(conflict['attendees'])
            
            # Calculate time overlap
            overlap = conflict.get('overlap_minutes', 0)
            analysis['time_overlap_minutes'] += overlap
        
        # Determine resolution complexity
        if analysis['severity_distribution']['critical'] > 0 or analysis['total_conflicts'] > 5:
            analysis['resolution_complexity'] = 'very_complex'
        elif analysis['severity_distribution']['high'] > 2 or analysis['total_conflicts'] > 3:
            analysis['resolution_complexity'] = 'complex'
        elif analysis['severity_distribution']['medium'] > 1 or analysis['total_conflicts'] > 1:
            analysis['resolution_complexity'] = 'moderate'
        
        return analysis
    
    def _determine_resolution_strategy(
        self,
        conflict_analysis: Dict[str, Any],
        alternatives: List[Dict[str, Any]],
        context: ExecutionContext
    ) -> str:
        """Determine the best conflict resolution strategy."""
        # Priority-based decision tree
        if conflict_analysis['severity_distribution']['critical'] > 0:
            return 'escalate_to_human'
        
        if conflict_analysis['total_conflicts'] == 1 and len(alternatives) > 0:
            return 'auto_reschedule'
        
        if conflict_analysis['resolution_complexity'] == 'simple' and len(alternatives) >= 2:
            return 'propose_alternatives'
        
        if len(context.conflict_resolution_history) > 2:
            return 'escalate_to_human'
        
        if conflict_analysis['total_conflicts'] > 3:
            return 'batch_resolution'
        
        return 'interactive_resolution'
    
    def _build_schedule_meeting_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for scheduling a new meeting."""
        steps = []
        
        # Step 1: Validate and authenticate
        steps.append(ExecutionStep(
            step_id="validate_auth",
            tool_type=ToolType.OAUTH_MANAGER,
            action="validate_tokens",
            inputs={"attendees": request_data.get('attendees', [])},
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=500
        ))
        
        # Step 2: Gather availability
        steps.append(ExecutionStep(
            step_id="gather_availability",
            tool_type=ToolType.AVAILABILITY_AGGREGATOR,
            action="get_availability",
            inputs={
                "attendees": request_data.get('attendees', []),
                "time_range": request_data.get('time_range'),
                "duration": request_data.get('duration_minutes', 60)
            },
            dependencies=["validate_auth"],
            priority=Priority.HIGH,
            estimated_duration_ms=2000
        ))
        
        # Step 3: Find optimal time (complexity-dependent)
        if complexity['complexity_level'] in ['complex', 'very_complex']:
            steps.append(ExecutionStep(
                step_id="ai_optimization",
                tool_type=ToolType.SCHEDULING_AGENT,
                action="find_optimal_time",
                inputs={
                    "meeting_request": request_data,
                    "availability_data": "{{gather_availability.result}}",
                    "preferences": request_data.get('preferences', {})
                },
                dependencies=["gather_availability"],
                priority=Priority.MEDIUM,
                estimated_duration_ms=3000
            ))
        
        # Step 4: Create meeting
        steps.append(ExecutionStep(
            step_id="create_meeting",
            tool_type=ToolType.CALENDAR_SERVICE,
            action="create_meeting",
            inputs={
                "meeting_details": request_data,
                "selected_time": "{{ai_optimization.result}}" if complexity['complexity_level'] in ['complex', 'very_complex'] else "{{gather_availability.best_slot}}"
            },
            dependencies=["ai_optimization"] if complexity['complexity_level'] in ['complex', 'very_complex'] else ["gather_availability"],
            priority=Priority.HIGH,
            estimated_duration_ms=1500
        ))
        
        return steps
    
    def _build_conflict_resolution_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for resolving scheduling conflicts."""
        steps = []
        
        # Step 1: Analyze conflicts
        steps.append(ExecutionStep(
            step_id="analyze_conflicts",
            tool_type=ToolType.SCHEDULING_AGENT,
            action="resolve_conflicts",
            inputs={
                "conflicts": request_data.get('conflicts', []),
                "meeting_request": request_data.get('original_request'),
                "available_slots": request_data.get('alternatives', [])
            },
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=2500
        ))
        
        # Step 2: Generate alternatives
        steps.append(ExecutionStep(
            step_id="generate_alternatives",
            tool_type=ToolType.AVAILABILITY_AGGREGATOR,
            action="find_alternatives",
            inputs={
                "conflict_analysis": "{{analyze_conflicts.result}}",
                "constraints": request_data.get('constraints', {})
            },
            dependencies=["analyze_conflicts"],
            priority=Priority.MEDIUM,
            estimated_duration_ms=1800
        ))
        
        # Step 3: Update meeting
        steps.append(ExecutionStep(
            step_id="update_meeting",
            tool_type=ToolType.CALENDAR_SERVICE,
            action="update_meeting",
            inputs={
                "meeting_id": request_data.get('meeting_id'),
                "new_details": "{{generate_alternatives.best_option}}"
            },
            dependencies=["generate_alternatives"],
            priority=Priority.HIGH,
            estimated_duration_ms=1200
        ))
        
        return steps
    
    def _build_availability_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for finding availability."""
        return [
            ExecutionStep(
                step_id="aggregate_availability",
                tool_type=ToolType.AVAILABILITY_AGGREGATOR,
                action="get_comprehensive_availability",
                inputs=request_data,
                dependencies=[],
                priority=Priority.MEDIUM,
                estimated_duration_ms=1500
            )
        ]
    
    def _build_reschedule_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for rescheduling meetings."""
        steps = []
        
        # Step 1: Generate communication
        steps.append(ExecutionStep(
            step_id="generate_communication",
            tool_type=ToolType.SCHEDULING_AGENT,
            action="generate_rescheduling_communication",
            inputs={
                "original_meeting": request_data.get('original_meeting'),
                "new_time": request_data.get('new_time'),
                "reason": request_data.get('reason', 'Schedule conflict'),
                "attendees": request_data.get('attendees', [])
            },
            dependencies=[],
            priority=Priority.MEDIUM,
            estimated_duration_ms=2000
        ))
        
        # Step 2: Update meeting
        steps.append(ExecutionStep(
            step_id="reschedule_meeting",
            tool_type=ToolType.CALENDAR_SERVICE,
            action="reschedule_meeting",
            inputs={
                "meeting_id": request_data.get('meeting_id'),
                "new_time": request_data.get('new_time'),
                "communication": "{{generate_communication.result}}"
            },
            dependencies=["generate_communication"],
            priority=Priority.HIGH,
            estimated_duration_ms=1500
        ))
        
        return steps
    
    def _build_cancel_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for canceling meetings."""
        return [
            ExecutionStep(
                step_id="cancel_meeting",
                tool_type=ToolType.CALENDAR_SERVICE,
                action="cancel_meeting",
                inputs={
                    "meeting_id": request_data.get('meeting_id'),
                    "reason": request_data.get('reason'),
                    "notify_attendees": request_data.get('notify_attendees', True)
                },
                dependencies=[],
                priority=Priority.HIGH,
                estimated_duration_ms=1000
            )
        ]
    
    def _build_preferences_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for updating preferences."""
        return [
            ExecutionStep(
                step_id="update_preferences",
                tool_type=ToolType.PREFERENCE_SERVICE,
                action="update_user_preferences",
                inputs={
                    "user_id": request_data.get('user_id'),
                    "preferences": request_data.get('preferences')
                },
                dependencies=[],
                priority=Priority.LOW,
                estimated_duration_ms=800
            )
        ]
    
    def _build_communication_workflow(
        self,
        request_data: Dict[str, Any],
        complexity: Dict[str, Any]
    ) -> List[ExecutionStep]:
        """Build workflow for generating communications."""
        return [
            ExecutionStep(
                step_id="generate_communication",
                tool_type=ToolType.COMMUNICATION_GENERATOR,
                action="generate_message",
                inputs=request_data,
                dependencies=[],
                priority=Priority.MEDIUM,
                estimated_duration_ms=1500
            )
        ]
    
    def _build_conflict_resolution_steps(
        self,
        strategy: str,
        conflicts: List[Dict[str, Any]],
        alternatives: List[Dict[str, Any]]
    ) -> List[ExecutionStep]:
        """Build specific steps for conflict resolution based on strategy."""
        steps = []
        
        if strategy == "auto_reschedule":
            steps.append(ExecutionStep(
                step_id="auto_reschedule",
                tool_type=ToolType.CALENDAR_SERVICE,
                action="auto_reschedule",
                inputs={
                    "conflicts": conflicts,
                    "alternatives": alternatives
                },
                dependencies=[],
                priority=Priority.HIGH,
                estimated_duration_ms=2000
            ))
        
        elif strategy == "propose_alternatives":
            steps.append(ExecutionStep(
                step_id="propose_alternatives",
                tool_type=ToolType.SCHEDULING_AGENT,
                action="propose_alternatives",
                inputs={
                    "conflicts": conflicts,
                    "alternatives": alternatives
                },
                dependencies=[],
                priority=Priority.MEDIUM,
                estimated_duration_ms=1800
            ))
        
        elif strategy == "interactive_resolution":
            steps.extend([
                ExecutionStep(
                    step_id="analyze_options",
                    tool_type=ToolType.SCHEDULING_AGENT,
                    action="analyze_resolution_options",
                    inputs={"conflicts": conflicts, "alternatives": alternatives},
                    dependencies=[],
                    priority=Priority.MEDIUM,
                    estimated_duration_ms=2200
                ),
                ExecutionStep(
                    step_id="present_options",
                    tool_type=ToolType.COMMUNICATION_GENERATOR,
                    action="format_resolution_options",
                    inputs={"analysis": "{{analyze_options.result}}"},
                    dependencies=["analyze_options"],
                    priority=Priority.LOW,
                    estimated_duration_ms=1000
                )
            ])
        
        elif strategy == "batch_resolution":
            steps.append(ExecutionStep(
                step_id="batch_resolve",
                tool_type=ToolType.SCHEDULING_AGENT,
                action="batch_conflict_resolution",
                inputs={
                    "conflicts": conflicts,
                    "alternatives": alternatives
                },
                dependencies=[],
                priority=Priority.HIGH,
                estimated_duration_ms=4000
            ))
        
        elif strategy == "escalate_to_human":
            steps.append(ExecutionStep(
                step_id="escalate",
                tool_type=ToolType.COMMUNICATION_GENERATOR,
                action="generate_escalation_summary",
                inputs={
                    "conflicts": conflicts,
                    "attempted_resolutions": alternatives
                },
                dependencies=[],
                priority=Priority.CRITICAL,
                estimated_duration_ms=1500
            ))
        
        return steps
    
    def _generate_conflict_explanation(
        self,
        conflicts: List[Dict[str, Any]],
        strategy: str,
        alternatives: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language explanation for conflict resolution decisions."""
        conflict_count = len(conflicts)
        alternative_count = len(alternatives)
        
        explanation = f"I detected {conflict_count} scheduling conflict{'s' if conflict_count != 1 else ''} "
        
        if conflict_count == 1:
            explanation += "involving overlapping time slots. "
        else:
            explanation += "with multiple overlapping meetings. "
        
        if strategy == "auto_reschedule":
            explanation += f"Since there {'are' if alternative_count != 1 else 'is'} {alternative_count} suitable alternative time{'s' if alternative_count != 1 else ''} available, I'm automatically rescheduling to the best option to minimize disruption."
        elif strategy == "propose_alternatives":
            explanation += f"I found {alternative_count} alternative time slots and will present them for your review, allowing you to choose the most convenient option."
        elif strategy == "interactive_resolution":
            explanation += "The conflicts require careful consideration of multiple factors, so I'll present a detailed analysis with options for your decision."
        elif strategy == "batch_resolution":
            explanation += "Multiple conflicts detected require coordinated resolution to avoid creating new conflicts while solving existing ones."
        elif strategy == "escalate_to_human":
            explanation += "The complexity of these conflicts exceeds automated resolution capabilities, requiring human judgment to determine the best course of action."
        else:
            explanation += f"I'm applying the {strategy} approach to resolve these conflicts effectively."
        
        return explanation