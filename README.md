# AWS Meeting Scheduling Agent

An AI-powered meeting scheduling system that automates calendar management across Gmail and Outlook using Amazon Bedrock with Claude Sonnet 4.5 and AgentCore primitives.

## Project Structure

```
aws-meeting-scheduling-agent/
├── infrastructure/          # AWS CDK TypeScript infrastructure
│   ├── lib/
│   │   ├── stacks/         # CDK stack definitions
│   │   └── app.ts          # CDK app entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── cdk.json
├── backend/                # Python Lambda functions
│   ├── src/
│   │   ├── handlers/       # Lambda function handlers
│   │   ├── models/         # Pydantic data models
│   │   └── utils/          # Shared utilities
│   └── requirements.txt
├── frontend/               # React/Next.js frontend
│   ├── src/
│   │   ├── pages/          # Next.js pages
│   │   ├── components/     # React components
│   │   └── styles/         # CSS styles
│   ├── package.json
│   └── next.config.js
└── .env.example           # Environment variables template
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- AWS CLI configured with appropriate permissions
- AWS CDK CLI installed (`npm install -g aws-cdk`)

## Quick Start

### 1. Set up Infrastructure

```bash
cd infrastructure
npm install
npm run build
cdk bootstrap
cdk deploy --all
```

### 2. Set up Backend

```bash
cd backend
pip install -r requirements.txt
```

### 3. Set up Frontend

```bash
cd frontend
npm install
npm run build
```

## Environment Configuration

1. Copy `.env.example` to `.env`
2. Update the environment variables with your AWS account details
3. Configure OAuth credentials for Google and Microsoft (see OAuth Setup section)

## OAuth Setup

### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API and Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs
6. Copy client ID and secret to environment variables

### Microsoft OAuth Setup
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application in Azure AD
3. Configure API permissions for Microsoft Graph (Calendars.ReadWrite, Mail.Send)
4. Create client secret
5. Copy application ID and secret to environment variables

## Development

### Infrastructure Development
```bash
cd infrastructure
npm run watch    # Watch for changes
npm run test     # Run tests
cdk diff         # Show changes
```

### Backend Development
```bash
cd backend
pytest           # Run tests
```

### Frontend Development
```bash
cd frontend
npm run dev      # Start development server
npm run test     # Run tests
```

## Deployment

### Full Deployment
```bash
# Deploy infrastructure
cd infrastructure
cdk deploy --all

# Build and deploy frontend
cd ../frontend
npm run build
# Frontend will be deployed to S3 via CDK
```

## Architecture

The system follows a serverless architecture with:

- **Frontend**: React/Next.js SPA hosted on S3 + CloudFront
- **API**: API Gateway + Lambda functions (Python)
- **AI**: Amazon Bedrock with Claude Sonnet 4.5 + AgentCore
- **Data**: DynamoDB tables with KMS encryption
- **Auth**: Amazon Cognito for user management
- **Integration**: OAuth 2.0 for Google and Microsoft APIs

## Features

- ✅ Multi-platform calendar integration (Gmail + Outlook)
- ✅ AI-powered conflict detection and resolution
- ✅ Intelligent meeting prioritization
- ✅ Automated email confirmations
- ✅ User preference management
- ✅ Comprehensive audit trails
- ✅ Secure token management with KMS encryption

## Contributing

1. Follow the task-based implementation plan in `.kiro/specs/aws-meeting-scheduling-agent/tasks.md`
2. Implement one task at a time
3. Test thoroughly before moving to next task
4. Update documentation as needed

## License

MIT License - see LICENSE file for details