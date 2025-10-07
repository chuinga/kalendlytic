import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from '@/components/auth/LoginForm'
import { useAuth } from '@/contexts/AuthContext'

// Mock the auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>

describe('LoginForm', () => {
  const mockLogin = jest.fn()
  const mockClearError = jest.fn()
  const mockOnSwitchToRegister = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: mockLogin,
      register: jest.fn(),
      logout: jest.fn(),
      updateProfile: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
    })
  })

  it('should render login form', () => {
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    const submitButton = screen.getByRole('button', { name: 'Sign In' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
      expect(screen.getByText('Password is required')).toBeInTheDocument()
    })
  })

  it('should validate email format', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    const emailInput = screen.getByLabelText('Email Address')
    await user.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: 'Sign In' })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeInTheDocument()
    })
  })

  it('should call login with correct credentials', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    const emailInput = screen.getByLabelText('Email Address')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign In' })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      })
    })
  })

  it('should show loading state during login', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      login: mockLogin,
      register: jest.fn(),
      logout: jest.fn(),
      updateProfile: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
    })

    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    expect(screen.getByText('Signing In...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
  })

  it('should display error message', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: 'Invalid credentials',
      login: mockLogin,
      register: jest.fn(),
      logout: jest.fn(),
      updateProfile: jest.fn(),
      refreshToken: jest.fn(),
      clearError: mockClearError,
    })

    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
  })

  it('should toggle password visibility', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    const passwordInput = screen.getByLabelText('Password')
    const toggleButton = screen.getByRole('button', { name: '' }) // Eye icon button

    expect(passwordInput).toHaveAttribute('type', 'password')

    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')

    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('should call onSwitchToRegister when sign up link is clicked', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSwitchToRegister={mockOnSwitchToRegister} />)

    const signUpLink = screen.getByText('Sign up')
    await user.click(signUpLink)

    expect(mockOnSwitchToRegister).toHaveBeenCalled()
  })
})