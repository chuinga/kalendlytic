# Frequently Asked Questions (FAQ)

This document answers common questions about the AWS Meeting Scheduling Agent.

## General Questions

### What is the AWS Meeting Scheduling Agent?

The AWS Meeting Scheduling Agent is an AI-powered meeting scheduling system that automates calendar management across Gmail and Outlook using Amazon Bedrock and AgentCore primitives. It intelligently detects conflicts, suggests optimal meeting times, and handles scheduling coordination automatically.

### What calendar platforms are supported?

Currently supported platforms:
- **Google Calendar** (via Google Calendar API)
- **Microsoft Outlook** (via Microsoft Graph API)
- **Gmail** (for email notifications)
- **Outlook** (for email notifications)

### How does the AI scheduling work?

The system uses Amazon Bedrock with Claude 3.5 Sonnet to:
- Analyze calendar availability across all connected accounts
- Detect and resolve scheduling conflicts
- Prioritize meetings based on importance and attendee preferences
- Suggest optimal time slots considering working hours and preferences
- Generate intelligent rescheduling recommendations

### Is my calendar data secure?

Yes, security is a top priority:
- **OAuth 2.0 + PKCE** for secure authentication
- **KMS encryption** for all stored data
- **Encrypted tokens** in AWS Secrets Manager
- **PII redaction** in logs and monitoring
- **Least-privilege IAM policies** for all resources
- **Audit logging** for all user actions

## Setup and Configuration

### What AWS services are required?

The system uses the following AWS services:
- **Amazon Bedrock** (Claude 3.5 Sonnet)
- **AWS Lambda** (compute)
- **Amazon DynamoDB** (database)
- **Amazon Cognito** (authentication)
- **API Gateway** (API management)
- **CloudFront** (CDN)
- **S3** (static hosting)
- **Secrets Manager** (credential storage)
- **CloudWatch** (monitoring)

### How much does it cost to run?

Costs depend on usage but typical monthly costs for moderate use:
- **Bedrock**: $10-50 (based on AI requests)
- **Lambda**: $5-20 (based on function executions)
- **DynamoDB**: $5-15 (based on data storage and requests)
- **Other services**: $10-25 (API Gateway, CloudFront, etc.)

**Total estimated cost**: $30-110/month for typical usage

### Can I run this locally for development?

Yes, the system supports local development:
```bash
# Backend (using SAM)
cd backend
sam local start-api

# Frontend
cd frontend
npm run dev
```

You'll need to configure OAuth applications to point to `localhost:3000` for local testing.

### How do I get OAuth credentials?

Follow the detailed [OAuth Setup Guide](./oauth-setup.md):

1. **Google**: Create project in Google Cloud Console, enable APIs, create OAuth client
2. **Microsoft**: Register app in Azure Portal, configure permissions, create client secret

Both require setting up redirect URIs and proper scopes.

## Usage Questions

### How do I connect my calendar accounts?

1. **Login** to the application with your Cognito credentials
2. **Navigate** to Settings or Dashboard
3. **Click** "Connect Google Calendar" or "Connect Microsoft Calendar"
4. **Authorize** the application in the OAuth flow
5. **Verify** the connection appears in your connected accounts

### Can I connect multiple Google or Outlook accounts?

Yes, you can connect multiple accounts from the same provider:
- Multiple Gmail accounts
- Multiple Outlook accounts
- Mix of personal and work accounts

Each connection is managed separately with its own OAuth tokens.

### How does conflict detection work?

The AI analyzes:
- **Time overlaps** between meetings
- **Travel time** between locations
- **Buffer time** preferences
- **Meeting priorities** and importance
- **Attendee availability** across all connected calendars

When conflicts are detected, the system suggests:
- Alternative time slots
- Meeting duration adjustments
- Priority-based rescheduling

### Can I set working hours and preferences?

Yes, you can configure:
- **Working hours** (start/end times, days of week)
- **Time zone** preferences
- **Default meeting duration**
- **Buffer time** between meetings
- **Meeting priorities** and weighting
- **Notification preferences**

### How accurate are the AI suggestions?

The AI provides confidence scores with each suggestion:
- **90-100%**: High confidence, optimal time found
- **70-89%**: Good option with minor compromises
- **50-69%**: Acceptable but requires trade-offs
- **Below 50%**: Limited options, manual review recommended

