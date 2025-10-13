/**
 * Audit trail page with dashboard and detailed trail view.
 */

import React, { useState, useEffect } from 'react';
import { GetServerSideProps } from 'next';
import Head from 'next/head';
import { useAuth } from '../contexts/AuthContext';
import { AuthService } from '../utils/auth';
import { AuditDashboard } from '../components/audit/AuditDashboard';
import { AuditTrail } from '../components/audit/AuditTrail';

type TabType = 'dashboard' | 'trail';

interface AuditPageProps {
  initialTab?: TabType;
}

const AuditPage: React.FC<AuditPageProps> = ({ initialTab = 'dashboard' }) => {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>(initialTab);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const getToken = async () => {
      if (isAuthenticated) {
        try {
          const tokens = await AuthService.getTokens();
          if (tokens) {
            setToken(tokens.accessToken);
          }
        } catch (error) {
          console.error('Failed to get token:', error);
        }
      }
    };
    getToken();
  }, [isAuthenticated]);

  if (!user || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Authentication Required
          </h2>
          <p className="text-gray-600">
            Please log in to view the audit trail.
          </p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'dashboard' as TabType, name: 'Dashboard', icon: '📊' },
    { id: 'trail' as TabType, name: 'Audit Trail', icon: '📋' }
  ];

  return (
    <>
      <Head>
        <title>Audit Trail - Meeting Scheduling Agent</title>
        <meta name="description" content="View agent decisions, tool usage, and audit trail" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Audit & Analytics
            </h1>
            <p className="text-gray-600">
              Monitor agent decisions, track performance, and review system activity
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="mb-8">
            <nav className="flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'dashboard' && (
              <AuditDashboard token={token || ''} />
            )}
            
            {activeTab === 'trail' && (
              <AuditTrail 
                userId={user.id}
                token={token || ''}
              />
            )}
          </div>

          {/* Export Actions */}
          <div className="mt-8 flex justify-end">
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  // Implement CSV export
                  window.open(`/api/audit/export?format=csv`, '_blank');
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Export CSV
              </button>
              <button
                onClick={() => {
                  // Implement JSON export
                  window.open(`/api/audit/export?format=json`, '_blank');
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Export JSON
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { tab } = context.query;
  
  return {
    props: {
      initialTab: tab === 'trail' ? 'trail' : 'dashboard'
    }
  };
};

export default AuditPage;