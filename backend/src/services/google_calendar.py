"""
Google Calendar API integration service.
Handles calendar events, availability calculation, and timezone normalization.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pytz

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .google_oauth import GoogleOAuthService
from ..models.meeting import TimeSlot, Availability, Meeting
from ..utils.logging import setup_logger, redact_pii

logger = setup_logger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar API operations."""
    
    def __init__(self):
        self.oauth_service = GoogleOAuthService()
    
    def _get_calendar_service(self, user_id: str):
        """Get authenticated Google Calendar service."""
        try:
            credentials = self.oauth_service.get_valid_credentials(user_id)
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Failed to get calendar service for user {user_id}: {str(e)}")
            raise Exception(f"Calendar service unavailable: {str(e)}")    

    def _normalize_timezone(self, dt_str: str, timezone: Optional[str] = None) -> datetime:
        """
        Normalize datetime string to UTC with proper timezone handling.
        
        Args:
            dt_str: ISO 8601 datetime string
            timezone: Optional timezone identifier
            
        Returns:
            UTC datetime object
        """
        try:
            # Parse the datetime string
            if 'T' in dt_str:
                if dt_str.endswith('Z'):
                    # Already UTC
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                elif '+' in dt_str or dt_str.endswith(('00', '30')):
                    # Has timezone offset
                    dt = datetime.fromisoformat(dt_str)
                else:
                    # No timezone info, use provided timezone or assume UTC
                    dt = datetime.fromisoformat(dt_str)
                    if timezone:
                        tz = pytz.timezone(timezone)
                        dt = tz.localize(dt) if dt.tzinfo is None else dt
                    elif dt.tzinfo is None:
                        dt = dt.replace(tzinfo=pytz.UTC)
            else:
                # Date only, assume start of day in provided timezone or UTC
                dt = datetime.fromisoformat(dt_str + 'T00:00:00')
                if timezone:
                    tz = pytz.timezone(timezone)
                    dt = tz.localize(dt)
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
    
    def _format_iso8601(self, dt: datetime, timezone: str = 'UTC') -> str:
        """
        Format datetime as ISO 8601 string with timezone.
        
        Args:
            dt: Datetime object
            timezone: Target timezone identifier
            
        Returns:
            ISO 8601 formatted string
        """
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            
            if timezone != 'UTC':
                target_tz = pytz.timezone(timezone)
                dt = dt.astimezone(target_tz)
            
            return dt.isoformat()
            
        except Exception as e:
            logger.error(f"Failed to format datetime {dt}: {str(e)}")
            return dt.isoformat()
    
    def fetch_calendar_events(self, user_id: str, start_time: datetime, end_time: datetime, 
                            calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """
        Fetch calendar events from Google Calendar API.
        
        Args:
            user_id: User identifier
            start_time: Start of time range (UTC)
            end_time: End of time range (UTC)
            calendar_id: Calendar ID to fetch from (default: primary)
            
        Returns:
            List of normalized calendar events
        """
        try:
            service = self._get_calendar_service(user_id)
            
            # Format times for API call
            time_min = self._format_iso8601(start_time)
            time_max = self._format_iso8601(end_time)
            
            logger.info(f"Fetching events for user {user_id} from {time_min} to {time_max}")
            
            # Call Google Calendar API
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=2500  # Google's max limit
            ).execute()
            
            events = events_result.get('items', [])
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
            
        except HttpError as e:
            logger.error(f"Google Calendar API error for user {user_id}: {str(e)}")
            if e.resp.status == 401:
                raise Exception("Authentication failed - token may be expired")
            elif e.resp.status == 403:
                raise Exception("Access denied - insufficient permissions")
            elif e.resp.status == 404:
                raise Exception(f"Calendar {calendar_id} not found")
            else:
                raise Exception(f"Calendar API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to fetch calendar events for user {user_id}: {str(e)}")
            raise Exception(f"Failed to fetch calendar events: {str(e)}")
    
    def _normalize_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize Google Calendar event to internal format.
        
        Args:
            event: Raw Google Calendar event
            
        Returns:
            Normalized event dictionary or None if invalid
        """
        try:
            # Skip events without start/end times (like all-day events without time)
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            if not start_data or not end_data:
                return None
            
            # Handle different time formats
            start_time = None
            end_time = None
            is_all_day = False
            
            if 'dateTime' in start_data:
                start_time = self._normalize_timezone(
                    start_data['dateTime'], 
                    start_data.get('timeZone')
                )
                end_time = self._normalize_timezone(
                    end_data['dateTime'], 
                    end_data.get('timeZone')
                )
            elif 'date' in start_data:
                # All-day event
                start_time = self._normalize_timezone(start_data['date'])
                end_time = self._normalize_timezone(end_data['date'])
                is_all_day = True
            else:
                return None
            
            # Extract attendees
            attendees = []
            for attendee in event.get('attendees', []):
                if attendee.get('email'):
                    attendees.append({
                        'email': attendee['email'],
                        'name': attendee.get('displayName', ''),
                        'response_status': attendee.get('responseStatus', 'needsAction'),
                        'optional': attendee.get('optional', False)
                    })
            
            return {
                'id': event.get('id'),
                'title': event.get('summary', 'No Title'),
                'description': event.get('description', ''),
                'start': start_time,
                'end': end_time,
                'is_all_day': is_all_day,
                'status': event.get('status', 'confirmed'),
                'attendees': attendees,
                'creator': event.get('creator', {}).get('email', ''),
                'organizer': event.get('organizer', {}).get('email', ''),
                'location': event.get('location', ''),
                'visibility': event.get('visibility', 'default'),
                'transparency': event.get('transparency', 'opaque'),  # opaque = busy, transparent = free
                'recurring_event_id': event.get('recurringEventId'),
                'original_start_time': event.get('originalStartTime'),
                'html_link': event.get('htmlLink', ''),
                'updated': self._normalize_timezone(event.get('updated', datetime.utcnow().isoformat())),
                'provider': 'google',
                'raw_event': redact_pii(event)  # Store redacted version for debugging
            }
            
        except Exception as e:
            logger.error(f"Failed to normalize event: {str(e)}")
            return None
    
    def create_event(self, user_id: str, event_data: Dict[str, Any], 
                   calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            user_id: User identifier
            event_data: Event data dictionary
            calendar_id: Target calendar ID
            
        Returns:
            Created event information
        """
        try:
            service = self._get_calendar_service(user_id)
            
            # Build Google Calendar event structure
            google_event = {
                'summary': event_data.get('title', 'New Meeting'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': self._format_iso8601(event_data['start']),
                    'timeZone': event_data.get('timezone', 'UTC')
                },
                'end': {
                    'dateTime': self._format_iso8601(event_data['end']),
                    'timeZone': event_data.get('timezone', 'UTC')
                }
            }
            
            # Add location if provided
            if event_data.get('location'):
                google_event['location'] = event_data['location']
            
            # Add attendees if provided
            if event_data.get('attendees'):
                google_event['attendees'] = [
                    {'email': attendee} if isinstance(attendee, str) else attendee
                    for attendee in event_data['attendees']
                ]
            
            # Add conference data if requested
            if event_data.get('add_conference', False):
                google_event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            
            logger.info(f"Creating event for user {user_id}: {event_data.get('title', 'Untitled')}")
            
            # Create the event
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=google_event,
                conferenceDataVersion=1 if event_data.get('add_conference') else 0,
                sendUpdates='all' if event_data.get('send_notifications', True) else 'none'
            ).execute()
            
            # Return normalized event
            normalized_event = self._normalize_event(created_event)
            logger.info(f"Successfully created event {created_event.get('id')} for user {user_id}")
            
            return {
                'event_id': created_event.get('id'),
                'html_link': created_event.get('htmlLink'),
                'hangout_link': created_event.get('hangoutLink'),
                'event_data': normalized_event
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error creating event for user {user_id}: {str(e)}")
            if e.resp.status == 401:
                raise Exception("Authentication failed - token may be expired")
            elif e.resp.status == 403:
                raise Exception("Access denied - insufficient permissions")
            else:
                raise Exception(f"Calendar API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create event for user {user_id}: {str(e)}")
            raise Exception(f"Failed to create event: {str(e)}")
    
    def update_event(self, user_id: str, event_id: str, event_data: Dict[str, Any], 
                   calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        Update an existing calendar event.
        
        Args:
            user_id: User identifier
            event_id: Google Calendar event ID
            event_data: Updated event data
            calendar_id: Calendar ID containing the event
            
        Returns:
            Updated event information
        """
        try:
            service = self._get_calendar_service(user_id)
            
            # Get existing event
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if 'title' in event_data:
                existing_event['summary'] = event_data['title']
            
            if 'description' in event_data:
                existing_event['description'] = event_data['description']
            
            if 'start' in event_data:
                existing_event['start'] = {
                    'dateTime': self._format_iso8601(event_data['start']),
                    'timeZone': event_data.get('timezone', 'UTC')
                }
            
            if 'end' in event_data:
                existing_event['end'] = {
                    'dateTime': self._format_iso8601(event_data['end']),
                    'timeZone': event_data.get('timezone', 'UTC')
                }
            
            if 'location' in event_data:
                existing_event['location'] = event_data['location']
            
            if 'attendees' in event_data:
                existing_event['attendees'] = [
                    {'email': attendee} if isinstance(attendee, str) else attendee
                    for attendee in event_data['attendees']
                ]
            
            logger.info(f"Updating event {event_id} for user {user_id}")
            
            # Update the event
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event,
                sendUpdates='all' if event_data.get('send_notifications', True) else 'none'
            ).execute()
            
            # Return normalized event
            normalized_event = self._normalize_event(updated_event)
            logger.info(f"Successfully updated event {event_id} for user {user_id}")
            
            return {
                'event_id': updated_event.get('id'),
                'html_link': updated_event.get('htmlLink'),
                'event_data': normalized_event
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error updating event {event_id} for user {user_id}: {str(e)}")
            if e.resp.status == 401:
                raise Exception("Authentication failed - token may be expired")
            elif e.resp.status == 403:
                raise Exception("Access denied - insufficient permissions")
            elif e.resp.status == 404:
                raise Exception(f"Event {event_id} not found")
            else:
                raise Exception(f"Calendar API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to update event {event_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to update event: {str(e)}")
    
    def delete_event(self, user_id: str, event_id: str, calendar_id: str = 'primary', 
                   send_notifications: bool = True) -> bool:
        """
        Delete a calendar event.
        
        Args:
            user_id: User identifier
            event_id: Google Calendar event ID
            calendar_id: Calendar ID containing the event
            send_notifications: Whether to send cancellation notifications
            
        Returns:
            True if deletion was successful
        """
        try:
            service = self._get_calendar_service(user_id)
            
            logger.info(f"Deleting event {event_id} for user {user_id}")
            
            # Delete the event
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates='all' if send_notifications else 'none'
            ).execute()
            
            logger.info(f"Successfully deleted event {event_id} for user {user_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar API error deleting event {event_id} for user {user_id}: {str(e)}")
            if e.resp.status == 401:
                raise Exception("Authentication failed - token may be expired")
            elif e.resp.status == 403:
                raise Exception("Access denied - insufficient permissions")
            elif e.resp.status == 404:
                # Event already deleted or doesn't exist
                logger.warning(f"Event {event_id} not found for deletion")
                return True
            else:
                raise Exception(f"Calendar API error: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to delete event {event_id} for user {user_id}: {str(e)}")
            raise Exception(f"Failed to delete event: {str(e)}")
    
    def calculate_availability(self, user_id: str, start_date: datetime, end_date: datetime,
                             working_hours: Optional[Dict[str, Any]] = None,
                             time_slot_duration: int = 30) -> Availability:
        """
        Calculate availability based on Google Calendar events.
        
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
            
            # Skip declined events
            if event.get('status') == 'cancelled':
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
        Get list of user's calendars.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of calendar information
        """
        try:
            service = self._get_calendar_service(user_id)
            
            calendar_list = service.calendarList().list().execute()
            calendars = []
            
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar.get('id'),
                    'name': calendar.get('summary', ''),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole', ''),
                    'background_color': calendar.get('backgroundColor', ''),
                    'foreground_color': calendar.get('foregroundColor', ''),
                    'selected': calendar.get('selected', True),
                    'timezone': calendar.get('timeZone', 'UTC')
                })
            
            return calendars
            
        except Exception as e:
            logger.error(f"Failed to get calendar list for user {user_id}: {str(e)}")
            raise Exception(f"Failed to get calendar list: {str(e)}")