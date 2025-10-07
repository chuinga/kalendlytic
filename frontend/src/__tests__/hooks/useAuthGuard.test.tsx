import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { AuthProvider } from '@/contexts/AuthContext'
import { AuthService } from '@/utils/auth'

// Mock AuthService
jest.mock('@/utils/auth')
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>

// Mock Next.js router
const mockPush = jest.fn()
const mockReplace = jest.fn()
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    pathname: '/dashboard',
    query: {},
    asPath: '/dashboard'
  })
}))

const AuthWrapper = ({ children }: { children: React.ReactNode }) => {
  return <AuthProvider>{children}</AuthProvider>
}

describe('useAuthGuard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPush.mockClear()
    mockReplace.mockClear()
  })

  it('allows access when user is authenticated', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.user).toEqual(mockUser)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('redirects to login when user is not authenticated', async () => {
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.user).toBe(null)
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('redirects to custom path when specified', async () => {
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)

    const { result } = renderHook(() => useAuthGuard({ redirectTo: '/custom-login' }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(mockPush).toHaveBeenCalledWith('/custom-login')
  })

  it('uses replace instead of push when specified', async () => {
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)

    const { result } = renderHook(() => useAuthGuard({ replace: true }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(mockReplace).toHaveBeenCalledWith('/login')
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('does not redirect when disabled', async () => {
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)

    const { result } = renderHook(() => useAuthGuard({ enabled: false }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(mockPush).not.toHaveBeenCalled()
    expect(mockReplace).not.toHaveBeenCalled()
  })

  it('shows loading state during authentication check', () => {
    mockAuthService.isSessionValid.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    )

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    expect(result.current.isLoading).toBe(true)
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.user).toBe(null)
  })

  it('handles authentication errors gracefully', async () => {
    mockAuthService.isSessionValid.mockRejectedValue(new Error('Auth error'))

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBe('Auth error')
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('requires specific roles when specified', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['user']
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuthGuard({ requiredRoles: ['admin'] }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.hasRequiredRole).toBe(false)
    expect(mockPush).toHaveBeenCalledWith('/unauthorized')
  })

  it('allows access when user has required role', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['admin', 'user']
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuthGuard({ requiredRoles: ['admin'] }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.hasRequiredRole).toBe(true)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('checks permissions when specified', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      permissions: ['read:calendar', 'write:calendar']
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuthGuard({ requiredPermissions: ['write:calendar'] }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.hasRequiredPermission).toBe(true)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('denies access when user lacks required permission', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      permissions: ['read:calendar']
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)

    const { result } = renderHook(() => useAuthGuard({ requiredPermissions: ['admin:users'] }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)
    expect(result.current.hasRequiredPermission).toBe(false)
    expect(mockPush).toHaveBeenCalledWith('/unauthorized')
  })

  it('refreshes authentication when token is near expiry', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    mockAuthService.refreshSession.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuthGuard({ autoRefresh: true }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)

    // Simulate token near expiry
    jest.advanceTimersByTime(50 * 60 * 1000) // 50 minutes

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(mockAuthService.refreshSession).toHaveBeenCalled()
  })

  it('handles refresh failures by signing out user', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    mockAuthService.refreshSession.mockRejectedValue(new Error('Refresh failed'))
    mockAuthService.signOut.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuthGuard({ autoRefresh: true }), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    expect(result.current.isAuthenticated).toBe(true)

    // Simulate refresh failure
    jest.advanceTimersByTime(50 * 60 * 1000)

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 100))
    })

    expect(mockAuthService.signOut).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('provides manual refresh function', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    mockAuthService.refreshSession.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.refresh()
    })

    expect(mockAuthService.refreshSession).toHaveBeenCalled()
  })

  it('provides manual logout function', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }

    mockAuthService.isSessionValid.mockResolvedValue(true)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
    mockAuthService.signOut.mockResolvedValue(undefined)

    const { result } = renderHook(() => useAuthGuard(), {
      wrapper: AuthWrapper
    })

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })

    await act(async () => {
      await result.current.logout()
    })

    expect(mockAuthService.signOut).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})