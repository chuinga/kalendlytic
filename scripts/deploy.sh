#!/bin/bash

# AWS Meeting Scheduling Agent Deployment Script
set -e

echo "🚀 Starting deployment of AWS Meeting Scheduling Agent..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required but not installed."
    exit 1
fi

if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK CLI is required but not installed. Run: npm install -g aws-cdk"
    exit 1
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "eu-west-1")

echo "✅ AWS Account: $AWS_ACCOUNT"
echo "✅ AWS Region: $AWS_REGION"

# Set environment variables
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT
export CDK_DEFAULT_REGION=$AWS_REGION

# Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
cd infrastructure

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building TypeScript..."
npm run build

echo "🚀 Bootstrapping CDK (if needed)..."
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION

echo "📋 Showing deployment diff..."
cdk diff

echo "🚀 Deploying stacks..."
cdk deploy --all --require-approval never

echo "✅ Infrastructure deployment complete!"

# Build frontend
echo "🌐 Building frontend..."
cd ../frontend

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building application..."
npm run build

echo "✅ Frontend build complete!"

# Setup backend dependencies
echo "🐍 Setting up backend dependencies..."
cd ../backend

echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

echo "✅ Backend setup complete!"

echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Configure OAuth credentials in AWS Secrets Manager"
echo "2. Update frontend environment variables with deployed resources"
echo "3. Test the application"
echo ""
echo "For OAuth setup instructions, see README.md"