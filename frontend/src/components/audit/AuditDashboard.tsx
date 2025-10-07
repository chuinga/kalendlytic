/**
 * Audit dashboard component showing analytics and recent activity.
 */

import React, { useState, useEffect } from 'react';
import { AuditDashboardData, DecisionAnalytics } from '../../types/audit';
import { fetchAuditDashboard } from '../../utils/audit';
import { AuditEntryCard } from './AuditEntryCard';

interface AuditDashboardProps {
  token: string;
  className?: string;
}

export const AuditDashboard: React.FC<AuditDashboardProps> = ({
  token,
  className = ''
}) => {
  const [dashboardData, setDashboardData] = useState<AuditDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, [token]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await fetchAuditDashboard(token);
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const renderAnalyticsCard = (analytics: DecisionAnalytics) => (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Decision Analytics (Last {analytics.period_days} days)
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {analytics.total_decisions}
          </div>
          <div className="text-sm text-gray-600">Total Decisions</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {(analytics.average_confidence * 100).toFixed(0)}%
          </div>
          <div className="text-sm text-gray-600">Avg Confidence</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {(analytics.approval_rate * 100).toFixed(0)}%
          </div>
          <div className="text-sm text-gray-600">Approval Rate</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            ${analytics.cost_summary.total_cost_usd.toFixed(4)}
          </div>
          <div className="text-sm text-gray-600">Total Cost</div>
        </div>
      </div>
      
      {Object.keys(analytics.decision_types).length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Decision Types</h4>
          <div className="space-y-2">
            {Object.entries(analytics.decision_types).map(([type, count]) => (
              <div key={type} className="flex justify-between items-center">
                <span className="text-sm text-gray-600 capitalize">
                  {type.replace('_', ' ')}
                </span>
                <span className="text-sm font-medium">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderToolUsage = () => {
    if (!dashboardData?.tool_usage?.length) return null;

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Tool Usage (Last 7 days)
        </h3>
        
        <div className="space-y-3">
          {dashboardData.tool_usage.map((tool, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium text-gray-900">{tool.tool_name}</div>
                <div className="text-sm text-gray-600">
                  {tool.total_calls} calls • {(tool.success_rate * 100).toFixed(0)}% success
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">
                  {tool.average_execution_time_ms.toFixed(0)}ms avg
                </div>
                <div className="text-xs text-gray-500">
                  ${tool.total_cost_usd.toFixed(4)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderUserActions = () => {
    if (!dashboardData?.user_actions?.length) return null;

    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Recent User Actions
        </h3>
        
        <div className="space-y-2">
          {dashboardData.user_actions.map((action, index) => (
            <div key={index} className="flex justify-between items-center">
              <span className="text-sm text-gray-600 capitalize">
                {action.action_type.replace('_', ' ')}
              </span>
              <div className="text-right">
                <div className="text-sm font-medium">{action.count}</div>
                <div className="text-xs text-gray-500">
                  {new Date(action.last_performed).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`audit-dashboard ${className}`}>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`audit-dashboard ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-400">⚠️</div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Error loading dashboard
              </h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className={`audit-dashboard ${className}`}>
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📊</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No dashboard data available
          </h3>
        </div>
      </div>
    );
  }

  return (
    <div className={`audit-dashboard ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Audit Dashboard
        </h2>
        <p className="text-gray-600">
          Overview of agent decisions, tool usage, and user interactions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {renderAnalyticsCard(dashboardData.analytics)}
        {renderToolUsage()}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {renderUserActions()}
        
        {dashboardData.pending_approvals.length > 0 && (
          <div className="lg:col-span-2">
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Pending Approvals ({dashboardData.pending_approvals.length})
              </h3>
              
              <div className="space-y-3">
                {dashboardData.pending_approvals.slice(0, 3).map((entry, index) => (
                  <AuditEntryCard
                    key={index}
                    entry={entry}
                    onApprovalUpdate={loadDashboardData}
                    token={token}
                    className="border-yellow-200 bg-yellow-50"
                  />
                ))}
              </div>
              
              {dashboardData.pending_approvals.length > 3 && (
                <div className="mt-3 text-center">
                  <span className="text-sm text-gray-500">
                    +{dashboardData.pending_approvals.length - 3} more pending approvals
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {dashboardData.recent_decisions.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Recent Decisions (Last 7 days)
          </h3>
          
          <div className="space-y-4">
            {dashboardData.recent_decisions.slice(0, 5).map((entry, index) => (
              <AuditEntryCard
                key={index}
                entry={entry}
                onApprovalUpdate={loadDashboardData}
                token={token}
              />
            ))}
          </div>
          
          {dashboardData.recent_decisions.length > 5 && (
            <div className="mt-4 text-center">
              <button className="text-blue-600 hover:text-blue-800 text-sm">
                View all recent decisions →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};