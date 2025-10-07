import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RegisterForm from '@/components/auth/RegisterForm'
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

const defaultProps = {
  onSwitchToLogin: jest.fn(),
  onRegistrationSuccess: jest.fn()
}

describe('RegisterForm', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    jest.clearAllMocks()
    mockAuthService.isSessionValid.mockResolvedValue(false)
    mockAuthService.getCurrentUser.mockResolvedValue(null)
  })

  it('renders register form correctly', () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    expect(screen.getByText('Create Account')).toBeInTheDocument()
    expect(screen.getByText('Join Meeting Scheduler today')).toBeInTheDocument()
    expect(screen.getByLabelText('Full Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Timezone')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument()
    expect(screen.getByText('Already have an account?')).toBeInTheDocument()
  })

  it('validates all required fields', async () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    const submitButton = screen.getByRole('button', { name: 'Create Account' })
    
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument()
      expect(screen.getByText('Email is required')).toBeInTheDocument()
      expect(screen.getByText('Password is required')).toBeInTheDocument()
      expect(screen.getByText('Timezone is required')).toBeInTheDocument()
    })
  })

  it('validates email format', async () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    const emailInput = screen.getByLabelText('Email Address')
    const submitButton = screen.getByRole('button', { name: 'Create Account' })
    
    await user.type(emailInput, 'invalid-email')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeInTheDocument()
    })
  })

  it('validates password requirements', async () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Create Account' })
    
    // Test short password
    await user.type(passwordInput, '123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument()
    })
    
    // Test password without requirements
    await user.clear(passwordInput)
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Password must contain uppercase, lowercase, number, and special character')).toBeInTheDocument()
    })
  })

  it('submits form with valid data', async () => {
    mockAuthService.signUp.mockResolvedValue(undefined)
    
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
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
  })

  it('shows success message after successful registration', async () => {
    mockAuthService.signUp.mockResolvedValue(undefined)
    
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
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
    
    expect(defaultProps.onRegistrationSuccess).toHaveBeenCalledTimes(1)
  })

  it('handles registration errors', async () => {
    const error = new Error('UsernameExistsException')
    mockAuthService.signUp.mockRejectedValue(error)
    
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
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
      expect(screen.getByText('An account with this email already exists.')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    mockAuthService.signUp.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
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
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    expect(screen.getByText('Creating Account...')).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('calls onSwitchToLogin when sign in link is clicked', async () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    const signInLink = screen.getByText('Sign in')
    await user.click(signInLink)
    
    expect(defaultProps.onSwitchToLogin).toHaveBeenCalledTimes(1)
  })

  it('toggles password visibility', async () => {
    renderWithAuth(<RegisterForm {...defaultProps} />)
    
    const passwordInput = screen.getByLabelText('Password')
    const toggleButton = screen.getByRole('button', { name: '' }) // Eye icon button
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')
    
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })
})