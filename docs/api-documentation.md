# API Documentation

This document provides comprehensive API documentation for the AWS Meeting Scheduling Agent, including authentication, endpoints, request/response formats, and usage examples.

## Base URL

```
Production: https://api.meeting-agent.example.com
Development: https://dev-api.meeting-agent.example.com
Local: http://localhost:3000/api
```

## Authentication

All API requests require authentication using JWT tokens obtained from Amazon Cognito.

### Authentication Header
```http
Authorization: Bearer <jwt_token>
```

### Getting Authentication Token

```javascript
// Using AWS Amplify
import { Auth } from 'aws-amplify';

const session = await Auth.currentSession();
const token = session.getIdToken().getJwtToken();
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/login
Authenticate user with Cognito credentials.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJSUzI1NiIs...",
    "refreshToken": "eyJjdHkiOiJKV1QiLCJlbmMi...",
    "idToken": "eyJraWQiOiJVbzFuK0Fv...",
    "user": {
      "id": "user-123",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

#### POST /auth/refresh
Refresh authentication token.

**Request:**
```json
{
  "refreshToken": "eyJjdHkiOiJKV1QiLCJlbmMi..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJSUzI1NiIs...",
    "idToken": "eyJraWQiOiJVbzFuK0Fv..."
  }
}
```

### OAuth Integration Endpoints

#### GET /oauth/google/authorize
Initiate Google OAuth flow.

**Query Parameters:**
- `redirect_uri` (string): Callback URL after authorization

**Response:**
```json
{
  "success": true,
  "data": {
    "authUrl": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
    "state": "random-state-string"
  }
}
```

#### POST /oauth/google/callback
Handle Google OAuth callback.

**Request:**
```json
{
  "code": "authorization_code",
  "state": "random-state-string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "connectionId": "conn-123",
    "provider": "google",
    "accountEmail": "user@gmail.com",
    "isActive": true
  }
}
```

#### GET /oauth/microsoft/authorize
Initiate Microsoft OAuth flow.

**Query Parameters:**
- `redirect_uri` (string): Callback URL after authorization

**Response:**
```json
{
  "success": true,
  "data": {
    "authUrl": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=...",
    "state": "random-state-string"
  }
}
```

#### POST /oauth/microsoft/callback
Handle Microsoft OAuth callback.

**Request:**
```json
{
  "code": "authorization_code",
  "state": "random-state-string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "connectionId": "conn-456",
    "provider": "microsoft",
    "accountEmail": "user@outlook.com",
    "isActive": true
  }
}
```

### Calendar Management Endpoints

#### GET /calendar/connections
Get user's calendar connections.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "connectionId": "conn-123",
      "provider": "google",
      "accountEmail": "user@gmail.com",
      "isActive": true,
      "lastSync": "2024-01-15T10:30:00Z",
      "createdAt": "2024-01-01T00:00:00Z"
    },
    {
      "connectionId": "conn-456",
      "provider": "microsoft",
      "accountEmail": "user@outlook.com",
      "isActive": true,
      "lastSync": "2024-01-15T10:25:00Z",
      "createdAt": "2024-01-02T00:00:00Z"
    }
  ]
}
```

#### POST /calendar/sync
Trigger calendar synchronization.

**Request:**
```json
{
  "connectionId": "conn-123",
  "forceSync": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "syncId": "sync-789",
    "status": "in_progress",
    "eventsProcessed": 0,
    "startedAt": "2024-01-15T10:35:00Z"
  }
}
```

#### GET /calendar/events
Get calendar events.

