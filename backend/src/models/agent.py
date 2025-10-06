"""
Agent execution and audit trail data models.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class ToolCall(BaseModel):
    """Individual tool call information."""
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None


class CostEstimate(BaseModel):
    """Cost estimation for agent execution."""
    bedrock_tokens: int
    estimated_cost_usd: float


class AgentRun(BaseModel):
    """Agent execution run model for DynamoDB storage."""
    pk: str  # run#abc123
    user_id: str
    request_type: str
    inputs: Dict[str, Any]
    tools_used: List[str]
    outputs: Dict[str, Any]
    cost_estimate: CostEstimate
    execution_time_ms: int
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditLog(BaseModel):
    """Audit log entry model for DynamoDB storage."""
    pk: str  # user#12345
    sk: str  # timestamp#step
    run_id: str
    step: str
    action: str
    rationale: str
    tool_calls: List[str]
    decision: str
    alternatives_proposed: int = 0
    user_action_required: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }