import { getCurrentUser, signIn, signUp, signOut, fetchAuthSession, updateUserAttributes, fetchUserAttributes, confirmSignUp, resendSignUpCode } from 'aws-amplify/auth'
import { User, LoginCredentials, RegisterCredentials, UserProfile } from '@/types/auth'

export class AuthService {
  /**
   * Get current authenticated user
   */
  static async getCurrentUser(): Promise<User | null> {
    try {
      const user = await getCurrentUser()
      const attributes = await fetchUserAttributes()
      console.log('Raw user object:', user) // Debug log
      console.log('User attributes:', attributes) // Debug log
      const userEmail = user.signInDetails?.loginId || attributes.email || ''
      const emailVerified = attributes.email_verified === 'true' || (attributes.email_verified as any) === true
      
      return {
        id: user.userId,
        email: userEmail,
        attributes: {
          email: userEmail,
          email_verified: emailVerified,
          name: attributes.name,
          ...Object.fromEntries(
            Object.entries(attributes).filter(([key]) => !['email', 'email_verified', 'name'].includes(key))
          )
        }
      }
    } catch (error) {
      console.error('Error getting current user:', error)
      return null
    }
  }

  /**
   * Sign in user with email and password
   */
  static async signIn(credentials: LoginCredentials): Promise<User> {
    try {
      const { isSignedIn, nextStep } = await signIn({
        username: credentials.email,
        password: credentials.password
      })

      if (!isSignedIn) {
        throw new Error(`Sign in incomplete: ${nextStep?.signInStep}`)
      }

      const user = await this.getCurrentUser()
      if (!user) {
        throw new Error('Failed to get user after sign in')
      }

      return user
    } catch (error: any) {
      console.error('Sign in error:', error)
      throw new Error(error.message || 'Failed to sign in')
    }
  }

  /**
   * Register new user
   */
  static async signUp(credentials: RegisterCredentials): Promise<void> {
    try {
      const { isSignUpComplete, nextStep } = await signUp({
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

      if (!isSignUpComplete && nextStep?.signUpStep === 'CONFIRM_SIGN_UP') {
        throw new Error('CONFIRM_SIGN_UP_REQUIRED')
      }
    } catch (error: any) {
      console.error('Sign up error:', error)
      throw new Error(error.message || 'Failed to sign up')
    }
  }

  /**
   * Sign out current user
   */
  static async signOut(): Promise<void> {
    try {
      await signOut()
    } catch (error: any) {
      console.error('Sign out error:', error)
      throw new Error(error.message || 'Failed to sign out')
    }
  }

  /**
   * Get current JWT tokens
   */
  static async getTokens(): Promise<{ accessToken: string; idToken: string; refreshToken: string } | null> {
    try {
      const session = await fetchAuthSession()
      const tokens = session.tokens
      
      if (!tokens) {
        return null
      }

      return {
        accessToken: tokens.accessToken?.toString() || '',
        idToken: tokens.idToken?.toString() || '',
        refreshToken: (tokens as any).refreshToken?.toString() || ''
      }
    } catch (error) {
      console.error('Error getting tokens:', error)
      return null
    }
  }

  /**
   * Check if current session is valid
   */
  static async isSessionValid(): Promise<boolean> {
    try {
      const session = await fetchAuthSession()
      return !!session.tokens?.accessToken
    } catch (error) {
      return false
    }
  }

  /**
   * Update user profile attributes
   */
  static async updateUserProfile(profile: Partial<UserProfile>): Promise<void> {
    try {
      const attributes: Record<string, string> = {}
      
      if (profile.name) {
        attributes.name = profile.name
      }
      if (profile.timezone) {
        attributes['custom:timezone'] = profile.timezone
      }

      await updateUserAttributes({
        userAttributes: attributes
      })
    } catch (error: any) {
      console.error('Update profile error:', error)
      throw new Error(error.message || 'Failed to update profile')
    }
  }

  /**
   * Confirm user sign up with verification code
   */
  static async confirmSignUp(email: string, code: string): Promise<void> {
    try {
      const { isSignUpComplete } = await confirmSignUp({
        username: email,
        confirmationCode: code
      })

      if (!isSignUpComplete) {
        throw new Error('Sign up confirmation failed')
      }
    } catch (error: any) {
      console.error('Confirm sign up error:', error)
      throw new Error(error.message || 'Failed to confirm sign up')
    }
  }

  /**
   * Resend confirmation code to user's email
   */
  static async resendConfirmationCode(email: string): Promise<void> {
    try {
      await resendSignUpCode({
        username: email
      })
    } catch (error: any) {
      console.error('Resend confirmation code error:', error)
      throw new Error(error.message || 'Failed to resend confirmation code')
    }
  }

  /**
   * Refresh authentication session
   */
  static async refreshSession(): Promise<void> {
    try {
      // Force refresh the session
      await fetchAuthSession({ forceRefresh: true })
    } catch (error: any) {
      console.error('Refresh session error:', error)
      throw new Error(error.message || 'Failed to refresh session')
    }
  }
}