"""
Preference management tool for intelligent meeting prioritization and user preference handling.
Provides natural language preference extraction, priority scoring, and VIP contact management.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..services.bedrock_client import BedrockClient
from ..models.preferences import Preferences, VIPContact, MeetingType, FocusBlock, WorkingHours
from ..models.meeting import Meeting
from ..utils.aws_clients import get_dynamodb_resource
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class PreferenceExtractionResult:
    """Result of natural language preference extraction."""
    working_hours: Dict[str, WorkingHours]
    buffer_minutes: int
    focus_blocks: List[FocusBlock]
    vip_contacts: List[str]
    meeting_types: Dict[str, MeetingType]
    confidence_score: float
    extracted_text: str


@dataclass
class MeetingPriorityScore:
    """Meeting priority scoring result."""
    meeting_id: str
    priority_score: float
    priority_factors: Dict[str, float]
    is_vip_meeting: bool
    meeting_type: Optional[str]
    reasoning: str


class PreferenceManagementTool:
    """
    Intelligent preference management tool for meeting scheduling.
    Handles natural language processing, priority scoring, and preference storage.
    """
    
    def __init__(self):
        """Initialize the preference management tool."""
        self.bedrock_client = BedrockClient()
        self.dynamodb = get_dynamodb_resource()
        self.preferences_table = self.dynamodb.Table('UserPreferences')
        self.tool_name = "manage_preferences"
        self.tool_description = "Extract and manage user preferences for intelligent meeting scheduling"
    
    def extract_preferences(self, natural_language_input: str, user_id: str) -> PreferenceExtractionResult:
        """
        Extract user preferences from natural language input using Claude.
        
        Args:
            natural_language_input: User's natural language description of preferences
            user_id: User identifier for context
            
        Returns:
            Structured preference extraction result
        """
        logger.info(f"Extracting preferences for user {user_id} from natural language input")
        
        try:
            # Create prompt for Claude to extract structured preferences
            prompt = self._build_preference_extraction_prompt(natural_language_input)
            
            # Get response from Claude
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=2048,
                temperature=0.1
            )
            
            # Parse the structured response
            extracted_data = self._parse_preference_response(response.content)
            
            # Convert to preference models
            result = self._convert_to_preference_models(extracted_data, natural_language_input)
            
            logger.info(f"Successfully extracted preferences with confidence {result.confidence_score}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract preferences: {str(e)}")
            # Return default preferences on error
            return PreferenceExtractionResult(
                working_hours={},
                buffer_minutes=15,
                focus_blocks=[],
                vip_contacts=[],
                meeting_types={},
                confidence_score=0.0,
                extracted_text=natural_language_input
            )
    
    def _build_preference_extraction_prompt(self, user_input: str) -> str:
        """Build prompt for Claude to extract preferences."""
        return f"""
You are an AI assistant that extracts structured meeting preferences from natural language.

Extract the following information from the user's input and return it as valid JSON:

1. working_hours: Object with day names (monday, tuesday, etc.) as keys and start/end times in HH:MM format
2. buffer_minutes: Number of minutes between meetings (default 15)
3. focus_blocks: Array of objects with day, start, end, and title
4. vip_contacts: Array of email addresses mentioned as important/VIP
5. meeting_types: Object with type names as keys and duration/priority info
6. confidence_score: Float 0-1 indicating extraction confidence

User input: "{user_input}"

