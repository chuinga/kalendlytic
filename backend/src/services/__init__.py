"""
Service layer for business logic and external integrations.
"""

from .google_oauth import GoogleOAuthService
from .microsoft_oauth import MicrosoftOAuthService
from .google_calendar import GoogleCalendarService
from .microsoft_calendar import MicrosoftCalendarService
from .oauth_manager import UnifiedOAuthManager
from .availability_aggregation import AvailabilityAggregationService

__all__ = [
    'GoogleOAuthService',
    'MicrosoftOAuthService',
    'GoogleCalendarService',
    'MicrosoftCalendarService',
    'UnifiedOAuthManager',
    'AvailabilityAggregationService'
]