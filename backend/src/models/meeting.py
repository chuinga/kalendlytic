"""
Meeting and calendar data models.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TimeSlot(BaseModel):
    """Time slot for availability and scheduling."""
    start: datetime
    end: datetime
    available: bool = True
    score: Optional[float] = None


class Availability(BaseModel):
    """Aggregated availability across calendars."""
    user_id: str
    date_range_start: datetime
    date_range_end: datetime
    time_slots: List[TimeSlot]
    last_updated: datetime


class Meeting(BaseModel):
    """Meeting model for DynamoDB storage."""
    pk: str  # user#12345
    sk: str  # meeting#event123
    provider_event_id: str
    provider: str  # google or microsoft
    title: str
    start: datetime
    end: datetime
    attendees: List[str]
    status: str = "confirmed"
    priority_score: float = 0.5
    created_by_agent: bool = False
    last_modified: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }