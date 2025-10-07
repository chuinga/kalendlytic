/**
 * Audit trail display component with filtering and search capabilities.
 */

import React, { useState, useEffect } from 'react';
import { 
  AuditLogEntry, 
  AuditTrailFilters, 
  AuditEventType,
  AgentDecisionType,
  ApprovalStatus 
} from '../../types/audit';
import { fetchAuditTrail } from '../../utils/audit';
import { AuditEntryCard } from './AuditEntryCard';
import { AuditFilters } from './AuditFilters';

interface AuditTrailProps {
  userId: string;
  token: string;
  className?: string;
}

export const AuditTrail: React.FC<AuditTrailProps> = ({
  userId,
  token,
  className = ''
}) => {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  
  const [filters, setFilters] = useState<AuditTrailFilters>({
    dateRange: { start: null, end: null },
    eventTypes: [],
    decisionTypes: [],
    approvalStatus: [],
    confidenceRange: { min: 0, max: 1 },
    searchQuery: ''
  });

  const loadEntries = async (reset = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const query = {
        user_id: userId,
        start_date: filters.dateRange.start?.toISOString(),
        end_date: filters.dateRange.end?.toISOString(),
        event_types: filters.eventTypes.length > 0 ? filters.eventTypes : undefined,
        limit: 20,
        offset: reset ? 0 : offset
      };

      const response = await fetchAuditTrail(query, token);
      
      if (reset) {
        setEntries(response.entries);
        setOffset(response.entries.length);
      } else {
        setEntries(prev => [...prev, ...response.entries]);
        setOffset(prev => prev + response.entries.length);
      }
      
      setHasMore(response.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEntries(true);
  }, [filters, userId, token]);

  const handleLoadMore = () => {
    if (!loading && hasMore) {
      loadEntries(false);
    }
  };

  const filteredEntries = entries.filter(entry => {
    // Apply client-side filters for better UX
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      const searchableText = [
        entry.rationale,
        entry.enhanced_rationale,
        entry.tool_name,
        entry.feedback
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(query)) {
        return false;
      }
    }

    if (filters.decisionTypes.length > 0 && entry.decision_type) {
      if (!filters.decisionTypes.includes(entry.decision_type)) {
        return false;
      }
    }

    if (filters.approvalStatus.length > 0 && entry.approval_status) {
      if (!filters.approvalStatus.includes(entry.approval_status)) {
        return false;
      }
    }

    if (entry.confidence_score !== undefined) {
      if (entry.confidence_score < filters.confidenceRange.min || 
          entry.confidence_score > filters.confidenceRange.max) {
        return false;
      }
    }

    return true;
  });

  return (
    <div className={`audit-trail ${className}`}>
      <div className="audit-trail-header">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Audit Trail
        </h2>
        <p className="text-gray-600 mb-6">
          Track all agent decisions, tool invocations, and user actions
        </p>
      </div>

      <AuditFilters 
        filters={filters}
        onFiltersChange={setFilters}
        className="mb-6"
      />

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="text-red-400">⚠️</div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading audit trail
              </h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="audit-entries">
        {filteredEntries.length === 0 && !loading ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📋</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No audit entries found
            </h3>
            <p className="text-gray-600">
              Try adjusting your filters or check back later
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredEntries.map((entry, index) => (
              <AuditEntryCard 
                key={`${entry.audit_id}-${index}`}
                entry={entry}
                onApprovalUpdate={() => loadEntries(true)}
                token={token}
              />
            ))}
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {hasMore && !loading && (
          <div className="text-center py-6">
            <button
              onClick={handleLoadMore}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Load More
            </button>
          </div>
        )}
      </div>
    </div>
  );
};