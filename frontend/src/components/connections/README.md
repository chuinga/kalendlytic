# OAuth Connection Interface

This module implements the OAuth connection interface for the AWS Meeting Scheduling Agent, allowing users to connect their Google and Microsoft accounts for calendar and email integration.

## Components

### ConnectionsPage
The main page component that displays all OAuth connections and allows users to manage them.

**Features:**
- Displays connection status for Google and Microsoft accounts
- Shows connection health indicators
- Provides connect/disconnect/reconnect functionality
- Displays required permissions and privacy information

### ConnectionCard
Individual connection card component for each OAuth provider.

**Features:**
- Shows connection status (connected, disconnected, error, expired)
- Displays connected email and last refresh time
- Provides action buttons (Connect, Disconnect, Reconnect, Test Connection)
- Shows connection health test results
- Displays error messages when connections fail

### ConnectionStatus
A compact status indicator component that can be used in headers or dashboards.

**Features:**
- Shows overall connection status
- Displays connection count (e.g., "2/2 connected")
- Can show detailed status for each provider
- Links to the connections management page

### OAuthCallback
Handles OAuth callback processing after users authorize their accounts.

**Features:**
- Processes OAuth authorization codes
- Displays loading, success, and error states
- Automatically redirects back to connections page
- Handles errors gracefully

## Hooks

### useConnections
React hook for managing OAuth connections state and operations.

**Returns:**
- `connections`: Array of connection status objects
- `loading`: Boolean indicating if operations are in progress
- `error`: Error message if operations fail
- `refreshConnections()`: Refresh connection status from server
- `connectProvider(provider)`: Start OAuth flow for a provider
- `disconnectProvider(provider)`: Disconnect a provider
- `reconnectProvider(provider)`: Reconnect/refresh a provider
- `testConnection(provider)`: Test connection health
- `clearError()`: Clear error state

## Services

### ConnectionsService
API service for OAuth connection operations.

**Methods:**
- `getConnections()`: Get all user connections
- `getConnectionStatus(provider)`: Get status for specific provider
- `startOAuthFlow(provider)`: Start OAuth authorization
- `completeOAuthFlow(callback)`: Complete OAuth with authorization code
- `disconnectProvider(provider)`: Remove provider connection
- `reconnectProvider(provider)`: Refresh provider connection
- `testConnection(provider)`: Test connection health
- `refreshTokens(provider)`: Refresh OAuth tokens

## Types

### OAuthProvider
Union type for supported providers: `'google' | 'microsoft'`

### OAuthConnectionStatus
Interface representing the status of an OAuth connection:
```typescript
{
  provider: OAuthProvider
  connected: boolean
  status: 'connected' | 'disconnected' | 'error' | 'expired'
  email?: string
  scopes?: string[]
  lastRefresh?: string
  expiresAt?: string
  error?: string
  healthCheck?: {
    calendar: boolean
    email: boolean
    lastChecked: string
  }
}
```

## OAuth Flows

### Google OAuth Flow
1. User clicks "Connect Google"
2. `startOAuthFlow('google')` creates authorization URL
3. User is redirected to Google OAuth consent screen
4. Google redirects to `/oauth/google/callback` with authorization code
5. `completeOAuthFlow()` exchanges code for tokens
6. Tokens are encrypted and stored in DynamoDB
7. User is redirected back to connections page

### Microsoft OAuth Flow
1. User clicks "Connect Microsoft"
2. `startOAuthFlow('microsoft')` creates authorization URL
3. User is redirected to Microsoft OAuth consent screen
4. Microsoft redirects to `/oauth/microsoft/callback` with authorization code
5. `completeOAuthFlow()` exchanges code for tokens
6. Tokens are encrypted and stored in DynamoDB
7. User is redirected back to connections page

## Required Scopes

### Google Scopes
- `https://www.googleapis.com/auth/calendar` - Calendar read/write
- `https://www.googleapis.com/auth/calendar.events` - Calendar events
- `https://www.googleapis.com/auth/gmail.send` - Send emails

### Microsoft Scopes
- `https://graph.microsoft.com/Calendars.ReadWrite` - Calendar read/write
- `https://graph.microsoft.com/Mail.Send` - Send emails

## Security Features

- OAuth tokens are encrypted using AWS KMS before storage
- Tokens are automatically refreshed when expired
- Connection health checks verify API access
- Minimal required scopes are requested
- Secure callback URL validation

## Usage Example

```tsx
import { ConnectionsPage } from '@/components/connections'

export default function ConnectionsRoute() {
  return <ConnectionsPage />
}
```

```tsx
import { ConnectionStatus } from '@/components/connections'

export default function Header() {
  return (
    <header>
      <ConnectionStatus showDetails />
    </header>
  )
}
```