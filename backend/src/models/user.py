"""
User data models for authentication and profile management.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    """User profile information."""
    name: str
    default_meeting_duration: int = 30
    auto_book_enabled: bool = False


class User(BaseModel):
    """Main user model for DynamoDB storage."""
    pk: str  # user#12345
    email: EmailStr
    timezone: str = "America/New_York"
    created_at: datetime
    profile: UserProfile
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }