"""
Prompt templates for AI-powered meeting scheduling agent.
Contains structured prompts for different scheduling scenarios.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


class SchedulingPrompts:
    """Prompt templates for meeting scheduling AI reasoning."""
    
    @staticmethod
    def conflict_resolution_prompt(
        meeting_request: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        available_slots: List[Dict[str, Any]]
    ) -> str:
        """
        Generate prompt for resolving scheduling conflicts.
        
        Args:
            meeting_request: Original meeting request details
            conflicts: List of conflicting meetings
            available_slots: Alternative time slots available
            
        Returns:
            Formatted prompt for conflict resolution
        """
        prompt = f"""You are an intelligent meeting scheduling assistant. A meeting request has conflicts with existing meetings. Please analyze the situation and provide recommendations.

MEETING REQUEST:
- Title: {meeting_request.get('title', 'Untitled Meeting')}
- Duration: {meeting_request.get('duration_minutes', 60)} minutes
- Requested Time: {meeting_request.get('requested_time')}
- Priority: {meeting_request.get('priority', 'medium')}
- Attendees: {', '.join(meeting_request.get('attendees', []))}
- Description: {meeting_request.get('description', 'No description provided')}

CONFLICTS DETECTED:
"""
        
        for i, conflict in enumerate(conflicts, 1):
            prompt += f"""
Conflict {i}:
- Title: {conflict.get('title', 'Untitled')}
- Time: {conflict.get('start_time')} - {conflict.get('end_time')}
- Attendees: {', '.join(conflict.get('attendees', []))}
- Priority: {conflict.get('priority', 'medium')}
"""
        
        prompt += f"""
AVAILABLE ALTERNATIVE SLOTS:
"""
        
        for i, slot in enumerate(available_slots, 1):
            prompt += f"""
Option {i}: {slot.get('start_time')} - {slot.get('end_time')}
"""
        
        prompt += """
Please provide your analysis and recommendations in the following JSON format:

{
  "analysis": {
    "conflict_severity": "low|medium|high",
    "impact_assessment": "Brief description of the impact",
    "recommendation_type": "reschedule|override|split|decline"
  },
  "recommendations": [
    {
      "option": 1,
      "action": "reschedule|override|split|decline",
      "new_time": "ISO datetime if rescheduling",
      "rationale": "Explanation for this recommendation",
      "confidence": 0.85
    }
  ],
  "reasoning": "Detailed explanation of your decision-making process"
}

Consider factors like:
- Meeting priorities and importance
- Attendee availability and conflicts
- Business impact of rescheduling
- Time zone considerations
- Meeting dependencies
"""
        
        return prompt
    
    @staticmethod
    def optimal_scheduling_prompt(
        meeting_request: Dict[str, Any],
        attendee_availability: Dict[str, List[Dict[str, Any]]],
        preferences: Dict[str, Any]
    ) -> str:
        """
        Generate prompt for finding optimal meeting times.
        
        Args:
            meeting_request: Meeting request details
            attendee_availability: Availability data for each attendee
            preferences: Scheduling preferences and constraints
            
        Returns:
            Formatted prompt for optimal scheduling
        """
        prompt = f"""You are an intelligent meeting scheduling assistant. Find the optimal time for a meeting based on attendee availability and preferences.

MEETING REQUEST:
- Title: {meeting_request.get('title', 'Untitled Meeting')}
- Duration: {meeting_request.get('duration_minutes', 60)} minutes
- Preferred Time Range: {meeting_request.get('preferred_start')} - {meeting_request.get('preferred_end')}
- Priority: {meeting_request.get('priority', 'medium')}
- Meeting Type: {meeting_request.get('meeting_type', 'general')}
- Attendees: {', '.join(meeting_request.get('attendees', []))}

ATTENDEE AVAILABILITY:
"""
        
        for attendee, availability in attendee_availability.items():
            prompt += f"""
{attendee}:
"""
            for slot in availability:
                prompt += f"  - {slot.get('start')} to {slot.get('end')} (Status: {slot.get('status', 'free')})\n"
        
        prompt += f"""
SCHEDULING PREFERENCES:
- Business Hours: {preferences.get('business_hours', '9:00 AM - 5:00 PM')}
- Time Zone: {preferences.get('timezone', 'UTC')}
- Buffer Time: {preferences.get('buffer_minutes', 15)} minutes between meetings
- Preferred Days: {', '.join(preferences.get('preferred_days', ['Monday-Friday']))}
- Avoid Times: {', '.join(preferences.get('avoid_times', ['Lunch hours']))}

Please analyze the availability and provide optimal scheduling recommendations in JSON format:

