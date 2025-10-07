"""
Priority scoring system for intelligent meeting prioritization.
Implements attendee analysis, VIP detection, meeting type classification, and learning mechanisms.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..services.bedrock_client import BedrockClient
from ..models.preferences import Preferences, VIPContact, MeetingType
from ..models.meeting import Meeting
from ..utils.aws_clients import get_dynamodb_resource
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class PriorityScore:
    """Meeting priority scoring result with detailed breakdown."""
    meeting_id: str
    priority_score: float
    priority_factors: Dict[str, float]
    vip_attendees: List[str]
    meeting_type: Optional[str]
    urgency_level: str
    confidence_score: float
    reasoning: str
    learning_feedback: Optional[str] = None


@dataclass
class AttendeeAnalysis:
    """Analysis of meeting attendees for priority scoring."""
    total_attendees: int
    vip_attendees: List[str]
    vip_ratio: float
    attendee_importance_score: float
    domain_analysis: Dict[str, int]


class PrioritizationTool:
    """
    Intelligent meeting prioritization system.
    Implements priority scoring based on attendees, subject analysis, VIP detection, and learning.
    """
    
    def __init__(self):
        """Initialize the prioritization tool."""
        self.bedrock_client = BedrockClient()
        self.dynamodb = get_dynamodb_resource()
        self.priority_table = self.dynamodb.Table('MeetingPriorities')
        self.learning_table = self.dynamodb.Table('PriorityLearning')
        self.tool_name = "prioritize_meeting"
        self.tool_description = "Analyze and score meeting priority based on attendees, subject, and user preferences"
        
        # Priority weights (can be adjusted through learning)
        self.default_weights = {
            'vip_contacts': 0.30,
            'meeting_type': 0.25,
            'subject_analysis': 0.20,
            'attendee_importance': 0.15,
            'urgency': 0.10
        }
    
    def prioritize_meeting(self, meeting: Meeting, preferences: Preferences, 
                          user_id: str) -> PriorityScore:
        """
        Main function to prioritize a meeting based on all factors.
        
        Args:
            meeting: Meeting object to prioritize
            preferences: User preferences for priority calculation
            user_id: User identifier for personalized scoring
            
        Returns:
            Comprehensive priority score with detailed analysis
        """
        logger.info(f"Prioritizing meeting {meeting.sk} for user {user_id}")
        
        try:
            # Get personalized weights (learned from user feedback)
            weights = self._get_personalized_weights(user_id)
            
            # Analyze attendees
            attendee_analysis = self._analyze_attendees(meeting, preferences)
            
            # Calculate individual priority factors
            priority_factors = {}
            
            # Factor 1: VIP Contact Priority (Requirements 4.2)
            vip_score = self._calculate_vip_priority(attendee_analysis, preferences)
            priority_factors['vip_contacts'] = vip_score
            
            # Factor 2: Meeting Type Priority (Requirements 4.1, 4.3)
            type_score, meeting_type = self._classify_meeting_type(meeting, preferences)
            priority_factors['meeting_type'] = type_score
            
            # Factor 3: Subject Analysis (Requirements 4.1)
            subject_score = self._analyze_meeting_subject(meeting)
            priority_factors['subject_analysis'] = subject_score
            
            # Factor 4: Attendee Importance
            attendee_score = attendee_analysis.attendee_importance_score
            priority_factors['attendee_importance'] = attendee_score
            
            # Factor 5: Urgency Analysis
            urgency_score, urgency_level = self._calculate_urgency_score(meeting)
            priority_factors['urgency'] = urgency_score
            
            # Calculate weighted final score
            final_score = self._calculate_weighted_score(priority_factors, weights)
            
            # Calculate confidence based on available data
            confidence = self._calculate_confidence_score(meeting, preferences, priority_factors)
            
            # Generate reasoning
            reasoning = self._generate_priority_reasoning(
                priority_factors, final_score, attendee_analysis, meeting_type, urgency_level
            )
            
            # Create result
            result = PriorityScore(
                meeting_id=meeting.sk,
                priority_score=final_score,
                priority_factors=priority_factors,
                vip_attendees=attendee_analysis.vip_attendees,
                meeting_type=meeting_type,
                urgency_level=urgency_level,
                confidence_score=confidence,
                reasoning=reasoning
            )
            
            # Store priority score for learning
            self._store_priority_score(user_id, result)
            
            logger.info(f"Meeting {meeting.sk} priority: {final_score:.3f} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to prioritize meeting {meeting.sk}: {str(e)}")
            # Return default priority on error
            return PriorityScore(
                meeting_id=meeting.sk,
                priority_score=0.5,
                priority_factors={'error': 1.0},
                vip_attendees=[],
                meeting_type=None,
                urgency_level='unknown',
                confidence_score=0.0,
                reasoning=f"Error in prioritization: {str(e)}"
            )
    
    def _analyze_attendees(self, meeting: Meeting, preferences: Preferences) -> AttendeeAnalysis:
        """
        Comprehensive attendee analysis for priority scoring.
        
        Args:
            meeting: Meeting to analyze
            preferences: User preferences with VIP contacts
            
        Returns:
            Detailed attendee analysis
        """
        if not meeting.attendees:
            return AttendeeAnalysis(
                total_attendees=0,
                vip_attendees=[],
                vip_ratio=0.0,
                attendee_importance_score=0.3,
                domain_analysis={}
            )
        
        total_attendees = len(meeting.attendees)
        vip_attendees = []
        domain_analysis = {}
        
        # Identify VIP attendees
        vip_emails = [vip.lower() for vip in preferences.vip_contacts] if preferences.vip_contacts else []
        
        for attendee_email in meeting.attendees:
            if attendee_email.lower() in vip_emails:
                vip_attendees.append(attendee_email)
            
            # Analyze email domains for organizational importance
            if '@' in attendee_email:
                domain = attendee_email.split('@')[1].lower()
                domain_analysis[domain] = domain_analysis.get(domain, 0) + 1
        
        vip_ratio = len(vip_attendees) / total_attendees if total_attendees > 0 else 0.0
        
        # Calculate attendee importance score
        importance_score = self._calculate_attendee_importance_score(
            total_attendees, vip_ratio, domain_analysis
        )
        
        return AttendeeAnalysis(
            total_attendees=total_attendees,
            vip_attendees=vip_attendees,
            vip_ratio=vip_ratio,
            attendee_importance_score=importance_score,
            domain_analysis=domain_analysis
        )
    
    def _calculate_vip_priority(self, attendee_analysis: AttendeeAnalysis, 
                              preferences: Preferences) -> float:
        """
        Calculate VIP contact priority score with enhanced detection.
        
        Args:
            attendee_analysis: Analysis of meeting attendees
            preferences: User preferences with VIP contacts
            
        Returns:
            VIP priority score (0.0 to 1.0)
        """
        if not attendee_analysis.vip_attendees:
            return 0.0
        
        # Base score for having any VIP attendees
        base_vip_score = 0.7
        
        # Bonus for higher VIP ratio
        vip_ratio_bonus = attendee_analysis.vip_ratio * 0.3
        
        # Bonus for multiple VIP attendees
        multiple_vip_bonus = min(0.2, (len(attendee_analysis.vip_attendees) - 1) * 0.1)
        
        total_score = base_vip_score + vip_ratio_bonus + multiple_vip_bonus
        
        return min(1.0, total_score)
    
    def _classify_meeting_type(self, meeting: Meeting, preferences: Preferences) -> Tuple[float, Optional[str]]:
        """
        Classify meeting type and return priority score.
        
        Args:
            meeting: Meeting to classify
            preferences: User preferences with meeting types
            
        Returns:
            Tuple of (priority_score, meeting_type)
        """
        if not meeting.title:
            return 0.5, None
        
        subject_lower = meeting.title.lower()
        
        # Check user-defined meeting types first
        if preferences.meeting_types:
            for type_name, type_config in preferences.meeting_types.items():
                if type_name.lower() in subject_lower:
                    priority_map = {
                        'low': 0.2,
                        'medium': 0.5,
                        'high': 0.8,
                        'critical': 1.0
                    }
                    score = priority_map.get(type_config.priority.lower(), 0.5)
                    return score, type_name
        
        # Use AI-powered classification for unknown types
        classified_type, confidence = self._ai_classify_meeting_type(meeting)
        
        if classified_type and confidence > 0.7:
            # Default priority mapping for AI-classified types
            type_priority_map = {
                'executive': 0.9,
                'board': 1.0,
                'client': 0.8,
                'interview': 0.7,
                'review': 0.6,
                'standup': 0.4,
                'social': 0.2,
                'training': 0.3,
                'demo': 0.6,
                'planning': 0.7
            }
            score = type_priority_map.get(classified_type, 0.5)
            return score, classified_type
        
        return 0.5, None
    
    def _ai_classify_meeting_type(self, meeting: Meeting) -> Tuple[Optional[str], float]:
        """
        Use AI to classify meeting type from subject and context.
        
        Args:
            meeting: Meeting to classify
            
        Returns:
            Tuple of (meeting_type, confidence_score)
        """
        try:
            prompt = f"""
