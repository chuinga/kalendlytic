"""
Email Communication Tool for intelligent meeting notifications and confirmations.
Provides send_email function for Gmail and Outlook integration with template support,
thread management, and auto-send vs draft-only modes based on user preferences.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..services.gmail_service import GmailService
from ..services.outlook_service import OutlookService
from ..models.meeting import Meeting
from ..models.preferences import Preferences
from ..models.connection import Connection
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class EmailType(Enum):
    """Types of meeting-related emails."""
    CONFIRMATION = "confirmation"
    RESCHEDULE = "reschedule"
    CANCELLATION = "cancellation"
    REMINDER = "reminder"
    CONFLICT_NOTIFICATION = "conflict_notification"


class EmailProvider(Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    AUTO = "auto"  # Choose based on available connections


@dataclass
class EmailRequest:
    """Request parameters for email operations."""
    user_id: str
    email_type: EmailType
    recipients: List[str]
    subject: str = ""
    body: str = ""
    meeting_data: Dict[str, Any] = None
    thread_id: Optional[str] = None
    provider: EmailProvider = EmailProvider.AUTO
    auto_send: bool = True
    template_data: Dict[str, Any] = None
    priority: str = "normal"  # normal, high, low


@dataclass
class EmailResponse:
    """Response containing email operation results."""
    success: bool
    email_id: str = None
    thread_id: str = None
    provider_used: str = None
    is_draft: bool = False
    recipients_sent: List[str] = None
    error_message: str = None
    execution_time_ms: int = 0


class EmailCommunicationTool:
    """
    Intelligent email communication tool with template support and thread management.
    Handles meeting confirmations, updates, and notifications across Gmail and Outlook.
    """
    
    def __init__(self):
        """Initialize the email communication tool."""
        self.gmail_service = GmailService()
        self.outlook_service = OutlookService()
        self.tool_name = "send_email"
        self.tool_description = "Send meeting-related emails with template support and thread management"
    
    def send_email(self, request: EmailRequest, 
                   connections: List[Connection],
                   preferences: Optional[Preferences] = None) -> EmailResponse:
        """
        Send meeting-related email with template support and thread management.
        
        Args:
            request: Email request parameters
            connections: Active email connections
            preferences: User preferences for email settings
            
        Returns:
            Email sending response with metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Sending {request.email_type.value} email for user {request.user_id}")
            
            # Step 1: Validate email request
            validation_result = self._validate_email_request(request)
            if not validation_result["valid"]:
                return EmailResponse(
                    success=False,
                    error_message=validation_result["error"],
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 2: Determine email provider
            provider = self._determine_email_provider(request.provider, connections)
            if not provider:
                return EmailResponse(
                    success=False,
                    error_message="No active email connections available",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Step 3: Generate email content from template
            email_content = self._generate_email_content(request, preferences)
            
            # Step 4: Check auto-send preference
            should_auto_send = self._should_auto_send(request, preferences)
            
            # Step 5: Send or draft email based on provider
            if provider == "gmail":
                result = self._send_gmail_email(
                    request, email_content, should_auto_send, connections
                )
            elif provider == "outlook":
                result = self._send_outlook_email(
                    request, email_content, should_auto_send, connections
                )
            else:
                return EmailResponse(
                    success=False,
                    error_message=f"Unsupported email provider: {provider}",
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            logger.info(f"Successfully {'sent' if should_auto_send else 'drafted'} email via {provider}")
            
            return EmailResponse(
                success=True,
                email_id=result.get("email_id"),
                thread_id=result.get("thread_id"),
                provider_used=provider,
                is_draft=not should_auto_send,
                recipients_sent=request.recipients if should_auto_send else [],
                execution_time_ms=self._calculate_execution_time(start_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to send email for user {request.user_id}: {str(e)}")
            return EmailResponse(
                success=False,
                error_message=f"Email sending failed: {str(e)}",
                execution_time_ms=self._calculate_execution_time(start_time)
            )    

    def _validate_email_request(self, request: EmailRequest) -> Dict[str, Any]:
        """Validate email request parameters."""
        try:
            # Check required fields
            if not request.recipients:
                return {"valid": False, "error": "Recipients list is required"}
            
            # Validate email addresses
            for recipient in request.recipients:
                if not self._is_valid_email(recipient):
                    return {"valid": False, "error": f"Invalid email address: {recipient}"}
            
            # Check email type
            if not isinstance(request.email_type, EmailType):
                return {"valid": False, "error": "Invalid email type"}
            
            # Validate meeting data for meeting-related emails
            if request.email_type in [EmailType.CONFIRMATION, EmailType.RESCHEDULE, EmailType.CANCELLATION]:
                if not request.meeting_data:
                    return {"valid": False, "error": "Meeting data is required for meeting-related emails"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _determine_email_provider(self, requested_provider: EmailProvider, 
                                 connections: List[Connection]) -> Optional[str]:
        """Determine which email provider to use."""
        active_connections = [conn for conn in connections if conn.is_active]
        
        if requested_provider == EmailProvider.GMAIL:
            gmail_conn = next((conn for conn in active_connections if conn.provider == "google"), None)
            return "gmail" if gmail_conn else None
        
        elif requested_provider == EmailProvider.OUTLOOK:
            outlook_conn = next((conn for conn in active_connections if conn.provider == "microsoft"), None)
            return "outlook" if outlook_conn else None
        
        elif requested_provider == EmailProvider.AUTO:
            # Prefer Gmail, fallback to Outlook
            gmail_conn = next((conn for conn in active_connections if conn.provider == "google"), None)
            if gmail_conn:
                return "gmail"
            
            outlook_conn = next((conn for conn in active_connections if conn.provider == "microsoft"), None)
            if outlook_conn:
                return "outlook"
        
        return None    

    def _generate_email_content(self, request: EmailRequest, 
                               preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate email content using templates."""
        template_data = request.template_data or {}
        meeting_data = request.meeting_data or {}
        
        # Use custom content if provided, otherwise generate from template
        if request.subject and request.body:
            return {
                "subject": request.subject,
                "body": request.body
            }
        
        # Generate content based on email type
        if request.email_type == EmailType.CONFIRMATION:
            return self._generate_confirmation_email(meeting_data, template_data, preferences)
        elif request.email_type == EmailType.RESCHEDULE:
            return self._generate_reschedule_email(meeting_data, template_data, preferences)
        elif request.email_type == EmailType.CANCELLATION:
            return self._generate_cancellation_email(meeting_data, template_data, preferences)
        elif request.email_type == EmailType.REMINDER:
            return self._generate_reminder_email(meeting_data, template_data, preferences)
        elif request.email_type == EmailType.CONFLICT_NOTIFICATION:
            return self._generate_conflict_notification_email(meeting_data, template_data, preferences)
        else:
            return {
                "subject": "Meeting Update",
                "body": "This is an automated message regarding your meeting."
            }
    
    def _generate_confirmation_email(self, meeting_data: Dict[str, Any], 
                                   template_data: Dict[str, Any],
                                   preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate meeting confirmation email content."""
        title = meeting_data.get("title", "Meeting")
        start_time = meeting_data.get("start", "")
        end_time = meeting_data.get("end", "")
        location = meeting_data.get("location", "")
        conference_url = meeting_data.get("conference_url", "")
        organizer_name = template_data.get("organizer_name", "Meeting Organizer")
        
        # Format datetime if provided
        if isinstance(start_time, datetime):
            start_formatted = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
        else:
            start_formatted = str(start_time)
        
        if isinstance(end_time, datetime):
            end_formatted = end_time.strftime("%I:%M %p")
        else:
            end_formatted = str(end_time)
        
        subject = f"Meeting Confirmed: {title}"
        
        body = f"""Hello,

Your meeting has been confirmed:

📅 **{title}**
🕐 {start_formatted} - {end_formatted}"""
        
        if location:
            body += f"\n📍 Location: {location}"
        
        if conference_url:
            body += f"\n💻 Join online: {conference_url}"
        
        body += f"""

This meeting was scheduled automatically by your AI scheduling assistant.

If you need to make any changes, please reply to this email or contact {organizer_name}.

Best regards,
Your AI Scheduling Assistant"""
        
        return {"subject": subject, "body": body} 
   
    def _generate_reschedule_email(self, meeting_data: Dict[str, Any], 
                                 template_data: Dict[str, Any],
                                 preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate meeting reschedule email content."""
        title = meeting_data.get("title", "Meeting")
        old_start = meeting_data.get("old_start", "")
        old_end = meeting_data.get("old_end", "")
        new_start = meeting_data.get("start", "")
        new_end = meeting_data.get("end", "")
        reason = template_data.get("reschedule_reason", "scheduling conflict")
        organizer_name = template_data.get("organizer_name", "Meeting Organizer")
        
        # Format datetime
        if isinstance(old_start, datetime):
            old_start_formatted = old_start.strftime("%A, %B %d, %Y at %I:%M %p")
        else:
            old_start_formatted = str(old_start)
        
        if isinstance(new_start, datetime):
            new_start_formatted = new_start.strftime("%A, %B %d, %Y at %I:%M %p")
            new_end_formatted = new_end.strftime("%I:%M %p") if isinstance(new_end, datetime) else str(new_end)
        else:
            new_start_formatted = str(new_start)
            new_end_formatted = str(new_end)
        
        subject = f"Meeting Rescheduled: {title}"
        
        body = f"""Hello,

Your meeting has been rescheduled due to {reason}:

📅 **{title}**

❌ **Previous Time:** {old_start_formatted}
✅ **New Time:** {new_start_formatted} - {new_end_formatted}

Please update your calendar accordingly. This change was made automatically by your AI scheduling assistant to resolve conflicts.

If you have any concerns about this change, please reply to this email or contact {organizer_name}.

Best regards,
Your AI Scheduling Assistant"""
        
        return {"subject": subject, "body": body}
    
    def _generate_cancellation_email(self, meeting_data: Dict[str, Any], 
                                    template_data: Dict[str, Any],
                                    preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate meeting cancellation email content."""
        title = meeting_data.get("title", "Meeting")
        start_time = meeting_data.get("start", "")
        reason = template_data.get("cancellation_reason", "scheduling conflict")
        organizer_name = template_data.get("organizer_name", "Meeting Organizer")
        
        # Format datetime
        if isinstance(start_time, datetime):
            start_formatted = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
        else:
            start_formatted = str(start_time)
        
        subject = f"Meeting Cancelled: {title}"
        
        body = f"""Hello,

Unfortunately, the following meeting has been cancelled:

📅 **{title}**
🕐 Originally scheduled for: {start_formatted}
❌ **Reason:** {reason}

This cancellation was processed automatically by your AI scheduling assistant.

We apologize for any inconvenience. If you need to reschedule this meeting, please reply to this email or contact {organizer_name}.

Best regards,
Your AI Scheduling Assistant"""
        
        return {"subject": subject, "body": body}    

    def _generate_reminder_email(self, meeting_data: Dict[str, Any], 
                               template_data: Dict[str, Any],
                               preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate meeting reminder email content."""
        title = meeting_data.get("title", "Meeting")
        start_time = meeting_data.get("start", "")
        location = meeting_data.get("location", "")
        conference_url = meeting_data.get("conference_url", "")
        
        # Format datetime
        if isinstance(start_time, datetime):
            start_formatted = start_time.strftime("%A, %B %d, %Y at %I:%M %p")
            time_until = start_time - datetime.utcnow()
            if time_until.days > 0:
                time_desc = f"in {time_until.days} day(s)"
            elif time_until.seconds > 3600:
                hours = time_until.seconds // 3600
                time_desc = f"in {hours} hour(s)"
            else:
                minutes = time_until.seconds // 60
                time_desc = f"in {minutes} minute(s)"
        else:
            start_formatted = str(start_time)
            time_desc = "soon"
        
        subject = f"Reminder: {title} {time_desc}"
        
        body = f"""Hello,

This is a reminder about your upcoming meeting:

📅 **{title}**
🕐 {start_formatted}"""
        
        if location:
            body += f"\n📍 Location: {location}"
        
        if conference_url:
            body += f"\n💻 Join online: {conference_url}"
        
        body += f"""

Please make sure you're prepared and available for this meeting.

Best regards,
Your AI Scheduling Assistant"""
        
        return {"subject": subject, "body": body}
    
    def _generate_conflict_notification_email(self, meeting_data: Dict[str, Any], 
                                            template_data: Dict[str, Any],
                                            preferences: Optional[Preferences]) -> Dict[str, str]:
        """Generate conflict notification email content."""
        title = meeting_data.get("title", "Meeting")
        conflicts = template_data.get("conflicts", [])
        alternatives = template_data.get("alternatives", [])
        organizer_name = template_data.get("organizer_name", "Meeting Organizer")
        
        subject = f"Scheduling Conflict Detected: {title}"
        
        body = f"""Hello,

A scheduling conflict has been detected for the following meeting:

📅 **{title}**

**Conflicts detected:**"""
        
        for i, conflict in enumerate(conflicts[:3], 1):  # Show up to 3 conflicts
            conflict_time = conflict.get("start", "")
            if isinstance(conflict_time, datetime):
                conflict_formatted = conflict_time.strftime("%A, %B %d, %Y at %I:%M %p")
            else:
                conflict_formatted = str(conflict_time)
            body += f"\n{i}. {conflict_formatted}"
        
        if alternatives:
            body += f"\n\n**Suggested alternative times:**"
            for i, alt in enumerate(alternatives[:3], 1):  # Show up to 3 alternatives
                alt_start = alt.get("start", "")
                alt_end = alt.get("end", "")
                if isinstance(alt_start, datetime):
                    alt_formatted = alt_start.strftime("%A, %B %d, %Y at %I:%M %p")
                    if isinstance(alt_end, datetime):
                        alt_formatted += f" - {alt_end.strftime('%I:%M %p')}"
                else:
                    alt_formatted = f"{alt_start} - {alt_end}"
                body += f"\n{i}. {alt_formatted}"
        
        body += f"""

Please review these conflicts and let us know your preferred alternative time by replying to this email or contacting {organizer_name}.

Best regards,
Your AI Scheduling Assistant"""
        
        return {"subject": subject, "body": body}    

    def _should_auto_send(self, request: EmailRequest, 
                         preferences: Optional[Preferences]) -> bool:
        """Determine if email should be auto-sent or saved as draft."""
        # Check request-level preference first
        if not request.auto_send:
            return False
        
        # Check user preferences
        if preferences:
            # Check global auto-send preference
            if hasattr(preferences, 'auto_send_emails') and not preferences.auto_send_emails:
                return False
            
            # Check email type specific preferences
            if hasattr(preferences, 'email_preferences'):
                email_prefs = preferences.email_preferences
                if request.email_type.value in email_prefs:
                    type_prefs = email_prefs[request.email_type.value]
                    if 'auto_send' in type_prefs:
                        return type_prefs['auto_send']
        
        # Default to auto-send for confirmations and reminders, draft for others
        auto_send_types = [EmailType.CONFIRMATION, EmailType.REMINDER]
        return request.email_type in auto_send_types
    
    def _send_gmail_email(self, request: EmailRequest, email_content: Dict[str, str],
                         auto_send: bool, connections: List[Connection]) -> Dict[str, Any]:
        """Send email via Gmail service."""
        try:
            if auto_send:
                result = self.gmail_service.send_email(
                    user_id=request.user_id,
                    to_addresses=request.recipients,
                    subject=email_content['subject'],
                    body=email_content['body'],
                    thread_id=request.thread_id,
                    priority=request.priority
                )
            else:
                result = self.gmail_service.create_draft(
                    user_id=request.user_id,
                    to_addresses=request.recipients,
                    subject=email_content['subject'],
                    body=email_content['body'],
                    thread_id=request.thread_id,
                    priority=request.priority
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Gmail email: {str(e)}")
            raise Exception(f"Gmail sending failed: {str(e)}")
    
    def _send_outlook_email(self, request: EmailRequest, email_content: Dict[str, str],
                           auto_send: bool, connections: List[Connection]) -> Dict[str, Any]:
        """Send email via Outlook service."""
        try:
            if auto_send:
                result = self.outlook_service.send_email(
                    user_id=request.user_id,
                    to_addresses=request.recipients,
                    subject=email_content['subject'],
                    body=email_content['body'],
                    thread_id=request.thread_id,
                    priority=request.priority
                )
            else:
                result = self.outlook_service.create_draft(
                    user_id=request.user_id,
                    to_addresses=request.recipients,
                    subject=email_content['subject'],
                    body=email_content['body'],
                    thread_id=request.thread_id,
                    priority=request.priority
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Outlook email: {str(e)}")
            raise Exception(f"Outlook sending failed: {str(e)}")
    
    def _calculate_execution_time(self, start_time: datetime) -> int:
        """Calculate execution time in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)   
 
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get the tool schema for agent integration."""
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier for email sending"
                    },
                    "email_type": {
                        "type": "string",
                        "enum": ["confirmation", "reschedule", "cancellation", "reminder", "conflict_notification"],
                        "description": "Type of meeting-related email to send"
                    },
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipient email addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (optional, will be generated from template if not provided)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (optional, will be generated from template if not provided)"
                    },
                    "meeting_data": {
                        "type": "object",
                        "description": "Meeting information for template generation",
                        "properties": {
                            "title": {"type": "string"},
                            "start": {"type": "string", "format": "date-time"},
                            "end": {"type": "string", "format": "date-time"},
                            "location": {"type": "string"},
                            "conference_url": {"type": "string"}
                        }
                    },
                    "thread_id": {
                        "type": "string",
                        "description": "Email thread ID for conversation continuity (optional)"
                    },
                    "provider": {
                        "type": "string",
                        "enum": ["gmail", "outlook", "auto"],
                        "description": "Email provider to use (auto selects best available)"
                    },
                    "auto_send": {
                        "type": "boolean",
                        "description": "Whether to send immediately or save as draft"
                    },
                    "template_data": {
                        "type": "object",
                        "description": "Additional data for email template generation",
                        "properties": {
                            "organizer_name": {"type": "string"},
                            "reschedule_reason": {"type": "string"},
                            "cancellation_reason": {"type": "string"},
                            "conflicts": {"type": "array"},
                            "alternatives": {"type": "array"}
                        }
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["normal", "high", "low"],
                        "description": "Email priority level"
                    }
                },
                "required": ["user_id", "email_type", "recipients"]
            }
        }


# Convenience functions for common email operations
def send_meeting_confirmation(user_id: str, recipients: List[str], meeting_data: Dict[str, Any],
                            connections: List[Connection], preferences: Optional[Preferences] = None,
                            organizer_name: str = "Meeting Organizer") -> EmailResponse:
    """Send meeting confirmation email."""
    tool = EmailCommunicationTool()
    request = EmailRequest(
        user_id=user_id,
        email_type=EmailType.CONFIRMATION,
        recipients=recipients,
        meeting_data=meeting_data,
        template_data={"organizer_name": organizer_name}
    )
    return tool.send_email(request, connections, preferences)


def send_meeting_reschedule(user_id: str, recipients: List[str], meeting_data: Dict[str, Any],
                          connections: List[Connection], preferences: Optional[Preferences] = None,
                          reschedule_reason: str = "scheduling conflict",
                          organizer_name: str = "Meeting Organizer") -> EmailResponse:
    """Send meeting reschedule notification email."""
    tool = EmailCommunicationTool()
    request = EmailRequest(
        user_id=user_id,
        email_type=EmailType.RESCHEDULE,
        recipients=recipients,
        meeting_data=meeting_data,
        template_data={
            "reschedule_reason": reschedule_reason,
            "organizer_name": organizer_name
        }
    )
    return tool.send_email(request, connections, preferences)


def send_meeting_cancellation(user_id: str, recipients: List[str], meeting_data: Dict[str, Any],
                            connections: List[Connection], preferences: Optional[Preferences] = None,
                            cancellation_reason: str = "scheduling conflict",
                            organizer_name: str = "Meeting Organizer") -> EmailResponse:
    """Send meeting cancellation notification email."""
    tool = EmailCommunicationTool()
    request = EmailRequest(
        user_id=user_id,
        email_type=EmailType.CANCELLATION,
        recipients=recipients,
        meeting_data=meeting_data,
        template_data={
            "cancellation_reason": cancellation_reason,
            "organizer_name": organizer_name
        }
    )
    return tool.send_email(request, connections, preferences)


def send_conflict_notification(user_id: str, recipients: List[str], meeting_data: Dict[str, Any],
                             conflicts: List[Dict[str, Any]], alternatives: List[Dict[str, Any]],
                             connections: List[Connection], preferences: Optional[Preferences] = None,
                             organizer_name: str = "Meeting Organizer") -> EmailResponse:
    """Send scheduling conflict notification email."""
    tool = EmailCommunicationTool()
    request = EmailRequest(
        user_id=user_id,
        email_type=EmailType.CONFLICT_NOTIFICATION,
        recipients=recipients,
        meeting_data=meeting_data,
        template_data={
            "conflicts": conflicts,
            "alternatives": alternatives,
            "organizer_name": organizer_name
        }
    )
    return tool.send_email(request, connections, preferences)