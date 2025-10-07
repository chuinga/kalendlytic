/**
 * Type definitions for audit trail and agent decision logging.
 */

export enum AuditEventType {
  AGENT_DECISION = 'agent_decision',
  TOOL_INVOCATION = 'tool_invocation',
  USER_ACTION = 'user_action',
  APPROVAL_WORKFLOW = 'approval_workflow',
  ERROR_HANDLING = 'error_handling',
  SYSTEM_EVENT = 'system_event'
}

export enum AgentDecisionType {
  SCHEDULING = 'scheduling',
  CONFLICT_RESOLUTION = 'conflict_resolution',
  PRIORITIZATION = 'prioritization',
  PREFERENCE_EXTRACTION = 'preference_extraction',
  TOOL_INVOCATION = 'tool_invocation',
  ERROR_HANDLING = 'error_handling'
}

export enum UserActionType {
  APPROVE_MEETING = 'approve_meeting',
  REJECT_MEETING = 'reject_meeting',
  MODIFY_PREFERENCES = 'modify_preferences',
  OVERRIDE_DECISION = 'override_decision',
  CANCEL_REQUEST = 'cancel_request',
  PROVIDE_FEEDBACK = 'provide_feedback'
}

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  TIMEOUT = 'timeout',
  CANCELLED = 'cancelled'
}

export interface CostEstimate {
  bedrock_tokens: number;
  estimated_cost_usd: number;
}

export interface AlternativeOption {
  summary: string;
  score: number;
  details?: Record<string, any>;
}

export interface AuditLogEntry {
  audit_id: string;
  pk: string;
  sk: string;
  event_type: AuditEventType;
  timestamp: string;
  created_at: string;
  run_id?: string;
  
  // Agent decision specific fields
  decision_type?: AgentDecisionType;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  rationale?: string;
  enhanced_rationale?: string;
  confidence_score?: number;
  alternatives_considered?: AlternativeOption[];
  alternatives_count?: number;
  tool_calls?: string[];
  cost_estimate?: CostEstimate;
  requires_approval?: boolean;
  approval_status?: ApprovalStatus;
  
  // Tool invocation specific fields
  tool_name?: string;
  execution_time_ms?: number;
  success?: boolean;
  error_message?: string;
  
  // User action specific fields
  action_type?: UserActionType;
  context?: Record<string, any>;
  related_decision_id?: string;
  feedback?: string;
  
  // Approval workflow specific fields
  decision_id?: string;
  approver_id?: string;
  approval_context?: Record<string, any>;
}

export interface AuditTrailQuery {
  user_id: string;
  start_date?: string;
  end_date?: string;
  event_types?: AuditEventType[];
  limit?: number;
  offset?: number;
}

export interface DecisionAnalytics {
  total_decisions: number;
  period_days: number;
  decision_types: Record<string, number>;
  average_confidence: number;
  approval_rate: number;
  cost_summary: {
    total_cost_usd: number;
    average_cost_per_decision_usd: number;
  };
}

export interface AuditTrailFilters {
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  eventTypes: AuditEventType[];
  decisionTypes: AgentDecisionType[];
  approvalStatus: ApprovalStatus[];
  confidenceRange: {
    min: number;
    max: number;
  };
  searchQuery: string;
}

export interface AuditTrailResponse {
  entries: AuditLogEntry[];
  total_count: number;
  has_more: boolean;
  next_offset?: number;
}

export interface ToolInvocationSummary {
  tool_name: string;
  total_calls: number;
  success_rate: number;
  average_execution_time_ms: number;
  total_cost_usd: number;
}

export interface UserActionSummary {
  action_type: UserActionType;
  count: number;
  last_performed: string;
}

export interface AuditDashboardData {
  recent_decisions: AuditLogEntry[];
  analytics: DecisionAnalytics;
  tool_usage: ToolInvocationSummary[];
  user_actions: UserActionSummary[];
  pending_approvals: AuditLogEntry[];
}