**Query Parameters:**
- `startDate` (string): Start date (ISO 8601)
- `endDate` (string): End date (ISO 8601)
- `connectionId` (string, optional): Filter by connection
- `limit` (number, optional): Maximum events to return (default: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "events": [
      {
        "eventId": "event-123",
        "title": "Team Meeting",
        "description": "Weekly team sync",
        "startTime": "2024-01-15T14:00:00Z",
        "endTime": "2024-01-15T15:00:00Z",
        "timezone": "America/New_York",
        "attendees": [
          {
            "email": "attendee@example.com",
            "name": "Jane Smith",
            "status": "accepted"
          }
        ],
        "location": "Conference Room A",
        "provider": "google",
        "connectionId": "conn-123"
      }
    ],
    "pagination": {
      "total": 25,
      "limit": 100,
      "offset": 0
    }
  }
}
```

### Meeting Scheduling Endpoints

#### POST /meetings/schedule
Schedule a new meeting with AI assistance.

**Request:**
```json
{
  "title": "Project Review Meeting",
  "description": "Review Q1 project progress",
  "attendees": [
    {
      "email": "attendee1@example.com",
      "name": "John Doe"
    },
    {
      "email": "attendee2@example.com", 
      "name": "Jane Smith"
    }
  ],
  "duration": 60,
  "preferredTimes": [
    {
      "startTime": "2024-01-16T14:00:00Z",
      "endTime": "2024-01-16T17:00:00Z"
    }
  ],
  "priority": "high",
  "requirements": {
    "requiresAllAttendees": true,
    "allowConflicts": false,
    "bufferTime": 15
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "meetingId": "meeting-123",
    "schedulingStatus": "scheduled",
    "scheduledTime": {
      "startTime": "2024-01-16T15:00:00Z",
      "endTime": "2024-01-16T16:00:00Z",
      "timezone": "America/New_York"
    },
    "aiAnalysis": {
      "conflictsDetected": 0,
      "alternativesConsidered": 3,
      "confidenceScore": 0.95,
      "reasoning": "Optimal time slot found with no conflicts for all attendees"
    },
    "invitationsSent": true
  }
}
```

#### GET /meetings/{meetingId}
Get meeting details.

**Response:**
```json
{
  "success": true,
  "data": {
    "meetingId": "meeting-123",
    "title": "Project Review Meeting",
    "description": "Review Q1 project progress",
    "startTime": "2024-01-16T15:00:00Z",
    "endTime": "2024-01-16T16:00:00Z",
    "timezone": "America/New_York",
    "attendees": [
      {
        "email": "attendee1@example.com",
        "name": "John Doe",
        "status": "accepted"
      }
    ],
    "status": "scheduled",
    "createdAt": "2024-01-15T10:40:00Z",
    "updatedAt": "2024-01-15T10:40:00Z"
  }
}
```

#### PUT /meetings/{meetingId}
Update meeting details.

**Request:**
```json
{
  "title": "Updated Project Review Meeting",
  "description": "Updated description",
  "startTime": "2024-01-16T16:00:00Z",
  "endTime": "2024-01-16T17:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "meetingId": "meeting-123",
    "updated": true,
    "changes": ["title", "description", "startTime", "endTime"],
    "reschedulingRequired": true
  }
}
```

#### DELETE /meetings/{meetingId}
Cancel a meeting.

**Response:**
```json
{
  "success": true,
  "data": {
    "meetingId": "meeting-123",
    "cancelled": true,
    "cancellationsSent": true
  }
}
```

### Conflict Resolution Endpoints

#### GET /conflicts
Get scheduling conflicts.

**Query Parameters:**
- `status` (string, optional): Filter by status (pending, resolved, ignored)
- `limit` (number, optional): Maximum conflicts to return

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "conflictId": "conflict-123",
      "meetingId": "meeting-123",
      "conflictingMeetingId": "meeting-456",
      "conflictType": "time_overlap",
      "status": "pending",
      "resolutionSuggestions": [
        {
          "type": "reschedule",
          "suggestedTime": "2024-01-16T17:00:00Z",
          "confidence": 0.9
        },
        {
          "type": "shorten",
          "suggestedDuration": 30,
          "confidence": 0.7
        }
      ],
      "detectedAt": "2024-01-15T10:45:00Z"
    }
  ]
}
```

#### POST /conflicts/{conflictId}/resolve
Resolve a scheduling conflict.

**Request:**
```json
{
  "resolution": "reschedule",
  "newStartTime": "2024-01-16T17:00:00Z",
  "newEndTime": "2024-01-16T18:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conflictId": "conflict-123",
    "resolved": true,
    "resolution": "reschedule",
    "updatedMeetings": ["meeting-123"],
    "resolvedAt": "2024-01-15T10:50:00Z"
  }
}
```

### AI Analysis Endpoints

#### POST /ai/analyze-schedule
Get AI analysis of scheduling request.

