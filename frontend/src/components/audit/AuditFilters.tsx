/**
 * Audit trail filtering component.
 */

import React from 'react';
import { 
  AuditTrailFilters, 
  AuditEventType, 
  AgentDecisionType, 
  ApprovalStatus 
} from '../../types/audit';

interface AuditFiltersProps {
  filters: AuditTrailFilters;
  onFiltersChange: (filters: AuditTrailFilters) => void;
  className?: string;
}

export const AuditFilters: React.FC<AuditFiltersProps> = ({
  filters,
  onFiltersChange,
  className = ''
}) => {
  const updateFilters = (updates: Partial<AuditTrailFilters>) => {
    onFiltersChange({ ...filters, ...updates });
  };

  const handleEventTypeToggle = (eventType: AuditEventType) => {
    const newEventTypes = filters.eventTypes.includes(eventType)
      ? filters.eventTypes.filter(t => t !== eventType)
      : [...filters.eventTypes, eventType];
    
    updateFilters({ eventTypes: newEventTypes });
  };

  const handleDecisionTypeToggle = (decisionType: AgentDecisionType) => {
    const newDecisionTypes = filters.decisionTypes.includes(decisionType)
      ? filters.decisionTypes.filter(t => t !== decisionType)
      : [...filters.decisionTypes, decisionType];
    
    updateFilters({ decisionTypes: newDecisionTypes });
  };

  const handleApprovalStatusToggle = (status: ApprovalStatus) => {
    const newStatuses = filters.approvalStatus.includes(status)
      ? filters.approvalStatus.filter(s => s !== status)
      : [...filters.approvalStatus, status];
    
    updateFilters({ approvalStatus: newStatuses });
  };

  const clearAllFilters = () => {
    onFiltersChange({
      dateRange: { start: null, end: null },
      eventTypes: [],
      decisionTypes: [],
      approvalStatus: [],
      confidenceRange: { min: 0, max: 1 },
      searchQuery: ''
    });
  };

  return (
    <div className={`audit-filters bg-gray-50 p-4 rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <button
          onClick={clearAllFilters}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Clear All
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Search Query */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => updateFilters({ searchQuery: e.target.value })}
            placeholder="Search rationale, tools, feedback..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={filters.dateRange.start?.toISOString().split('T')[0] || ''}
            onChange={(e) => updateFilters({
              dateRange: {
                ...filters.dateRange,
                start: e.target.value ? new Date(e.target.value) : null
              }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={filters.dateRange.end?.toISOString().split('T')[0] || ''}
            onChange={(e) => updateFilters({
              dateRange: {
                ...filters.dateRange,
                end: e.target.value ? new Date(e.target.value) : null
              }
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        {/* Confidence Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Confidence
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={filters.confidenceRange.min}
            onChange={(e) => updateFilters({
              confidenceRange: {
                ...filters.confidenceRange,
                min: parseFloat(e.target.value)
              }
            })}
            className="w-full"
          />
          <div className="text-xs text-gray-500 mt-1">
            {(filters.confidenceRange.min * 100).toFixed(0)}%
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Confidence
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={filters.confidenceRange.max}
            onChange={(e) => updateFilters({
              confidenceRange: {
                ...filters.confidenceRange,
                max: parseFloat(e.target.value)
              }
            })}
            className="w-full"
          />
          <div className="text-xs text-gray-500 mt-1">
            {(filters.confidenceRange.max * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Event Types */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Event Types
        </label>
        <div className="flex flex-wrap gap-2">
          {Object.values(AuditEventType).map(eventType => (
            <button
              key={eventType}
              onClick={() => handleEventTypeToggle(eventType)}
              className={`px-3 py-1 text-sm rounded-full border ${
                filters.eventTypes.includes(eventType)
                  ? 'bg-blue-100 border-blue-300 text-blue-800'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {eventType.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Decision Types */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Decision Types
        </label>
        <div className="flex flex-wrap gap-2">
          {Object.values(AgentDecisionType).map(decisionType => (
            <button
              key={decisionType}
              onClick={() => handleDecisionTypeToggle(decisionType)}
              className={`px-3 py-1 text-sm rounded-full border ${
                filters.decisionTypes.includes(decisionType)
                  ? 'bg-green-100 border-green-300 text-green-800'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {decisionType.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Approval Status */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Approval Status
        </label>
        <div className="flex flex-wrap gap-2">
          {Object.values(ApprovalStatus).map(status => (
            <button
              key={status}
              onClick={() => handleApprovalStatusToggle(status)}
              className={`px-3 py-1 text-sm rounded-full border ${
                filters.approvalStatus.includes(status)
                  ? 'bg-purple-100 border-purple-300 text-purple-800'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {status.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};