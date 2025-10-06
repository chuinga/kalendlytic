"""
OAuth connection data models for Google and Microsoft integration.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class OAuthToken(BaseModel):
    """OAuth token information."""
    access_token_encrypted: str
    refresh_token_encrypted: str
    expires_at: datetime
    scopes: List[str]


class Connection(BaseModel):
    """OAuth connection model for DynamoDB storage."""
    pk: str  # user#12345#google
    provider: str  # google or microsoft
    access_token_encrypted: str
    refresh_token_encrypted: str
    scopes: List[str]
    expires_at: datetime
    created_at: datetime
    last_refresh: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }