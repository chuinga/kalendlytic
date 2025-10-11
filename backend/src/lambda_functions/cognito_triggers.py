"""
Cognito trigger handlers for user lifecycle events.
Handles post-confirmation user profile creation and other user events.
"""

import json
import logging
import boto3
from datetime import datetime
from typing import Dict, Any
import os

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')


def post_confirmation_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cognito Post Confirmation trigger handler.
    Creates user profile in DynamoDB after successful email confirmation.
    
    Args:
        event: Cognito trigger event containing user details
        context: Lambda context object
        
    Returns:
        Modified event (required by Cognito triggers)
    """
    try:
        logger.info(f"Post confirmation trigger received: {json.dumps(event, default=str)}")
        
        # Extract user information from Cognito event
        user_attributes = event.get('request', {}).get('userAttributes', {})
        user_id = user_attributes.get('sub')
        email = user_attributes.get('email')
        name = user_attributes.get('name', '')
        timezone = user_attributes.get('custom:timezone', 'UTC')
        
        if not user_id or not email:
            logger.error("Missing required user attributes (sub or email)")
            return event
        
        # Get table names from environment variables
        users_table_name = os.environ.get('USERS_TABLE_NAME', 'meeting-agent-users')
        preferences_table_name = os.environ.get('PREFERENCES_TABLE_NAME', 'meeting-agent-preferences')
        
        users_table = dynamodb.Table(users_table_name)
        preferences_table = dynamodb.Table(preferences_table_name)
        
        # Create user profile in DynamoDB
        user_profile = {
            'pk': f'user#{user_id}',
            'email': email,
            'timezone': timezone,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'profile': {
                'name': name,
                'default_meeting_duration': 30,
                'auto_book_enabled': False
            },
            'preferences': {
                'working_hours': {
                    'monday': {'start': '09:00', 'end': '17:00'},
                    'tuesday': {'start': '09:00', 'end': '17:00'},
                    'wednesday': {'start': '09:00', 'end': '17:00'},
                    'thursday': {'start': '09:00', 'end': '17:00'},
                    'friday': {'start': '09:00', 'end': '17:00'},
                    'saturday': {'start': '10:00', 'end': '14:00'},
                    'sunday': {'start': '10:00', 'end': '14:00'}
                },
                'buffer_minutes': 15,
                'focus_blocks': [],
                'vip_contacts': [],
                'meeting_types': {
                    'standup': {'duration': 15, 'priority': 'medium'},
                    'interview': {'duration': 60, 'priority': 'high'},
                    'meeting': {'duration': 30, 'priority': 'medium'}
                }
            },
            'status': 'active',
            'last_login': None,
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Store user profile in DynamoDB
        users_table.put_item(Item=user_profile)
        
        logger.info(f"Successfully created user profile for {email} (ID: {user_id})")
        
        # Also create default preferences entry
        create_default_preferences(preferences_table, user_id, timezone)
        
        return event
        
    except Exception as e:
        logger.error(f"Error in post confirmation handler: {str(e)}")
        # Don't fail the Cognito flow, just log the error
        return event


def create_default_preferences(preferences_table, user_id: str, timezone: str) -> None:
    """
    Create default preferences entry for new user.
    
    Args:
        preferences_table: DynamoDB table resource
        user_id: Cognito user ID
        timezone: User's timezone
    """
    try:
        default_preferences = {
            'pk': f'user#{user_id}',
            'working_hours': {
                'monday': {'start': '09:00', 'end': '17:00'},
                'tuesday': {'start': '09:00', 'end': '17:00'},
                'wednesday': {'start': '09:00', 'end': '17:00'},
                'thursday': {'start': '09:00', 'end': '17:00'},
                'friday': {'start': '09:00', 'end': '17:00'},
                'saturday': {'start': '10:00', 'end': '14:00'},
                'sunday': {'start': '10:00', 'end': '14:00'}
            },
            'buffer_minutes': 15,
            'focus_blocks': [],
            'vip_contacts': [],
            'meeting_types': {
                'standup': {'duration': 15, 'priority': 'medium'},
                'interview': {'duration': 60, 'priority': 'high'},
                'meeting': {'duration': 30, 'priority': 'medium'},
                'one-on-one': {'duration': 30, 'priority': 'high'},
                'team-meeting': {'duration': 45, 'priority': 'medium'}
            },
            'timezone': timezone,
            'auto_book_enabled': False,
            'notification_preferences': {
                'email_confirmations': True,
                'email_reminders': True,
                'conflict_notifications': True
            },
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        preferences_table.put_item(Item=default_preferences)
        logger.info(f"Created default preferences for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error creating default preferences for user {user_id}: {str(e)}")


def pre_sign_up_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cognito Pre Sign Up trigger handler.
    Can be used for custom validation or auto-confirmation.
    
    Args:
        event: Cognito trigger event
        context: Lambda context object
        
    Returns:
        Modified event with confirmation settings
    """
    try:
        logger.info(f"Pre sign up trigger received: {json.dumps(event, default=str)}")
        
        # Auto-confirm user (skip email verification for development)
        # Remove this in production to require email verification
        # event['response']['autoConfirmUser'] = True
        # event['response']['autoVerifyEmail'] = True
        
        return event
        
    except Exception as e:
        logger.error(f"Error in pre sign up handler: {str(e)}")
        return event


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Cognito triggers.
    Routes to appropriate handler based on trigger source.
    
    Args:
        event: Cognito trigger event
        context: Lambda context object
        
    Returns:
        Modified event
    """
    try:
        trigger_source = event.get('triggerSource')
        
        logger.info(f"Cognito trigger received: {trigger_source}")
        
        if trigger_source == 'PostConfirmation_ConfirmSignUp':
            return post_confirmation_handler(event, context)
        elif trigger_source == 'PreSignUp_SignUp':
            return pre_sign_up_handler(event, context)
        else:
            logger.warning(f"Unhandled trigger source: {trigger_source}")
            return event
            
    except Exception as e:
        logger.error(f"Error in Cognito trigger handler: {str(e)}")
        return event