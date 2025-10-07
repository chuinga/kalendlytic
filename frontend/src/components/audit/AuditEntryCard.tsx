/**
 * Individual audit entry card component.
 */

import React, { useState } from 'react';
import { AuditLogEntry, ApprovalStatus, UserActionType } from '../../types/audit';
import { 
  formatAuditEntry, 
  getConfidenceColor, 
  formatCost, 
  getApprovalStatusColor,
  logUserAction,
  updateApprovalStatus 
} from '../../utils/audit';

interface AuditEntryCardProps {
  entry: AuditLogEntry;
  onApprovalUpdate: () => void;
  token: string;
  className?: string;
}

export const AuditEntryCard: React.FC<AuditEntryCardProps> = ({
  entry,
  onApprovalUpdate,
  token,
  className = ''
}) => {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [feedback, setFeedback] = useState('');
  
  const formatted = formatAuditEntry(entry);
  const confidenceColor = getConfidenceColor(entry.confidence_score);
  const approvalColor = getApprovalStatusColor(entry.approval_status);

  const handleApproval = async (status: ApprovalStatus) => {
    if (!entry.audit_id) return;
    
    try {
      setUpdating(true);
      
      // Update approval status
      await updateApprovalStatus(entry.audit_id, status, feedback, token);
      
      // Log user action
      await logUserAction(
        status === ApprovalStatus.APPROVED ? UserActionType.APPROVE_MEETING : UserActionType.REJECT_MEETING,
        { decision_id: entry.audit_id, status },
        entry.audit_id,
        feedback,
        token
      );
      
      onApprovalUpdate();
    } catch (error) {
      console.error('Failed to update approval:', error);
    } finally {
      setUpdating(false);
    }
  };

  const renderApprovalActions = () => {
    if (entry.approval_status !== ApprovalStatus.PENDING) return null;

    return (
      <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <h4 className="text-sm font-medium text-yellow-800 mb-2">
          Approval Required
        </h4>
        
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Optional feedback..."
          className="w-full p-2 border border-gray-300 rounded-md text-sm mb-3"
          rows={2}
        />
        
        <div className="flex space-x-2">
          <button
            onClick={() => handleApproval(ApprovalStatus.APPROVED)}
            disabled={updating}
            className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50"
          >
            {updating ? '...' : 'Approve'}
          </button>
          <button
            onClick={() => handleApproval(ApprovalStatus.REJECTED)}
            disabled={updating}
            className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            {updating ? '...' : 'Reject'}
          </button>
        </div>
      </div>
    );
  };

  const renderDetails = () => {
    if (!expanded) return null;

    return (
      <div className="mt-4 space-y-3">
        {entry.inputs && Object.keys(entry.inputs).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">Inputs</h4>
            <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
              {JSON.stringify(entry.inputs, null, 2)}
            </pre>
          </div>
        )}

        {entry.outputs && Object.keys(entry.outputs).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">Outputs</h4>
            <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto">
              {JSON.stringify(entry.outputs, null, 2)}
            </pre>
          </div>
        )}

        {entry.alternatives_considered && entry.alternatives_considered.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">
              Alternatives Considered ({entry.alternatives_considered.length})
            </h4>
            <div className="space-y-2">
              {entry.alternatives_considered.map((alt, index) => (
                <div key={index} className="text-xs bg-blue-50 p-2 rounded border">
                  <div className="font-medium">{alt.summary}</div>
                  <div className="text-gray-600">Score: {alt.score.toFixed(2)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {entry.tool_calls && entry.tool_calls.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">Tools Used</h4>
            <div className="flex flex-wrap gap-1">
              {entry.tool_calls.map((tool, index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}

        {entry.error_message && (
          <div>
            <h4 className="text-sm font-medium text-red-700 mb-1">Error</h4>
            <div className="text-xs bg-red-50 p-2 rounded border text-red-800">
              {entry.error_message}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`audit-entry-card bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <div className="text-2xl">{formatted.icon}</div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-1">
              <h3 className="text-sm font-medium text-gray-900 truncate">
                {formatted.title}
              </h3>
              
              {entry.confidence_score !== undefined && (
                <span 
                  className={`px-2 py-1 text-xs rounded-full bg-${confidenceColor}-100 text-${confidenceColor}-800`}
                >
                  {(entry.confidence_score * 100).toFixed(0)}%
                </span>
              )}
              
              {entry.approval_status && (
                <span 
                  className={`px-2 py-1 text-xs rounded-full bg-${approvalColor}-100 text-${approvalColor}-800`}
                >
                  {entry.approval_status.toUpperCase()}
                </span>
              )}
            </div>
            
            <p className="text-sm text-gray-600 mb-2">
              {formatted.description}
            </p>
            
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <span>{formatted.timestamp}</span>
              
              {entry.execution_time_ms && (
                <span>{entry.execution_time_ms}ms</span>
              )}
              
              {entry.cost_estimate && (
                <span>{formatCost(entry.cost_estimate.estimated_cost_usd)}</span>
              )}
              
              {entry.run_id && (
                <span className="font-mono">Run: {entry.run_id.slice(-8)}</span>
              )}
            </div>
          </div>
        </div>
        
        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-2 p-1 text-gray-400 hover:text-gray-600"
        >
          {expanded ? '▼' : '▶'}
        </button>
      </div>

      {renderDetails()}
      {renderApprovalActions()}
    </div>
  );
};