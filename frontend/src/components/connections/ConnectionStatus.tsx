import React from 'react'
import Link from 'next/link'
import { useConnections } from '@/hooks/useConnections'

interface ConnectionStatusProps {
  showDetails?: boolean
  className?: string
}

export function ConnectionStatus({ showDetails = false, className = '' }: ConnectionStatusProps) {
  const { connections, loading } = useConnections()

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-4 bg-gray-200 rounded w-32"></div>
      </div>
    )
  }

  const connectedCount = connections.filter(conn => conn.connected).length
  const totalProviders = connections.length
  const hasErrors = connections.some(conn => conn.status === 'error' || conn.status === 'expired')

  const getStatusColor = () => {
    if (hasErrors) return 'text-yellow-600'
    if (connectedCount === 0) return 'text-red-600'
    if (connectedCount < totalProviders) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getStatusText = () => {
    if (connectedCount === 0) return 'No connections'
    if (hasErrors) return 'Connection issues'
    if (connectedCount < totalProviders) return 'Partial connections'
    return 'All connected'
  }

  return (
    <div className={className}>
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${getStatusColor().replace('text-', 'bg-')}`}></div>
        <span className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
        <span className="text-sm text-gray-500">
          ({connectedCount}/{totalProviders})
        </span>
      </div>

      {showDetails && (
        <div className="mt-2 space-y-1">
          {connections.map((connection) => (
            <div key={connection.provider} className="flex items-center justify-between text-xs">
              <span className="capitalize">{connection.provider}</span>
              <span className={`${
                connection.connected ? 'text-green-600' : 'text-gray-400'
              }`}>
                {connection.connected ? '✓' : '○'}
              </span>
            </div>
          ))}
          
          <Link 
            href="/connections"
            className="inline-block mt-2 text-xs text-blue-600 hover:text-blue-700"
          >
            Manage connections →
          </Link>
        </div>
      )}
    </div>
  )
}