**Request:**
```json
{
  "attendees": ["user1@example.com", "user2@example.com"],
  "duration": 60,
  "preferredTimes": [
    {
      "startTime": "2024-01-16T14:00:00Z",
      "endTime": "2024-01-16T17:00:00Z"
    }
  ],
  "requirements": {
    "priority": "high",
    "requiresAllAttendees": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": {
      "optimalTimeSlots": [
        {
          "startTime": "2024-01-16T15:00:00Z",
          "endTime": "2024-01-16T16:00:00Z",
          "confidence": 0.95,
          "reasoning": "No conflicts, all attendees available"
        }
      ],
      "conflicts": [],
      "alternatives": [
        {
          "startTime": "2024-01-16T16:00:00Z",
          "endTime": "2024-01-16T17:00:00Z",
          "confidence": 0.85,
          "reasoning": "Minor conflict with one attendee's low-priority meeting"
        }
      ],
      "recommendations": [
        "Schedule at 3:00 PM for optimal availability",
        "Consider 15-minute buffer before next meeting"
      ]
    }
  }
}
```

#### POST /ai/suggest-reschedule
Get AI suggestions for rescheduling.

**Request:**
```json
{
  "meetingId": "meeting-123",
  "reason": "conflict_detected",
  "constraints": {
    "mustBeThisWeek": true,
    "preferredDays": ["monday", "tuesday", "wednesday"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "startTime": "2024-01-17T14:00:00Z",
        "endTime": "2024-01-17T15:00:00Z",
        "confidence": 0.9,
        "reasoning": "All attendees available, no conflicts"
      },
      {
        "startTime": "2024-01-18T10:00:00Z",
        "endTime": "2024-01-18T11:00:00Z",
        "confidence": 0.8,
        "reasoning": "Good availability, early morning slot"
      }
    ],
    "analysisId": "analysis-456"
  }
}
```### U
ser Preferences Endpoints

#### GET /user/preferences
Get user preferences and settings.

**Response:**
```json
{
  "success": true,
  "data": {
    "userId": "user-123",
    "preferences": {
      "timezone": "America/New_York",
      "workingHours": {
        "start": "09:00",
        "end": "17:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
      },
      "meetingDefaults": {
        "duration": 30,
        "bufferTime": 15,
        "autoAcceptInvites": false
      },
      "notifications": {
        "email": true,
        "inApp": true,
        "reminderMinutes": 15
      },
      "aiSettings": {
        "aggressiveScheduling": false,
        "allowConflictResolution": true,
        "priorityWeighting": "balanced"
      }
    }
  }
}
```

#### PUT /user/preferences
Update user preferences.

**Request:**
```json
{
  "timezone": "America/Los_Angeles",
  "workingHours": {
    "start": "08:00",
    "end": "16:00"
  },
  "aiSettings": {
    "aggressiveScheduling": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "updated": true,
    "changes": ["timezone", "workingHours", "aiSettings"]
  }
}
```

### Notification Endpoints

#### GET /notifications
Get user notifications.

**Query Parameters:**
- `status` (string, optional): Filter by status (unread, read, all)
- `type` (string, optional): Filter by type (meeting, conflict, system)
- `limit` (number, optional): Maximum notifications to return

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "notificationId": "notif-123",
      "type": "meeting",
      "title": "Meeting Scheduled",
      "message": "Your meeting 'Project Review' has been scheduled for Jan 16 at 3:00 PM",
      "status": "unread",
      "createdAt": "2024-01-15T10:40:00Z",
      "data": {
        "meetingId": "meeting-123",
        "action": "scheduled"
      }
    }
  ]
}
```

#### PUT /notifications/{notificationId}/read
Mark notification as read.

**Response:**
```json
{
  "success": true,
  "data": {
    "notificationId": "notif-123",
    "marked": "read"
  }
}
```

### Health and Status Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:55:00Z",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "bedrock": "healthy",
      "oauth": "healthy"
    }
  }
}
```

#### GET /status
System status and metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "uptime": 86400,
    "activeUsers": 150,
    "meetingsScheduled": 1250,
    "conflictsResolved": 45,
    "lastDeployment": "2024-01-15T08:00:00Z"
  }
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "requestId": "req-123456"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### OAuth-Specific Errors

| Code | Description |
|------|-------------|
| `OAUTH_INVALID_CODE` | Invalid authorization code |
| `OAUTH_EXPIRED_TOKEN` | OAuth token has expired |
| `OAUTH_REVOKED_ACCESS` | User revoked access |
| `OAUTH_SCOPE_INSUFFICIENT` | Insufficient OAuth scopes |

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Authenticated requests**: 1000 requests per hour per user
- **OAuth endpoints**: 10 requests per minute per IP
- **AI analysis endpoints**: 100 requests per hour per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## Pagination

