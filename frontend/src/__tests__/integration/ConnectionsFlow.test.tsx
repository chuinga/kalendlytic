import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConnectionsPage } from '@/components/connections/ConnectionsPage'
import { AuthProvider } from '@/contexts/AuthContext'
import { ConnectionsService } from '@/utils/connections'
import { OAuthConnectionStatus } from '@/types/connections'

// Mock ConnectionsService
jest.mock('@/utils/connections')
const mockConnectionsService = ConnectionsService as jest.Mocked<typeof ConnectionsService>

// Mock AuthService
jest.mock('@/utils/auth', () => ({
  AuthService: {
    isSessionValid: jest.fn().mockResolvedValue(true),
    getCurrentUser: jest.fn().mockResolvedValue({
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    })
  }
}))

// Mock window.location
delete (window as any).location
window.location = { href: '' } as any

const mockConnections: OAuthConnectionStatus[] = [
  {
    provider: 'google',
    connected: false,
    status: 'disconnected'
  },
  {
    provider: 'microsoft',
    connected: false,
    status: 'disconnected'
  }
]

const mockConnectedConnections: OAuthConnectionStatus[] = [
  {
    provider: 'google',
    connected: true,
    status: 'connected',
    email: 'test@gmail.com',
    scopes: ['calendar', 'gmail.send'],
    lastRefresh: '2024-01-01T00:00:00Z',
    expiresAt: '2024-01-01T01:00:00Z'
  },
  {
    provider: 'microsoft',
    connected: true,
    status: 'connected',
    email: 'test@outlook.com',
    scopes: ['Calendars.ReadWrite', 'Mail.Send'],
    lastRefresh: '2024-01-01T00:00:00Z',
    expiresAt: '2024-01-01T01:00:00Z'
  }
]

const ConnectionsFlowTestApp = () => {
  return (
    <AuthProvider>
      <ConnectionsPage />
    </AuthProvider>
  )
}

