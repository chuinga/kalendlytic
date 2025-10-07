import { apiClient } from './api'
import { 
  OAuthProvider, 
  OAuthConnection, 
  OAuthConnectionStatus, 
  OAuthAuthorizationUrl, 
  OAuthCallback,
  ConnectionHealthCheck
} from '@/types/connections'

export class ConnectionsService {
  /**
   * Get all OAuth connections for the current user
   */
  static async getConnections(): Promise<OAuthConnectionStatus[]> {
    try {
      const response = await apiClient.get<{ connections: OAuthConnectionStatus[] }>('/connections')
      return response.data.connections
    } catch (error: any) {
      console.error('Error getting connections:', error)
      throw new Error(error.response?.data?.message || 'Failed to get connections')
    }
  }

  /**
   * Get connection status for a specific provider
   */
  static async getConnectionStatus(provider: OAuthProvider): Promise<OAuthConnectionStatus | null> {
    try {
      const response = await apiClient.get<{ connection: OAuthConnectionStatus }>(`/connections/${provider}`)
      return response.data.connection
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null
      }
      console.error(`Error getting ${provider} connection status:`, error)
      throw new Error(error.response?.data?.message || `Failed to get ${provider} connection status`)
    }
  }

  /**
   * Start OAuth authorization flow
   */
  static async startOAuthFlow(provider: OAuthProvider): Promise<OAuthAuthorizationUrl> {
    try {
      const response = await apiClient.post<OAuthAuthorizationUrl>('/connections/oauth/start', {
        provider
      })
      return response.data
    } catch (error: any) {
      console.error(`Error starting ${provider} OAuth flow:`, error)
      throw new Error(error.response?.data?.message || `Failed to start ${provider} OAuth flow`)
    }
  }

  /**
   * Complete OAuth authorization flow
   */
  static async completeOAuthFlow(callback: OAuthCallback): Promise<OAuthConnection> {
    try {
      const response = await apiClient.post<{ connection: OAuthConnection }>('/connections/oauth/callback', callback)
      return response.data.connection
    } catch (error: any) {
      console.error(`Error completing ${callback.provider} OAuth flow:`, error)
      throw new Error(error.response?.data?.message || `Failed to complete ${callback.provider} OAuth flow`)
    }
  }

  /**
   * Disconnect OAuth provider
   */
  static async disconnectProvider(provider: OAuthProvider): Promise<void> {
    try {
      await apiClient.delete(`/connections/${provider}`)
    } catch (error: any) {
      console.error(`Error disconnecting ${provider}:`, error)
      throw new Error(error.response?.data?.message || `Failed to disconnect ${provider}`)
    }
  }

  /**
   * Reconnect OAuth provider (refresh connection)
   */
  static async reconnectProvider(provider: OAuthProvider): Promise<OAuthConnection> {
    try {
      const response = await apiClient.post<{ connection: OAuthConnection }>(`/connections/${provider}/reconnect`)
      return response.data.connection
    } catch (error: any) {
      console.error(`Error reconnecting ${provider}:`, error)
      throw new Error(error.response?.data?.message || `Failed to reconnect ${provider}`)
    }
  }

  /**
   * Test connection health
   */
  static async testConnection(provider: OAuthProvider): Promise<ConnectionHealthCheck> {
    try {
      const response = await apiClient.post<ConnectionHealthCheck>(`/connections/${provider}/health-check`)
      return response.data
    } catch (error: any) {
      console.error(`Error testing ${provider} connection:`, error)
      throw new Error(error.response?.data?.message || `Failed to test ${provider} connection`)
    }
  }

  /**
   * Refresh OAuth tokens
   */
  static async refreshTokens(provider: OAuthProvider): Promise<OAuthConnection> {
    try {
      const response = await apiClient.post<{ connection: OAuthConnection }>(`/connections/${provider}/refresh`)
      return response.data.connection
    } catch (error: any) {
      console.error(`Error refreshing ${provider} tokens:`, error)
      throw new Error(error.response?.data?.message || `Failed to refresh ${provider} tokens`)
    }
  }

  /**
   * Get OAuth authorization URL for manual redirect
   */
  static getOAuthRedirectUrl(authUrl: string): void {
    window.location.href = authUrl
  }

  /**
   * Handle OAuth callback from URL parameters
   */
  static parseOAuthCallback(): OAuthCallback | null {
    if (typeof window === 'undefined') return null

    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    const provider = urlParams.get('provider') as OAuthProvider

    if (!code || !state || !provider) {
      return null
    }

    return { provider, code, state }
  }

  /**
   * Clear OAuth callback parameters from URL
   */
  static clearOAuthCallback(): void {
    if (typeof window === 'undefined') return

    const url = new URL(window.location.href)
    url.searchParams.delete('code')
    url.searchParams.delete('state')
    url.searchParams.delete('provider')
    
    window.history.replaceState({}, document.title, url.toString())
  }
}