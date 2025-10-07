"""
Agent tools for calendar and email operations.
"""

from .availability_tool import AvailabilityTool, AvailabilityRequest, AvailabilityResponse
from .email_communication_tool import (
    EmailCommunicationTool, EmailRequest, EmailResponse, EmailType, EmailProvider,
    send_meeting_confirmation, send_meeting_reschedule, send_meeting_cancellation,
    send_conflict_notification
)

__all__ = [
    'AvailabilityTool', 'AvailabilityRequest', 'AvailabilityResponse',
    'EmailCommunicationTool', 'EmailRequest', 'EmailResponse', 'EmailType', 'EmailProvider',
    'send_meeting_confirmation', 'send_meeting_reschedule', 'send_meeting_cancellation',
    'send_conflict_notification'
]