describe('Connections Flow Integration', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockConnectionsService.getConnections.mockResolvedValue(mockConnections)
    mockConnectionsService.parseOAuthCallback.mockReturnValue(null)
  })

  describe('Initial Connection Setup', () => {
    it('displays disconnected connections on initial load', async () => {
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Google')).toBeInTheDocument()
        expect(screen.getByText('Microsoft')).toBeInTheDocument()
      })
      
      expect(screen.getAllByText('Not Connected')).toHaveLength(2)
      expect(screen.getByText('Connect Google')).toBeInTheDocument()
      expect(screen.getByText('Connect Microsoft')).toBeInTheDocument()
    })

    it('initiates Google OAuth flow when connect button is clicked', async () => {
      const mockAuthUrl = 'https://accounts.google.com/oauth/authorize?...'
      mockConnectionsService.startOAuthFlow.mockResolvedValue({
        provider: 'google',
        authUrl: mockAuthUrl,
        state: 'random-state'
      })
      mockConnectionsService.getOAuthRedirectUrl = jest.fn()
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connect Google')).toBeInTheDocument()
      })
      
      const connectButton = screen.getByText('Connect Google')
      await user.click(connectButton)
      
      await waitFor(() => {
        expect(mockConnectionsService.startOAuthFlow).toHaveBeenCalledWith('google')
        expect(mockConnectionsService.getOAuthRedirectUrl).toHaveBeenCalledWith(mockAuthUrl)
      })
    })

    it('initiates Microsoft OAuth flow when connect button is clicked', async () => {
      const mockAuthUrl = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?...'
      mockConnectionsService.startOAuthFlow.mockResolvedValue({
        provider: 'microsoft',
        authUrl: mockAuthUrl,
        state: 'random-state'
      })
      mockConnectionsService.getOAuthRedirectUrl = jest.fn()
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connect Microsoft')).toBeInTheDocument()
      })
      
      const connectButton = screen.getByText('Connect Microsoft')
      await user.click(connectButton)
      
      await waitFor(() => {
        expect(mockConnectionsService.startOAuthFlow).toHaveBeenCalledWith('microsoft')
        expect(mockConnectionsService.getOAuthRedirectUrl).toHaveBeenCalledWith(mockAuthUrl)
      })
    })
  })

  describe('Connected State Management', () => {
    beforeEach(() => {
      mockConnectionsService.getConnections.mockResolvedValue(mockConnectedConnections)
    })

    it('displays connected connections with details', async () => {
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Connected')).toHaveLength(2)
      })
      
      expect(screen.getByText('test@gmail.com')).toBeInTheDocument()
      expect(screen.getByText('test@outlook.com')).toBeInTheDocument()
      expect(screen.getByText('Test Connection')).toBeInTheDocument()
      expect(screen.getByText('Disconnect')).toBeInTheDocument()
    })

    it('tests connection health when test button is clicked', async () => {
      const mockHealthCheck = {
        provider: 'google' as const,
        calendar: { accessible: true },
        email: { accessible: true },
        lastChecked: '2024-01-01T00:00:00Z'
      }
      
      mockConnectionsService.testConnection.mockResolvedValue(mockHealthCheck)
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Test Connection')).toBeInTheDocument()
      })
      
      const testButtons = screen.getAllByText('Test Connection')
      await user.click(testButtons[0]) // Test Google connection
      
      await waitFor(() => {
        expect(mockConnectionsService.testConnection).toHaveBeenCalledWith('google')
      })
      
      expect(screen.getByText('Connection Test Results')).toBeInTheDocument()
      expect(screen.getByText('✓ Working')).toBeInTheDocument()
    })

    it('disconnects provider when disconnect button is clicked', async () => {
      mockConnectionsService.disconnectProvider.mockResolvedValue()
      
      // Mock window.confirm
      window.confirm = jest.fn(() => true)
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Disconnect')).toBeInTheDocument()
      })
      
      const disconnectButtons = screen.getAllByText('Disconnect')
      await user.click(disconnectButtons[0]) // Disconnect Google
      
      await waitFor(() => {
        expect(mockConnectionsService.disconnectProvider).toHaveBeenCalledWith('google')
      })
    })

    it('shows confirmation dialog before disconnecting', async () => {
      window.confirm = jest.fn(() => false) // User cancels
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Disconnect')).toBeInTheDocument()
      })
      
      const disconnectButtons = screen.getAllByText('Disconnect')
      await user.click(disconnectButtons[0])
      
      expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to disconnect Google?')
      expect(mockConnectionsService.disconnectProvider).not.toHaveBeenCalled()
    })
  })

  describe('Error State Handling', () => {
    it('displays connection errors', async () => {
      const errorConnections = [
        {
          ...mockConnectedConnections[0],
          status: 'error' as const,
          error: 'Token expired'
        },
        mockConnectedConnections[1]
      ]
      
      mockConnectionsService.getConnections.mockResolvedValue(errorConnections)
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
        expect(screen.getByText('Token expired')).toBeInTheDocument()
        expect(screen.getByText('Reconnect')).toBeInTheDocument()
      })
    })

    it('handles reconnection for expired tokens', async () => {
      const errorConnections = [
        {
          ...mockConnectedConnections[0],
          status: 'expired' as const,
          error: 'Token expired'
        }
      ]
      
      mockConnectionsService.getConnections.mockResolvedValue(errorConnections)
      mockConnectionsService.reconnectProvider.mockResolvedValue()
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Reconnect')).toBeInTheDocument()
      })
      
      const reconnectButton = screen.getByText('Reconnect')
      await user.click(reconnectButton)
      
      await waitFor(() => {
        expect(mockConnectionsService.reconnectProvider).toHaveBeenCalledWith('google')
      })
    })

    it('handles API errors gracefully', async () => {
      mockConnectionsService.getConnections.mockRejectedValue(new Error('API Error'))
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load connections')).toBeInTheDocument()
      })
    })

    it('shows loading states during operations', async () => {
      mockConnectionsService.startOAuthFlow.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      )
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connect Google')).toBeInTheDocument()
      })
      
      const connectButton = screen.getByText('Connect Google')
      await user.click(connectButton)
      
      expect(screen.getByText('Connecting...')).toBeInTheDocument()
      expect(connectButton).toBeDisabled()
    })
  })

  describe('OAuth Callback Handling', () => {
    it('processes OAuth callback on page load', async () => {
      const mockCallbackData = {
        provider: 'google' as const,
        code: 'auth_code_123',
        state: 'random_state'
      }
      
      mockConnectionsService.parseOAuthCallback.mockReturnValue(mockCallbackData)
      mockConnectionsService.completeOAuthFlow.mockResolvedValue()
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(mockConnectionsService.parseOAuthCallback).toHaveBeenCalled()
        expect(mockConnectionsService.completeOAuthFlow).toHaveBeenCalledWith(mockCallbackData)
      })
    })

    it('handles OAuth callback errors', async () => {
      const mockCallbackData = {
        provider: 'google' as const,
        error: 'access_denied',
        error_description: 'User denied access'
      }
      
      mockConnectionsService.parseOAuthCallback.mockReturnValue(mockCallbackData)
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connection failed: User denied access')).toBeInTheDocument()
      })
    })
  })

  describe('Connection Status Updates', () => {
    it('refreshes connection status periodically', async () => {
      jest.useFakeTimers()
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(mockConnectionsService.getConnections).toHaveBeenCalledTimes(1)
      })
      
      // Fast-forward time to trigger refresh
      jest.advanceTimersByTime(30000) // 30 seconds
      
      await waitFor(() => {
        expect(mockConnectionsService.getConnections).toHaveBeenCalledTimes(2)
      })
      
      jest.useRealTimers()
    })

    it('updates connection status after successful operations', async () => {
      mockConnectionsService.startOAuthFlow.mockResolvedValue({
        provider: 'google',
        authUrl: 'https://example.com',
        state: 'state'
      })
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connect Google')).toBeInTheDocument()
      })
      
      const connectButton = screen.getByText('Connect Google')
      await user.click(connectButton)
      
      // Should refresh connections after operation
      await waitFor(() => {
        expect(mockConnectionsService.getConnections).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Scopes and Permissions', () => {
    it('displays required scopes for each provider', async () => {
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connect your Gmail and Google Calendar')).toBeInTheDocument()
        expect(screen.getByText('Connect your Outlook and Microsoft Calendar')).toBeInTheDocument()
      })
    })

    it('shows granted scopes for connected accounts', async () => {
      mockConnectionsService.getConnections.mockResolvedValue(mockConnectedConnections)
      
      render(<ConnectionsFlowTestApp />)
      
      await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument()
      })
      
      // Scopes should be displayed in connection details
      expect(screen.getByText('test@gmail.com')).toBeInTheDocument()
      expect(screen.getByText('test@outlook.com')).toBeInTheDocument()
    })
  })
})