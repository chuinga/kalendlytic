"""
Conflict resolution tool for intelligent meeting scheduling.
Provides conflict detection, resolution option generation, and automatic rescheduling
with priority-based ranking and user approval workflows.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..services.conflict_resolution_engine import (
    ConflictResolutionEngine, 
    ConflictDetails, 
    ResolutionOption,
    ConflictResolutionResult
)
from ..models.meeting import Meeting
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class ConflictDetectionRequest:
    """Request parameters for conflict detection."""
    user_id: str
    start_date: datetime
    end_date: datetime
    connections: List[Connection]
    preferences: Optional[Preferences] = None
    proposed_meeting: Optional[Dict[str, Any]] = None


@dataclass
class ConflictResolutionRequest:
    """Request parameters for conflict resolution."""
    user_id: str
    conflict_id: str
    connections: List[Connection]
    preferences: Optional[Preferences] = None
    auto_execute: bool = False


@dataclass
class ConflictDetectionResponse:
    """Response containing detected conflicts."""
    conflicts: List[Dict[str, Any]]
    total_conflicts: int
    has_conflicts: bool
    detection_time_ms: int
    summary: Dict[str, Any]


@dataclass
class ConflictResolutionResponse:
    """Response containing resolution options."""
    conflict_id: str
    resolution_options: List[Dict[str, Any]]
    recommended_option: Optional[Dict[str, Any]]
    workflow_id: str
    requires_approval: bool
    processing_time_ms: int


class ConflictResolutionTool:
    """
    Intelligent conflict resolution tool that integrates with the scheduling agent.
    Provides comprehensive conflict detection and resolution capabilities.
    """
    
    def __init__(self):
        """Initialize the conflict resolution tool."""
        self.conflict_engine = ConflictResolutionEngine()
        self.tool_name = "resolve_scheduling_conflicts"
        self.tool_description = "Detect and resolve scheduling conflicts with intelligent recommendations"
    
    def detect_conflicts(self, request: ConflictDetectionRequest) -> ConflictDetectionResponse:
        """
        Detect scheduling conflicts in a given time range.
        
        Args:
            request: Conflict detection request parameters
            
        Returns:
            Conflict detection response with detailed conflict information
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Detecting conflicts for user {request.user_id} "
                       f"from {request.start_date} to {request.end_date}")
            
            # Detect conflicts using the engine
            conflicts = self.conflict_engine.detect_conflicts(
                user_id=request.user_id,
                start_date=request.start_date,
                end_date=request.end_date,
                connections=request.connections,
                preferences=request.preferences,
                proposed_meeting=request.proposed_meeting
            )
            
            # Convert conflicts to serializable format
            conflicts_data = []
            for conflict in conflicts:
                conflict_data = {
                    'conflict_id': conflict.conflict_id,
                    'conflict_type': conflict.conflict_type.value,
                    'severity': conflict.severity.value,
                    'description': conflict.description,
                    'primary_meeting': {
                        'id': conflict.primary_meeting.sk,
                        'title': conflict.primary_meeting.title,
                        'start': conflict.primary_meeting.start.isoformat(),
                        'end': conflict.primary_meeting.end.isoformat(),
                        'provider': conflict.primary_meeting.provider
                    },
                    'conflicting_meetings': [
                        {
                            'id': meeting.sk,
                            'title': meeting.title,
                            'start': meeting.start.isoformat(),
                            'end': meeting.end.isoformat(),
                            'provider': meeting.provider
                        }
                        for meeting in conflict.conflicting_meetings
                    ],
                    'affected_time_range': {
                        'start': conflict.affected_time_range[0].isoformat(),
                        'end': conflict.affected_time_range[1].isoformat()
                    },
                    'suggested_strategy': conflict.suggested_strategy.value
                }
                conflicts_data.append(conflict_data)
            
            # Generate summary statistics
            summary = self._generate_conflict_summary(conflicts)
            
            # Calculate processing time
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            logger.info(f"Detected {len(conflicts)} conflicts for user {request.user_id}")
            
            return ConflictDetectionResponse(
                conflicts=conflicts_data,
                total_conflicts=len(conflicts),
                has_conflicts=len(conflicts) > 0,
                detection_time_ms=processing_time,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts for user {request.user_id}: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ConflictDetectionResponse(
                conflicts=[],
                total_conflicts=0,
                has_conflicts=False,
                detection_time_ms=processing_time,
                summary={'error': str(e)}
            )
    
    def generate_resolution_options(self, request: ConflictResolutionRequest,
                                  conflict_details: ConflictDetails) -> ConflictResolutionResponse:
        """
        Generate resolution options for a detected conflict.
        
        Args:
            request: Conflict resolution request parameters
            conflict_details: Details of the conflict to resolve
            
        Returns:
            Conflict resolution response with available options
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating resolution options for conflict {request.conflict_id}")
            
            # Generate resolution options
            options = self.conflict_engine.generate_resolution_options(
                conflict=conflict_details,
                user_id=request.user_id,
                connections=request.connections,
                preferences=request.preferences
            )
            
            # Convert options to serializable format
            options_data = []
            recommended_option = None
            
            for option in options:
                option_data = {
                    'option_id': option.option_id,
                    'strategy': option.strategy.value,
                    'description': option.description,
                    'confidence_score': option.confidence_score,
                    'requires_approval': option.requires_approval,
                    'estimated_impact': option.estimated_impact,
                    'affected_meetings': option.affected_meetings,
                    'alternative_slots': [
                        {
                            'start': slot.start.isoformat(),
                            'end': slot.end.isoformat(),
                            'score': slot.score,
                            'available': slot.available
                        }
                        for slot in option.alternative_slots
                    ] if option.alternative_slots else []
                }
                options_data.append(option_data)
                
                # Set recommended option (highest confidence score)
                if recommended_option is None or option.confidence_score > recommended_option['confidence_score']:
                    recommended_option = option_data
            
            # Create approval workflow
            workflow = self.conflict_engine.create_approval_workflow(
                conflict=conflict_details,
                options=options,
                user_id=request.user_id
            )
            
            # Calculate processing time
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            logger.info(f"Generated {len(options)} resolution options for conflict {request.conflict_id}")
            
            return ConflictResolutionResponse(
                conflict_id=request.conflict_id,
                resolution_options=options_data,
                recommended_option=recommended_option,
                workflow_id=workflow['workflow_id'],
                requires_approval=any(opt['requires_approval'] for opt in options_data),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to generate resolution options: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return ConflictResolutionResponse(
                conflict_id=request.conflict_id,
                resolution_options=[],
                recommended_option=None,
                workflow_id="",
                requires_approval=True,
                processing_time_ms=processing_time
            )
    
    def execute_resolution(self, workflow_id: str, selected_option_id: str,
                          user_id: str, connections: List[Connection],
                          user_feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an approved conflict resolution.
        
        Args:
            workflow_id: Approval workflow identifier
            selected_option_id: ID of the selected resolution option
            user_id: User identifier
            connections: List of active calendar connections
            user_feedback: Optional user feedback
            
        Returns:
            Execution results with success/failure details
        """
        try:
            logger.info(f"Executing resolution for workflow {workflow_id}")
            
            # Process user approval
            resolution_result = self.conflict_engine.process_user_approval(
                workflow_id=workflow_id,
                selected_option_id=selected_option_id,
                user_feedback=user_feedback
            )
            
            # Execute the resolution
            execution_result = self.conflict_engine.execute_resolution(
                resolution_result=resolution_result,
                user_id=user_id,
                connections=connections
            )
            
            logger.info(f"Resolution execution completed: {execution_result.get('success', False)}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Failed to execute resolution: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'workflow_id': workflow_id,
                'completed_at': datetime.utcnow().isoformat()
            }
    
    def get_conflict_statistics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Get conflict resolution statistics for a user.
        
        Args:
            user_id: User identifier
            days_back: Number of days to look back for statistics
            
        Returns:
            Dictionary with conflict resolution statistics
        """
        try:
            # This would typically query stored conflict resolution data
            # For now, return mock statistics
            return {
                'user_id': user_id,
                'period_days': days_back,
                'total_conflicts_detected': 0,
                'total_conflicts_resolved': 0,
                'resolution_success_rate': 0.0,
                'average_resolution_time_minutes': 0,
                'conflict_types': {
                    'direct_overlap': 0,
                    'buffer_violation': 0,
                    'focus_block_conflict': 0,
                    'working_hours_violation': 0,
                    'double_booking': 0
                },
                'resolution_strategies': {
                    'reschedule_lower_priority': 0,
                    'find_alternative_slots': 0,
                    'shorten_meetings': 0,
                    'escalate_to_human': 0,
                    'auto_decline': 0
                },
                'user_satisfaction_score': 0.0,
                'recommendations': []
            }
            
        except Exception as e:
            logger.error(f"Failed to get conflict statistics: {str(e)}")
            return {
                'error': str(e),
                'user_id': user_id
            }
    
    def _generate_conflict_summary(self, conflicts: List[ConflictDetails]) -> Dict[str, Any]:
        """Generate summary statistics for detected conflicts."""
        if not conflicts:
            return {
                'total_conflicts': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'recommendations': ['No conflicts detected']
            }
        
        # Count by severity
        severity_counts = {}
        for conflict in conflicts:
            severity = conflict.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by type
        type_counts = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type.value
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
        
        # Generate recommendations
        recommendations = []
        
        if severity_counts.get('critical', 0) > 0:
            recommendations.append("Immediate attention required for critical conflicts")
        
        if severity_counts.get('high', 0) > 2:
            recommendations.append("Multiple high-priority conflicts detected - consider rescheduling")
        
        if type_counts.get('direct_overlap', 0) > 0:
            recommendations.append("Direct meeting overlaps require immediate resolution")
        
        if type_counts.get('buffer_violation', 0) > 3:
            recommendations.append("Consider increasing buffer time between meetings")
        
        if not recommendations:
            recommendations.append("All conflicts are manageable with standard resolution strategies")
        
        return {
            'total_conflicts': len(conflicts),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'recommendations': recommendations,
            'most_common_type': max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None,
            'highest_severity': max(severity_counts.keys()) if severity_counts else None
        }
    
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
                        "enum": ["detect_conflicts", "generate_options", "execute_resolution", "get_statistics"],
                        "description": "Action to perform: detect conflicts, generate resolution options, execute resolution, or get statistics"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier for conflict resolution operations"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Start date for conflict detection (ISO format)"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date-time",
                        "description": "End date for conflict detection (ISO format)"
                    },
                    "connections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "provider": {"type": "string"},
                                "status": {"type": "string"}
                            }
                        },
                        "description": "List of active calendar connections"
                    },
                    "preferences": {
                        "type": "object",
                        "description": "User preferences for scheduling and conflict resolution"
                    },
                    "proposed_meeting": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "start": {"type": "string", "format": "date-time"},
                            "end": {"type": "string", "format": "date-time"},
                            "attendees": {"type": "array", "items": {"type": "string"}}
                        },
                        "description": "Optional proposed meeting to check for conflicts"
                    },
                    "conflict_id": {
                        "type": "string",
                        "description": "Conflict identifier for resolution operations"
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow identifier for resolution execution"
                    },
                    "selected_option_id": {
                        "type": "string",
                        "description": "Selected resolution option identifier"
                    },
                    "user_feedback": {
                        "type": "string",
                        "description": "Optional user feedback for resolution"
                    },
                    "auto_execute": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to automatically execute the best resolution option"
                    },
                    "days_back": {
                        "type": "integer",
                        "default": 30,
                        "description": "Number of days to look back for statistics"
                    }
                },
                "required": ["action", "user_id"]
            }
        }
    
    def invoke(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main tool invocation method for agent integration.
        
        Args:
            parameters: Tool parameters from the agent
            
        Returns:
            Tool execution results
        """
        try:
            action = parameters.get('action')
            user_id = parameters.get('user_id')
            
            if not action or not user_id:
                return {
                    'success': False,
                    'error': 'Missing required parameters: action and user_id'
                }
            
            if action == 'detect_conflicts':
                return self._handle_detect_conflicts(parameters)
            elif action == 'generate_options':
                return self._handle_generate_options(parameters)
            elif action == 'execute_resolution':
                return self._handle_execute_resolution(parameters)
            elif action == 'get_statistics':
                return self._handle_get_statistics(parameters)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
                
        except Exception as e:
            logger.error(f"Tool invocation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_detect_conflicts(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conflict detection action."""
        try:
            request = ConflictDetectionRequest(
                user_id=parameters['user_id'],
                start_date=datetime.fromisoformat(parameters['start_date']),
                end_date=datetime.fromisoformat(parameters['end_date']),
                connections=parameters.get('connections', []),
                preferences=parameters.get('preferences'),
                proposed_meeting=parameters.get('proposed_meeting')
            )
            
            response = self.detect_conflicts(request)
            
            return {
                'success': True,
                'action': 'detect_conflicts',
                'data': {
                    'conflicts': response.conflicts,
                    'total_conflicts': response.total_conflicts,
                    'has_conflicts': response.has_conflicts,
                    'detection_time_ms': response.detection_time_ms,
                    'summary': response.summary
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Conflict detection failed: {str(e)}'
            }
    
    def _handle_generate_options(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resolution options generation action."""
        try:
            # This would typically retrieve conflict details from storage
            # For now, return a placeholder response
            return {
                'success': True,
                'action': 'generate_options',
                'data': {
                    'conflict_id': parameters.get('conflict_id'),
                    'resolution_options': [],
                    'recommended_option': None,
                    'workflow_id': f"workflow_{int(datetime.utcnow().timestamp())}",
                    'requires_approval': True,
                    'processing_time_ms': 100
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Option generation failed: {str(e)}'
            }
    
    def _handle_execute_resolution(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resolution execution action."""
        try:
            workflow_id = parameters.get('workflow_id')
            selected_option_id = parameters.get('selected_option_id')
            user_id = parameters['user_id']
            connections = parameters.get('connections', [])
            user_feedback = parameters.get('user_feedback')
            
            result = self.execute_resolution(
                workflow_id=workflow_id,
                selected_option_id=selected_option_id,
                user_id=user_id,
                connections=connections,
                user_feedback=user_feedback
            )
            
            return {
                'success': result.get('success', False),
                'action': 'execute_resolution',
                'data': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Resolution execution failed: {str(e)}'
            }
    
    def _handle_get_statistics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle statistics retrieval action."""
        try:
            user_id = parameters['user_id']
            days_back = parameters.get('days_back', 30)
            
            stats = self.get_conflict_statistics(user_id, days_back)
            
            return {
                'success': True,
                'action': 'get_statistics',
                'data': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Statistics retrieval failed: {str(e)}'
            }