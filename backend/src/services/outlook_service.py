"""
Outlook service for sending emails via Microsoft Graph API.
Provides email sending functionality with thread management and draft support.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from .microsoft_oauth import MicrosoftOAuthService
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class OutlookService:
    """Service for Outlook email operations via Microsoft Graph API."""
    
    def __init__(self):
        """Initialize Outlook service."""
        self.oauth_service = MicrosoftOAuthService()
    
    def send_email(self, user_id: str, to_addresses: List[str], subject: str,
                   body: str, thread_id: Optional[str] = None,
                   priority: str = "normal") -> Dict[str, Any]:
        """
        Send email via Microsoft Graph API.
        
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
            # Get valid access token
            access_token = self.oauth_service.get_valid_access_token(user_id)
            
            # Create email message
            message = self._create_email_message(
                to_addresses, subject, body, thread_id, priority
            )
            
            # Send via Microsoft Graph API
            result = self._send_via_api(access_token, message)
            
            logger.info(f"Successfully sent email via Outlook for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send Outlook email: {str(e)}")
            raise Exception(f"Outlook sending failed: {str(e)}")
    
    def create_draft(self, user_id: str, to_addresses: List[str], subject: str,
                     body: str, thread_id: Optional[str] = None,
                     priority: str = "normal") -> Dict[str, Any]:
        """
        Create email draft via Microsoft Graph API.
        
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
            # Get valid access token
            access_token = self.oauth_service.get_valid_access_token(user_id)
            
            # Create email message
            message = self._create_email_message(
                to_addresses, subject, body, thread_id, priority
            )
            
            # Create draft via Microsoft Graph API
            result = self._create_draft_via_api(access_token, message)
            
            logger.info(f"Successfully created Outlook draft for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Outlook draft: {str(e)}")
            raise Exception(f"Outlook draft creation failed: {str(e)}")
    
    def _create_email_message(self, to_addresses: List[str], subject: str, body: str,
                             thread_id: Optional[str] = None, priority: str = "normal") -> Dict[str, Any]:
        """Create email message object for Microsoft Graph API."""
        message = {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": address}} 
                for address in to_addresses
            ]
        }
        
        # Set priority if specified
        if priority == "high":
            message["importance"] = "high"
        elif priority == "low":
            message["importance"] = "low"
        
        # Note: Microsoft Graph handles thread continuity differently
        # Thread ID is managed automatically based on subject and recipients
        
        return message
    
    def _send_via_api(self, access_token: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Microsoft Graph API."""
        # Prepare API request
        graph_api_url = "https://graph.microsoft.com/v1.0/me/sendMail"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {"message": message}
        
        # Send request
        response = requests.post(graph_api_url, json=payload, headers=headers)
        
        if response.status_code != 202:  # Microsoft Graph returns 202 for successful send
            raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
        
        # For sent emails, we don't get an ID back, so generate a placeholder
        return {
            "email_id": f"sent_{datetime.utcnow().isoformat()}",
            "thread_id": None,  # Microsoft Graph manages threads automatically
            "provider": "outlook",
            "sent": True
        }
    
    def _create_draft_via_api(self, access_token: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Create draft via Microsoft Graph API."""
        # Prepare API request
        graph_api_url = "https://graph.microsoft.com/v1.0/me/messages"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Send request
        response = requests.post(graph_api_url, json=message, headers=headers)
        
        if response.status_code != 201:
            raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        return {
            "email_id": result.get('id'),
            "thread_id": result.get('conversationId'),
            "provider": "outlook",
            "sent": False
        }