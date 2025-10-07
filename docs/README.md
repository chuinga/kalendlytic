# AWS Meeting Scheduling Agent

An AI-powered meeting scheduling system that automates calendar management across Gmail and Outlook using Amazon Bedrock and AgentCore primitives.

## 🚀 Quick Start

1. **Prerequisites Setup**
   ```bash
   # Install AWS CDK
   npm install -g aws-cdk
   
   # Install Python dependencies
   cd backend
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd ../frontend
   npm install
   ```

2. **Deploy Infrastructure**
   ```bash
   # Bootstrap CDK (first time only)
   cdk bootstrap
   
   # Deploy all stacks
   cdk deploy --all
   ```

3. **Configure OAuth Applications**
   - Follow the [OAuth Setup Guide](./oauth-setup.md)
   - Update environment variables with client credentials

4. **Access the Application**
   - Frontend URL will be displayed after deployment
   - Login with Cognito credentials
   - Connect your Gmail/Outlook accounts

## 📚 Documentation

- [Setup and Deployment Guide](./setup-deployment.md)
- [OAuth Configuration](./oauth-setup.md)
- [API Documentation](./api-documentation.md)
- [Architecture Overview](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)
- [FAQ](./faq.md)

## 🏗️ Architecture

The system uses a serverless architecture on AWS with:
- **Frontend**: React/Next.js hosted on S3 + CloudFront
- **Backend**: API Gateway + Lambda functions
- **AI Engine**: Amazon Bedrock with Claude Sonnet 4.5
- **Storage**: DynamoDB with KMS encryption
- **Authentication**: Amazon Cognito

## 🔧 Key Features

- ✅ Multi-platform calendar integration (Gmail + Outlook)
- ✅ AI-powered conflict detection and resolution
- ✅ Intelligent meeting prioritization
- ✅ Automated email confirmations
- ✅ Secure OAuth token management
- ✅ Comprehensive audit logging

## 🛡️ Security

- OAuth 2.0 with PKCE for secure authentication
- KMS encryption for sensitive data
- Least-privilege IAM policies
- PII redaction in logs
- Comprehensive audit trails

## 📊 Monitoring

- CloudWatch metrics and alarms
- Structured JSON logging
- Bedrock usage tracking
- Performance monitoring dashboards

## 🤝 Contributing

This project was built for the AWS hackathon. For development setup and contribution guidelines, see the [Setup Guide](./setup-deployment.md).

## 📄 License

MIT License - see LICENSE file for details.