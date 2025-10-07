export interface User {
  id: string
  email: string
  name?: string
  timezone?: string
  profile?: UserProfile
  attributes?: {
    email: string
    email_verified?: boolean
    name?: string
    [key: string]: any
  }
}

export interface UserProfile {
  name: string
  timezone: string
  defaultMeetingDuration: number
  autoBookEnabled: boolean
  createdAt: string
  updatedAt: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
  name: string
  timezone: string
}

export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (profile: Partial<UserProfile>) => Promise<void>
  refreshToken: () => Promise<void>
  clearError: () => void
}