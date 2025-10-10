# AWS Meeting Scheduling Agent

An AI-powered meeting scheduling system that automates calendar management across Gmail and Outlook using Amazon Bedrock with Claude Sonnet 4.5 and AgentCore primitives.

## 🚀 Quick Start Guide

Choose your preferred way to run the application:

### Option 1: Development Mode (Recommended for Testing)

**Automated Setup:**
```bash
# Run the setup script (handles everything automatically)
./scripts/setup-dev.sh

# Then start the application in 3 separate terminals:

# Terminal 1 - Backend API
cd backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend  
npm run dev

# Terminal 3 - Infrastructure (optional)
cd infrastructure
npm run watch
```

**Access your application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 2: Full AWS Deployment

**Automated Deployment:**
```bash
# Deploy everything to AWS
./scripts/deploy.sh
```

**Manual Deployment:**
```bash
# 1. Configure AWS credentials
aws configure

# 2. Deploy infrastructure
cd infrastructure
npm install && npm run build
cdk bootstrap  # First time only
cdk deploy --all

# 3. Frontend is automatically deployed via CDK
```

## Prerequisites

Before running the application, ensure you have:

- **Node.js** 18+ and npm ([Download](https://nodejs.org/))
- **Python** 3.9+ ([Download](https://python.org/))
- **AWS CLI** configured ([Setup Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **AWS CDK** CLI: `npm install -g aws-cdk`
- **Git** for cloning the repository

## Project Structure

```
aws-meeting-scheduling-agent/
├── infrastructure/          # AWS CDK TypeScript infrastructure
├── backend/                # Python Lambda functions & API
├── frontend/               # React/Next.js web application
├── e2e/                   # End-to-end testing suite
├── scripts/               # Automation scripts
├── docs/                  # Detailed documentation
└── .env.example          # Environment configuration template
```

## ⚙️ Configuration

### Environment Setup

1. **Create your environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update key variables in `.env`:**
   ```bash
   # AWS Configuration
   AWS_REGION=eu-west-1
   AWS_ACCOUNT_ID=your-account-id
   
   # OAuth Credentials (required for calendar integration)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   MICROSOFT_CLIENT_ID=your-microsoft-client-id
   MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
   ```

### OAuth Application Setup (Required)

The application needs OAuth credentials to integrate with Google and Microsoft calendars:

#### Google OAuth Setup
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable APIs: Google Calendar API, Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Add redirect URIs:
   - `http://localhost:3000/auth/google/callback` (development)
   - `https://your-domain.com/auth/google/callback` (production)
6. Copy Client ID and Secret to your `.env` file

#### Microsoft OAuth Setup
1. Visit [Azure Portal](https://portal.azure.com/)
2. Go to Azure Active Directory > App registrations
3. Register new application
4. Add API permissions: `Calendars.ReadWrite`, `Mail.Send`, `User.Read`
5. Create client secret
6. Add redirect URIs:
   - `http://localhost:3000/auth/microsoft/callback` (development)
   - `https://your-domain.com/auth/microsoft/callback` (production)
7. Copy Application ID and Secret to your `.env` file

> **Note**: For detailed OAuth setup instructions, see `docs/oauth-setup.md`

## 🧪 Testing

Run the comprehensive test suite to verify everything works:

```bash
# Run all tests (deployment verification, performance, E2E)
./scripts/run_all_tests.sh

# Run specific test suites
cd backend && pytest                    # Backend unit tests
cd frontend && npm test                 # Frontend component tests  
cd e2e && ./run-tests.sh all           # End-to-end tests
```

## 🛠️ Development

### Local Development
```bash
# Backend development with auto-reload
cd backend
python -m uvicorn src.main:app --reload

# Frontend development server
cd frontend
npm run dev

# Infrastructure changes
cd infrastructure
npm run watch
```

### Testing During Development
```bash
# Backend tests with coverage
cd backend
pytest --cov=src

# Frontend tests in watch mode
cd frontend
npm test -- --watch

# E2E tests with browser UI
cd e2e
./run-tests.sh all chromium true
```

## 🏗️ Architecture

The system follows a serverless architecture:

- **Frontend**: React/Next.js SPA hosted on S3 + CloudFront
- **API**: API Gateway + Lambda functions (Python)
- **AI**: Amazon Bedrock with Claude Sonnet 4.5 + AgentCore
- **Data**: DynamoDB tables with KMS encryption
- **Auth**: Amazon Cognito for user management
- **Integration**: OAuth 2.0 for Google and Microsoft APIs

## ✨ Features

- ✅ Multi-platform calendar integration (Gmail + Outlook)
- ✅ AI-powered conflict detection and resolution
- ✅ Intelligent meeting prioritization
- ✅ Automated email confirmations
- ✅ User preference management
- ✅ Comprehensive audit trails
- ✅ Secure token management with KMS encryption

## 🔧 Common Issues & Solutions

### Setup Issues
```bash
# Node.js version issues
node --version  # Should be 18+
npm install -g n && n latest

# Python version issues  
python3 --version  # Should be 3.9+

# AWS CLI not configured
aws configure
aws sts get-caller-identity  # Verify credentials
```

### Development Issues
```bash
# Port already in use
lsof -ti:3000 | xargs kill -9  # Kill process on port 3000
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000

# Dependencies issues
rm -rf node_modules package-lock.json && npm install  # Frontend
rm -rf __pycache__ && pip install -r requirements.txt  # Backend
```

### OAuth Issues
- **Google**: Ensure redirect URIs match exactly (including http/https)
- **Microsoft**: Verify API permissions are granted by admin
- **Both**: Check client IDs and secrets are correctly copied

## 📚 Documentation

For detailed information, see the `docs/` directory:

- **[Setup & Deployment Guide](docs/setup-deployment.md)** - Comprehensive setup instructions
- **[OAuth Configuration](docs/oauth-setup.md)** - Detailed OAuth setup guide
- **[API Documentation](docs/api-documentation.md)** - Complete API reference
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[FAQ](docs/faq.md)** - Frequently asked questions

## 🆘 Getting Help

1. **Quick Issues**: Check the [Troubleshooting Guide](docs/troubleshooting.md)
2. **Setup Problems**: Review the [Setup Guide](docs/setup-deployment.md)
3. **OAuth Issues**: See the [OAuth Setup Guide](docs/oauth-setup.md)
4. **API Questions**: Check the [API Documentation](docs/api-documentation.md)

## 🤝 Contributing

1. Follow the task-based implementation plan in `.kiro/specs/aws-meeting-scheduling-agent/tasks.md`
2. Implement one task at a time
3. Test thoroughly before moving to next task
4. Update documentation as needed

## 📄 License

MIT License - see LICENSE file for details