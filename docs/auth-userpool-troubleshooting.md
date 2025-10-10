# Auth UserPool Configuration Troubleshooting

## Problem: "Auth UserPool not configured"

This error occurs when your frontend application cannot connect to the Cognito User Pool because the `.env` file contains placeholder values instead of the actual deployed Cognito User Pool ID and Client ID.

## Root Cause

Your CDK infrastructure properly defines and deploys the Cognito User Pool, but the frontend configuration (`.env` file) still has placeholder values:

```bash
# ❌ Placeholder values (causing the error)
NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Solution Steps

### Step 1: Get the Actual Cognito Values

Choose one of these methods to get the real values:

#### Method A: AWS CloudFormation Console (Recommended)
1. Go to [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation/)
2. Select region: **eu-west-1**
3. Find stack: **meeting-scheduling-agent-dev-core**
4. Click on the stack name
5. Go to **Outputs** tab
6. Look for:
   - `UserPoolId` (starts with `eu-west-1_`)
   - `UserPoolClientId` (long alphanumeric string)

#### Method B: AWS Cognito Console
1. Go to [AWS Cognito Console](https://console.aws.amazon.com/cognito/)
2. Select region: **eu-west-1**
3. Click **User pools**
4. Find pool: **meeting-agent-users**
5. Copy the **User Pool ID**
6. Go to **App integration** tab
7. Find client: **meeting-agent-web-client**
8. Copy the **Client ID**

#### Method C: AWS CLI (if credentials configured)
```bash
aws cloudformation describe-stacks \
  --stack-name meeting-scheduling-agent-dev-core \
  --region eu-west-1 \
  --query 'Stacks[0].Outputs'
```

#### Method D: CDK CLI
```bash
cd infrastructure
cdk deploy meeting-scheduling-agent-dev-core --outputs-file outputs.json
cat outputs.json
```

### Step 2: Update Your .env File

#### Option A: Use the Update Script
```bash
# Replace with your actual values
python scripts/update_env_cognito.py eu-west-1_YourPoolId YourClientId
```

#### Option B: Manual Update
Edit your `.env` file and replace:

```bash
# BEFORE
NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_xxxxxxxxx
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# AFTER (use your actual values)
NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_abc123def456
NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

### Step 3: Restart Your Application
```bash
# If running frontend development server
cd frontend
npm run dev

# Or if running full stack
python start_fullstack.py
```

## Verification

After updating, you should see:
- ✅ No more "Auth UserPool not configured" errors
- ✅ Login/signup forms working properly
- ✅ Authentication flows completing successfully

## Common Issues

### Issue: "Stack not found"
**Cause**: Infrastructure not deployed or wrong stack name
**Solution**: 
```bash
cd infrastructure
cdk deploy --all
```

### Issue: "Access denied" when checking AWS resources
**Cause**: AWS credentials not configured
**Solution**:
```bash
aws configure
# Enter your AWS credentials
```

### Issue: Values still showing as placeholders
**Cause**: CDK deployment didn't complete successfully
**Solution**:
```bash
cd infrastructure
cdk deploy meeting-scheduling-agent-dev-core --force
```

### Issue: Frontend still shows auth errors after update
**Cause**: Frontend cache or server not restarted
**Solution**:
```bash
# Clear browser cache and restart dev server
cd frontend
rm -rf .next
npm run dev
```

## Expected Values Format

- **User Pool ID**: `eu-west-1_` followed by 9 alphanumeric characters
  - Example: `eu-west-1_abc123def`
- **Client ID**: 26-character alphanumeric string
  - Example: `1a2b3c4d5e6f7g8h9i0j1k2l3m`

## Helper Scripts

We've created several scripts to help with this issue:

1. **`scripts/get_cognito_values.py`** - Shows instructions for getting values
2. **`scripts/update_cognito_config.py`** - Automatically extracts and updates (requires AWS credentials)
3. **`scripts/update_env_cognito.py`** - Updates .env with provided values

## Prevention

To avoid this issue in future deployments:

1. **Automate the process**: Use the `update_cognito_config.py` script after deployment
2. **Document the values**: Keep a secure record of your Cognito IDs
3. **Use environment-specific configs**: Consider separate .env files for different environments

## Need Help?

If you're still experiencing issues:

1. Check that your AWS region is set to `eu-west-1`
2. Verify the CDK stack deployed successfully
3. Ensure your AWS credentials have the necessary permissions
4. Check the browser console for specific error messages

The Cognito User Pool is properly configured in your infrastructure - this is just a configuration sync issue between your deployed resources and your local environment variables.