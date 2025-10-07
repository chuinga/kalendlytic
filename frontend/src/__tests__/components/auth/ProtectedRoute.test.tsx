import React from 'react'
import { render, screen } from '@testing-library/react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { AuthProvider } from '@/contexts/AuthContext'
import { AuthService } from '@/utils/auth'

// Mock AuthService
jest.mock('@/utils/auth')
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>

// Mock Next.js router
const mockPush = jest.fn()
jest.mock('next/router', () => ({
  useRouter: () => ({
    push: mockPush,
    pathname: '/dashboard'
  })
}))

// Mock LoadingSpinner
jest.mock('@/components/ui/LoadingSpinner', () => {
  return function LoadingSpinner() {
    return <div data-testid="loading-spinner">Loading...</div>
  }
})

const MockAuthProvider = ({ 
  children, 
  mockUser = null, 
  mockLoading = false 
}: { 
  children: React.ReactNode
  mockUser?: any
  mockLoading?: boolean 
}) => {
  // Mock the auth context values
  React.useEffect(() => {
    mockAuthService.isSessionValid.mockResolvedValue(!!mockUser)
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
  }, [mockUser])

  return <AuthProvider>{children}</AuthProvider>
}

const TestComponent = () => <div data-testid="protected-content">Protected Content</div>

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPush.mockClear()
  })

  it('shows loading spinner while checking authentication', () => {
    mockAuthService.isSessionValid.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(
      <MockAuthProvider mockLoading={true}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('renders children when user is authenticated', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }
    
    render(
      <MockAuthProvider mockUser={mockUser}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    // Wait for auth check to complete
    await screen.findByTestId('protected-content')
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('redirects to login when user is not authenticated', async () => {
    render(
      <MockAuthProvider mockUser={null}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    // Wait for auth check to complete and redirect
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(mockPush).toHaveBeenCalledWith('/login')
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('redirects to custom redirect path when provided', async () => {
    render(
      <MockAuthProvider mockUser={null}>
        <ProtectedRoute redirectTo="/custom-login">
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    // Wait for auth check to complete and redirect
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(mockPush).toHaveBeenCalledWith('/custom-login')
  })

  it('shows fallback component when user is not authenticated and fallback is provided', async () => {
    const FallbackComponent = () => <div data-testid="fallback">Please log in</div>
    
    render(
      <MockAuthProvider mockUser={null}>
        <ProtectedRoute fallback={<FallbackComponent />}>
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    await screen.findByTestId('fallback')
    expect(screen.getByTestId('fallback')).toBeInTheDocument()
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('handles authentication errors gracefully', async () => {
    mockAuthService.isSessionValid.mockRejectedValue(new Error('Auth error'))
    
    render(
      <MockAuthProvider mockUser={null}>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </MockAuthProvider>
    )
    
    // Wait for error handling and redirect
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(mockPush).toHaveBeenCalledWith('/login')
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })
})