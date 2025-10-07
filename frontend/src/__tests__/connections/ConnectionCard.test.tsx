import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ConnectionCard } from '@/components/connections/ConnectionCard'
import { OAuthConnectionStatus, OAuthProvider } from '@/types/connections'

const mockConnection: OAuthConnectionStatus = {
  provider: 'google' as OAuthProvider,
  connected: false,
  status: 'disconnected'
}

const mockConnectedConnection: OAuthConnectionStatus = {
  provider: 'google' as OAuthProvider,
  connected: true,
  status: 'connected',
  email: 'test@example.com',
  scopes: ['calendar', 'gmail.send'],
  lastRefresh: '2024-01-01T00:00:00Z',
  expiresAt: '2024-01-01T01:00:00Z'
}

const mockProps = {
  onConnect: jest.fn(),
  onDisconnect: jest.fn(),
  onReconnect: jest.fn(),
  onTestConnection: jest.fn()
}

describe('ConnectionCard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders disconnected connection correctly', () => {
    render(<ConnectionCard connection={mockConnection} {...mockProps} />)
    
    expect(screen.getByText('Google')).toBeInTheDocument()
    expect(screen.getByText('Connect your Gmail and Google Calendar')).toBeInTheDocument()
    expect(screen.getByText('Not Connected')).toBeInTheDocument()
    expect(screen.getByText('Connect Google')).toBeInTheDocument()
  })

  it('renders connected connection correctly', () => {
    render(<ConnectionCard connection={mockConnectedConnection} {...mockProps} />)
    
    expect(screen.getByText('Google')).toBeInTheDocument()
    expect(screen.getByText('Connected')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
    expect(screen.getByText('Test Connection')).toBeInTheDocument()
    expect(screen.getByText('Disconnect')).toBeInTheDocument()
  })

  it('calls onConnect when connect button is clicked', async () => {
    render(<ConnectionCard connection={mockConnection} {...mockProps} />)
    
    const connectButton = screen.getByText('Connect Google')
    fireEvent.click(connectButton)
    
    await waitFor(() => {
      expect(mockProps.onConnect).toHaveBeenCalledWith('google')
    })
  })

  it('calls onDisconnect when disconnect button is clicked', async () => {
    // Mock window.confirm
    window.confirm = jest.fn(() => true)
    
    render(<ConnectionCard connection={mockConnectedConnection} {...mockProps} />)
    
    const disconnectButton = screen.getByText('Disconnect')
    fireEvent.click(disconnectButton)
    
    await waitFor(() => {
      expect(mockProps.onDisconnect).toHaveBeenCalledWith('google')
    })
  })

  it('calls onTestConnection when test button is clicked', async () => {
    const mockHealthCheck = {
      provider: 'google' as OAuthProvider,
      calendar: { accessible: true },
      email: { accessible: true },
      lastChecked: '2024-01-01T00:00:00Z'
    }
    
    mockProps.onTestConnection.mockResolvedValue(mockHealthCheck)
    
    render(<ConnectionCard connection={mockConnectedConnection} {...mockProps} />)
    
    const testButton = screen.getByText('Test Connection')
    fireEvent.click(testButton)
    
    await waitFor(() => {
      expect(mockProps.onTestConnection).toHaveBeenCalledWith('google')
    })
  })

  it('shows error state correctly', () => {
    const errorConnection = {
      ...mockConnectedConnection,
      status: 'error' as const,
      error: 'Token expired'
    }
    
    render(<ConnectionCard connection={errorConnection} {...mockProps} />)
    
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Token expired')).toBeInTheDocument()
    expect(screen.getByText('Reconnect')).toBeInTheDocument()
  })
})