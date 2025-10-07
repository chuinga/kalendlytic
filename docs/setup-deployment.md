# Setup and Deployment Guide

This guide walks you through setting up and deploying the AWS Meeting Scheduling Agent from scratch.

## Prerequisites

### Required Software
- **Node.js** (v18 or later)
- **Python** (3.9 or later)
- **AWS CLI** (v2)
- **AWS CDK** (v2)
- **Git**

### AWS Account Setup
1. **AWS Account**: Ensure you have an AWS account with appropriate permissions
2. **AWS CLI Configuration**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and default region
   ```
3. **CDK Bootstrap** (first time only):
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

## Environment Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd aws-meeting-scheduling-agent
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

### 4. Infrastructure Setup
```bash
cd ../infrastructure
npm install
```

## OAuth Application Configuration

Before deployment, you must configure OAuth applications for Google and Microsoft integration.

### Google OAuth Setup

1. **Go to Google Cloud Console**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**
   ```bash
   # Enable required APIs
   gcloud services enable calendar-json.googleapis.com
   gcloud services enable gmail.googleapis.com
   ```

3. **Create OAuth 2.0 Credentials**
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Authorized redirect URIs:
     ```
     https://your-cloudfront-domain.com/auth/google/callback
     http://localhost:3000/auth/google/callback  # For development
     ```

4. **Download Credentials**
   - Download the JSON file
   - Note the `client_id` and `client_secret`

### Microsoft OAuth Setup

1. **Go to Azure Portal**
   - Visit [Azure Portal](https://portal.azure.com/)
   - Navigate to "Azure Active Directory" > "App registrations"

2. **Register New Application**
   - Click "New registration"
   - Name: "AWS Meeting Scheduling Agent"
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: 
     ```
     https://your-cloudfront-domain.com/auth/microsoft/callback
     http://localhost:3000/auth/microsoft/callback  # For development
     ```

3. **Configure API Permissions**
   - Go to "API permissions"
   - Add permissions:
     - Microsoft Graph > Delegated permissions:
       - `Calendars.ReadWrite`
       - `Mail.Send`
       - `User.Read`

4. **Create Client Secret**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Copy the secret value (you won't see it again)

## Environment Variables

Create environment configuration files:

### Backend Environment (.env)
```bash
# Create backend/.env
cat > backend/.env << EOF
AWS_REGION=us-east-1
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
EOF
```

### Frontend Environment (.env.local)
```bash
# Create frontend/.env.local
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=https://your-api-gateway-url
NEXT_PUBLIC_COGNITO_USER_POOL_ID=your-user-pool-id
NEXT_PUBLIC_COGNITO_CLIENT_ID=your-cognito-client-id
NEXT_PUBLIC_AWS_REGION=us-east-1
EOF
```

### Infrastructure Environment
```bash
# Create infrastructure/.env
cat > infrastructure/.env << EOF
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
DOMAIN_NAME=your-domain.com  # Optional
CERTIFICATE_ARN=arn:aws:acm:us-east-1:123456789012:certificate/xxx  # Optional
EOF
```

## Deployment Steps

### 1. Deploy Infrastructure
```bash
cd infrastructure

# Review what will be deployed
cdk diff

# Deploy all stacks
cdk deploy --all --require-approval never

# Or deploy stacks individually
cdk deploy CoreStack
cdk deploy ApiStack
cdk deploy WebStack
cdk deploy MonitoringStack
```

### 2. Store OAuth Secrets
After infrastructure deployment, store OAuth credentials in AWS Secrets Manager:

```bash
# Store Google OAuth credentials
aws secretsmanager put-secret-value \
  --secret-id "meeting-agent/google-oauth" \
  --secret-string '{"client_id":"your-google-client-id","client_secret":"your-google-client-secret"}'

# Store Microsoft OAuth credentials
aws secretsmanager put-secret-value \
  --secret-id "meeting-agent/microsoft-oauth" \
  --secret-string '{"client_id":"your-microsoft-client-id","client_secret":"your-microsoft-client-secret"}'
```

### 3. Build and Deploy Frontend
```bash
cd ../frontend

# Build the application
npm run build

# Deploy to S3 (automated via CDK)
# The WebStack handles S3 upload and CloudFront invalidation
```

### 4. Verify Deployment
```bash
# Check stack status
cdk list
aws cloudformation describe-stacks --stack-name CoreStack
aws cloudformation describe-stacks --stack-name ApiStack
aws cloudformation describe-stacks --stack-name WebStack

# Test API endpoints
curl https://your-api-gateway-url/health

# Check CloudFront distribution
aws cloudfront list-distributions
```

## Post-Deployment Configuration

### 1. Update OAuth Redirect URIs
After deployment, update your OAuth applications with the actual CloudFront domain:

**Google Console:**
- Update authorized redirect URIs with your CloudFront domain
- Format: `https://your-cloudfront-domain.com/auth/google/callback`

**Azure Portal:**
- Update redirect URI in your app registration
- Format: `https://your-cloudfront-domain.com/auth/microsoft/callback`

### 2. Configure Cognito User Pool
```bash
# Create an admin user for testing
aws cognito-idp admin-create-user \
  --user-pool-id your-user-pool-id \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password TempPassword123! \
  --message-action SUPPRESS
```

### 3. Test the Application
1. Navigate to your CloudFront URL
2. Register/login with Cognito
3. Connect Google and/or Microsoft accounts
4. Test scheduling functionality

## Development Setup

For local development:

### 1. Start Backend Services
```bash
cd backend
# Install SAM CLI for local testing
pip install aws-sam-cli

# Start local API
sam local start-api --template-file ../infrastructure/template.yaml
```

### 2. Start Frontend Development Server
```bash
cd frontend
npm run dev
```

### 3. Environment Variables for Development
Update your `.env.local` files to point to local services:
```bash
NEXT_PUBLIC_API_URL=http://localhost:3000
```

## Monitoring and Logging

### CloudWatch Dashboards
After deployment, access monitoring dashboards:
- AWS Console > CloudWatch > Dashboards
- Look for "MeetingAgent-*" dashboards

### Log Groups
Monitor application logs:
```bash
# View Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/meeting-agent"

# Tail logs in real-time
aws logs tail /aws/lambda/meeting-agent-auth --follow
```

### Metrics and Alarms
Key metrics to monitor:
- Lambda function duration and errors
- API Gateway 4xx/5xx errors
- DynamoDB throttling
- Bedrock token usage and costs

## Cleanup

To remove all resources:
```bash
cd infrastructure
cdk destroy --all
```

**Warning**: This will delete all data including user accounts, preferences, and meeting history.

## Next Steps

1. Review the [API Documentation](./api-documentation.md)
2. Check the [Troubleshooting Guide](./troubleshooting.md) if you encounter issues
3. See the [FAQ](./faq.md) for common questions

## Support

For issues and questions:
1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Review CloudWatch logs for error details
3. Ensure all OAuth applications are properly configured
4. Verify AWS permissions and quotas