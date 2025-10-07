export type OAuthProvider = 'google' | 'microsoft'

export interface OAuthConnection {
  id: string
  userId: string
  provider: OAuthProvider
  email: string
  scopes: string[]
  status: 'connected' | 'disconnected' | 'error' | 'expired'
  connectedAt: string
  lastRefresh?: string
  expiresAt?: string
  error?: string
}

export interface OAuthConnectionStatus {
  provider: OAuthProvider
  connected: boolean
  email?: string
  scopes?: string[]
  status: 'connected' | 'disconnected' | 'error' | 'expired'
  lastRefresh?: string
  expiresAt?: string
  error?: string
  healthCheck?: {
    calendar: boolean
    email: boolean
    lastChecked: string
  }
}

export interface OAuthAuthorizationUrl {
  provider: OAuthProvider
  authUrl: string
  state: string
}

export interface OAuthCallback {
  provider: OAuthProvider
  code: string
  state: string
}

export interface OAuthScopes {
  google: {
    calendar: string[]
    email: string[]
    required: string[]
  }
  microsoft: {
    calendar: string[]
    email: string[]
    required: string[]
  }
}

export const OAUTH_SCOPES: OAuthScopes = {
  google: {
    calendar: [
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.events'
    ],
    email: [
      'https://www.googleapis.com/auth/gmail.send'
    ],
    required: [
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.events',
      'https://www.googleapis.com/auth/gmail.send'
    ]
  },
  microsoft: {
    calendar: [
      'https://graph.microsoft.com/Calendars.ReadWrite'
    ],
    email: [
      'https://graph.microsoft.com/Mail.Send'
    ],
    required: [
      'https://graph.microsoft.com/Calendars.ReadWrite',
      'https://graph.microsoft.com/Mail.Send'
    ]
  }
}

export interface ConnectionHealthCheck {
  provider: OAuthProvider
  calendar: {
    accessible: boolean
    error?: string
  }
  email: {
    accessible: boolean
    error?: string
  }
  lastChecked: string
}