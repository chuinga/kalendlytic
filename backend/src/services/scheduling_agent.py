"""
AI-powered scheduling agent that uses Bedrock Claude for intelligent meeting scheduling.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from .bedrock_client import BedrockClient, BedrockResponse, BedrockClientError
from .scheduling_prompts import SchedulingPrompts
from .audit_service import AuditService, AgentDecisionType
from ..models.agent import CostEstimate
from ..utils.logging import create_agent_logger, AgentDecisionType as LoggingDecisionType

logger = logging.getLogger(__name__)


class SchedulingAgentError(Exception):
    """Custom exception for scheduling agent errors."""
    pass


class SchedulingAgent:
    """
    AI-powered scheduling agent using Amazon Bedrock Claude Sonnet 4.5.
    Provides intelligent meeting scheduling, conflict resolution, and optimization.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None, user_id: Optional[str] = None):
        """
        Initialize the scheduling agent.
        
        Args:
            bedrock_client: Optional pre-configured Bedrock client
            user_id: User ID for audit logging
        """
        self.bedrock_client = bedrock_client or BedrockClient()
        self.prompts = SchedulingPrompts()
        self.audit_service = AuditService()
        self.user_id = user_id
        self.run_id = str(uuid.uuid4())
        self.audit_logger = create_agent_logger('scheduling_agent', user_id=user_id)
        self.audit_logger.set_agent_run_id(self.run_id)
        
    def resolve_conflicts(
        self,
        meeting_request: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        available_slots: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use AI to resolve scheduling conflicts and provide recommendations.
        
        Args:
            meeting_request: Original meeting request details
            conflicts: List of conflicting meetings
            available_slots: Alternative time slots available
            
        Returns:
            AI-generated conflict resolution recommendations
        """
        start_time = datetime.utcnow()
        
        try:
            prompt = self.prompts.conflict_resolution_prompt(
                meeting_request, conflicts, available_slots
            )
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent reasoning
                max_tokens=2048
            )
            
            # Parse JSON response
            try:
                recommendations = json.loads(response.content)
                
                # Calculate confidence score based on number of alternatives and conflicts
                confidence_score = self._calculate_confidence_score(
                    len(conflicts), len(available_slots), recommendations
                )
                
                # Generate rationale
                rationale = self._generate_conflict_resolution_rationale(
                    conflicts, available_slots, recommendations, confidence_score
                )
                
                # Create cost estimate
                cost_estimate = CostEstimate(
                    bedrock_tokens=response.token_usage.total_tokens,
                    estimated_cost_usd=response.token_usage.estimated_cost_usd
                )
                
                # Log agent decision
                if self.user_id:
                    self.audit_service.log_agent_decision(
                        user_id=self.user_id,
                        run_id=self.run_id,
                        decision_type=LoggingDecisionType.CONFLICT_RESOLUTION,
                        inputs={
                            'meeting_request': meeting_request,
                            'conflicts_count': len(conflicts),
                            'available_slots_count': len(available_slots)
                        },
                        outputs=recommendations,
                        rationale=rationale,
                        confidence_score=confidence_score,
                        alternatives_considered=self._extract_alternatives(recommendations),
                        cost_estimate=cost_estimate,
                        requires_approval=confidence_score < 0.7
                    )
                
                # Add metadata
                recommendations['_metadata'] = {
                    'model_id': response.model_id,
                    'timestamp': response.timestamp.isoformat(),
                    'token_usage': {
                        'input_tokens': response.token_usage.input_tokens,
                        'output_tokens': response.token_usage.output_tokens,
                        'total_tokens': response.token_usage.total_tokens,
                        'estimated_cost_usd': response.token_usage.estimated_cost_usd
                    },
                    'confidence_score': confidence_score,
                    'requires_approval': confidence_score < 0.7
                }
                
                logger.info(f"Conflict resolution completed: {len(conflicts)} conflicts analyzed")
                return recommendations
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise SchedulingAgentError(f"Invalid AI response format: {e}")
                
        except BedrockClientError as e:
            logger.error(f"Bedrock client error in conflict resolution: {e}")
            raise SchedulingAgentError(f"AI service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in conflict resolution: {e}")
            raise SchedulingAgentError(f"Conflict resolution failed: {e}")
    
    def find_optimal_time(
        self,
        meeting_request: Dict[str, Any],
        attendee_availability: Dict[str, List[Dict[str, Any]]],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to find optimal meeting times based on availability and preferences.
        
        Args:
            meeting_request: Meeting request details
            attendee_availability: Availability data for each attendee
            preferences: Scheduling preferences and constraints
            
        Returns:
            AI-generated optimal scheduling recommendations
        """
        start_time = datetime.utcnow()
        
        try:
            prompt = self.prompts.optimal_scheduling_prompt(
                meeting_request, attendee_availability, preferences
            )
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                temperature=0.2,  # Slightly higher for creative scheduling
                max_tokens=2048
            )
            
            try:
                recommendations = json.loads(response.content)
                
                # Calculate confidence score
                attendee_count = len(attendee_availability)
                confidence_score = self._calculate_confidence_score(
                    0, len(recommendations.get('alternative_times', [])), recommendations
                )
                
                # Adjust confidence based on attendee complexity
                if attendee_count > 5:
                    confidence_score -= 0.1
                elif attendee_count > 10:
                    confidence_score -= 0.2
                
                # Generate rationale
                rationale = self._generate_scheduling_rationale(
                    attendee_count, preferences, recommendations, confidence_score
                )
                
                # Create cost estimate
                cost_estimate = CostEstimate(
                    bedrock_tokens=response.token_usage.total_tokens,
                    estimated_cost_usd=response.token_usage.estimated_cost_usd
                )
                
                # Log agent decision
                if self.user_id:
                    self.audit_service.log_agent_decision(
                        user_id=self.user_id,
                        run_id=self.run_id,
                        decision_type=LoggingDecisionType.SCHEDULING,
                        inputs={
                            'meeting_request': meeting_request,
                            'attendee_count': attendee_count,
                            'preferences': preferences
                        },
                        outputs=recommendations,
                        rationale=rationale,
                        confidence_score=confidence_score,
                        alternatives_considered=self._extract_alternatives(recommendations),
                        cost_estimate=cost_estimate,
                        requires_approval=confidence_score < 0.6 or attendee_count > 8
                    )
                
                # Add metadata
                recommendations['_metadata'] = {
                    'model_id': response.model_id,
                    'timestamp': response.timestamp.isoformat(),
                    'token_usage': {
                        'input_tokens': response.token_usage.input_tokens,
                        'output_tokens': response.token_usage.output_tokens,
                        'total_tokens': response.token_usage.total_tokens,
                        'estimated_cost_usd': response.token_usage.estimated_cost_usd
                    },
                    'confidence_score': confidence_score,
                    'requires_approval': confidence_score < 0.6 or attendee_count > 8
                }
                
                logger.info(f"Optimal scheduling completed for {len(attendee_availability)} attendees")
                return recommendations
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise SchedulingAgentError(f"Invalid AI response format: {e}")
                
        except BedrockClientError as e:
            logger.error(f"Bedrock client error in optimal scheduling: {e}")
            raise SchedulingAgentError(f"AI service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in optimal scheduling: {e}")
            raise SchedulingAgentError(f"Optimal scheduling failed: {e}")
    
    def prepare_meeting(
        self,
        meeting_details: Dict[str, Any],
        attendee_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use AI to generate meeting preparation recommendations.
        
        Args:
            meeting_details: Details about the upcoming meeting
            attendee_context: Context about attendees and their roles
            
        Returns:
            AI-generated meeting preparation recommendations
        """
        try:
            prompt = self.prompts.meeting_preparation_prompt(
                meeting_details, attendee_context
            )
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                temperature=0.3,  # Higher creativity for preparation ideas
                max_tokens=2048
            )
            
            try:
                recommendations = json.loads(response.content)
                
                # Add metadata
                recommendations['_metadata'] = {
                    'model_id': response.model_id,
                    'timestamp': response.timestamp.isoformat(),
                    'token_usage': {
                        'input_tokens': response.token_usage.input_tokens,
                        'output_tokens': response.token_usage.output_tokens,
                        'total_tokens': response.token_usage.total_tokens,
                        'estimated_cost_usd': response.token_usage.estimated_cost_usd
                    }
                }
                
                logger.info("Meeting preparation recommendations generated")
                return recommendations
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise SchedulingAgentError(f"Invalid AI response format: {e}")
                
        except BedrockClientError as e:
            logger.error(f"Bedrock client error in meeting preparation: {e}")
            raise SchedulingAgentError(f"AI service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in meeting preparation: {e}")
            raise SchedulingAgentError(f"Meeting preparation failed: {e}")
    
    def generate_rescheduling_communication(
        self,
        original_meeting: Dict[str, Any],
        new_meeting_time: str,
        reason: str,
        attendees: List[str]
    ) -> Dict[str, Any]:
        """
        Use AI to generate professional rescheduling communications.
        
        Args:
            original_meeting: Original meeting details
            new_meeting_time: New proposed meeting time
            reason: Reason for rescheduling
            attendees: List of meeting attendees
            
        Returns:
            AI-generated rescheduling communications
        """
        try:
            prompt = self.prompts.rescheduling_communication_prompt(
                original_meeting, new_meeting_time, reason, attendees
            )
            
            response = self.bedrock_client.invoke_model(
                prompt=prompt,
                temperature=0.4,  # Higher creativity for communication
                max_tokens=1536
            )
            
            try:
                communications = json.loads(response.content)
                
                # Add metadata
                communications['_metadata'] = {
                    'model_id': response.model_id,
                    'timestamp': response.timestamp.isoformat(),
                    'token_usage': {
                        'input_tokens': response.token_usage.input_tokens,
                        'output_tokens': response.token_usage.output_tokens,
                        'total_tokens': response.token_usage.total_tokens,
                        'estimated_cost_usd': response.token_usage.estimated_cost_usd
                    }
                }
                
                logger.info("Rescheduling communications generated")
                return communications
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise SchedulingAgentError(f"Invalid AI response format: {e}")
                
        except BedrockClientError as e:
            logger.error(f"Bedrock client error in communication generation: {e}")
            raise SchedulingAgentError(f"AI service error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in communication generation: {e}")
            raise SchedulingAgentError(f"Communication generation failed: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the scheduling agent.
        
        Returns:
            Dictionary containing usage statistics
        """
        # This would typically be implemented with a usage tracking service
        # For now, return basic client information
        return {
            'model_id': self.bedrock_client.MODEL_ID,
            'region': self.bedrock_client.region_name,
            'max_retries': self.bedrock_client.max_retries,
            'pricing': {
                'input_token_cost_per_1k': self.bedrock_client.INPUT_TOKEN_COST_PER_1K,
                'output_token_cost_per_1k': self.bedrock_client.OUTPUT_TOKEN_COST_PER_1K
            }
        }
    
    def _calculate_confidence_score(
        self, 
        conflicts_count: int, 
        available_slots_count: int, 
        recommendations: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for agent decisions.
        
        Args:
            conflicts_count: Number of conflicts to resolve
            available_slots_count: Number of available alternative slots
            recommendations: AI-generated recommendations
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.8
        
        # Reduce confidence based on complexity
        if conflicts_count > 3:
            base_confidence -= 0.2
        elif conflicts_count > 1:
            base_confidence -= 0.1
        
        # Increase confidence if many alternatives available
        if available_slots_count > 5:
            base_confidence += 0.1
        elif available_slots_count < 2:
            base_confidence -= 0.2
        
        # Check if recommendations include uncertainty indicators
        recommendation_text = json.dumps(recommendations).lower()
        uncertainty_keywords = ['might', 'could', 'possibly', 'uncertain', 'difficult']
        
        for keyword in uncertainty_keywords:
            if keyword in recommendation_text:
                base_confidence -= 0.1
                break
        
        return max(0.1, min(1.0, base_confidence))
    
    def _generate_conflict_resolution_rationale(
        self,
        conflicts: List[Dict[str, Any]],
        available_slots: List[Dict[str, Any]],
        recommendations: Dict[str, Any],
        confidence_score: float
    ) -> str:
        """
        Generate natural language rationale for conflict resolution decisions.
        
        Args:
            conflicts: List of conflicting meetings
            available_slots: Available alternative slots
            recommendations: AI recommendations
            confidence_score: Calculated confidence score
            
        Returns:
            Natural language rationale
        """
        rationale_parts = []
        
        # Base decision context
        rationale_parts.append(f"Analyzed {len(conflicts)} scheduling conflicts with {len(available_slots)} alternative time slots available.")
        
        # Confidence context
        if confidence_score > 0.8:
            rationale_parts.append("High confidence in recommendations due to clear alternatives and minimal complexity.")
        elif confidence_score > 0.6:
            rationale_parts.append("Moderate confidence - some complexity in scheduling constraints.")
        else:
            rationale_parts.append("Lower confidence due to complex conflicts or limited alternatives. Manual review recommended.")
        
        # Recommendation summary
        if 'recommended_action' in recommendations:
            action = recommendations['recommended_action']
            rationale_parts.append(f"Recommended action: {action}")
        
        if 'alternative_times' in recommendations:
            alt_count = len(recommendations['alternative_times'])
            rationale_parts.append(f"Identified {alt_count} viable alternative time slots.")
        
        return " ".join(rationale_parts)
    
    def _extract_alternatives(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract alternative options from AI recommendations.
        
        Args:
            recommendations: AI-generated recommendations
            
        Returns:
            List of alternative options with scores
        """
        alternatives = []
        
        if 'alternative_times' in recommendations:
            for i, alt_time in enumerate(recommendations['alternative_times']):
                alternatives.append({
                    'summary': f"Alternative time slot: {alt_time.get('start_time', 'Unknown')}",
                    'score': alt_time.get('preference_score', 0.5),
                    'details': alt_time
                })
        
        if 'rescheduling_options' in recommendations:
            for i, option in enumerate(recommendations['rescheduling_options']):
                alternatives.append({
                    'summary': f"Reschedule option: {option.get('description', 'Unknown')}",
                    'score': option.get('feasibility_score', 0.5),
                    'details': option
                })
        
        return alternatives[:5]  # Limit to top 5 alternatives
    
    def _generate_scheduling_rationale(
        self,
        attendee_count: int,
        preferences: Dict[str, Any],
        recommendations: Dict[str, Any],
        confidence_score: float
    ) -> str:
        """
        Generate natural language rationale for optimal scheduling decisions.
        
        Args:
            attendee_count: Number of attendees
            preferences: Scheduling preferences
            recommendations: AI recommendations
            confidence_score: Calculated confidence score
            
        Returns:
            Natural language rationale
        """
        rationale_parts = []
        
        # Base decision context
        rationale_parts.append(f"Optimized scheduling for {attendee_count} attendees considering preferences and constraints.")
        
        # Preference considerations
        if preferences.get('preferred_times'):
            rationale_parts.append("Factored in preferred meeting times.")
        
        if preferences.get('avoid_times'):
            rationale_parts.append("Avoided specified blackout periods.")
        
        # Confidence context
        if confidence_score > 0.8:
            rationale_parts.append("High confidence - strong alignment with preferences and availability.")
        elif confidence_score > 0.6:
            rationale_parts.append("Good confidence with some minor preference trade-offs.")
        else:
            rationale_parts.append("Lower confidence due to conflicting preferences or limited availability.")
        
        # Recommendation summary
        if 'optimal_time' in recommendations:
            optimal = recommendations['optimal_time']
            rationale_parts.append(f"Selected optimal time: {optimal.get('start_time', 'Unknown')}")
        
        return " ".join(rationale_parts)