### What happens if I decline a suggested time?

The system will:
1. **Learn** from your preference
2. **Generate** new suggestions
3. **Adjust** future recommendations based on your patterns
4. **Consider** alternative approaches (shorter meetings, different days, etc.)

## Technical Questions

### How is data synchronized between calendars?

The system uses:
- **Real-time sync** via webhooks when possible
- **Periodic sync** every 15-30 minutes as fallback
- **On-demand sync** when scheduling meetings
- **Incremental updates** to minimize API calls

### What happens if a calendar service is down?

The system includes resilience features:
- **Graceful degradation** - works with available calendars
- **Retry logic** with exponential backoff
- **Cached data** for recent calendar information
- **Status notifications** when services are unavailable

### Can I export my data?

Yes, you can export:
- **Meeting history** via API or dashboard
- **Calendar connections** and settings
- **AI analysis** and suggestions
- **Audit logs** of all actions

Data is available in JSON format through the API.

### How do I backup my configuration?

Configuration is automatically backed up:
- **DynamoDB** point-in-time recovery (35 days)
- **Cross-region replication** for critical data
- **Configuration export** via API
- **OAuth tokens** securely stored in Secrets Manager

### Is there an API for integration?

Yes, comprehensive REST API available:
- **Authentication** endpoints
- **Calendar management** 
- **Meeting scheduling**
- **Conflict resolution**
- **User preferences**
- **Webhooks** for real-time notifications

See the [API Documentation](./api-documentation.md) for details.

## Troubleshooting

### Why aren't my calendar events showing up?

Common causes and solutions:

1. **OAuth token expired**:
   - Reconnect your calendar account
   - Check token expiration in settings

2. **Insufficient permissions**:
   - Verify OAuth scopes include calendar read access
   - Re-authorize with proper permissions

3. **Sync issues**:
   - Trigger manual sync from settings
   - Check last sync timestamp

4. **Date range filters**:
   - Verify you're looking at the correct date range
   - Check timezone settings

### Why is scheduling taking a long time?

Possible reasons:

1. **Complex scheduling requirements**:
   - Many attendees with busy calendars
   - Limited available time slots
   - Multiple constraints and preferences

2. **Large calendar datasets**:
   - Extensive meeting history
   - Multiple connected accounts
   - High frequency of events

3. **AI processing time**:
   - Complex conflict resolution
   - Multiple alternative scenarios
   - Detailed analysis and reasoning

### How do I resolve OAuth errors?

Common OAuth issues:

1. **"redirect_uri_mismatch"**:
   - Verify redirect URI exactly matches OAuth app configuration
   - Check for HTTP vs HTTPS, trailing slashes

2. **"invalid_client"**:
   - Verify client ID and secret are correct
   - Check if client secret has expired (Microsoft)

3. **"access_denied"**:
   - User declined permissions
   - App not approved for requested scopes

4. **"invalid_scope"**:
   - Requested permissions not configured in OAuth app
   - APIs not enabled (Google)

### What if the AI makes poor suggestions?

To improve AI performance:

1. **Provide feedback**:
   - Rate suggestions (thumbs up/down)
   - Specify why suggestions don't work

2. **Update preferences**:
   - Refine working hours and availability
   - Set meeting priorities and importance levels
   - Configure buffer times and constraints

3. **Add context**:
   - Include meeting descriptions and requirements
   - Specify attendee importance and roles
   - Set location and travel time considerations

## Privacy and Security

### What data is stored?

The system stores:
- **User profile** (name, email, preferences)
- **Calendar connections** (OAuth tokens, encrypted)
- **Meeting metadata** (titles, times, attendees)
- **AI analysis** (suggestions, reasoning)
- **Audit logs** (user actions, system events)

**Not stored**:
- Meeting content or descriptions (unless explicitly provided)
- Email content
- Personal files or attachments

### How long is data retained?

Data retention policies:
- **Active user data**: Retained while account is active
- **Meeting history**: 2 years (configurable)
- **Audit logs**: 7 years (compliance)
- **OAuth tokens**: Until revoked or expired
- **AI analysis**: 90 days (for learning and improvement)

