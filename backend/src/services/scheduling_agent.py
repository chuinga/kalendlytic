"""
AI-powered scheduling agent that uses Bedrock Claude for intelligent meeting scheduling.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .bedrock_client import BedrockClient, BedrockResponse, BedrockClientError
from .scheduling_prompts import SchedulingPrompts

logger = logging.getLogger(__name__)


class SchedulingAgentError(Exception):
    """Custom exception for scheduling agent errors."""
    pass


class SchedulingAgent:
    """
    AI-powered scheduling agent using Amazon Bedrock Claude Sonnet 4.5.
    Provides intelligent meeting scheduling, conflict resolution, and optimization.
    """
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        """
        Initialize the scheduling agent.
        
        Args:
            bedrock_client: Optional pre-configured Bedrock client
        """
        self.bedrock_client = bedrock_client or BedrockClient()
        self.prompts = SchedulingPrompts()
        
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