{
  "optimal_slots": [
    {
      "start_time": "ISO datetime",
      "end_time": "ISO datetime", 
      "score": 0.95,
      "rationale": "Why this slot is optimal",
      "attendee_conflicts": [],
      "considerations": ["All attendees available", "Within business hours"]
    }
  ],
  "analysis": {
    "total_options_considered": 10,
    "constraints_applied": ["business_hours", "buffer_time"],
    "optimization_factors": ["attendee_availability", "time_preferences", "meeting_type"]
  },
  "recommendations": {
    "primary_choice": "ISO datetime of best option",
    "backup_options": ["ISO datetime 1", "ISO datetime 2"],
    "scheduling_notes": "Any important considerations for the organizer"
  }
}

Optimize for:
- Maximum attendee availability
- Preference alignment
- Minimal conflicts
- Business hour compliance
- Time zone considerations
"""
        
        return prompt
    
    @staticmethod
    def meeting_preparation_prompt(
        meeting_details: Dict[str, Any],
        attendee_context: Dict[str, Any]
    ) -> str:
        """
        Generate prompt for meeting preparation assistance.
        
        Args:
            meeting_details: Details about the upcoming meeting
            attendee_context: Context about attendees and their roles
            
        Returns:
            Formatted prompt for meeting preparation
        """
        prompt = f"""You are an intelligent meeting preparation assistant. Help prepare for an upcoming meeting by analyzing the context and providing actionable recommendations.

MEETING DETAILS:
- Title: {meeting_details.get('title')}
- Date/Time: {meeting_details.get('datetime')}
- Duration: {meeting_details.get('duration_minutes')} minutes
- Meeting Type: {meeting_details.get('meeting_type', 'general')}
- Agenda: {meeting_details.get('agenda', 'No agenda provided')}
- Objectives: {meeting_details.get('objectives', 'No objectives specified')}

ATTENDEE CONTEXT:
"""
        
        for attendee, context in attendee_context.items():
            prompt += f"""
{attendee}:
- Role: {context.get('role', 'Unknown')}
- Department: {context.get('department', 'Unknown')}
- Relevant Projects: {', '.join(context.get('projects', []))}
- Previous Meeting History: {context.get('meeting_history', 'No history')}
"""
        
        prompt += """
Please provide meeting preparation recommendations in JSON format:

{
  "preparation_checklist": [
    {
      "task": "Review quarterly reports",
      "priority": "high",
      "estimated_time": "15 minutes",
      "responsible": "meeting_organizer"
    }
  ],
  "agenda_suggestions": [
    {
      "item": "Project status update",
      "duration": "10 minutes",
      "presenter": "attendee_name",
      "materials_needed": ["status_report", "metrics_dashboard"]
    }
  ],
  "potential_discussion_points": [
    "Budget allocation for Q2",
    "Resource constraints",
    "Timeline adjustments"
  ],
  "recommended_materials": [
    {
      "document": "Q1 Performance Report",
      "relevance": "high",
      "sections": ["Executive Summary", "Key Metrics"]
    }
  ],
  "meeting_optimization": {
    "suggested_duration": "45 minutes",
    "recommended_format": "hybrid",
    "key_decisions_needed": ["Budget approval", "Timeline confirmation"],
    "follow_up_actions": ["Schedule follow-up", "Document decisions"]
  }
}

Consider:
- Meeting objectives and desired outcomes
- Attendee expertise and contributions
- Time efficiency and engagement
- Decision-making requirements
- Follow-up planning
"""
        
        return prompt
    
    @staticmethod
    def rescheduling_communication_prompt(
        original_meeting: Dict[str, Any],
        new_meeting_time: str,
        reason: str,
        attendees: List[str]
    ) -> str:
        """
        Generate prompt for crafting rescheduling communications.
        
        Args:
            original_meeting: Original meeting details
            new_meeting_time: New proposed meeting time
            reason: Reason for rescheduling
            attendees: List of meeting attendees
            
        Returns:
            Formatted prompt for communication generation
        """
        prompt = f"""You are an intelligent communication assistant. Generate professional and considerate rescheduling messages for a meeting change.

ORIGINAL MEETING:
- Title: {original_meeting.get('title')}
- Original Time: {original_meeting.get('original_time')}
- Duration: {original_meeting.get('duration_minutes')} minutes

RESCHEDULING DETAILS:
- New Time: {new_meeting_time}
- Reason: {reason}
- Attendees: {', '.join(attendees)}

Generate rescheduling communications in JSON format:

{
  "email_subject": "Meeting Rescheduled: [Meeting Title] - New Time [Date/Time]",
  "email_body": "Professional email content with apology, explanation, and new details",
  "calendar_update_message": "Brief message for calendar invitation update",
  "slack_notification": "Casual but professional Slack message",
  "sms_message": "Concise SMS for urgent notifications",
  "communication_strategy": {
    "primary_channel": "email",
    "follow_up_channels": ["calendar", "slack"],
    "timing": "Send immediately",
    "tone": "apologetic_professional"
  }
}

Ensure the communication:
- Acknowledges the inconvenience
- Clearly states the new time and date
- Provides the reason for rescheduling
- Maintains professional tone
- Includes all necessary meeting details
- Offers alternative contact methods if needed
"""
        
        return prompt