### Can I delete my data?

Yes, you have full control:
- **Account deletion**: Removes all associated data
- **Selective deletion**: Remove specific meetings or connections
- **Data export**: Download your data before deletion
- **Right to be forgotten**: Complete data removal upon request

### Who has access to my data?

Access is strictly controlled:
- **You**: Full access to your own data
- **System**: Automated processing only
- **AWS services**: Encrypted data processing only
- **No human access**: Unless explicitly authorized for support

### Is data shared with third parties?

No, your data is never shared:
- **No selling** of user data
- **No marketing** use of personal information
- **No third-party analytics** on personal data
- **OAuth providers**: Only receive standard API requests

## Billing and Limits

### Are there usage limits?

Current limits (can be increased):
- **API requests**: 1000/hour per user
- **AI requests**: 100/hour per user
- **Calendar connections**: 10 per user
- **Meeting history**: 10,000 meetings per user
- **File storage**: 1GB per user

### How is billing calculated?

Billing is based on:
- **Bedrock usage**: Per token consumed
- **Lambda executions**: Per function invocation
- **DynamoDB**: Storage and request units
- **Data transfer**: Minimal for typical usage

Most costs are usage-based with generous free tiers.

### Can I set spending limits?

Yes, you can configure:
- **AWS Budgets**: Set spending alerts and limits
- **CloudWatch alarms**: Monitor usage metrics
- **Cost allocation tags**: Track costs by feature
- **Usage quotas**: Limit API and AI requests

## Support and Community

### How do I get help?

Support options:
1. **Documentation**: Start with this FAQ and guides
2. **Troubleshooting Guide**: Common issues and solutions
3. **GitHub Issues**: Bug reports and feature requests
4. **AWS Support**: Infrastructure-related issues

### How do I report bugs?

To report bugs:
1. **Check** existing GitHub issues
2. **Collect** error logs and reproduction steps
3. **Include** system information and configuration
4. **Provide** minimal reproduction case

### Can I contribute to the project?

Yes, contributions are welcome:
- **Bug fixes** and improvements
- **Feature development**
- **Documentation** updates
- **Testing** and quality assurance

See the project repository for contribution guidelines.

### Is there a roadmap?

Planned features include:
- **Additional calendar providers** (Apple Calendar, etc.)
- **Advanced AI features** (meeting summarization, action items)
- **Mobile applications** (iOS, Android)
- **Enterprise features** (SSO, advanced admin controls)
- **Integration APIs** (Slack, Teams, Zoom)

## Getting Started

### What's the quickest way to try it out?

1. **Deploy** using the [Setup Guide](./setup-deployment.md)
2. **Configure** OAuth applications for Google/Microsoft
3. **Create** a Cognito user account
4. **Connect** your calendar accounts
5. **Schedule** a test meeting to see AI in action

### Do I need AWS experience?

Basic AWS knowledge is helpful but not required:
- **CDK deployment** is mostly automated
- **Configuration** is done through environment variables
- **Monitoring** uses standard CloudWatch dashboards
- **Troubleshooting** guides provide step-by-step instructions

### What if I get stuck during setup?

1. **Check** the [Troubleshooting Guide](./troubleshooting.md)
2. **Review** CloudFormation events for deployment issues
3. **Verify** OAuth configuration matches the guide exactly
4. **Test** individual components (authentication, API, etc.)
5. **Check** CloudWatch logs for detailed error information

### How long does deployment take?

Typical deployment timeline:
- **OAuth setup**: 30-60 minutes (first time)
- **CDK deployment**: 15-30 minutes
- **Configuration**: 15-30 minutes
- **Testing**: 15-30 minutes

**Total**: 1.5-3 hours for complete setup

## Next Steps

Ready to get started? Follow these guides in order:

1. [Setup and Deployment Guide](./setup-deployment.md) - Complete installation
2. [OAuth Configuration Guide](./oauth-setup.md) - Set up calendar integrations  
3. [API Documentation](./api-documentation.md) - Integrate with your applications
4. [Architecture Overview](./architecture.md) - Understand the system design
5. [Troubleshooting Guide](./troubleshooting.md) - Resolve common issues

Have a question not covered here? Check the other documentation or create a GitHub issue!