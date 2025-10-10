# 🚀 Actual Deployment Commands

## With Valid AWS Credentials, Run These Commands:

### **1. Bootstrap CDK (First Time Only)**
```bash
cd infrastructure
cdk bootstrap
```

### **2. Deploy All Stacks**
```bash
# Deploy everything at once
cdk deploy --all --require-approval never

# Or deploy individually for better control:
cdk deploy meeting-scheduling-agent-dev-core
cdk deploy meeting-scheduling-agent-dev-api  
cdk deploy meeting-scheduling-agent-dev-web
cdk deploy meeting-scheduling-agent-dev-monitoring
```

### **3. Get Deployment Outputs**
```bash
# Get API Gateway URL
aws cloudformation describe-stacks \
  --stack-name meeting-scheduling-agent-dev-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text

# Get Cognito User Pool ID
aws cloudformation describe-stacks \
  --stack-name meeting-scheduling-agent-dev-core \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Get CloudFront URL
aws cloudformation describe-stacks \
  --stack-name meeting-scheduling-agent-dev-web \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

### **4. Update Environment Configuration**
```bash
# Update .env with actual values from step 3
NEXT_PUBLIC_API_URL=https://[your-api-id].execute-api.eu-west-1.amazonaws.com/api
NEXT_PUBLIC_COGNITO_USER_POOL_ID=[your-user-pool-id]
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=[your-client-id]
```

### **5. Test Deployment**
```bash
# Test API health
curl https://[your-api-id].execute-api.eu-west-1.amazonaws.com/health

# Test Nova Pro integration
curl https://[your-api-id].execute-api.eu-west-1.amazonaws.com/nova/test

# Test meeting scheduling
curl -X POST https://[your-api-id].execute-api.eu-west-1.amazonaws.com/agent/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Meeting",
    "duration": 30,
    "attendees": ["test@example.com"]
  }'
```

## 🎯 **Expected Results:**
- ✅ 4 CloudFormation stacks deployed
- ✅ API Gateway responding to requests
- ✅ Nova Pro AI integration working
- ✅ Frontend deployed to CloudFront
- ✅ Monitoring dashboard active
- ✅ Total deployment time: ~20 minutes
- ✅ Monthly cost: $15-45