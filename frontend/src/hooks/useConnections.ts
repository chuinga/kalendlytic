import { useState, useEffect, useCallback } from 'react'
import { ConnectionsService } from '@/utils/connections'
import { 
  OAuthProvider, 
  OAuthConnectionStatus, 
  OAuthConnection,
  ConnectionHealthCheck
} from '@/types/connections'

interface UseConnectionsReturn {
  connections: OAuthConnectionStatus[]
  loading: boolean
  error: string | null
  refreshConnections: () => Promise<void>
  connectProvider: (provider: OAuthProvider) => Promise<void>
  disconnectProvider: (provider: OAuthProvider) => Promise<void>
  reconnectProvider: (provider: OAuthProvider) => Promise<void>
  testConnection: (provider: OAuthProvider) => Promise<ConnectionHealthCheck>
  clearError: () => void
}

export function useConnections(): UseConnectionsReturn {
  const [connections, setConnections] = useState<OAuthConnectionStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const refreshConnections = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const connectionsData = await ConnectionsService.getConnections()
      setConnections(connectionsData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const connectProvider = useCallback(async (provider: OAuthProvider) => {
    try {
      setError(null)
      const authData = await ConnectionsService.startOAuthFlow(provider)
      
      // Redirect to OAuth provider
      ConnectionsService.getOAuthRedirectUrl(authData.authUrl)
    } catch (err: any) {
      setError(err.message)
    }
  }, [])

  const disconnectProvider = useCallback(async (provider: OAuthProvider) => {
    try {
      setError(null)
      await ConnectionsService.disconnectProvider(provider)
      
      // Update local state
      setConnections(prev => 
        prev.map(conn => 
          conn.provider === provider 
            ? { ...conn, connected: false, status: 'disconnected' }
            : conn
        )
      )
    } catch (err: any) {
      setError(err.message)
    }
  }, [])

  const reconnectProvider = useCallback(async (provider: OAuthProvider) => {
    try {
      setError(null)
      const connection = await ConnectionsService.reconnectProvider(provider)
      
      // Update local state
      setConnections(prev => 
        prev.map(conn => 
          conn.provider === provider 
            ? { 
                ...conn, 
                connected: true, 
                status: 'connected',
                email: connection.email,
                scopes: connection.scopes,
                lastRefresh: connection.lastRefresh,
                expiresAt: connection.expiresAt,
                error: undefined
              }
            : conn
        )
      )
    } catch (err: any) {
      setError(err.message)
    }
  }, [])

  const testConnection = useCallback(async (provider: OAuthProvider): Promise<ConnectionHealthCheck> => {
    try {
      setError(null)
      const healthCheck = await ConnectionsService.testConnection(provider)
      
      // Update local state with health check results
      setConnections(prev => 
        prev.map(conn => 
          conn.provider === provider 
            ? { 
                ...conn, 
                healthCheck: {
                  calendar: healthCheck.calendar.accessible,
                  email: healthCheck.email.accessible,
                  lastChecked: healthCheck.lastChecked
                }
              }
            : conn
        )
      )
      
      return healthCheck
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }, [])

  // Load connections on mount
  useEffect(() => {
    refreshConnections()
  }, [refreshConnections])

  // Handle OAuth callback on mount
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const callback = ConnectionsService.parseOAuthCallback()
      if (callback) {
        try {
          setLoading(true)
          await ConnectionsService.completeOAuthFlow(callback)
          ConnectionsService.clearOAuthCallback()
          
          // Refresh connections to get updated status
          await refreshConnections()
        } catch (err: any) {
          setError(err.message)
          ConnectionsService.clearOAuthCallback()
        } finally {
          setLoading(false)
        }
      }
    }

    handleOAuthCallback()
  }, [refreshConnections])

  return {
    connections,
    loading,
    error,
    refreshConnections,
    connectProvider,
    disconnectProvider,
    reconnectProvider,
    testConnection,
    clearError
  }
}