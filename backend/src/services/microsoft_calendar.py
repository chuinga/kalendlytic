"""
Microsoft Graph Calendar API integration service.
Handles calendar events, availability calculation, and timezone normalization for Outlook.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pytz
import requests

from .microsoft_oauth import MicrosoftOAuthService
from ..models.meeting import TimeSlot, Availability, Meeting
from ..utils.logging import setup_logger, redact_pii

logger = setup_logger(__name__)


class MicrosoftCalendarService:
    """Service for Microsoft Graph Calendar API operations."""
    
    def __init__(self):
        self.oauth_service = MicrosoftOAuthService()
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
    
    def _get_auth_headers(self, user_id: str) -> Dict[str, str]:
        """Get authenticated headers for Microsoft Graph API."""
        try:
            access_token = self.oauth_service.get_valid_access_token(user_id)
            return {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        except Exception as e:
            logger.error(f"Failed to get auth headers for user {user_id}: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")

    def _normalize_timezone(self, dt_str: str, timezone: Optional[str] = None) -> datetime:
        """
        Normalize datetime string to UTC with proper timezone handling.
        
        Args:
            dt_str: ISO 8601 datetime string or Graph API datetime format
            timezone: Optional timezone identifier
            
        Returns:
            UTC datetime object
        """
        try:
            # Handle Microsoft Graph datetime format
            if isinstance(dt_str, dict):
                # Graph API returns datetime as {"dateTime": "2023-01-01T10:00:00", "timeZone": "UTC"}
                dt_str = dt_str.get('dateTime', dt_str)
                timezone = timezone or dt_str.get('timeZone')
            
            # Parse the datetime string
            if 'T' in dt_str:
                if dt_str.endswith('Z'):
                    # Already UTC
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                elif '+' in dt_str or dt_str.count(':') > 2:
                    # Has timezone offset
                    dt = datetime.fromisoformat(dt_str)
                else:
                    # No timezone info, use provided timezone or assume UTC
                    dt = datetime.fromisoformat(dt_str)
                    if timezone and timezone != 'tzone://Microsoft/Custom':
                        try:
                            tz = pytz.timezone(timezone)
                            dt = tz.localize(dt) if dt.tzinfo is None else dt
                        except:
                            # Fallback to UTC if timezone is invalid
                            dt = dt.replace(tzinfo=pytz.UTC) if dt.tzinfo is None else dt
                    elif dt.tzinfo is None:
                        dt = dt.replace(tzinfo=pytz.UTC)
            else:
                # Date only, assume start of day in provided timezone or UTC
                dt = datetime.fromisoformat(dt_str + 'T00:00:00')
                if timezone and timezone != 'tzone://Microsoft/Custom':
                    try:
                        tz = pytz.timezone(timezone)
                        dt = tz.localize(dt)
                    except:
                        dt = dt.replace(tzinfo=pytz.UTC)
                else:
                    dt = dt.replace(tzinfo=pytz.UTC)
            
            # Convert to UTC
            if dt.tzinfo != pytz.UTC:
                dt = dt.astimezone(pytz.UTC)
            
            return dt.replace(tzinfo=None)  # Remove timezone info for consistency
            
        except Exception as e:
            logger.error(f"Failed to normalize timezone for {dt_str}: {str(e)}")
            # Fallback to current time
            return datetime.utcnow()
    
    def _format_graph_datetime(self, dt: datetime, timezone: str = 'UTC') -> Dict[str, str]:
        """
        Format datetime for Microsoft Graph API.
        
        Args:
            dt: Datetime object
            timezone: Target timezone identifier
            
        Returns:
            Graph API datetime format
        """
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            
            if timezone != 'UTC':
                try:
                    target_tz = pytz.timezone(timezone)
                    dt = dt.astimezone(target_tz)
                except:
                    # Fallback to UTC if timezone is invalid
                    timezone = 'UTC'
            
            return {
                'dateTime': dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],  # Graph expects milliseconds
                'timeZone': timezone
            }
            
        except Exception as e:
            logger.error(f"Failed to format datetime {dt}: {str(e)}")
            return {
                'dateTime': dt.isoformat(),
                'timeZone': 'UTC'
            }
    
    def fetch_calendar_events(self, user_id: str, start_time: datetime, end_time: datetime, 
                            calendar_id: str = None) -> List[Dict[str, Any]]:
        """
        Fetch calendar events from Microsoft Graph Calendar API.
        
        Args:
            user_id: User identifier
            start_time: Start of time range (UTC)
            end_time: End of time range (UTC)
            calendar_id: Calendar ID to fetch from (default: primary calendar)
            
        Returns:
            List of normalized calendar events
        """
        try:
            headers = self._get_auth_headers(user_id)
            
            # Format times for API call (Graph expects ISO 8601)
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Build API endpoint
            if calendar_id:
                endpoint = f"{self.graph_base_url}/me/calendars/{calendar_id}/events"
            else:
                endpoint = f"{self.graph_base_url}/me/events"
            
            # Query parameters
            params = {
                '$filter': f"start/dateTime ge '{start_str}' and end/dateTime le '{end_str}'",
                '$orderby': 'start/dateTime',
                '$top': 1000,  # Microsoft Graph limit
                '$select': 'id,subject,body,start,end,attendees,organizer,location,isAllDay,showAs,sensitivity,categories,webLink,createdDateTime,lastModifiedDateTime,responseStatus,recurrence,seriesMasterId'
            }
            
            logger.info(f"Fetching events for user {user_id} from {start_str} to {end_str}")
            
            # Call Microsoft Graph API
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code == 404:
                raise Exception(f"Calendar {calendar_id} not found")
            elif response.status_code != 200:
                logger.error(f"Graph API error: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            data = response.json()
            events = data.get('value', [])
            normalized_events = []
            
            for event in events:
                try:
                    normalized_event = self._normalize_event(event)
                    if normalized_event:
                        normalized_events.append(normalized_event)
                except Exception as e:
                    logger.warning(f"Failed to normalize event {event.get('id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(normalized_events)} events for user {user_id}")
            return normalized_events
            
        except Exception as e:
            logger.error(f"Failed to fetch calendar events for user {user_id}: {str(e)}")
            raise Exception(f"Failed to fetch calendar events: {str(e)}")
    
    def _normalize_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Microsoft Graph event to internal format.
        
        Args:
            event: Raw Microsoft Graph event
            
        Returns:
            Normalized event dictionary or None if invalid
        """
        try:
            # Skip events without start/end times
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            if not start_data or not end_data:
                return None
            
            # Handle datetime normalization
            start_time = self._normalize_timezone(
                start_data.get('dateTime'), 
                start_data.get('timeZone')
            )
            end_time = self._normalize_timezone(
                end_data.get('dateTime'), 
                end_data.get('timeZone')
            )
            
            is_all_day = event.get('isAllDay', False)
            
            # Extract attendees
            attendees = []
            for attendee in event.get('attendees', []):
                email_address = attendee.get('emailAddress', {})
                if email_address.get('address'):
                    attendees.append({
                        'email': email_address['address'],
                        'name': email_address.get('name', ''),
                        'response_status': attendee.get('status', {}).get('response', 'none'),
                        'type': attendee.get('type', 'required')
                    })
            
            # Extract organizer
            organizer_data = event.get('organizer', {}).get('emailAddress', {})
            organizer_email = organizer_data.get('address', '')
            
            # Map Microsoft showAs to transparency
            show_as = event.get('showAs', 'busy')
            transparency = 'transparent' if show_as in ['free', 'workingElsewhere'] else 'opaque'
            
            return {
                'id': event.get('id'),
                'title': event.get('subject', 'No Title'),
                'description': event.get('body', {}).get('content', ''),
                'start': start_time,
                'end': end_time,
                'is_all_day': is_all_day,
                'status': 'confirmed',  # Microsoft doesn't have cancelled status in the same way
                'attendees': attendees,
                'creator': organizer_email,
                'organizer': organizer_email,
                'location': event.get('location', {}).get('displayName', ''),
                'visibility': 'private' if event.get('sensitivity') == 'private' else 'default',
                'transparency': transparency,
                'show_as': show_as,
                'recurring_event_id': event.get('seriesMasterId'),
                'categories': event.get('categories', []),
                'html_link': event.get('webLink', ''),
                'updated': self._normalize_timezone(event.get('lastModifiedDateTime', datetime.utcnow().isoformat())),
                'created': self._normalize_timezone(event.get('createdDateTime', datetime.utcnow().isoformat())),
                'provider': 'microsoft',
                'raw_event': redact_pii(event)  # Store redacted version for debugging
            }
            
        except Exception as e:
            logger.error(f"Failed to normalize event: {str(e)}")
            return None
    
    def create_event(self, user_id: str, event_data: Dict[str, Any], 
                   calendar_id: str = None) -> Dict[str, Any]:
        """
        Create a new calendar event in Microsoft Graph.
        
        Args:
            user_id: User identifier
            event_data: Event data dictionary
            calendar_id: Target calendar ID (default: primary calendar)
            
        Returns:
            Created event information
        """
        try:
            headers = self._get_auth_headers(user_id)
            
            # Build API endpoint
            if calendar_id:
                endpoint = f"{self.graph_base_url}/me/calendars/{calendar_id}/events"
            else:
                endpoint = f"{self.graph_base_url}/me/events"
            
            # Build Microsoft Graph event structure
            graph_event = {
                'subject': event_data.get('title', 'New Meeting'),
                'body': {
                    'contentType': 'HTML',
                    'content': event_data.get('description', '')
                },
                'start': self._format_graph_datetime(
                    event_data['start'], 
                    event_data.get('timezone', 'UTC')
                ),
                'end': self._format_graph_datetime(
                    event_data['end'], 
                    event_data.get('timezone', 'UTC')
                ),
                'isAllDay': event_data.get('is_all_day', False)
            }
            
            # Add location if provided
            if event_data.get('location'):
                graph_event['location'] = {
                    'displayName': event_data['location']
                }
            
            # Add attendees if provided
            if event_data.get('attendees'):
                graph_event['attendees'] = []
                for attendee in event_data['attendees']:
                    if isinstance(attendee, str):
                        graph_event['attendees'].append({
                            'emailAddress': {
                                'address': attendee,
                                'name': attendee
                            },
                            'type': 'required'
                        })
                    else:
                        graph_event['attendees'].append({
                            'emailAddress': {
                                'address': attendee.get('email', ''),
                                'name': attendee.get('name', attendee.get('email', ''))
                            },
                            'type': attendee.get('type', 'required')
                        })
            
            # Add online meeting if requested
            if event_data.get('add_conference', False):
                graph_event['isOnlineMeeting'] = True
                graph_event['onlineMeetingProvider'] = 'teamsForBusiness'
            
            # Set sensitivity if specified
            if event_data.get('sensitivity'):
                graph_event['sensitivity'] = event_data['sensitivity']
            
            # Set categories if provided
            if event_data.get('categories'):
                graph_event['categories'] = event_data['categories']
            
            logger.info(f"Creating event for user {user_id}: {event_data.get('title', 'Untitled')}")
            
            # Create the event
            response = requests.post(endpoint, headers=headers, json=graph_event, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code not in [200, 201]:
                logger.error(f"Graph API error creating event: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            created_event = response.json()
            
            # Return normalized event
            normalized_event = self._normalize_event(created_event)
            logger.info(f"Successfully created event {created_event.get('id')} for user {user_id}")
            
            return {
                'event_id': created_event.get('id'),
                'html_link': created_event.get('webLink'),
                'online_meeting_url': created_event.get('onlineMeeting', {}).get('joinUrl'),
                'event_data': normalized_event
            }
            
        except Exception as e:
            logger.error(f"Failed to create event for user {user_id}: {str(e)}")
            raise Exception(f"Failed to create event: {str(e)}")
    
    def update_event(self, user_id: str, event_id: str, event_data: Dict[str, Any], 
                   calendar_id: str = None) -> Dict[str, Any]:
        """
        Update an existing calendar event in Microsoft Graph.
        
        Args:
            user_id: User identifier
            event_id: Microsoft Graph event ID
            event_data: Updated event data
            calendar_id: Calendar ID containing the event
            
        Returns:
            Updated event information
        """
        try:
            headers = self._get_auth_headers(user_id)
            
            # Build API endpoint
            if calendar_id:
                endpoint = f"{self.graph_base_url}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                endpoint = f"{self.graph_base_url}/me/events/{event_id}"
            
            # Build update payload
            update_data = {}
            
            if 'title' in event_data:
                update_data['subject'] = event_data['title']
            
            if 'description' in event_data:
                update_data['body'] = {
                    'contentType': 'HTML',
                    'content': event_data['description']
                }
            
            if 'start' in event_data:
                update_data['start'] = self._format_graph_datetime(
                    event_data['start'], 
                    event_data.get('timezone', 'UTC')
                )
            
            if 'end' in event_data:
                update_data['end'] = self._format_graph_datetime(
                    event_data['end'], 
                    event_data.get('timezone', 'UTC')
                )
            
            if 'location' in event_data:
                update_data['location'] = {
                    'displayName': event_data['location']
                }
            
            if 'attendees' in event_data:
                update_data['attendees'] = []
                for attendee in event_data['attendees']:
                    if isinstance(attendee, str):
                        update_data['attendees'].append({
                            'emailAddress': {
                                'address': attendee,
                                'name': attendee
                            },
                            'type': 'required'
                        })
                    else:
                        update_data['attendees'].append({
                            'emailAddress': {
                                'address': attendee.get('email', ''),
                                'name': attendee.get('name', attendee.get('email', ''))
                            },
                            'type': attendee.get('type', 'required')
                        })
            
            if 'is_all_day' in event_data:
                update_data['isAllDay'] = event_data['is_all_day']
            
            if 'sensitivity' in event_data:
                update_data['sensitivity'] = event_data['sensitivity']
            
            if 'categories' in event_data:
                update_data['categories'] = event_data['categories']
            
            logger.info(f"Updating event {event_id} for user {user_id}")
            
            # Update the event
            response = requests.patch(endpoint, headers=headers, json=update_data, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code == 404:
                raise Exception(f"Event {event_id} not found")
            elif response.status_code != 200:
                logger.error(f"Graph API error updating event: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            updated_event = response.json()
            
            # Return normalized event
            normalized_event = self._normalize_event(updated_event)
            logger.info(f"Successfully updated event {event_id} for user {user_id}")
            
            return {
                'event_id': updated_event.get('id'),
                'html_link': updated_event.get('webLink'),
                'event_data': normalized_event
            }
            
        except Exception as e:
            logger.error(f"Failed to update event {event_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to update event: {str(e)}")
    
    def delete_event(self, user_id: str, event_id: str, calendar_id: str = None) -> bool:
        """
        Delete a calendar event from Microsoft Graph.
        
        Args:
            user_id: User identifier
            event_id: Microsoft Graph event ID
            calendar_id: Calendar ID containing the event
            
        Returns:
            True if deletion was successful
        """
        try:
            headers = self._get_auth_headers(user_id)
            
            # Build API endpoint
            if calendar_id:
                endpoint = f"{self.graph_base_url}/me/calendars/{calendar_id}/events/{event_id}"
            else:
                endpoint = f"{self.graph_base_url}/me/events/{event_id}"
            
            logger.info(f"Deleting event {event_id} for user {user_id}")
            
            # Delete the event
            response = requests.delete(endpoint, headers=headers, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code == 404:
                # Event already deleted or doesn't exist
                logger.warning(f"Event {event_id} not found for deletion")
                return True
            elif response.status_code != 204:  # Microsoft Graph returns 204 for successful deletion
                logger.error(f"Graph API error deleting event: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            logger.info(f"Successfully deleted event {event_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete event {event_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to delete event: {str(e)}")
    
    def calculate_availability(self, user_id: str, start_date: datetime, end_date: datetime,
                             working_hours: Optional[Dict[str, Any]] = None,
                             time_slot_duration: int = 30) -> Availability:
        """
        Calculate availability based on Microsoft Graph Calendar events.
        
        Args:
            user_id: User identifier
            start_date: Start of availability window (UTC)
            end_date: End of availability window (UTC)
            working_hours: Working hours configuration
            time_slot_duration: Duration of time slots in minutes
            
        Returns:
            Availability object with calculated time slots
        """
        try:
            # Default working hours (9 AM to 5 PM UTC, Monday to Friday)
            if not working_hours:
                working_hours = {
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'timezone': 'UTC',
                    'working_days': [0, 1, 2, 3, 4]  # Monday to Friday
                }
            
            # Fetch calendar events for the period
            events = self.fetch_calendar_events(user_id, start_date, end_date)
            
            # Generate time slots
            time_slots = self._generate_time_slots(
                start_date, end_date, working_hours, time_slot_duration
            )
            
            # Mark slots as unavailable based on events
            busy_slots = self._mark_busy_slots(time_slots, events)
            
            # Calculate availability scores
            scored_slots = self._calculate_availability_scores(busy_slots, events)
            
            logger.info(f"Calculated availability for user {user_id}: {len(scored_slots)} slots")
            
            return Availability(
                user_id=user_id,
                date_range_start=start_date,
                date_range_end=end_date,
                time_slots=scored_slots,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate availability for user {user_id}: {str(e)}")
            raise Exception(f"Failed to calculate availability: {str(e)}")
    
    def _generate_time_slots(self, start_date: datetime, end_date: datetime,
                           working_hours: Dict[str, Any], slot_duration: int) -> List[TimeSlot]:
        """Generate time slots within working hours."""
        slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        # Parse working hours
        start_time_str = working_hours.get('start_time', '09:00')
        end_time_str = working_hours.get('end_time', '17:00')
        working_days = working_hours.get('working_days', [0, 1, 2, 3, 4])
        timezone_str = working_hours.get('timezone', 'UTC')
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.UTC
        
        while current_date <= end_date_only:
            # Check if it's a working day (0 = Monday, 6 = Sunday)
            if current_date.weekday() in working_days:
                # Parse start and end times for this day
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                
                # Create datetime objects for the day
                day_start = datetime.combine(current_date, datetime.min.time().replace(
                    hour=start_hour, minute=start_minute
                ))
                day_end = datetime.combine(current_date, datetime.min.time().replace(
                    hour=end_hour, minute=end_minute
                ))
                
                # Localize to working timezone and convert to UTC
                if tz != pytz.UTC:
                    day_start = tz.localize(day_start).astimezone(pytz.UTC)
                    day_end = tz.localize(day_end).astimezone(pytz.UTC)
                else:
                    day_start = day_start.replace(tzinfo=pytz.UTC)
                    day_end = day_end.replace(tzinfo=pytz.UTC)
                
                # Remove timezone info for consistency
                day_start = day_start.replace(tzinfo=None)
                day_end = day_end.replace(tzinfo=None)
                
                # Generate slots for this day
                current_slot_start = day_start
                while current_slot_start < day_end:
                    slot_end = current_slot_start + timedelta(minutes=slot_duration)
                    
                    # Ensure slot doesn't exceed day end
                    if slot_end > day_end:
                        slot_end = day_end
                    
                    # Only add slot if it's within the requested range
                    if (current_slot_start >= start_date and 
                        slot_end <= end_date and 
                        slot_end > current_slot_start):
                        
                        slots.append(TimeSlot(
                            start=current_slot_start,
                            end=slot_end,
                            available=True,
                            score=1.0
                        ))
                    
                    current_slot_start = slot_end
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _mark_busy_slots(self, time_slots: List[TimeSlot], events: List[Dict[str, Any]]) -> List[TimeSlot]:
        """Mark time slots as unavailable based on calendar events."""
        for event in events:
            # Skip transparent events (marked as free time)
            if event.get('transparency') == 'transparent':
                continue
            
            # Skip events marked as free or working elsewhere
            if event.get('show_as') in ['free', 'workingElsewhere']:
                continue
            
            event_start = event['start']
            event_end = event['end']
            
            # Mark overlapping slots as unavailable
            for slot in time_slots:
                if self._slots_overlap(slot.start, slot.end, event_start, event_end):
                    slot.available = False
                    slot.score = 0.0
        
        return time_slots
    
    def _slots_overlap(self, slot_start: datetime, slot_end: datetime,
                      event_start: datetime, event_end: datetime) -> bool:
        """Check if a time slot overlaps with an event."""
        return (slot_start < event_end and slot_end > event_start)
    
    def _calculate_availability_scores(self, time_slots: List[TimeSlot], 
                                     events: List[Dict[str, Any]]) -> List[TimeSlot]:
        """Calculate availability scores based on surrounding events and preferences."""
        for slot in time_slots:
            if not slot.available:
                continue
            
            score = 1.0
            
            # Reduce score for slots adjacent to busy periods
            for event in events:
                event_start = event['start']
                event_end = event['end']
                
                # Check proximity to events (within 30 minutes)
                time_buffer = timedelta(minutes=30)
                
                if (abs((slot.start - event_end).total_seconds()) <= time_buffer.total_seconds() or
                    abs((event_start - slot.end).total_seconds()) <= time_buffer.total_seconds()):
                    score *= 0.8  # Reduce score for adjacent slots
                
                # Prefer slots with more buffer time
                if (abs((slot.start - event_end).total_seconds()) <= timedelta(hours=1).total_seconds() or
                    abs((event_start - slot.end).total_seconds()) <= timedelta(hours=1).total_seconds()):
                    score *= 0.9
            
            # Prefer mid-morning and early afternoon slots
            hour = slot.start.hour
            if 9 <= hour <= 11 or 13 <= hour <= 15:
                score *= 1.1
            elif hour < 9 or hour > 16:
                score *= 0.7
            
            slot.score = min(score, 1.0)  # Cap at 1.0
        
        return time_slots
    
    def get_calendar_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of user's Microsoft calendars.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of calendar information
        """
        try:
            headers = self._get_auth_headers(user_id)
            endpoint = f"{self.graph_base_url}/me/calendars"
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code != 200:
                logger.error(f"Graph API error getting calendars: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            data = response.json()
            calendars = []
            
            for calendar in data.get('value', []):
                calendars.append({
                    'id': calendar.get('id'),
                    'name': calendar.get('name', ''),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('isDefaultCalendar', False),
                    'can_edit': calendar.get('canEdit', False),
                    'can_share': calendar.get('canShare', False),
                    'can_view_private_items': calendar.get('canViewPrivateItems', False),
                    'owner': calendar.get('owner', {}).get('name', ''),
                    'color': calendar.get('color', 'auto'),
                    'change_key': calendar.get('changeKey', ''),
                    'is_removable': calendar.get('isRemovable', True)
                })
            
            return calendars
            
        except Exception as e:
            logger.error(f"Failed to get calendar list for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get calendar list: {str(e)}")
    
    def get_free_busy_info(self, user_id: str, start_time: datetime, end_time: datetime, 
                          email_addresses: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get free/busy information for multiple users using Microsoft Graph.
        
        Args:
            user_id: User identifier making the request
            start_time: Start of time range (UTC)
            end_time: End of time range (UTC)
            email_addresses: List of email addresses to check
            
        Returns:
            Dictionary mapping email addresses to their free/busy information
        """
        try:
            headers = self._get_auth_headers(user_id)
            endpoint = f"{self.graph_base_url}/me/calendar/getSchedule"
            
            # Format times for API call
            start_str = start_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            end_str = end_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            
            # Build request payload
            payload = {
                'schedules': email_addresses,
                'startTime': {
                    'dateTime': start_str,
                    'timeZone': 'UTC'
                },
                'endTime': {
                    'dateTime': end_str,
                    'timeZone': 'UTC'
                },
                'availabilityViewInterval': 30  # 30-minute intervals
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            elif response.status_code == 403:
                raise Exception("Access denied - insufficient permissions")
            elif response.status_code != 200:
                logger.error(f"Graph API error getting free/busy: {response.status_code} - {response.text}")
                raise Exception(f"Calendar API error: {response.status_code}")
            
            data = response.json()
            result = {}
            
            for schedule in data.get('value', []):
                email = schedule.get('scheduleId', '')
                busy_times = []
                
                for busy_time in schedule.get('busyViewEntries', []):
                    if busy_time.get('status') == 'busy':
                        busy_times.append({
                            'start': self._normalize_timezone(busy_time.get('start', {}).get('dateTime')),
                            'end': self._normalize_timezone(busy_time.get('end', {}).get('dateTime')),
                            'status': 'busy'
                        })
                
                result[email] = busy_times
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get free/busy info for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get free/busy info: {str(e)}")