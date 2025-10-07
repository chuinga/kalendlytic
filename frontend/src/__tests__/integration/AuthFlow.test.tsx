import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider } from '@/contexts/AuthContext'
import LoginForm from '@/components/auth/LoginForm'
import RegisterForm from '@/components/auth/RegisterForm'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
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

const AuthFlowTestApp = () => {
  const [currentView, setCurrentView] = React.useState<'login' | 'register' | 'dashboard'>('login')
  
  return (
    <AuthProvider>
      {currentView === 'login' && (
        <LoginForm onSwitchToRegister={() => setCurrentView('register')} />
      )}
      {currentView === 'register' && (
        <RegisterForm onSwitchToLogin={() => setCurrentView('login')} />
      )}
      {currentView === 'dashboard' && (
        <ProtectedRoute>
          <div data-testid="dashboard">Dashboard Content</div>
        </ProtectedRoute>
      )}
    </AuthProvider>
  )
}

describe('Authentication Flow Integration', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)
  })

  describe('Login Flow', () => {
    it('completes successful login flow', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User'
      }
      
      mockAuthService.signIn.mockResolvedValue(mockUser)
      mockAuthService.isSessionValid.mockResolvedValue(true)
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      
      render(<AuthFlowTestApp />)
      
      // Fill in login form
      const emailInput = screen.getByLabelText('Email Address')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: 'Sign In' })
      
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)
      
      // Verify login was called
      await waitFor(() => {
        expect(mockAuthService.signIn).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123'
        })
      })
    })

    it('handles login errors gracefully', async () => {
      mockAuthService.signIn.mockRejectedValue(new Error('NotAuthorizedException'))
      
      render(<AuthFlowTestApp />)
      
      const emailInput = screen.getByLabelText('Email Address')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: 'Sign In' })
      
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Invalid email or password.')).toBeInTheDocument()
      })
    })

    it('switches to register form when sign up link is clicked', async () => {
      render(<AuthFlowTestApp />)
      
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      expect(screen.getByText('Create Account')).toBeInTheDocument()
      expect(screen.getByText('Join Meeting Scheduler today')).toBeInTheDocument()
    })
  })

  describe('Registration Flow', () => {
    it('completes successful registration flow', async () => {
      mockAuthService.signUp.mockResolvedValue(undefined)
      
      render(<AuthFlowTestApp />)
      
      // Switch to register form
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      // Fill in registration form
      const nameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email Address')
      const passwordInput = screen.getByLabelText('Password')
      const timezoneSelect = screen.getByLabelText('Timezone')
      const submitButton = screen.getByRole('button', { name: 'Create Account' })
      
      await user.type(nameInput, 'John Doe')
      await user.type(emailInput, 'john@example.com')
      await user.type(passwordInput, 'Password123')
      await user.selectOptions(timezoneSelect, 'America/New_York')
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(mockAuthService.signUp).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          password: 'Password123',
          timezone: 'America/New_York'
        })
      })
      
      expect(screen.getByText('Account created successfully!')).toBeInTheDocument()
    })

    it('handles registration validation errors', async () => {
      render(<AuthFlowTestApp />)
      
      // Switch to register form
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      // Try to submit without filling required fields
      const submitButton = screen.getByRole('button', { name: 'Create Account' })
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Name is required')).toBeInTheDocument()
        expect(screen.getByText('Email is required')).toBeInTheDocument()
        expect(screen.getByText('Password is required')).toBeInTheDocument()
        expect(screen.getByText('Timezone is required')).toBeInTheDocument()
      })
    })

    it('switches back to login form when sign in link is clicked', async () => {
      render(<AuthFlowTestApp />)
      
      // Switch to register form
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      // Switch back to login
      const signInLink = screen.getByText('Sign in')
      await user.click(signInLink)
      
      expect(screen.getByText('Sign In')).toBeInTheDocument()
      expect(screen.getByText('Welcome back to Meeting Scheduler')).toBeInTheDocument()
    })
  })

  describe('Protected Route Flow', () => {
    it('redirects unauthenticated users to login', async () => {
      mockAuthService.isSessionValid.mockResolvedValue(false)
      mockAuthService.getCurrentUser.mockResolvedValue(null)
      
      const ProtectedApp = () => (
        <AuthProvider>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      )
      
      render(<ProtectedApp />)
      
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
      
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('allows authenticated users to access protected content', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User'
      }
      
      mockAuthService.isSessionValid.mockResolvedValue(true)
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      
      const ProtectedApp = () => (
        <AuthProvider>
          <ProtectedRoute>
            <div data-testid="protected-content">Protected Content</div>
          </ProtectedRoute>
        </AuthProvider>
      )
      
      render(<ProtectedApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      })
      
      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('Session Management', () => {
    it('handles session expiration gracefully', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User'
      }
      
      // Initially authenticated
      mockAuthService.isSessionValid.mockResolvedValue(true)
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      
      const SessionApp = () => (
        <AuthProvider>
          <div data-testid="app-content">App Content</div>
        </AuthProvider>
      )
      
      render(<SessionApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-content')).toBeInTheDocument()
      })
      
      // Simulate session expiration
      mockAuthService.refreshSession.mockRejectedValue(new Error('Session expired'))
      
      // Wait for auto-refresh to fail and user to be signed out
      await waitFor(() => {
        // The auth context should handle the error and sign out the user
        expect(mockAuthService.refreshSession).toHaveBeenCalled()
      }, { timeout: 3000 })
    })

    it('automatically refreshes valid sessions', async () => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User'
      }
      
      mockAuthService.isSessionValid.mockResolvedValue(true)
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser)
      mockAuthService.refreshSession.mockResolvedValue(undefined)
      
      const SessionApp = () => (
        <AuthProvider>
          <div data-testid="app-content">App Content</div>
        </AuthProvider>
      )
      
      render(<SessionApp />)
      
      await waitFor(() => {
        expect(screen.getByTestId('app-content')).toBeInTheDocument()
      })
      
      // Wait for auto-refresh to be called
      await waitFor(() => {
        expect(mockAuthService.refreshSession).toHaveBeenCalled()
      }, { timeout: 3000 })
    })
  })

  describe('Form Validation Integration', () => {
    it('validates email format across login and register forms', async () => {
      render(<AuthFlowTestApp />)
      
      // Test login form validation
      const emailInput = screen.getByLabelText('Email Address')
      const submitButton = screen.getByRole('button', { name: 'Sign In' })
      
      await user.type(emailInput, 'invalid-email')
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Invalid email address')).toBeInTheDocument()
      })
      
      // Switch to register form
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      // Test register form validation
      const registerEmailInput = screen.getByLabelText('Email Address')
      const registerSubmitButton = screen.getByRole('button', { name: 'Create Account' })
      
      await user.type(registerEmailInput, 'another-invalid-email')
      await user.click(registerSubmitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Invalid email address')).toBeInTheDocument()
      })
    })

    it('validates password requirements consistently', async () => {
      render(<AuthFlowTestApp />)
      
      // Test login form password validation
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: 'Sign In' })
      
      await user.type(passwordInput, '123')
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
      })
      
      // Switch to register form
      const signUpLink = screen.getByText('Sign up')
      await user.click(signUpLink)
      
      // Test register form password validation (more strict)
      const registerPasswordInput = screen.getByLabelText('Password')
      const registerSubmitButton = screen.getByRole('button', { name: 'Create Account' })
      
      await user.type(registerPasswordInput, 'password123')
      await user.click(registerSubmitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Password must contain at least one uppercase letter')).toBeInTheDocument()
      })
    })
  })
})