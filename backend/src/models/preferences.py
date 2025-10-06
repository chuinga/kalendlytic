"""
User preferences and scheduling rules data models.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, EmailStr


class WorkingHours(BaseModel):
    """Working hours for a specific day."""
    start: str  # HH:MM format
    end: str    # HH:MM format


class VIPContact(BaseModel):
    """VIP contact information."""
    email: EmailStr
    priority_weight: float = 1.0


class MeetingType(BaseModel):
    """Meeting type configuration."""
    duration: int  # minutes
    priority: str  # low, medium, high
    buffer_before: int = 0  # minutes
    buffer_after: int = 0   # minutes


class FocusBlock(BaseModel):
    """Focus time block configuration."""
    day: str  # monday, tuesday, etc.
    start: str  # HH:MM format
    end: str    # HH:MM format
    title: str


class Preferences(BaseModel):
    """User preferences model for DynamoDB storage."""
    pk: str  # user#12345
    working_hours: Dict[str, WorkingHours]  # day -> working hours
    buffer_minutes: int = 15
    focus_blocks: List[FocusBlock] = []
    vip_contacts: List[str] = []  # email addresses
    meeting_types: Dict[str, MeetingType] = {}
    
    class Config:
        json_encoders = {
            # Add any custom encoders if needed
        }