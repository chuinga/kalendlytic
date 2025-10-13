import React from 'react'
import Link from 'next/link'
import { useConnections } from '@/hooks/useConnections'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { cn } from '@/lib/utils'
import { Wifi, WifiOff, AlertTriangle } from 'lucide-react'

interface ConnectionStatusProps {
  showDetails?: boolean
  variant?: 'compact' | 'detailed'
  className?: string
}

export function ConnectionStatus({ 
  showDetails = false, 
  variant = 'compact',
  className = '' 
}: ConnectionStatusProps) {
  const { connections, loading, error } = useConnections()

  if (loading) {
    return (
      <div className={cn('animate-pulse', className)}>
        <div className="h-6 bg-gray-200 rounded-lg w-32"></div>
      </div>
    )
  }

  // Handle API errors gracefully
  if (error || connections.length === 0) {
    if (variant === 'compact') {
      return (
        <div className={cn('flex items-center space-x-2', className)}>
          <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
          <span className="text-sm font-medium text-gray-700">
            API Offline
          </span>
        </div>
      )
    }
    
    return (
      <div className={cn('bg-yellow-50 rounded-lg p-3 border border-yellow-200', className)}>
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-yellow-100 text-yellow-600">
            <WifiOff className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <span className="text-sm font-medium text-yellow-800">
              Backend API Offline
            </span>
            <p className="text-xs text-yellow-600 mt-1">
              Calendar connections unavailable
            </p>
          </div>
        </div>
      </div>
    )
  }

  const connectedCount = connections.filter(conn => conn.connected).length
  const totalProviders = connections.length
  const hasErrors = connections.some(conn => conn.status === 'error' || conn.status === 'expired')

  const getStatus = () => {
    if (hasErrors) return 'error'
    if (connectedCount === 0) return 'offline'
    if (connectedCount < totalProviders) return 'connecting'
    return 'online'
  }

  const getStatusText = () => {
    if (connectedCount === 0) return 'No connections'
    if (hasErrors) return 'Connection issues'
    if (connectedCount < totalProviders) return 'Partial connections'
    return 'All connected'
  }

  const getStatusIcon = () => {
    const status = getStatus()
    if (status === 'offline') return WifiOff
    if (status === 'error' || status === 'connecting') return AlertTriangle
    return Wifi
  }

  const StatusIcon = getStatusIcon()
  const status = getStatus()

  if (variant === 'compact') {
    return (
      <div className={cn('flex items-center space-x-2', className)}>
        <StatusBadge status={status} size="sm" />
        <span className="text-sm font-medium text-neutral-700">
          {connectedCount}/{totalProviders}
        </span>
      </div>
    )
  }

  return (
    <div className={cn('bg-white/60 backdrop-blur-sm rounded-xl p-3 border border-white/40', className)}>
      <div className="flex items-center space-x-3">
        <div className={cn(
          'w-8 h-8 rounded-lg flex items-center justify-center',
          status === 'online' ? 'bg-success/10 text-success' :
          status === 'error' ? 'bg-error/10 text-error' :
          status === 'connecting' ? 'bg-warning/10 text-warning' :
          'bg-neutral-100 text-neutral-500'
        )}>
          <StatusIcon className="w-4 h-4" />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-neutral-800">
              {getStatusText()}
            </span>
            <span className="text-xs text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded-full">
              {connectedCount}/{totalProviders}
            </span>
          </div>
          
          {showDetails && (
            <div className="mt-2 space-y-1">
              {connections.map((connection) => (
                <div key={connection.provider} className="flex items-center justify-between text-xs">
                  <span className="capitalize text-neutral-600">{connection.provider}</span>
                  <StatusBadge 
                    status={connection.connected ? 'online' : 'offline'} 
                    size="sm" 
                  />
                </div>
              ))}
              
              <Link 
                href="/connections"
                className="inline-flex items-center mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium transition-colors duration-200"
              >
                Manage connections →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}