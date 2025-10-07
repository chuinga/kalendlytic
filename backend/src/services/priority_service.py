"""
Priority service for integrating meeting prioritization with the scheduling agent.
Provides high-level interface for priority scoring and conflict resolution.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..tools.prioritization_tool import PrioritizationTool, PriorityScore
from ..tools.preference_management_tool import PreferenceManagementTool
from ..models.meeting import Meeting
from ..models.preferences import Preferences
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class PriorityService:
    """
    High-level service for meeting prioritization and conflict resolution.
    Integrates prioritization tool with scheduling workflows.
    """
    
    def __init__(self):
        """Initialize the priority service."""
        self.prioritization_tool = PrioritizationTool()
        self.preference_tool = PreferenceManagementTool()
    
    def prioritize_meetings(self, meetings: List[Meeting], user_id: str) -> List[Tuple[Meeting, PriorityScore]]:
        """
        Prioritize a list of meetings for a user.
        
        Args:
            meetings: List of meetings to prioritize
            user_id: User identifier
            
        Returns:
            List of (meeting, priority_score) tuples sorted by priority
        """
        logger.info(f"Prioritizing {len(meetings)} meetings for user {user_id}")
        
        try:
            # Get user preferences
            preferences = self.preference_tool.retrieve_preferences(user_id)
            if not preferences:
                logger.warning(f"No preferences found for user {user_id}, using defaults")
                preferences = self._get_default_preferences(user_id)
            
            # Calculate priority for each meeting
            prioritized_meetings = []
            for meeting in meetings:
                try:
                    priority_score = self.prioritization_tool.prioritize_meeting(
                        meeting, preferences, user_id
                    )
                    prioritized_meetings.append((meeting, priority_score))
                except Exception as e:
                    logger.error(f"Failed to prioritize meeting {meeting.sk}: {str(e)}")
                    # Add with default priority
                    default_score = PriorityScore(
                        meeting_id=meeting.sk,
                        priority_score=0.5,
                        priority_factors={'error': 1.0},
                        vip_attendees=[],
                        meeting_type=None,
                        urgency_level='unknown',
                        confidence_score=0.0,
                        reasoning="Error in prioritization"
                    )
                    prioritized_meetings.append((meeting, default_score))
            
            # Sort by priority score (highest first)
            prioritized_meetings.sort(key=lambda x: x[1].priority_score, reverse=True)
            
            logger.info(f"Successfully prioritized {len(prioritized_meetings)} meetings")
            return prioritized_meetings
            
        except Exception as e:
            logger.error(f"Failed to prioritize meetings for user {user_id}: {str(e)}")
            # Return meetings with default priority
            return [(meeting, self._get_default_priority_score(meeting)) for meeting in meetings]
    
    def resolve_conflicts(self, conflicting_meetings: List[Meeting], 
                         user_id: str) -> Dict[str, any]:
        """
        Resolve meeting conflicts based on priority scores.
        
        Args:
            conflicting_meetings: List of conflicting meetings
            user_id: User identifier
            
        Returns:
            Dictionary with conflict resolution recommendations
        """
        logger.info(f"Resolving conflicts for {len(conflicting_meetings)} meetings")
        
        try:
            # Prioritize the conflicting meetings
            prioritized = self.prioritize_meetings(conflicting_meetings, user_id)
            
            if len(prioritized) < 2:
                return {
                    'status': 'no_conflict',
                    'message': 'No conflicts to resolve'
                }
            
            # Identify the highest priority meeting
            highest_priority = prioritized[0]
            conflicting_lower = prioritized[1:]
            
            recommendations = {
                'status': 'conflict_resolved',
                'keep_meeting': {
                    'meeting_id': highest_priority[0].sk,
                    'title': highest_priority[0].title,
                    'priority_score': highest_priority[1].priority_score,
                    'reasoning': highest_priority[1].reasoning
                },
                'reschedule_meetings': [],
                'cancel_meetings': []
            }
            
            # Categorize lower priority meetings
            for meeting, priority_score in conflicting_lower:
                if priority_score.priority_score > 0.3:  # Worth rescheduling
                    recommendations['reschedule_meetings'].append({
                        'meeting_id': meeting.sk,
                        'title': meeting.title,
                        'priority_score': priority_score.priority_score,
                        'reasoning': priority_score.reasoning,
                        'suggested_action': 'reschedule'
                    })
                else:  # Low priority, suggest cancellation
                    recommendations['cancel_meetings'].append({
                        'meeting_id': meeting.sk,
                        'title': meeting.title,
                        'priority_score': priority_score.priority_score,
                        'reasoning': priority_score.reasoning,
                        'suggested_action': 'cancel'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {str(e)}")
            return {
                'status': 'error',
                'message': f"Failed to resolve conflicts: {str(e)}"
            }
    
    def update_priority_from_feedback(self, user_id: str, meeting_id: str,
                                    feedback: str, correct_priority: float) -> bool:
        """
        Update priority scoring based on user feedback.
        
        Args:
            user_id: User identifier
            meeting_id: Meeting that received feedback
            feedback: User's feedback text
            correct_priority: User's corrected priority score
            
        Returns:
            True if update was successful
        """
        logger.info(f"Updating priority from feedback for meeting {meeting_id}")
        
        try:
            return self.prioritization_tool.learn_from_feedback(
                user_id, meeting_id, feedback, correct_priority
            )
        except Exception as e:
            logger.error(f"Failed to update priority from feedback: {str(e)}")
            return False
    
    def get_priority_insights(self, meetings: List[Meeting], user_id: str) -> Dict[str, any]:
        """
        Get insights about meeting priorities for a user.
        
        Args:
            meetings: List of meetings to analyze
            user_id: User identifier
            
        Returns:
            Dictionary with priority insights and statistics
        """
        logger.info(f"Generating priority insights for {len(meetings)} meetings")
        
        try:
            prioritized = self.prioritize_meetings(meetings, user_id)
            
            if not prioritized:
                return {
                    'total_meetings': 0,
                    'insights': []
                }
            
            # Calculate statistics
            priority_scores = [score.priority_score for _, score in prioritized]
            avg_priority = sum(priority_scores) / len(priority_scores)
            
            high_priority_count = len([s for s in priority_scores if s >= 0.7])
            medium_priority_count = len([s for s in priority_scores if 0.4 <= s < 0.7])
            low_priority_count = len([s for s in priority_scores if s < 0.4])
            
            # VIP meeting analysis
            vip_meetings = [
                (meeting, score) for meeting, score in prioritized 
                if score.vip_attendees
            ]
            
            # Meeting type distribution
            meeting_types = {}
            for _, score in prioritized:
                if score.meeting_type:
                    meeting_types[score.meeting_type] = meeting_types.get(score.meeting_type, 0) + 1
            
            insights = {
                'total_meetings': len(meetings),
                'average_priority': round(avg_priority, 3),
                'priority_distribution': {
                    'high': high_priority_count,
                    'medium': medium_priority_count,
                    'low': low_priority_count
                },
                'vip_meetings': len(vip_meetings),
                'meeting_types': meeting_types,
                'top_priority_meetings': [
                    {
                        'title': meeting.title,
                        'priority_score': score.priority_score,
                        'reasoning': score.reasoning
                    }
                    for meeting, score in prioritized[:5]  # Top 5
                ],
                'recommendations': self._generate_priority_recommendations(prioritized)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate priority insights: {str(e)}")
            return {
                'total_meetings': len(meetings),
                'error': str(e)
            }
    
    def _get_default_preferences(self, user_id: str) -> Preferences:
        """Get default preferences for a user."""
        return Preferences(
            pk=f"user#{user_id}",
            working_hours={},
            buffer_minutes=15,
            focus_blocks=[],
            vip_contacts=[],
            meeting_types={}
        )
    
    def _get_default_priority_score(self, meeting: Meeting) -> PriorityScore:
        """Get default priority score for a meeting."""
        return PriorityScore(
            meeting_id=meeting.sk,
            priority_score=0.5,
            priority_factors={'default': 1.0},
            vip_attendees=[],
            meeting_type=None,
            urgency_level='unknown',
            confidence_score=0.5,
            reasoning="Default priority (no preferences available)"
        )
    
    def _generate_priority_recommendations(self, prioritized_meetings: List[Tuple[Meeting, PriorityScore]]) -> List[str]:
        """Generate actionable recommendations based on priority analysis."""
        recommendations = []
        
        if not prioritized_meetings:
            return recommendations
        
        # Check for too many high-priority meetings
        high_priority_meetings = [
            (meeting, score) for meeting, score in prioritized_meetings 
            if score.priority_score >= 0.7
        ]
        
        if len(high_priority_meetings) > 5:
            recommendations.append(
                f"You have {len(high_priority_meetings)} high-priority meetings. "
                "Consider rescheduling some to reduce scheduling pressure."
            )
        
        # Check for VIP meeting clustering
        vip_meetings = [
            (meeting, score) for meeting, score in prioritized_meetings 
            if score.vip_attendees
        ]
        
        if len(vip_meetings) > 3:
            recommendations.append(
                f"You have {len(vip_meetings)} meetings with VIP attendees. "
                "Ensure adequate preparation time between these meetings."
            )
        
        # Check for low-confidence scores
        low_confidence_meetings = [
            (meeting, score) for meeting, score in prioritized_meetings 
            if score.confidence_score < 0.5
        ]
        
        if len(low_confidence_meetings) > 0:
            recommendations.append(
                f"{len(low_confidence_meetings)} meetings have low confidence scores. "
                "Consider updating your preferences or adding more meeting details."
            )
        
        return recommendations