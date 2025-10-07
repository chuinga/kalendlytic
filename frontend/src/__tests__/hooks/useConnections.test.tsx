import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { useConnections } from '@/hooks/useConnections'
import { ConnectionsService } from '@/utils/connections'
import { OAuthConnectionStatus } from '@/types/connections'

// Mock the ConnectionsService
jest.mock('@/utils/connections')
const mockConnectionsService = ConnectionsService as jest.Mocked<typeof ConnectionsService>

const mockConnections: OAuthConnectionStatus[] = [
  {
    provider: 'google',
    connected: true,
    status: 'connected',
    email: 'test@gmail.com',
    scopes: ['calendar', 'gmail.send']
  },
  {
    provider: 'microsoft',
    connected: false,
    status: 'disconnected'
  }
]

describe('useConnections', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockConnectionsService.getConnections.mockResolvedValue(mockConnections)
    mockConnectionsService.parseOAuthCallback.mockReturnValue(null)
  })

  it('loads connections on mount', async () => {
    const { result } = renderHook(() => useConnections())

    expect(result.current.loading).toBe(true)

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.connections).toEqual(mockConnections)
    expect(mockConnectionsService.getConnections).toHaveBeenCalledTimes(1)
  })

  it('handles connection errors', async () => {
    const errorMessage = 'Failed to load connections'
    mockConnectionsService.getConnections.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(() => useConnections())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe(errorMessage)
    expect(result.current.connections).toEqual([])
  })

  it('connects provider successfully', async () => {
    const authUrl = 'https://accounts.google.com/oauth/authorize?...'
    mockConnectionsService.startOAuthFlow.mockResolvedValue({
      provider: 'google',
      authUrl,
      state: 'random-state'
    })
    
    // Mock window.location.href
    delete (window as any).location
    window.location = { href: '' } as any
    mockConnectionsService.getOAuthRedirectUrl = jest.fn()

    const { result } = renderHook(() => useConnections())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.connectProvider('google')
    })

    expect(mockConnectionsService.startOAuthFlow).toHaveBeenCalledWith('google')
    expect(mockConnectionsService.getOAuthRedirectUrl).toHaveBeenCalledWith(authUrl)
  })

  it('disconnects provider successfully', async () => {
    mockConnectionsService.disconnectProvider.mockResolvedValue()

    const { result } = renderHook(() => useConnections())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.disconnectProvider('google')
    })

    expect(mockConnectionsService.disconnectProvider).toHaveBeenCalledWith('google')
    
    // Check that the connection status was updated locally
    const googleConnection = result.current.connections.find(c => c.provider === 'google')
    expect(googleConnection?.connected).toBe(false)
    expect(googleConnection?.status).toBe('disconnected')
  })

  it('clears error successfully', async () => {
    const errorMessage = 'Test error'
    mockConnectionsService.getConnections.mockRejectedValue(new Error(errorMessage))

    const { result } = renderHook(() => useConnections())

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.error).toBe(errorMessage)

    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBe(null)
  })
})