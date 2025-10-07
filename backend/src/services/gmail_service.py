"""
Gmail service for sending emails via Gmail API.
Provides email sending functionality with thread management and draft support.
"""

import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from .google_oauth import GoogleOAuthService
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class GmailService:
    """Service for Gmail email operations via Gmail API."""
    
    def __init__(self):
        """Initialize Gmail service."""
        self.oauth_service = GoogleOAuthService()
    
    def send_email(self, user_id: str, to_addresses: List[str], subject: str, 
                   body: str, thread_id: Optional[str] = None, 
                   priority: str = "normal") -> Dict[str, Any]:
        """
        Send email via Gmail API.
        
        Args:
            user_id: User identifier
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body content
            thread_id: Optional thread ID for conversation continuity
            priority: Email priority (normal, high, low)
            
        Returns:
            Dictionary containing email sending results
        """
        try:
            # Get valid credentials
            credentials = self.oauth_service.get_valid_credentials(user_id)
            access_token = credentials.token
            
            # Create email message
            message = self._create_email_message(
                to_addresses, subject, body, thread_id, priority
            )
            
            # Send via Gmail API
            result = self._send_via_api(access_token, message, thread_id)
            
            logger.info(f"Successfully sent email via Gmail for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Gmail email: {str(e)}")
            raise Exception(f"Gmail sending failed: {str(e)}")
    
    def create_draft(self, user_id: str, to_addresses: List[str], subject: str,
                     body: str, thread_id: Optional[str] = None,
                     priority: str = "normal") -> Dict[str, Any]:
        """
        Create email draft via Gmail API.
        
        Args:
            user_id: User identifier
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body content
            thread_id: Optional thread ID for conversation continuity
            priority: Email priority (normal, high, low)
            
        Returns:
            Dictionary containing draft creation results
        """
        try:
            # Get valid credentials
            credentials = self.oauth_service.get_valid_credentials(user_id)
            access_token = credentials.token
            
            # Create email message
            message = self._create_email_message(
                to_addresses, subject, body, thread_id, priority
            )
            
            # Create draft via Gmail API
            result = self._create_draft_via_api(access_token, message, thread_id)
            
            logger.info(f"Successfully created Gmail draft for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Gmail draft: {str(e)}")
            raise Exception(f"Gmail draft creation failed: {str(e)}")
    
    def _create_email_message(self, to_addresses: List[str], subject: str, body: str,
                             thread_id: Optional[str] = None, priority: str = "normal") -> MIMEMultipart:
        """Create email message object."""
        message = MIMEMultipart()
        message['to'] = ', '.join(to_addresses)
        message['subject'] = subject
        
        # Add thread ID if provided for conversation continuity
        if thread_id:
            message['In-Reply-To'] = thread_id
            message['References'] = thread_id
        
        # Set priority if specified
        if priority == "high":
            message['X-Priority'] = '1'
            message['Importance'] = 'high'
        elif priority == "low":
            message['X-Priority'] = '5'
            message['Importance'] = 'low'
        
        # Add body
        body_part = MIMEText(body, 'plain')
        message.attach(body_part)
        
        return message
    
    def _send_via_api(self, access_token: str, message: MIMEMultipart,
                      thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Send email via Gmail API."""
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Prepare API request
        gmail_api_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'raw': raw_message
        }
        
        # Add thread ID to payload if provided
        if thread_id:
            payload['threadId'] = thread_id
        
        # Send request
        response = requests.post(gmail_api_url, json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Gmail API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        return {
            "email_id": result.get('id'),
            "thread_id": result.get('threadId'),
            "provider": "gmail",
            "sent": True
        }
    
    def _create_draft_via_api(self, access_token: str, message: MIMEMultipart,
                             thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Create draft via Gmail API."""
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Prepare API request
        gmail_api_url = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'message': {
                'raw': raw_message
            }
        }
        
        # Add thread ID to payload if provided
        if thread_id:
            payload['message']['threadId'] = thread_id
        
        # Send request
        response = requests.post(gmail_api_url, json=payload, headers=headers)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Gmail API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        return {
            "email_id": result.get('id'),
            "thread_id": result.get('message', {}).get('threadId'),
            "provider": "gmail",
            "sent": False
        }