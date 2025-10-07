import React from 'react'
import { useConnections } from '@/hooks/useConnections'
import { ConnectionCard } from './ConnectionCard'
import { OAUTH_SCOPES } from '@/types/connections'

export function ConnectionsPage() {
  const {
    connections,
    loading,
    error,
    refreshConnections,
    connectProvider,
    disconnectProvider,
    reconnectProvider,
    testConnection,
    clearError
  } = useConnections()

  const connectedCount = connections.filter(conn => conn.connected).length
  const totalProviders = connections.length

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Calendar Connections</h1>
        <p className="text-gray-600">
          Connect your calendar and email accounts to enable AI-powered meeting scheduling.
        </p>
        
        <div className="mt-4 flex items-center space-x-4">
          <div className="bg-blue-50 px-3 py-1 rounded-full">
            <span className="text-sm font-medium text-blue-700">
              {connectedCount} of {totalProviders} connected
            </span>
          </div>
          
          <button
            onClick={refreshConnections}
            disabled={loading}
            className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh Status'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button
              onClick={clearError}
              className="text-red-400 hover:text-red-600"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {connections.map((connection) => (
          <ConnectionCard
            key={connection.provider}
            connection={connection}
            onConnect={connectProvider}
            onDisconnect={disconnectProvider}
            onReconnect={reconnectProvider}
            onTestConnection={testConnection}
            loading={loading}
          />
        ))}
      </div>

      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Required Permissions</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Google Permissions</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Calendar read/write access</li>
              <li>• Gmail send access</li>
              <li>• View calendar events</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Microsoft Permissions</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Calendar read/write access</li>
              <li>• Mail send access</li>
              <li>• View calendar events</li>
            </ul>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-700">
            <strong>Privacy Note:</strong> Your calendar and email data is encrypted and stored securely. 
            We only access the minimum permissions required for scheduling functionality.
          </p>
        </div>
      </div>

      <div className="mt-8 bg-yellow-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Connection Health</h2>
        <p className="text-sm text-gray-600 mb-4">
          Use the "Test Connection" button to verify that your calendar and email integrations are working properly.
          This will check if the AI agent can access your calendars and send emails on your behalf.
        </p>
        
        <div className="text-sm text-gray-600">
          <strong>What we test:</strong>
          <ul className="mt-1 space-y-1">
            <li>• Calendar API access and event reading</li>
            <li>• Email sending capabilities</li>
            <li>• Token validity and refresh status</li>
          </ul>
        </div>
      </div>
    </div>
  )
}