import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { AuthService } from '@/utils/auth'
import { User, AuthState, AuthContextType, LoginCredentials, RegisterCredentials, UserProfile } from '@/types/auth'

// Auth reducer
type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
        error: null
      }
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false }
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    default:
      return state
  }
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth()
  }, [])

  // Set up automatic token refresh
  useEffect(() => {
    if (state.isAuthenticated) {
      const interval = setInterval(async () => {
        try {
          await AuthService.refreshSession()
        } catch (error) {
          console.error('Auto refresh failed:', error)
          // If refresh fails, sign out user
          await logout()
        }
      }, 50 * 60 * 1000) // Refresh every 50 minutes

      return () => clearInterval(interval)
    }
  }, [state.isAuthenticated])

  const initializeAuth = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      
      const isValid = await AuthService.isSessionValid()
      if (isValid) {
        const user = await AuthService.getCurrentUser()
        dispatch({ type: 'SET_USER', payload: user })
      } else {
        dispatch({ type: 'SET_USER', payload: null })
      }
    } catch (error: any) {
      console.error('Auth initialization error:', error)
      dispatch({ type: 'SET_ERROR', payload: error.message })
      dispatch({ type: 'SET_USER', payload: null })
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      dispatch({ type: 'CLEAR_ERROR' })
      
      const user = await AuthService.signIn(credentials)
      dispatch({ type: 'SET_USER', payload: user })
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  const register = async (credentials: RegisterCredentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      dispatch({ type: 'CLEAR_ERROR' })
      
      await AuthService.signUp(credentials)
      // Note: User will need to confirm email before they can sign in
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  const logout = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      await AuthService.signOut()
      dispatch({ type: 'SET_USER', payload: null })
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  const updateProfile = async (profile: Partial<UserProfile>) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true })
      await AuthService.updateUserProfile(profile)
      
      // Refresh user data
      const user = await AuthService.getCurrentUser()
      dispatch({ type: 'SET_USER', payload: user })
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  const refreshToken = async () => {
    try {
      await AuthService.refreshSession()
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
      throw error
    }
  }

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' })
  }

  const value: AuthContextType = {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    login,
    register,
    logout,
    updateProfile,
    refreshToken,
    clearError
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}