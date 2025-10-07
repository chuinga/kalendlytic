"""
Service layer for business logic and external integrations.
"""

from .google_oauth import GoogleOAuthService
from .microsoft_oauth import MicrosoftOAuthService
from .google_calendar import GoogleCalendarService
from .microsoft_calendar import MicrosoftCalendarService
from .oauth_manager import UnifiedOAuthManager
from .availability_aggregation import AvailabilityAggregationService
from .bedrock_client import BedrockClient, BedrockResponse, TokenUsage, BedrockClientError
from .scheduling_agent import SchedulingAgent, SchedulingAgentError
from .scheduling_prompts import SchedulingPrompts

__all__ = [
    'GoogleOAuthService',
    'MicrosoftOAuthService',
    'GoogleCalendarService',
    'MicrosoftCalendarService',
    'UnifiedOAuthManager',
    'AvailabilityAggregationService',
    'BedrockClient',
    'BedrockResponse',
    'TokenUsage',
    'BedrockClientError',
    'SchedulingAgent',
    'SchedulingAgentError',
    'SchedulingPrompts'
]