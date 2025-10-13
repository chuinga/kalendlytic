# 🚀 Quick Backend Deployment Guide

## Prerequisites ✅

1. **AWS Account** with administrative permissions
2. **AWS CLI** installed and configured
3. **Node.js** (version 18+) installed
4. **AWS CDK** installed globally: `npm install -g aws-cdk`

## Step-by-Step Deployment 📋

### 1. Configure AWS Credentials

```powershell
# Configure your AWS credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: eu-west-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### 2. Deploy Backend Infrastructure

```powershell
# Run the deployment script
.\deploy_backend.ps1
```

This script will:
- ✅ Check all prerequisites
- ✅ Install CDK dependencies
- ✅ Bootstrap CDK (first time only)
- ✅ Deploy all 4 stacks:
  - `meeting-scheduling-agent-dev-core` (DynamoDB, Cognito, KMS)
  - `meeting-scheduling-agent-dev-api` (Lambda, API Gateway)
  - `meeting-scheduling-agent-dev-web` (S3, CloudFront)
  - `meeting-scheduling-agent-dev-monitoring` (CloudWatch)

**⏱️ Expected deployment time: 15-25 minutes**

### 3. Test Deployment

```powershell
# Test the deployed infrastructure
.\test_deployment.ps1
```

### 4. Manual Deployment (Alternative)

If you prefer manual commands:

```powershell
# Navigate to infrastructure directory
cd infrastructure

# Install dependencies
npm install

# Build the project
npm run build

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all --require-approval never

# Get deployment outputs
aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-api" --query 'Stacks[0].Outputs'
```

## Expected Outputs 📊

After successful deployment, you'll get:

1. **API Gateway URL**: `https://[id].execute-api.eu-west-1.amazonaws.com/api`
2. **Cognito User Pool ID**: `eu-west-1_[id]`
3. **CloudFront Distribution URL**: `https://[id].cloudfront.net`

## Update Environment Configuration 🔧

Update your `.env` file with the deployment outputs:

```bash
NEXT_PUBLIC_API_URL=https://[your-api-id].execute-api.eu-west-1.amazonaws.com/api
NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_[your-pool-id]
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=[your-client-id]
```

## Troubleshooting 🔧

### Common Issues:

1. **AWS Credentials Invalid**
   ```powershell
   aws configure
   aws sts get-caller-identity
   ```

2. **CDK Not Bootstrapped**
   ```powershell
   cd infrastructure
   cdk bootstrap
   ```

3. **Deployment Timeout**
   - Wait for completion (can take 20+ minutes)
   - Check CloudFormation console for progress

4. **Stack Already Exists**
   ```powershell
   cdk deploy --all --force
   ```

## Cost Estimate 💰

**Expected monthly costs:**
- DynamoDB: $5-20
- Lambda: $1-10
- API Gateway: $3-15
- Cognito: $0-5
- S3: $1-5
- CloudFront: $1-10
- **Total: ~$10-65/month**

## Next Steps 🎯

1. ✅ Backend deployed
2. 🔄 Update environment variables
3. 🧪 Test API endpoints
4. 🌐 Deploy frontend
5. 🔐 Configure OAuth credentials

## Cleanup (If Needed) 🧹

To remove all resources:

```powershell
cd infrastructure
cdk destroy --all --force
```

---

**🎉 Your AWS Meeting Scheduling Agent backend is now ready!**