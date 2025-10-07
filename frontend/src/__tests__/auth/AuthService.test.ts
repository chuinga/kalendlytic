import { AuthService } from '@/utils/auth'
import { getCurrentUser, signIn, signUp, signOut, fetchAuthSession, updateUserAttributes } from 'aws-amplify/auth'

// Mock AWS Amplify
jest.mock('aws-amplify/auth', () => ({
  getCurrentUser: jest.fn(),
  signIn: jest.fn(),
  signUp: jest.fn(),
  signOut: jest.fn(),
  fetchAuthSession: jest.fn(),
  updateUserAttributes: jest.fn(),
}))

const mockGetCurrentUser = getCurrentUser as jest.MockedFunction<typeof getCurrentUser>
const mockSignIn = signIn as jest.MockedFunction<typeof signIn>
const mockSignUp = signUp as jest.MockedFunction<typeof signUp>
const mockSignOut = signOut as jest.MockedFunction<typeof signOut>
const mockFetchAuthSession = fetchAuthSession as jest.MockedFunction<typeof fetchAuthSession>
const mockUpdateUserAttributes = updateUserAttributes as jest.MockedFunction<typeof updateUserAttributes>

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('getCurrentUser', () => {
    it('should return user when authenticated', async () => {
      const mockUser = {
        userId: 'user123',
        signInDetails: { loginId: 'test@example.com' },
        attributes: { email: 'test@example.com', name: 'Test User' }
      }
      
      mockGetCurrentUser.mockResolvedValue(mockUser as any)

      const result = await AuthService.getCurrentUser()

      expect(result).toEqual({
        id: 'user123',
        email: 'test@example.com',
        attributes: { email: 'test@example.com', name: 'Test User' }
      })
    })

    it('should return null when not authenticated', async () => {
      mockGetCurrentUser.mockRejectedValue(new Error('Not authenticated'))

      const result = await AuthService.getCurrentUser()

      expect(result).toBeNull()
    })
  })

  describe('signIn', () => {
    it('should sign in user successfully', async () => {
      const credentials = { email: 'test@example.com', password: 'password123' }
      const mockUser = {
        userId: 'user123',
        signInDetails: { loginId: 'test@example.com' },
        attributes: { email: 'test@example.com' }
      }

      mockSignIn.mockResolvedValue({ isSignedIn: true, nextStep: undefined } as any)
      mockGetCurrentUser.mockResolvedValue(mockUser as any)

      const result = await AuthService.signIn(credentials)

      expect(mockSignIn).toHaveBeenCalledWith({
        username: credentials.email,
        password: credentials.password
      })
      expect(result).toEqual({
        id: 'user123',
        email: 'test@example.com',
        attributes: { email: 'test@example.com' }
      })
    })

    it('should throw error when sign in fails', async () => {
      const credentials = { email: 'test@example.com', password: 'wrongpassword' }
      
      mockSignIn.mockRejectedValue(new Error('Invalid credentials'))

      await expect(AuthService.signIn(credentials)).rejects.toThrow('Invalid credentials')
    })
  })

  describe('signUp', () => {
    it('should sign up user successfully', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
        timezone: 'America/New_York'
      }

      mockSignUp.mockResolvedValue({ isSignUpComplete: true, nextStep: undefined } as any)

      await expect(AuthService.signUp(credentials)).resolves.not.toThrow()

      expect(mockSignUp).toHaveBeenCalledWith({
        username: credentials.email,
        password: credentials.password,
        options: {
          userAttributes: {
            email: credentials.email,
            name: credentials.name,
            'custom:timezone': credentials.timezone
          }
        }
      })
    })

    it('should throw error when email confirmation is required', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
        timezone: 'America/New_York'
      }

      mockSignUp.mockResolvedValue({
        isSignUpComplete: false,
        nextStep: { signUpStep: 'CONFIRM_SIGN_UP' }
      } as any)

      await expect(AuthService.signUp(credentials)).rejects.toThrow('CONFIRM_SIGN_UP_REQUIRED')
    })
  })

  describe('getTokens', () => {
    it('should return tokens when session is valid', async () => {
      const mockTokens = {
        accessToken: { toString: () => 'access-token' },
        idToken: { toString: () => 'id-token' },
        refreshToken: { toString: () => 'refresh-token' }
      }

      mockFetchAuthSession.mockResolvedValue({ tokens: mockTokens } as any)

      const result = await AuthService.getTokens()

      expect(result).toEqual({
        accessToken: 'access-token',
        idToken: 'id-token',
        refreshToken: 'refresh-token'
      })
    })

    it('should return null when no tokens available', async () => {
      mockFetchAuthSession.mockResolvedValue({ tokens: null } as any)

      const result = await AuthService.getTokens()

      expect(result).toBeNull()
    })
  })

  describe('isSessionValid', () => {
    it('should return true when session is valid', async () => {
      mockFetchAuthSession.mockResolvedValue({
        tokens: { accessToken: { toString: () => 'token' } }
      } as any)

      const result = await AuthService.isSessionValid()

      expect(result).toBe(true)
    })

    it('should return false when session is invalid', async () => {
      mockFetchAuthSession.mockRejectedValue(new Error('Invalid session'))

      const result = await AuthService.isSessionValid()

      expect(result).toBe(false)
    })
  })
})