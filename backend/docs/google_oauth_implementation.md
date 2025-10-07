# Google OAuth 2.0 Implementation

This document describes the Google OAuth 2.0 implementation with PKCE support for the AWS Meeting Scheduling Agent.

## Overview

The Google OAuth implementation provides secure authentication and authorization for accessing Google Calendar and Gmail APIs. It includes:

- OAuth 2.0 authorization flow with PKCE (Proof Key for Code Exchange)
- Secure token storage with AWS KMS encryption
- Automatic token refresh handling
- Scope validation for Google Calendar and Gmail APIs
- Connection health monitoring

## Architecture

### Components

1. **GoogleOAuthService** (`src/services/google_oauth.py`)
   - Core OAuth service handling authorization flows
   - Token management and encryption
   - Connection status monitoring

2. **Connections Handler** (`src/handlers/connections.py`)
   - Lambda handler for OAuth API endpoints
   - Request routing and response formatting
   - Error handling and CORS support

3. **Encryption Utilities** (`src/utils/encryption.py`)
   - KMS-based token encryption/decryption
   - Secure storage of sensitive OAuth tokens

## API Endpoints

### Start OAuth Flow
```
POST /connections/google/auth/start
```

**Request Body:**
```json
{
  "redirect_uri": "https://your-app.com/callback",
  "state": "optional-csrf-token"
}
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "generated-state-token",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

### Handle OAuth Callback
```
POST /connections/google/auth/callback
```

**Request Body:**
```json
{
  "code": "authorization-code-from-google",
  "state": "state-token-from-start-flow"
}
```

**Response:**
```json
{
  "connection_id": "user123#google",
  "provider": "google",
  "profile": {
    "email": "user@example.com",
    "name": "User Name",
    "picture": "https://...",
    "google_id": "123456789"
  },
  "scopes": ["calendar", "gmail.send", "openid", "email", "profile"],
  "expires_at": "2024-01-01T01:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Check Connection Status
```
GET /connections/google/status
```

**Response:**
```json
{
  "connected": true,
  "provider": "google",
  "status": "active",
  "profile": {
    "email": "user@example.com",
    "name": "User Name"
  },
  "scopes": ["calendar", "gmail.send", "openid", "email", "profile"],
  "expires_at": "2024-01-01T01:00:00Z",
  "is_expired": false,
  "last_refresh": "2024-01-01T00:30:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Refresh Tokens
```
POST /connections/google/refresh
```

**Response:**
```json
{
  "connection_id": "user123#google",
  "expires_at": "2024-01-01T02:00:00Z",
  "last_refresh": "2024-01-01T01:00:00Z",
  "status": "active"
}
```

### Disconnect Account
```
DELETE /connections/google
```

**Response:**
```json
{
  "success": true
}
```

## Security Features

### PKCE (Proof Key for Code Exchange)
- Generates cryptographically secure code verifier and challenge
- Protects against authorization code interception attacks
- Uses SHA256 hashing with base64url encoding

### Token Encryption
- All OAuth tokens encrypted using AWS KMS customer-managed keys
- Separate encryption for access tokens and refresh tokens
- Automatic key rotation support

### Scope Validation
- Validates requested scopes against allowed list
- Required scopes:
  - `https://www.googleapis.com/auth/calendar` - Calendar read/write access
  - `https://www.googleapis.com/auth/gmail.send` - Gmail send access
  - `openid`, `email`, `profile` - Basic profile information

### Error Handling
- Comprehensive error handling for OAuth failures
- Automatic token refresh with exponential backoff
- Connection health monitoring and status reporting

## Environment Variables

The following environment variables must be configured:

- `CONNECTIONS_TABLE` - DynamoDB table name for storing connections
- `GOOGLE_OAUTH_SECRET` - AWS Secrets Manager secret name for OAuth credentials
- `KMS_KEY_ID` - AWS KMS key ID for token encryption

## AWS Resources Required

### DynamoDB Table (Connections)
```json
{
  "TableName": "Connections",
  "KeySchema": [
    {"AttributeName": "pk", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "pk", "AttributeType": "S"}
  ]
}
```

### Secrets Manager Secret
```json
{
  "client_id": "your-google-oauth-client-id",
  "client_secret": "your-google-oauth-client-secret"
}
```

### KMS Key Policy
The Lambda execution role must have permissions to encrypt/decrypt using the KMS key.

## Usage Example

```python
from src.services.google_oauth import GoogleOAuthService

# Initialize service
oauth_service = GoogleOAuthService()

# Start OAuth flow
auth_result = oauth_service.generate_authorization_url(
    user_id="user123",
    redirect_uri="https://your-app.com/callback"
)

# User visits authorization_url and grants permissions
# Your callback endpoint receives the authorization code

# Exchange code for tokens
token_result = oauth_service.exchange_code_for_tokens(
    user_id="user123",
    authorization_code="received_auth_code",
    state=auth_result["state"]
)

# Get valid credentials for API calls
credentials = oauth_service.get_valid_credentials("user123")

# Use credentials with Google API clients
from googleapiclient.discovery import build
calendar_service = build('calendar', 'v3', credentials=credentials)
```

## Testing

Run the test suite to verify the implementation:

```bash
cd backend
python -m pytest tests/test_google_oauth_simple.py -v
python -m pytest tests/test_connections_handler.py -v
```

## Error Scenarios

### Common Error Cases
1. **Invalid State** - PKCE state validation fails
2. **Expired Authorization** - Authorization code or state expired
3. **Token Refresh Failure** - Refresh token invalid or revoked
4. **Insufficient Scopes** - Required scopes not granted by user
5. **Network Errors** - Google API unavailable or rate limited

### Error Response Format
```json
{
  "error": "Error description",
  "message": "Detailed error message"
}
```

## Next Steps

This implementation provides the foundation for Google OAuth integration. The next task (3.2) will implement similar functionality for Microsoft OAuth flows.