import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from '@/components/auth/LoginForm'
import { AuthProvider } from '@/contexts/AuthContext'
import { AuthService } from '@/utils/auth'

// Mock AuthService
jest.mock('@/utils/auth')
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>

// Mock LoadingSpinner
jest.mock('@/components/ui/LoadingSpinner', () => {
  return function LoadingSpinner({ size, className }: { size?: string; className?: string }) {
    return <div data-testid="loading-spinner" className={className}>Loading...</div>
  }
})

const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  return <AuthProvider>{children}</AuthProvider>
}

const renderWithAuth = (component: React.ReactElement) => {
  return render(component, { wrapper: MockAuthProvider })
}

describe('LoginForm', () => {
  const mockOnSwitchToRegister = jest.fn()
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)
  })

  it('renders login form correctly', () => {
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Welcome back to Meeting Scheduler')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
    expect(screen.getByText("Don't have an account?")).toBeInTheDocument()
  })

  it('validates email field correctly', async () => {
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const submitButton = screen.getByRole('button', { name: 'Sign In' })
    
    // Test empty email
    await user.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
    })
    
    // Test invalid email format
    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeInTheDocument()
    })
  })

  it('validates password field correctly', async () => {
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign In' })
    
    await user.type(emailInput, 'test@example.com')
    
    // Test empty password
    await user.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })
    
    // Test short password
    await user.type(passwordInput, '123')
    await user.click(submitButton)
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    })
  })

  it('toggles password visibility', async () => {
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const passwordInput = screen.getByLabelText('Password')
    const toggleButton = screen.getByRole('button', { name: '' }) // Eye icon button
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('submits form with valid credentials', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User'
    }
    
    mockAuthService.signIn.mockResolvedValue(mockUser)
    
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /Sign In|Signing In/ })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockAuthService.signIn).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
    })
  })

  it('handles UserNotConfirmedException error', async () => {
    const error = new Error('UserNotConfirmedException')
    mockAuthService.signIn.mockRejectedValue(error)
    
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /Sign In|Signing In/ })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Please check your email and confirm your account before signing in.')).toBeInTheDocument()
    })
  })

  it('handles NotAuthorizedException error', async () => {
    const error = new Error('NotAuthorizedException')
    mockAuthService.signIn.mockRejectedValue(error)
    
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /Sign In|Signing In/ })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid email or password.')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    mockAuthService.signIn.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /Sign In|Signing In/ })
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.getByText('Signing In...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('calls onSwitchToRegister when sign up link is clicked', async () => {
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const signUpLink = screen.getByText('Sign up')
    await user.click(signUpLink)
    
    expect(mockOnSwitchToRegister).toHaveBeenCalledTimes(1)
  })

  it('disables form elements when loading', async () => {
    mockAuthService.signIn.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    renderWithAuth(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: /Sign In|Signing In/ })
    const signUpLink = screen.getByText('Sign up')
    
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
    expect(submitButton).toBeDisabled()
    expect(signUpLink).toHaveAttribute('disabled')
  })
})