Return only valid JSON in this exact format:
{{
  "working_hours": {{"monday": {{"start": "09:00", "end": "17:00"}}}},
  "buffer_minutes": 15,
  "focus_blocks": [{{"day": "monday", "start": "14:00", "end": "16:00", "title": "Deep work"}}],
  "vip_contacts": ["boss@company.com"],
  "meeting_types": {{"standup": {{"duration": 30, "priority": "medium", "buffer_before": 0, "buffer_after": 5}}}},
  "confidence_score": 0.85
}}
"""
    
    def _parse_preference_response(self, response_content: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from response (Claude might include extra text)
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in Claude response")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {}
    
    def _convert_to_preference_models(self, extracted_data: Dict[str, Any], 
                                    original_text: str) -> PreferenceExtractionResult:
        """Convert extracted data to preference models."""
        # Convert working hours
        working_hours = {}
        for day, hours in extracted_data.get('working_hours', {}).items():
            if isinstance(hours, dict) and 'start' in hours and 'end' in hours:
                working_hours[day] = WorkingHours(
                    start=hours['start'],
                    end=hours['end']
                )
        
        # Convert focus blocks
        focus_blocks = []
        for block in extracted_data.get('focus_blocks', []):
            if isinstance(block, dict):
                focus_blocks.append(FocusBlock(
                    day=block.get('day', ''),
                    start=block.get('start', ''),
                    end=block.get('end', ''),
                    title=block.get('title', 'Focus time')
                ))
        
        # Convert meeting types
        meeting_types = {}
        for type_name, type_data in extracted_data.get('meeting_types', {}).items():
            if isinstance(type_data, dict):
                meeting_types[type_name] = MeetingType(
                    duration=type_data.get('duration', 30),
                    priority=type_data.get('priority', 'medium'),
                    buffer_before=type_data.get('buffer_before', 0),
                    buffer_after=type_data.get('buffer_after', 0)
                )
        
        return PreferenceExtractionResult(
            working_hours=working_hours,
            buffer_minutes=extracted_data.get('buffer_minutes', 15),
            focus_blocks=focus_blocks,
            vip_contacts=extracted_data.get('vip_contacts', []),
            meeting_types=meeting_types,
            confidence_score=extracted_data.get('confidence_score', 0.5),
            extracted_text=original_text
        )
    
    def store_preferences(self, user_id: str, preferences: Preferences) -> bool:
        """
        Store user preferences in DynamoDB.
        
        Args:
            user_id: User identifier
            preferences: Preferences object to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert preferences to DynamoDB item
            item = {
                'pk': f"user#{user_id}",
                'sk': 'preferences',
                'working_hours': {day: {'start': wh.start, 'end': wh.end} 
                                for day, wh in preferences.working_hours.items()},
                'buffer_minutes': preferences.buffer_minutes,
                'focus_blocks': [
                    {
                        'day': fb.day,
                        'start': fb.start,
                        'end': fb.end,
                        'title': fb.title
                    } for fb in preferences.focus_blocks
                ],
                'vip_contacts': preferences.vip_contacts,
                'meeting_types': {
                    name: {
                        'duration': mt.duration,
                        'priority': mt.priority,
                        'buffer_before': mt.buffer_before,
                        'buffer_after': mt.buffer_after
                    } for name, mt in preferences.meeting_types.items()
                },
                'updated_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
            }
            
            # Store in DynamoDB
            self.preferences_table.put_item(Item=item)
            
            logger.info(f"Successfully stored preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store preferences for user {user_id}: {str(e)}")
            return False
    
    def retrieve_preferences(self, user_id: str) -> Optional[Preferences]:
        """
        Retrieve user preferences from DynamoDB.
        
        Args:
            user_id: User identifier
            
        Returns:
            Preferences object if found, None otherwise
        """
        try:
            response = self.preferences_table.get_item(
                Key={
                    'pk': f"user#{user_id}",
                    'sk': 'preferences'
                }
            )
            
            if 'Item' not in response:
                logger.info(f"No preferences found for user {user_id}")
                return None
            
            item = response['Item']
            
            # Convert DynamoDB item back to Preferences object
            working_hours = {}
            for day, hours in item.get('working_hours', {}).items():
                working_hours[day] = WorkingHours(
                    start=hours['start'],
                    end=hours['end']
                )
            
            focus_blocks = []
            for block in item.get('focus_blocks', []):
                focus_blocks.append(FocusBlock(
                    day=block['day'],
                    start=block['start'],
                    end=block['end'],
                    title=block['title']
                ))
            
            meeting_types = {}
            for name, type_data in item.get('meeting_types', {}).items():
                meeting_types[name] = MeetingType(
                    duration=type_data['duration'],
                    priority=type_data['priority'],
                    buffer_before=type_data['buffer_before'],
                    buffer_after=type_data['buffer_after']
                )
            
            preferences = Preferences(
                pk=item['pk'],
                working_hours=working_hours,
                buffer_minutes=item.get('buffer_minutes', 15),
                focus_blocks=focus_blocks,
                vip_contacts=item.get('vip_contacts', []),
                meeting_types=meeting_types
            )
            
            logger.info(f"Successfully retrieved preferences for user {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to retrieve preferences for user {user_id}: {str(e)}")
            return None
    
    def evaluate_meeting_priority(self, meeting: Meeting, preferences: Preferences, 
                                user_id: str) -> MeetingPriorityScore:
        """
        Evaluate meeting priority based on user preferences and rules.
        
        Args:
            meeting: Meeting object to evaluate
            preferences: User preferences for priority calculation
            user_id: User identifier for context
            
        Returns:
            Meeting priority score with detailed factors
        """
        logger.debug(f"Evaluating priority for meeting {meeting.sk}")
        
        try:
            priority_factors = {}
            base_score = 0.5  # Start with neutral priority
            
            # Factor 1: VIP Contact Priority (Requirements 4.2)
            vip_score = self._calculate_vip_priority(meeting, preferences)
            priority_factors['vip_contacts'] = vip_score
            base_score += vip_score * 0.3  # 30% weight for VIP contacts
            
            # Factor 2: Meeting Type Priority (Requirements 4.5)
            type_score = self._calculate_meeting_type_priority(meeting, preferences)
            priority_factors['meeting_type'] = type_score
            base_score += type_score * 0.25  # 25% weight for meeting type
            
            # Factor 3: Subject/Title Analysis (Requirements 4.1)
            subject_score = self._analyze_meeting_subject(meeting)
            priority_factors['subject_analysis'] = subject_score
            base_score += subject_score * 0.2  # 20% weight for subject
            
            # Factor 4: Attendee Count and Importance
            attendee_score = self._calculate_attendee_importance(meeting, preferences)
            priority_factors['attendee_importance'] = attendee_score
            base_score += attendee_score * 0.15  # 15% weight for attendees
            
            # Factor 5: Time Sensitivity (urgency keywords, timing)
            urgency_score = self._calculate_urgency_score(meeting)
            priority_factors['urgency'] = urgency_score
            base_score += urgency_score * 0.1  # 10% weight for urgency
            
            # Normalize score to 0-1 range
            final_score = max(0.0, min(1.0, base_score))
            
            # Determine if this is a VIP meeting
            is_vip = vip_score > 0.5
            
            # Determine meeting type
            meeting_type = self._identify_meeting_type(meeting, preferences)
            
            # Generate reasoning
            reasoning = self._generate_priority_reasoning(priority_factors, final_score, is_vip)
            
            result = MeetingPriorityScore(
                meeting_id=meeting.sk,
                priority_score=final_score,
                priority_factors=priority_factors,
                is_vip_meeting=is_vip,
                meeting_type=meeting_type,
                reasoning=reasoning
            )
            
            logger.info(f"Meeting {meeting.sk} priority score: {final_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to evaluate meeting priority: {str(e)}")
            # Return default low priority on error
            return MeetingPriorityScore(
                meeting_id=meeting.sk,
                priority_score=0.3,
                priority_factors={'error': 1.0},
                is_vip_meeting=False,
                meeting_type=None,
                reasoning=f"Error evaluating priority: {str(e)}"
            )
    
    def _calculate_vip_priority(self, meeting: Meeting, preferences: Preferences) -> float:
        """Calculate VIP contact priority score."""
        if not preferences.vip_contacts or not meeting.attendees:
            return 0.0
        
        vip_attendees = []
        for attendee_email in meeting.attendees:
            if attendee_email.lower() in [vip.lower() for vip in preferences.vip_contacts]:
                vip_attendees.append(attendee_email)
        
        if not vip_attendees:
            return 0.0
        
        # Higher score for more VIP attendees
        vip_ratio = len(vip_attendees) / len(meeting.attendees)
        return min(1.0, 0.7 + (vip_ratio * 0.3))  # Base 0.7 for any VIP, up to 1.0
    
    def _calculate_meeting_type_priority(self, meeting: Meeting, preferences: Preferences) -> float:
        """Calculate meeting type priority score."""
        if not preferences.meeting_types:
            return 0.5  # Neutral if no types defined
        
        meeting_type = self._identify_meeting_type(meeting, preferences)
        if not meeting_type or meeting_type not in preferences.meeting_types:
            return 0.5
        
        type_config = preferences.meeting_types[meeting_type]
        priority_map = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'critical': 1.0
        }
        
        return priority_map.get(type_config.priority.lower(), 0.5)
    
    def _identify_meeting_type(self, meeting: Meeting, preferences: Preferences) -> Optional[str]:
        """Identify meeting type based on subject and preferences."""
        if not meeting.title or not preferences.meeting_types:
            return None
        
        subject_lower = meeting.title.lower()
        
        # Check for exact matches first
        for type_name in preferences.meeting_types.keys():
            if type_name.lower() in subject_lower:
                return type_name
        
        # Check for common patterns
        type_patterns = {
            'standup': ['standup', 'daily', 'scrum', 'sync'],
            'review': ['review', 'retrospective', 'retro', 'feedback'],
            'planning': ['planning', 'plan', 'roadmap', 'strategy'],
            'interview': ['interview', 'candidate', 'hiring'],
            'demo': ['demo', 'presentation', 'showcase'],
            'oneonone': ['1:1', 'one-on-one', 'check-in', 'catch up']
        }
        
        for type_name, patterns in type_patterns.items():
            if type_name in preferences.meeting_types:
                for pattern in patterns:
                    if pattern in subject_lower:
                        return type_name
        
        return None
    
    def _analyze_meeting_subject(self, meeting: Meeting) -> float:
        """Analyze meeting subject for priority keywords."""
        if not meeting.title:
            return 0.5
        
        subject_lower = meeting.title.lower()
        
        # High priority keywords
        high_priority_keywords = [
            'urgent', 'asap', 'emergency', 'critical', 'important',
            'board', 'executive', 'ceo', 'cto', 'vp', 'director',
            'crisis', 'escalation', 'deadline', 'launch'
        ]
        
        # Medium priority keywords
        medium_priority_keywords = [
            'review', 'decision', 'approval', 'sign-off',
            'client', 'customer', 'stakeholder', 'investor'
        ]
        
        # Low priority keywords
        low_priority_keywords = [
            'optional', 'fyi', 'social', 'coffee', 'lunch',
            'training', 'learning', 'workshop'
        ]
        
        # Calculate score based on keywords
        score = 0.5  # Base score
        
        for keyword in high_priority_keywords:
            if keyword in subject_lower:
                score += 0.3
                break
        
        for keyword in medium_priority_keywords:
            if keyword in subject_lower:
                score += 0.2
                break
        
        for keyword in low_priority_keywords:
            if keyword in subject_lower:
                score -= 0.2
                break
        
        return max(0.0, min(1.0, score))
    
    def _calculate_attendee_importance(self, meeting: Meeting, preferences: Preferences) -> float:
        """Calculate importance based on attendee count and roles."""
        if not meeting.attendees:
            return 0.3
        
        attendee_count = len(meeting.attendees)
        
        # More attendees generally means higher importance, but with diminishing returns
        if attendee_count == 1:
            return 0.3  # Just the user
        elif attendee_count <= 3:
            return 0.6  # Small group
        elif attendee_count <= 8:
            return 0.8  # Medium group
        else:
            return 0.9  # Large group (likely important)
    
    def _calculate_urgency_score(self, meeting: Meeting) -> float:
        """Calculate urgency based on timing and keywords."""
        if not meeting.start:
            return 0.5
        
        # Check how soon the meeting is
        now = datetime.utcnow()
        time_until_meeting = meeting.start - now
        
        if time_until_meeting.total_seconds() < 0:
            return 0.2  # Past meeting
        elif time_until_meeting.days == 0:
            return 0.9  # Today
        elif time_until_meeting.days == 1:
            return 0.7  # Tomorrow
        elif time_until_meeting.days <= 3:
            return 0.6  # This week
        else:
            return 0.5  # Future
    
    def _generate_priority_reasoning(self, factors: Dict[str, float], 
                                   final_score: float, is_vip: bool) -> str:
        """Generate human-readable reasoning for priority score."""
        reasoning_parts = []
        
        if is_vip:
            reasoning_parts.append("VIP attendees detected")
        
        if factors.get('meeting_type', 0) > 0.7:
            reasoning_parts.append("high-priority meeting type")
        
        if factors.get('subject_analysis', 0) > 0.7:
            reasoning_parts.append("urgent keywords in subject")
        
        if factors.get('attendee_importance', 0) > 0.8:
            reasoning_parts.append("large attendee group")
        
        if factors.get('urgency', 0) > 0.8:
            reasoning_parts.append("time-sensitive meeting")
        
        if not reasoning_parts:
            reasoning_parts.append("standard meeting priority")
        
        priority_level = "high" if final_score > 0.7 else "medium" if final_score > 0.4 else "low"
        
        return f"Priority: {priority_level} ({final_score:.2f}) - {', '.join(reasoning_parts)}"
    
    def update_preferences_from_feedback(self, user_id: str, meeting_id: str, 
                                       user_correction: str) -> bool:
        """
        Update preference weights based on user feedback (Requirements 4.4).
        
        Args:
            user_id: User identifier
            meeting_id: Meeting that was corrected
            user_correction: User's feedback on priority
            
        Returns:
            True if preferences were updated successfully
        """
        try:
            # This would implement machine learning to adjust weights
            # For now, log the feedback for future implementation
            logger.info(f"User {user_id} provided feedback on meeting {meeting_id}: {user_correction}")
            
            # In a full implementation, this would:
            # 1. Analyze the correction
            # 2. Identify which factors were wrong
            # 3. Adjust preference weights
            # 4. Store updated preferences
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update preferences from feedback: {str(e)}")
            return False
    
    def get_conflicting_meetings(self, meetings: List[Meeting], preferences: Preferences) -> List[Tuple[Meeting, Meeting]]:
        """
        Identify conflicting meetings and suggest which should be moved based on priority.
        
        Args:
            meetings: List of meetings to check for conflicts
            preferences: User preferences for priority evaluation
            
        Returns:
            List of conflicting meeting pairs with priority recommendations
        """
        conflicts = []
        
        # Sort meetings by start time
        sorted_meetings = sorted(meetings, key=lambda m: m.start or datetime.min)
        
        for i, meeting1 in enumerate(sorted_meetings):
            for meeting2 in sorted_meetings[i+1:]:
                if self._meetings_conflict(meeting1, meeting2):
                    conflicts.append((meeting1, meeting2))
        
        return conflicts
    
    def _meetings_conflict(self, meeting1: Meeting, meeting2: Meeting) -> bool:
        """Check if two meetings have time conflicts."""
        if not meeting1.start or not meeting1.end or \
           not meeting2.start or not meeting2.end:
            return False
        
        return (meeting1.start < meeting2.end and 
                meeting1.end > meeting2.start)
    
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
                        "enum": ["extract_preferences", "store_preferences", "retrieve_preferences", 
                                "evaluate_priority", "update_from_feedback"],
                        "description": "Action to perform with preferences"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "natural_language_input": {
                        "type": "string",
                        "description": "Natural language description of preferences (for extract_preferences)"
                    },
                    "meeting_data": {
                        "type": "object",
                        "description": "Meeting data for priority evaluation"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "User feedback for preference learning"
                    }
                },
                "required": ["action", "user_id"]
            }
        }