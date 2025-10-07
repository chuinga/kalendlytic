"""
API handlers for audit trail and agent decision logging.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..services.audit_service import AuditService, UserActionType, ApprovalStatus
from ..utils.auth import get_current_user
from ..utils.logging import create_agent_logger

router = APIRouter(prefix="/api/audit", tags=["audit"])
audit_service = AuditService()
logger = create_agent_logger('audit_handler')


class UserActionRequest(BaseModel):
    """Request model for logging user actions."""
    action_type: UserActionType
    context: Dict[str, Any]
    related_decision_id: Optional[str] = None
    feedback: Optional[str] = None


class ApprovalUpdateRequest(BaseModel):
    """Request model for updating approval status."""
    status: ApprovalStatus
    feedback: Optional[str] = None


@router.get("/trail")
async def get_audit_trail(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: List[str] = Query([]),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get audit trail entries for the current user.
    
    Args:
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        event_types: List of event types to filter by
        limit: Maximum number of entries to return
        offset: Offset for pagination
        current_user: Current authenticated user
        
    Returns:
        Paginated audit trail entries
    """
    try:
        user_id = current_user['user_id']
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Convert event types
        from ..services.audit_service import AuditEventType
        parsed_event_types = []
        for event_type in event_types:
            try:
                parsed_event_types.append(AuditEventType(event_type))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")
        
        # Get audit trail
        entries = audit_service.get_audit_trail(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            event_types=parsed_event_types if parsed_event_types else None,
            limit=limit + 1  # Get one extra to check if there are more
        )
        
        # Check if there are more entries
        has_more = len(entries) > limit
        if has_more:
            entries = entries[:limit]
        
        return {
            "entries": entries,
            "total_count": len(entries),
            "has_more": has_more,
            "next_offset": offset + limit if has_more else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit trail")


@router.get("/analytics")
async def get_decision_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get decision analytics for the current user.
    
    Args:
        days: Number of days to analyze
        current_user: Current authenticated user
        
    Returns:
        Decision analytics summary
    """
    try:
        user_id = current_user['user_id']
        
        analytics = audit_service.get_decision_analytics(
            user_id=user_id,
            days=days
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get decision analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.get("/dashboard")
async def get_audit_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get audit dashboard data for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dashboard data including recent decisions, analytics, and summaries
    """
    try:
        user_id = current_user['user_id']
        
        # Get recent decisions (last 7 days)
        recent_start = datetime.utcnow() - timedelta(days=7)
        from ..services.audit_service import AuditEventType
        
        recent_decisions = audit_service.get_audit_trail(
            user_id=user_id,
            start_date=recent_start,
            event_types=[AuditEventType.AGENT_DECISION],
            limit=10
        )
        
        # Get analytics for last 30 days
        analytics = audit_service.get_decision_analytics(user_id=user_id, days=30)
        
        # Get pending approvals
        pending_approvals = [
            entry for entry in recent_decisions 
            if entry.get('approval_status') == ApprovalStatus.PENDING.value
        ]
        
        # Get tool usage summary
        tool_entries = audit_service.get_audit_trail(
            user_id=user_id,
            start_date=recent_start,
            event_types=[AuditEventType.TOOL_INVOCATION],
            limit=100
        )
        
        tool_usage = {}
        for entry in tool_entries:
            tool_name = entry.get('tool_name', 'unknown')
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {
                    'tool_name': tool_name,
                    'total_calls': 0,
                    'success_count': 0,
                    'total_execution_time': 0,
                    'total_cost': 0.0
                }
            
            tool_usage[tool_name]['total_calls'] += 1
            if entry.get('success', False):
                tool_usage[tool_name]['success_count'] += 1
            
            exec_time = entry.get('execution_time_ms', 0)
            tool_usage[tool_name]['total_execution_time'] += exec_time
        
        # Calculate tool usage metrics
        tool_summaries = []
        for tool_data in tool_usage.values():
            tool_summaries.append({
                'tool_name': tool_data['tool_name'],
                'total_calls': tool_data['total_calls'],
                'success_rate': tool_data['success_count'] / tool_data['total_calls'] if tool_data['total_calls'] > 0 else 0,
                'average_execution_time_ms': tool_data['total_execution_time'] / tool_data['total_calls'] if tool_data['total_calls'] > 0 else 0,
                'total_cost_usd': tool_data['total_cost']
            })
        
        # Get user actions summary
        user_actions = audit_service.get_audit_trail(
            user_id=user_id,
            start_date=recent_start,
            event_types=[AuditEventType.USER_ACTION],
            limit=100
        )
        
        action_summaries = {}
        for entry in user_actions:
            action_type = entry.get('action_type', 'unknown')
            if action_type not in action_summaries:
                action_summaries[action_type] = {
                    'action_type': action_type,
                    'count': 0,
                    'last_performed': entry.get('timestamp')
                }
            
            action_summaries[action_type]['count'] += 1
            # Keep the most recent timestamp
            if entry.get('timestamp') > action_summaries[action_type]['last_performed']:
                action_summaries[action_type]['last_performed'] = entry.get('timestamp')
        
        return {
            "recent_decisions": recent_decisions,
            "analytics": analytics,
            "tool_usage": tool_summaries,
            "user_actions": list(action_summaries.values()),
            "pending_approvals": pending_approvals
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.post("/user-action")
async def log_user_action(
    request: UserActionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Log a user action.
    
    Args:
        request: User action details
        current_user: Current authenticated user
        
    Returns:
        Audit log entry ID
    """
    try:
        user_id = current_user['user_id']
        
        audit_id = audit_service.log_user_action(
            user_id=user_id,
            action_type=request.action_type,
            context=request.context,
            related_decision_id=request.related_decision_id,
            feedback=request.feedback
        )
        
        return {"audit_id": audit_id}
        
    except Exception as e:
        logger.error(f"Failed to log user action: {e}")
        raise HTTPException(status_code=500, detail="Failed to log user action")


@router.put("/approval/{decision_id}")
async def update_approval_status(
    decision_id: str,
    request: ApprovalUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update approval status for a decision.
    
    Args:
        decision_id: ID of the decision to update
        request: Approval update details
        current_user: Current authenticated user
    """
    try:
        user_id = current_user['user_id']
        
        # Log the approval workflow event
        audit_service.log_approval_workflow(
            user_id=user_id,
            decision_id=decision_id,
            status=request.status,
            approver_id=user_id,
            approval_context={"feedback": request.feedback} if request.feedback else None
        )
        
        return {"status": "updated"}
        
    except Exception as e:
        logger.error(f"Failed to update approval status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update approval status")


@router.get("/export")
async def export_audit_trail(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: List[str] = Query([]),
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Export audit trail data.
    
    Args:
        start_date: Start date filter (ISO format)
        end_date: End date filter (ISO format)
        event_types: List of event types to filter by
        format: Export format (csv or json)
        current_user: Current authenticated user
        
    Returns:
        Exported audit trail data
    """
    try:
        user_id = current_user['user_id']
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Convert event types
        from ..services.audit_service import AuditEventType
        parsed_event_types = []
        for event_type in event_types:
            try:
                parsed_event_types.append(AuditEventType(event_type))
            except ValueError:
                continue
        
        # Get all matching entries (no limit for export)
        entries = audit_service.get_audit_trail(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
            event_types=parsed_event_types if parsed_event_types else None,
            limit=10000  # Large limit for export
        )
        
        if format == "json":
            def generate_json():
                yield json.dumps({"entries": entries}, indent=2, default=str)
            
            return StreamingResponse(
                generate_json(),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=audit_trail_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.json"}
            )
        
        else:  # CSV format
            import csv
            import io
            
            def generate_csv():
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                headers = [
                    'timestamp', 'event_type', 'decision_type', 'tool_name', 
                    'action_type', 'rationale', 'confidence_score', 'success',
                    'execution_time_ms', 'cost_usd', 'approval_status'
                ]
                writer.writerow(headers)
                
                # Write data
                for entry in entries:
                    row = [
                        entry.get('timestamp', ''),
                        entry.get('event_type', ''),
                        entry.get('decision_type', ''),
                        entry.get('tool_name', ''),
                        entry.get('action_type', ''),
                        entry.get('rationale', ''),
                        entry.get('confidence_score', ''),
                        entry.get('success', ''),
                        entry.get('execution_time_ms', ''),
                        entry.get('cost_estimate', {}).get('estimated_cost_usd', '') if entry.get('cost_estimate') else '',
                        entry.get('approval_status', '')
                    ]
                    writer.writerow(row)
                
                output.seek(0)
                return output.getvalue()
            
            return StreamingResponse(
                iter([generate_csv()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=audit_trail_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
            )
        
    except Exception as e:
        logger.error(f"Failed to export audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit trail")