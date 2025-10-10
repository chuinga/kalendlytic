# 🚀 Full-Stack Deployment Guide
## AWS Meeting Scheduling Agent with Nova Pro

This guide will walk you through deploying the complete system to AWS.

---

## 📋 Prerequisites Checklist

### ✅ **Step 1: AWS Configuration**
```bash
# Configure AWS CLI with your credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]  
# Default region name: eu-west-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### ✅ **Step 2: Install AWS CDK**
```bash
# Install CDK globally
npm install -g aws-cdk

# Verify installation
cdk --version
```

### ✅ **Step 3: Verify Node.js**
```bash
# Check Node.js version (should be 18+ for CDK)
node --version
npm --version
```

---

## 🏗️ Backend Infrastructure Deployment

### **Step 1: Prepare Infrastructure**
```bash
cd infrastructure

# Install CDK dependencies
npm install

# Verify CDK app
cdk list
```

### **Step 2: Bootstrap CDK (First Time Only)**
```bash
# Bootstrap CDK in your AWS account
cdk bootstrap

# This creates the necessary S3 bucket and IAM roles for CDK
```

### **Step 3: Deploy Infrastructure**
```bash
# Deploy all stacks
cdk deploy --all

# Or deploy specific stacks
cdk deploy MeetingSchedulerCoreStack
cdk deploy MeetingSchedulerApiStack
cdk deploy MeetingSchedulerFrontendStack

# This will take 15-25 minutes for first deployment
```

### **Step 4: Verify Deployment**
```bash
# List deployed stacks
cdk list

# Check CloudFormation stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

---

## 🌐 Frontend Deployment

### **Step 1: Prepare Frontend**
```bash
cd frontend

# Install dependencies
npm install

# Update environment with deployed API URL
# Edit .env.local with outputs from CDK deployment
```

### **Step 2: Build and Deploy**
```bash
# Build the application
npm run build

# Deploy to S3 (if using S3 deployment)
aws s3 sync out/ s3://your-frontend-bucket --delete

# Or deploy via CDK (recommended)
cd ../infrastructure
cdk deploy MeetingSchedulerFrontendStack
```

---

## ⚙️ Configuration Updates

### **Step 1: Get Deployment Outputs**
```bash
# Get API Gateway URL
aws cloudformation describe-stacks --stack-name MeetingSchedulerApiStack --query 'Stacks[0].Outputs'

# Get Cognito User Pool details
aws cloudformation describe-stacks --stack-name MeetingSchedulerCoreStack --query 'Stacks[0].Outputs'
```

### **Step 2: Update Environment Files**
Update `.env` and `frontend/.env.local` with actual values:

```bash
# Backend .env
NEXT_PUBLIC_API_URL=https://your-api-id.execute-api.eu-west-1.amazonaws.com/api
NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Bedrock configuration
BEDROCK_MODEL_ID=eu.amazon.nova-pro-v1:0
BEDROCK_REGION=eu-west-1
```

---

## 🧪 Testing Deployment

### **Step 1: Test Backend API**
```bash
# Test health endpoint
curl https://your-api-id.execute-api.eu-west-1.amazonaws.com/health

# Test Nova Pro integration
curl https://your-api-id.execute-api.eu-west-1.amazonaws.com/nova/test

# Test meeting scheduling
curl -X POST https://your-api-id.execute-api.eu-west-1.amazonaws.com/agent/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Meeting",
    "duration": 30,
    "attendees": ["test@example.com"]
  }'
```

### **Step 2: Test Frontend**
```bash
# Visit your CloudFront distribution URL
# https://your-distribution.cloudfront.net

# Or your custom domain if configured
# https://your-domain.com
```

---

## 🔧 Post-Deployment Configuration

### **Step 1: OAuth Credentials**
```bash
# Store Google OAuth credentials in Secrets Manager
aws secretsmanager create-secret \
  --name "google-oauth-credentials" \
  --description "Google OAuth client credentials" \
  --secret-string '{
    "client_id": "your-google-client-id",
    "client_secret": "your-google-client-secret"
  }'

# Store Microsoft OAuth credentials
aws secretsmanager create-secret \
  --name "microsoft-oauth-credentials" \
  --description "Microsoft OAuth client credentials" \
  --secret-string '{
    "client_id": "your-microsoft-client-id",
    "client_secret": "your-microsoft-client-secret"
  }'
```

### **Step 2: Custom Domain (Optional)**
```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS \
  --region us-east-1  # CloudFront requires us-east-1

# Update CDK with domain configuration
# Redeploy frontend stack
cdk deploy MeetingSchedulerFrontendStack
```

---

## 📊 Monitoring and Maintenance

### **CloudWatch Dashboards**
- API Gateway metrics
- Lambda function performance
- DynamoDB usage
- Cognito authentication metrics

### **Cost Monitoring**
```bash
# Set up billing alerts
aws budgets create-budget --account-id YOUR_ACCOUNT_ID --budget '{
  "BudgetName": "MeetingSchedulerBudget",
  "BudgetLimit": {
    "Amount": "50",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}'
```

---

## 🚨 Troubleshooting

### **Common Issues**

1. **CDK Bootstrap Failed**
   ```bash
   # Ensure you have admin permissions
   aws iam get-user
   
   # Try bootstrapping with explicit account/region
   cdk bootstrap aws://ACCOUNT-NUMBER/eu-west-1
   ```

2. **Lambda Deployment Timeout**
   ```bash
   # Increase timeout in CDK configuration
   # Check Lambda logs
   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
   ```

3. **API Gateway 403 Errors**
   ```bash
   # Check IAM roles and policies
   # Verify Cognito configuration
   aws cognito-idp describe-user-pool --user-pool-id YOUR_POOL_ID
   ```

4. **Frontend Build Errors**
   ```bash
   # Clear cache and reinstall
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

---

## 💰 Cost Optimization

### **Expected Monthly Costs**
- **DynamoDB**: $5-20 (on-demand pricing)
- **Lambda**: $1-10 (first 1M requests free)
- **API Gateway**: $3-15 (first 1M requests $3.50)
- **Cognito**: $0-5 (first 50K MAU free)
- **S3**: $1-5 (storage and requests)
- **CloudFront**: $1-10 (data transfer)
- **Total**: ~$10-65/month

### **Cost Reduction Tips**
- Use DynamoDB provisioned capacity for predictable workloads
- Enable S3 Intelligent Tiering
- Set up CloudWatch alarms for cost monitoring
- Use AWS Cost Explorer for optimization recommendations

---

## 🎉 Success Checklist

- [ ] AWS CLI configured
- [ ] CDK installed and bootstrapped
- [ ] Infrastructure deployed successfully
- [ ] Frontend built and deployed
- [ ] API endpoints responding
- [ ] Nova Pro integration working
- [ ] OAuth credentials configured
- [ ] Custom domain set up (optional)
- [ ] Monitoring configured
- [ ] Cost alerts set up

---

## 📞 Support

If you encounter issues:

1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions and policies
3. Ensure all environment variables are correctly set
4. Test individual components before full integration
5. Use AWS CloudFormation console to debug stack issues

**The system is now ready for production use!** 🚀