Classify the following meeting into one of these categories based on the subject and attendee information:

Categories: executive, board, client, interview, review, standup, social, training, demo, planning, other

Meeting Subject: "{meeting.title}"
Number of Attendees: {len(meeting.attendees) if meeting.attendees else 0}
Duration: {(meeting.end - meeting.start).total_seconds() / 60 if meeting.start and meeting.end else 'unknown'} minutes

Return only a JSON object with "type" and "confidence" (0-1):
{{"type": "category_name", "confidence": 0.85}}
"""
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1
            )
            
            # Parse response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('type'), result.get('confidence', 0.0)
            
        except Exception as e:
            logger.warning(f"AI classification failed: {str(e)}")
        
        return None, 0.0 
   
    def _analyze_meeting_subject(self, meeting: Meeting) -> float:
        """
        Analyze meeting subject for priority keywords and patterns.
        
        Args:
            meeting: Meeting to analyze
            
        Returns:
            Subject priority score (0.0 to 1.0)
        """
        if not meeting.title:
            return 0.5
        
        subject_lower = meeting.title.lower()
        
        # Critical priority keywords
        critical_keywords = [
            'emergency', 'crisis', 'urgent', 'asap', 'critical',
            'board meeting', 'ceo', 'executive', 'escalation'
        ]
        
        # High priority keywords
        high_priority_keywords = [
            'important', 'deadline', 'launch', 'go-live', 'release',
            'client', 'customer', 'investor', 'stakeholder',
            'decision', 'approval', 'sign-off', 'review'
        ]
        
        # Medium priority keywords
        medium_priority_keywords = [
            'planning', 'strategy', 'roadmap', 'discussion',
            'update', 'status', 'sync', 'check-in'
        ]
        
        # Low priority keywords
        low_priority_keywords = [
            'optional', 'fyi', 'social', 'coffee', 'lunch',
            'training', 'learning', 'workshop', 'casual'
        ]
        
        # Calculate score based on keyword presence
        score = 0.5  # Base neutral score
        
        # Check for critical keywords (highest priority)
        for keyword in critical_keywords:
            if keyword in subject_lower:
                return 1.0  # Maximum priority
        
        # Check for high priority keywords
        for keyword in high_priority_keywords:
            if keyword in subject_lower:
                score = max(score, 0.8)
        
        # Check for medium priority keywords
        for keyword in medium_priority_keywords:
            if keyword in subject_lower:
                score = max(score, 0.6)
        
        # Check for low priority keywords (reduces score)
        for keyword in low_priority_keywords:
            if keyword in subject_lower:
                score = min(score, 0.3)
        
        # Additional analysis for urgency indicators
        urgency_patterns = [
            r'\basap\b', r'\burgent\b', r'\bemergency\b',
            r'\btoday\b', r'\bnow\b', r'\bimmediate\b'
        ]
        
        for pattern in urgency_patterns:
            if re.search(pattern, subject_lower):
                score = min(1.0, score + 0.2)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_attendee_importance_score(self, total_attendees: int, 
                                           vip_ratio: float, 
                                           domain_analysis: Dict[str, int]) -> float:
        """
        Calculate attendee importance score based on count and composition.
        
        Args:
            total_attendees: Total number of attendees
            vip_ratio: Ratio of VIP attendees
            domain_analysis: Email domain distribution
            
        Returns:
            Attendee importance score (0.0 to 1.0)
        """
        if total_attendees == 0:
            return 0.3
        
        # Base score from attendee count
        if total_attendees == 1:
            count_score = 0.3  # Just the user
        elif total_attendees <= 3:
            count_score = 0.5  # Small group
        elif total_attendees <= 8:
            count_score = 0.7  # Medium group
        elif total_attendees <= 15:
            count_score = 0.8  # Large group
        else:
            count_score = 0.9  # Very large group
        
        # Bonus for VIP ratio
        vip_bonus = vip_ratio * 0.2
        
        # Bonus for external domains (potential clients/partners)
        external_bonus = 0.0
        if domain_analysis:
            total_domains = len(domain_analysis)
            if total_domains > 1:  # Multiple organizations
                external_bonus = min(0.1, (total_domains - 1) * 0.05)
        
        final_score = count_score + vip_bonus + external_bonus
        return min(1.0, final_score)
    
    def _calculate_urgency_score(self, meeting: Meeting) -> Tuple[float, str]:
        """
        Calculate urgency score based on timing and context.
        
        Args:
            meeting: Meeting to analyze
            
        Returns:
            Tuple of (urgency_score, urgency_level)
        """
        if not meeting.start:
            return 0.5, 'unknown'
        
        now = datetime.utcnow()
        time_until_meeting = meeting.start - now
        
        # Past meetings
        if time_until_meeting.total_seconds() < 0:
            return 0.1, 'past'
        
        # Calculate urgency based on time remaining
        hours_until = time_until_meeting.total_seconds() / 3600
        
        if hours_until < 1:
            return 1.0, 'immediate'
        elif hours_until < 4:
            return 0.9, 'very_urgent'
        elif hours_until < 24:
            return 0.8, 'urgent'
        elif hours_until < 48:
            return 0.6, 'soon'
        elif hours_until < 168:  # 1 week
            return 0.5, 'this_week'
        else:
            return 0.4, 'future'
    
    def _calculate_weighted_score(self, factors: Dict[str, float], 
                                weights: Dict[str, float]) -> float:
        """
        Calculate final weighted priority score.
        
        Args:
            factors: Individual priority factor scores
            weights: Weights for each factor
            
        Returns:
            Final weighted score (0.0 to 1.0)
        """
        total_score = 0.0
        total_weight = 0.0
        
        for factor, score in factors.items():
            if factor in weights:
                weight = weights[factor]
                total_score += score * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.5  # Default neutral score
        
        return max(0.0, min(1.0, final_score))
    
    def _calculate_confidence_score(self, meeting: Meeting, preferences: Preferences,
                                  factors: Dict[str, float]) -> float:
        """
        Calculate confidence in the priority score based on available data.
        
        Args:
            meeting: Meeting being scored
            preferences: User preferences
            factors: Calculated priority factors
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence_factors = []
        
        # Subject analysis confidence
        if meeting.title and len(meeting.title.strip()) > 5:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.3)
        
        # Attendee analysis confidence
        if meeting.attendees and len(meeting.attendees) > 0:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.2)
        
        # VIP detection confidence
        if preferences.vip_contacts:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)
        
        # Meeting type confidence
        if preferences.meeting_types:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)
        
        # Timing confidence
        if meeting.start and meeting.end:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        
        return sum(confidence_factors) / len(confidence_factors)    

    def _generate_priority_reasoning(self, factors: Dict[str, float], final_score: float,
                                   attendee_analysis: AttendeeAnalysis, meeting_type: Optional[str],
                                   urgency_level: str) -> str:
        """
        Generate human-readable reasoning for the priority score.
        
        Args:
            factors: Priority factor scores
            final_score: Final calculated score
            attendee_analysis: Attendee analysis results
            meeting_type: Identified meeting type
            urgency_level: Urgency classification
            
        Returns:
            Human-readable reasoning string
        """
        reasoning_parts = []
        
        # Priority level classification
        if final_score >= 0.8:
            priority_level = "HIGH"
        elif final_score >= 0.6:
            priority_level = "MEDIUM-HIGH"
        elif final_score >= 0.4:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"
        
        reasoning_parts.append(f"Priority: {priority_level} ({final_score:.2f})")
        
        # VIP attendees
        if attendee_analysis.vip_attendees:
            vip_count = len(attendee_analysis.vip_attendees)
            reasoning_parts.append(f"{vip_count} VIP attendee{'s' if vip_count > 1 else ''} detected")
        
        # Meeting type
        if meeting_type:
            reasoning_parts.append(f"Meeting type: {meeting_type}")
        
        # Urgency
        if urgency_level in ['immediate', 'very_urgent', 'urgent']:
            reasoning_parts.append(f"Time-sensitive ({urgency_level})")
        
        # Attendee count
        if attendee_analysis.total_attendees > 8:
            reasoning_parts.append(f"Large meeting ({attendee_analysis.total_attendees} attendees)")
        elif attendee_analysis.total_attendees > 3:
            reasoning_parts.append(f"Group meeting ({attendee_analysis.total_attendees} attendees)")
        
        # Subject analysis
        subject_score = factors.get('subject_analysis', 0.5)
        if subject_score > 0.7:
            reasoning_parts.append("High-priority keywords detected")
        elif subject_score < 0.4:
            reasoning_parts.append("Low-priority indicators found")
        
        return " | ".join(reasoning_parts)
    
    def _get_personalized_weights(self, user_id: str) -> Dict[str, float]:
        """
        Get personalized priority weights based on user feedback learning.
        
        Args:
            user_id: User identifier
            
        Returns:
            Personalized weights dictionary
        """
        try:
            # Try to retrieve learned weights from DynamoDB
            response = self.learning_table.get_item(
                Key={
                    'pk': f"user#{user_id}",
                    'sk': 'priority_weights'
                }
            )
            
            if 'Item' in response:
                learned_weights = response['Item'].get('weights', {})
                # Merge with defaults
                weights = self.default_weights.copy()
                weights.update(learned_weights)
                return weights
            
        except Exception as e:
            logger.warning(f"Failed to retrieve personalized weights for user {user_id}: {str(e)}")
        
        return self.default_weights.copy()
    
    def _store_priority_score(self, user_id: str, priority_score: PriorityScore) -> bool:
        """
        Store priority score for future learning and analysis.
        
        Args:
            user_id: User identifier
            priority_score: Priority score result to store
            
        Returns:
            True if stored successfully
        """
        try:
            item = {
                'pk': f"user#{user_id}",
                'sk': f"priority#{priority_score.meeting_id}#{int(datetime.utcnow().timestamp())}",
                'meeting_id': priority_score.meeting_id,
                'priority_score': priority_score.priority_score,
                'priority_factors': priority_score.priority_factors,
                'vip_attendees': priority_score.vip_attendees,
                'meeting_type': priority_score.meeting_type,
                'urgency_level': priority_score.urgency_level,
                'confidence_score': priority_score.confidence_score,
                'reasoning': priority_score.reasoning,
                'timestamp': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            self.priority_table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store priority score: {str(e)}")
            return False
    
    def learn_from_feedback(self, user_id: str, meeting_id: str, 
                          user_feedback: str, correct_priority: float) -> bool:
        """
        Implement learning mechanism for priority adjustment based on user feedback.
        
        Args:
            user_id: User identifier
            meeting_id: Meeting that received feedback
            user_feedback: User's textual feedback
            correct_priority: User's corrected priority score
            
        Returns:
            True if learning was successful
        """
        logger.info(f"Learning from feedback for user {user_id}, meeting {meeting_id}")
        
        try:
            # Retrieve the original priority calculation
            original_score = self._get_stored_priority_score(user_id, meeting_id)
            if not original_score:
                logger.warning(f"No original score found for meeting {meeting_id}")
                return False
            
            # Calculate the error and identify which factors were most wrong
            priority_error = abs(correct_priority - original_score['priority_score'])
            
            if priority_error < 0.1:  # Small error, no learning needed
                return True
            
            # Analyze which factors contributed most to the error
            factor_adjustments = self._analyze_feedback_for_learning(
                user_feedback, original_score, correct_priority
            )
            
            # Update personalized weights
            current_weights = self._get_personalized_weights(user_id)
            updated_weights = self._adjust_weights(current_weights, factor_adjustments)
            
            # Store updated weights
            self._store_learned_weights(user_id, updated_weights, user_feedback)
            
            logger.info(f"Updated priority weights for user {user_id} based on feedback")
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn from feedback: {str(e)}")
            return False
    
    def _get_stored_priority_score(self, user_id: str, meeting_id: str) -> Optional[Dict]:
        """Retrieve stored priority score for a meeting."""
        try:
            # Query for the most recent priority score for this meeting
            response = self.priority_table.query(
                KeyConditionExpression='pk = :pk AND begins_with(sk, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"user#{user_id}",
                    ':sk_prefix': f"priority#{meeting_id}#"
                },
                ScanIndexForward=False,  # Most recent first
                Limit=1
            )
            
            if response['Items']:
                return response['Items'][0]
            
        except Exception as e:
            logger.error(f"Failed to retrieve stored priority score: {str(e)}")
        
        return None
    
    def _analyze_feedback_for_learning(self, feedback: str, original_score: Dict,
                                     correct_priority: float) -> Dict[str, float]:
        """
        Analyze user feedback to determine which factors need adjustment.
        
        Args:
            feedback: User's textual feedback
            original_score: Original priority calculation
            correct_priority: User's corrected priority
            
        Returns:
            Dictionary of factor adjustments
        """
        adjustments = {}
        feedback_lower = feedback.lower()
        
        # Analyze feedback for specific factor mentions
        if any(word in feedback_lower for word in ['vip', 'important person', 'boss', 'executive']):
            if correct_priority > original_score['priority_score']:
                adjustments['vip_contacts'] = 0.1  # Increase VIP weight
            else:
                adjustments['vip_contacts'] = -0.05  # Decrease VIP weight
        
        if any(word in feedback_lower for word in ['meeting type', 'kind of meeting', 'type']):
            if correct_priority > original_score['priority_score']:
                adjustments['meeting_type'] = 0.1
            else:
                adjustments['meeting_type'] = -0.05
        
        if any(word in feedback_lower for word in ['subject', 'title', 'topic', 'urgent', 'important']):
            if correct_priority > original_score['priority_score']:
                adjustments['subject_analysis'] = 0.1
            else:
                adjustments['subject_analysis'] = -0.05
        
        if any(word in feedback_lower for word in ['attendees', 'people', 'participants']):
            if correct_priority > original_score['priority_score']:
                adjustments['attendee_importance'] = 0.1
            else:
                adjustments['attendee_importance'] = -0.05
        
        if any(word in feedback_lower for word in ['time', 'urgent', 'soon', 'deadline']):
            if correct_priority > original_score['priority_score']:
                adjustments['urgency'] = 0.1
            else:
                adjustments['urgency'] = -0.05
        
        return adjustments
    
    def _adjust_weights(self, current_weights: Dict[str, float], 
                       adjustments: Dict[str, float]) -> Dict[str, float]:
        """
        Apply adjustments to current weights while maintaining normalization.
        
        Args:
            current_weights: Current weight values
            adjustments: Proposed adjustments
            
        Returns:
            Updated and normalized weights
        """
        updated_weights = current_weights.copy()
        
        # Apply adjustments
        for factor, adjustment in adjustments.items():
            if factor in updated_weights:
                updated_weights[factor] = max(0.05, min(0.6, 
                    updated_weights[factor] + adjustment))
        
        # Normalize weights to sum to 1.0
        total_weight = sum(updated_weights.values())
        if total_weight > 0:
            for factor in updated_weights:
                updated_weights[factor] /= total_weight
        
        return updated_weights
    
    def _store_learned_weights(self, user_id: str, weights: Dict[str, float], 
                             feedback_context: str) -> bool:
        """Store learned weights in DynamoDB."""
        try:
            item = {
                'pk': f"user#{user_id}",
                'sk': 'priority_weights',
                'weights': weights,
                'last_updated': datetime.utcnow().isoformat(),
                'feedback_context': feedback_context,
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
            }
            
            self.learning_table.put_item(Item=item)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store learned weights: {str(e)}")
            return False
    
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
                        "enum": ["prioritize_meeting", "learn_from_feedback"],
                        "description": "Action to perform"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "meeting_data": {
                        "type": "object",
                        "description": "Meeting data for prioritization"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "User feedback for learning"
                    },
                    "correct_priority": {
                        "type": "number",
                        "description": "User's corrected priority score (0.0-1.0)"
                    },
                    "meeting_id": {
                        "type": "string",
                        "description": "Meeting identifier for feedback"
                    }
                },
                "required": ["action", "user_id"]
            }
        }