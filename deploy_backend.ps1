# AWS Meeting Scheduling Agent - Backend Deployment Script
# PowerShell script for Windows deployment

Write-Host "🚀 AWS Meeting Scheduling Agent - Backend Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check AWS CLI
try {
    $awsVersion = aws --version
    Write-Host "✅ AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check CDK
try {
    $cdkVersion = cdk --version
    Write-Host "✅ AWS CDK: $cdkVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CDK not found. Please install: npm install -g aws-cdk" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host "`n🔐 Verifying AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "✅ AWS Account: $($identity.Account)" -ForegroundColor Green
    Write-Host "✅ AWS User: $($identity.Arn)" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials invalid. Please run 'aws configure' first." -ForegroundColor Red
    Write-Host "   You need valid AWS Access Key ID and Secret Access Key" -ForegroundColor Yellow
    exit 1
}

# Navigate to infrastructure directory
Set-Location infrastructure

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
npm install

# Build the project
Write-Host "`n🔨 Building CDK project..." -ForegroundColor Yellow
npm run build

# Bootstrap CDK (first time only)
Write-Host "`n🏗️ Bootstrapping CDK..." -ForegroundColor Yellow
Write-Host "This creates the necessary S3 bucket and IAM roles for CDK deployment" -ForegroundColor Cyan
try {
    cdk bootstrap
    Write-Host "✅ CDK bootstrap completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Bootstrap may have already been done, continuing..." -ForegroundColor Yellow
}

# List stacks to deploy
Write-Host "`n📋 Available stacks:" -ForegroundColor Yellow
cdk list

# Deploy all stacks
Write-Host "`n🚀 Deploying all stacks..." -ForegroundColor Yellow
Write-Host "This will take approximately 15-25 minutes for the first deployment" -ForegroundColor Cyan
Write-Host "Stacks will be deployed in this order:" -ForegroundColor Cyan
Write-Host "  1. Core Stack (DynamoDB, Cognito, KMS)" -ForegroundColor White
Write-Host "  2. API Stack (Lambda, API Gateway)" -ForegroundColor White
Write-Host "  3. Web Stack (S3, CloudFront)" -ForegroundColor White
Write-Host "  4. Monitoring Stack (CloudWatch)" -ForegroundColor White

$confirmation = Read-Host "`nProceed with deployment? (y/N)"
if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
    try {
        cdk deploy --all --require-approval never
        Write-Host "`n🎉 Deployment completed successfully!" -ForegroundColor Green
        
        # Get deployment outputs
        Write-Host "`n📊 Deployment Outputs:" -ForegroundColor Yellow
        Write-Host "Getting API Gateway URL..." -ForegroundColor Cyan
        try {
            $apiUrl = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-api" --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text
            Write-Host "✅ API Gateway URL: $apiUrl" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Could not retrieve API Gateway URL" -ForegroundColor Yellow
        }
        
        Write-Host "Getting Cognito User Pool ID..." -ForegroundColor Cyan
        try {
            $userPoolId = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-core" --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text
            Write-Host "✅ Cognito User Pool ID: $userPoolId" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Could not retrieve Cognito User Pool ID" -ForegroundColor Yellow
        }
        
        Write-Host "Getting CloudFront URL..." -ForegroundColor Cyan
        try {
            $cloudFrontUrl = aws cloudformation describe-stacks --stack-name "meeting-scheduling-agent-dev-web" --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text
            Write-Host "✅ CloudFront URL: $cloudFrontUrl" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Could not retrieve CloudFront URL" -ForegroundColor Yellow
        }
        
        Write-Host "`n🎯 Next Steps:" -ForegroundColor Yellow
        Write-Host "1. Update your .env file with the deployment outputs above" -ForegroundColor White
        Write-Host "2. Test the API endpoints" -ForegroundColor White
        Write-Host "3. Deploy the frontend to CloudFront" -ForegroundColor White
        Write-Host "4. Configure OAuth credentials in AWS Secrets Manager" -ForegroundColor White
        
    } catch {
        Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
        Write-Host "Check the error messages above for details." -ForegroundColor Yellow
        Write-Host "You can retry deployment by running this script again." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
}

# Return to original directory
Set-Location ..

Write-Host "`n✨ Backend deployment process completed!" -ForegroundColor Green