List endpoints support pagination using offset-based pagination:

**Request Parameters:**
- `limit` (number): Number of items per page (max 100, default 20)
- `offset` (number): Number of items to skip (default 0)

**Response Format:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "total": 150,
      "limit": 20,
      "offset": 0,
      "hasMore": true
    }
  }
}
```

## Webhooks

The system supports webhooks for real-time notifications:

### Webhook Events

- `meeting.scheduled` - New meeting scheduled
- `meeting.updated` - Meeting details updated
- `meeting.cancelled` - Meeting cancelled
- `conflict.detected` - Scheduling conflict detected
- `conflict.resolved` - Conflict resolved
- `calendar.synced` - Calendar synchronization completed

### Webhook Payload Format

```json
{
  "eventType": "meeting.scheduled",
  "timestamp": "2024-01-15T10:40:00Z",
  "userId": "user-123",
  "data": {
    "meetingId": "meeting-123",
    "title": "Project Review Meeting",
    "startTime": "2024-01-16T15:00:00Z",
    "endTime": "2024-01-16T16:00:00Z"
  }
}
```

## SDK Examples

### JavaScript/TypeScript

```javascript
import axios from 'axios';

class MeetingAgentAPI {
  constructor(baseURL, token) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async scheduleMeeting(meetingData) {
    const response = await this.client.post('/meetings/schedule', meetingData);
    return response.data;
  }

  async getCalendarEvents(startDate, endDate) {
    const response = await this.client.get('/calendar/events', {
      params: { startDate, endDate }
    });
    return response.data;
  }

  async connectGoogleCalendar(authCode, state) {
    const response = await this.client.post('/oauth/google/callback', {
      code: authCode,
      state
    });
    return response.data;
  }
}

// Usage
const api = new MeetingAgentAPI('https://api.meeting-agent.example.com', token);

const meeting = await api.scheduleMeeting({
  title: 'Team Standup',
  attendees: [{ email: 'team@example.com' }],
  duration: 30,
  preferredTimes: [{
    startTime: '2024-01-16T09:00:00Z',
    endTime: '2024-01-16T12:00:00Z'
  }]
});
```

### Python

```python
import requests
from datetime import datetime, timezone

class MeetingAgentAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def schedule_meeting(self, meeting_data):
        response = requests.post(
            f'{self.base_url}/meetings/schedule',
            json=meeting_data,
            headers=self.headers
        )
        return response.json()
    
    def get_calendar_events(self, start_date, end_date):
        params = {
            'startDate': start_date.isoformat(),
            'endDate': end_date.isoformat()
        }
        response = requests.get(
            f'{self.base_url}/calendar/events',
            params=params,
            headers=self.headers
        )
        return response.json()

# Usage
api = MeetingAgentAPI('https://api.meeting-agent.example.com', token)

meeting = api.schedule_meeting({
    'title': 'Team Standup',
    'attendees': [{'email': 'team@example.com'}],
    'duration': 30,
    'preferredTimes': [{
        'startTime': '2024-01-16T09:00:00Z',
        'endTime': '2024-01-16T12:00:00Z'
    }]
})
```

## Testing

### Postman Collection

A Postman collection is available for testing all API endpoints:

```json
{
  "info": {
    "name": "AWS Meeting Scheduling Agent API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{jwt_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://api.meeting-agent.example.com"
    }
  ]
}
```

### cURL Examples

**Schedule a meeting:**
```bash
curl -X POST https://api.meeting-agent.example.com/meetings/schedule \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "attendees": [{"email": "team@example.com"}],
    "duration": 60,
    "preferredTimes": [{
      "startTime": "2024-01-16T14:00:00Z",
      "endTime": "2024-01-16T17:00:00Z"
    }]
  }'
```

**Get calendar events:**
```bash
curl -X GET "https://api.meeting-agent.example.com/calendar/events?startDate=2024-01-16T00:00:00Z&endDate=2024-01-17T00:00:00Z" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Next Steps

1. Review the [Setup Guide](./setup-deployment.md) for API deployment
2. Check the [Troubleshooting Guide](./troubleshooting.md) for common API issues
3. See the [Architecture Overview](./architecture.md) for system design details