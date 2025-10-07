import React, { useState } from 'react'
import { OAuthConnectionStatus, OAuthProvider, ConnectionHealthCheck } from '@/types/connections'

interface ConnectionCardProps {
  connection: OAuthConnectionStatus
  onConnect: (provider: OAuthProvider) => Promise<void>
  onDisconnect: (provider: OAuthProvider) => Promise<void>
  onReconnect: (provider: OAuthProvider) => Promise<void>
  onTestConnection: (provider: OAuthProvider) => Promise<ConnectionHealthCheck>
  loading?: boolean
}

const PROVIDER_CONFIG = {
  google: {
    name: 'Google',
    icon: '🔍',
    color: 'bg-blue-500',
    description: 'Connect your Gmail and Google Calendar'
  },
  microsoft: {
    name: 'Microsoft',
    icon: '🏢',
    color: 'bg-blue-600',
    description: 'Connect your Outlook and Microsoft Calendar'
  }
}

export function ConnectionCard({ 
  connection, 
  onConnect, 
  onDisconnect, 
  onReconnect, 
  onTestConnection,
  loading = false 
}: ConnectionCardProps) {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<ConnectionHealthCheck | null>(null)
  
  const config = PROVIDER_CONFIG[connection.provider]
  const isConnected = connection.connected && connection.status === 'connected'
  const hasError = connection.status === 'error' || connection.status === 'expired'

  const handleConnect = async () => {
    await onConnect(connection.provider)
  }

  const handleDisconnect = async () => {
    if (window.confirm(`Are you sure you want to disconnect ${config.name}?`)) {
      await onDisconnect(connection.provider)
    }
  }

  const handleReconnect = async () => {
    await onReconnect(connection.provider)
  }

  const handleTestConnection = async () => {
    try {
      setTesting(true)
      const result = await onTestConnection(connection.provider)
      setTestResult(result)
    } catch (error) {
      console.error('Test connection failed:', error)
    } finally {
      setTesting(false)
    }
  }

  const getStatusColor = () => {
    switch (connection.status) {
      case 'connected':
        return 'text-green-600'
      case 'error':
      case 'expired':
        return 'text-red-600'
      case 'disconnected':
      default:
        return 'text-gray-500'
    }
  }

  const getStatusText = () => {
    switch (connection.status) {
      case 'connected':
        return 'Connected'
      case 'error':
        return 'Error'
      case 'expired':
        return 'Expired'
      case 'disconnected':
      default:
        return 'Not Connected'
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-12 h-12 rounded-lg ${config.color} flex items-center justify-center text-white text-xl`}>
            {config.icon}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{config.name}</h3>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>
        </div>
        
        <div className="text-right">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
      </div>

      {isConnected && (
        <div className="mt-4 space-y-2">
          <div className="text-sm text-gray-600">
            <strong>Email:</strong> {connection.email}
          </div>
          {connection.lastRefresh && (
            <div className="text-sm text-gray-600">
              <strong>Last Refresh:</strong> {new Date(connection.lastRefresh).toLocaleString()}
            </div>
          )}
          {connection.expiresAt && (
            <div className="text-sm text-gray-600">
              <strong>Expires:</strong> {new Date(connection.expiresAt).toLocaleString()}
            </div>
          )}
        </div>
      )}

      {hasError && connection.error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{connection.error}</p>
        </div>
      )}

      {testResult && (
        <div className="mt-4 p-3 bg-gray-50 border border-gray-200 rounded-md">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Connection Test Results</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span>Calendar Access:</span>
              <span className={testResult.calendar.accessible ? 'text-green-600' : 'text-red-600'}>
                {testResult.calendar.accessible ? '✓ Working' : '✗ Failed'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Email Access:</span>
              <span className={testResult.email.accessible ? 'text-green-600' : 'text-red-600'}>
                {testResult.email.accessible ? '✓ Working' : '✗ Failed'}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Last checked: {new Date(testResult.lastChecked).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 flex space-x-3">
        {!connection.connected ? (
          <button
            onClick={handleConnect}
            disabled={loading}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Connecting...' : `Connect ${config.name}`}
          </button>
        ) : (
          <>
            <button
              onClick={handleTestConnection}
              disabled={testing || loading}
              className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            
            {hasError ? (
              <button
                onClick={handleReconnect}
                disabled={loading}
                className="flex-1 bg-yellow-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Reconnecting...' : 'Reconnect'}
              </button>
            ) : (
              <button
                onClick={handleDisconnect}
                disabled={loading}
                className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Disconnecting...' : 'Disconnect'}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}