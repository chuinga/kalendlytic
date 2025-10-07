/**
 * API utilities for audit trail and agent decision logging.
 */

import { 
  AuditLogEntry, 
  AuditTrailQuery, 
  AuditTrailResponse, 
  DecisionAnalytics,
  AuditDashboardData,
  UserActionType,
  ApprovalStatus
} from '../types/audit';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch audit trail entries with filtering and pagination.
 */
export async function fetchAuditTrail(
  query: AuditTrailQuery,
  token: string
): Promise<AuditTrailResponse> {
  const params = new URLSearchParams();
  
  if (query.start_date) params.append('start_date', query.start_date);
  if (query.end_date) params.append('end_date', query.end_date);
  if (query.event_types?.length) {
    query.event_types.forEach(type => params.append('event_types', type));
  }
  if (query.limit) params.append('limit', query.limit.toString());
  if (query.offset) params.append('offset', query.offset.toString());

  const response = await fetch(
    `${API_BASE_URL}/api/audit/trail?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch audit trail: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch decision analytics for a user.
 */
export async function fetchDecisionAnalytics(
  days: number = 30,
  token: string
): Promise<DecisionAnalytics> {
  const response = await fetch(
    `${API_BASE_URL}/api/audit/analytics?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch decision analytics: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch audit dashboard data.
 */
export async function fetchAuditDashboard(token: string): Promise<AuditDashboardData> {
  const response = await fetch(
    `${API_BASE_URL}/api/audit/dashboard`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch audit dashboard: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Log a user action.
 */
export async function logUserAction(
  actionType: UserActionType,
  context: Record<string, any>,
  relatedDecisionId?: string,
  feedback?: string,
  token?: string
): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/api/audit/user-action`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action_type: actionType,
        context,
        related_decision_id: relatedDecisionId,
        feedback,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to log user action: ${response.statusText}`);
  }

  const result = await response.json();
  return result.audit_id;
}

/**
 * Update approval status for a decision.
 */
export async function updateApprovalStatus(
  decisionId: string,
  status: ApprovalStatus,
  feedback?: string,
  token?: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/audit/approval/${decisionId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status,
        feedback,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to update approval status: ${response.statusText}`);
  }
}

/**
 * Export audit trail data.
 */
export async function exportAuditTrail(
  query: AuditTrailQuery,
  format: 'csv' | 'json' = 'csv',
  token: string
): Promise<Blob> {
  const params = new URLSearchParams();
  
  if (query.start_date) params.append('start_date', query.start_date);
  if (query.end_date) params.append('end_date', query.end_date);
  if (query.event_types?.length) {
    query.event_types.forEach(type => params.append('event_types', type));
  }
  params.append('format', format);

  const response = await fetch(
    `${API_BASE_URL}/api/audit/export?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to export audit trail: ${response.statusText}`);
  }

  return response.blob();
}

/**
 * Format audit log entry for display.
 */
export function formatAuditEntry(entry: AuditLogEntry): {
  title: string;
  description: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high';
  icon: string;
} {
  const timestamp = new Date(entry.timestamp).toLocaleString();
  
  switch (entry.event_type) {
    case 'agent_decision':
      return {
        title: `Agent Decision: ${entry.decision_type?.replace('_', ' ').toUpperCase()}`,
        description: entry.enhanced_rationale || entry.rationale || 'No rationale provided',
        timestamp,
        severity: (entry.confidence_score || 1) < 0.5 ? 'high' : 'low',
        icon: '🤖'
      };
      
    case 'tool_invocation':
      return {
        title: `Tool: ${entry.tool_name}`,
        description: entry.success ? 'Executed successfully' : `Failed: ${entry.error_message}`,
        timestamp,
        severity: entry.success ? 'low' : 'high',
        icon: '🔧'
      };
      
    case 'user_action':
      return {
        title: `User Action: ${entry.action_type?.replace('_', ' ').toUpperCase()}`,
        description: entry.feedback || 'User performed action',
        timestamp,
        severity: 'medium',
        icon: '👤'
      };
      
    case 'approval_workflow':
      return {
        title: `Approval: ${entry.approval_status?.toUpperCase()}`,
        description: 'Approval workflow event',
        timestamp,
        severity: entry.approval_status === 'rejected' ? 'high' : 'medium',
        icon: '✅'
      };
      
    default:
      return {
        title: 'System Event',
        description: 'System event occurred',
        timestamp,
        severity: 'low',
        icon: '⚙️'
      };
  }
}

/**
 * Calculate confidence level color.
 */
export function getConfidenceColor(score?: number): string {
  if (!score) return 'gray';
  
  if (score >= 0.8) return 'green';
  if (score >= 0.6) return 'yellow';
  if (score >= 0.4) return 'orange';
  return 'red';
}

/**
 * Format cost estimate for display.
 */
export function formatCost(cost?: number): string {
  if (!cost) return '$0.00';
  
  if (cost < 0.01) {
    return `$${(cost * 1000).toFixed(2)}m`; // Show in millidollars
  }
  
  return `$${cost.toFixed(4)}`;
}

/**
 * Get approval status badge color.
 */
export function getApprovalStatusColor(status?: ApprovalStatus): string {
  switch (status) {
    case ApprovalStatus.APPROVED:
      return 'green';
    case ApprovalStatus.REJECTED:
      return 'red';
    case ApprovalStatus.PENDING:
      return 'yellow';
    case ApprovalStatus.TIMEOUT:
      return 'orange';
    case ApprovalStatus.CANCELLED:
      return 'gray';
    default:
      return 'gray';
  }
}