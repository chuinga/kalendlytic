#!/bin/bash

# Development Environment Setup Script
set -e

echo "🛠️  Setting up development environment for AWS Meeting Scheduling Agent..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.9+ from https://python.org/"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Setup infrastructure
echo "🏗️  Setting up infrastructure development environment..."
cd infrastructure

echo "📦 Installing CDK dependencies..."
npm install

echo "🔨 Building TypeScript..."
npm run build

echo "✅ Infrastructure setup complete!"

# Setup backend
echo "🐍 Setting up backend development environment..."
cd ../backend

echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

echo "✅ Backend setup complete!"

# Setup frontend
echo "🌐 Setting up frontend development environment..."
cd ../frontend

echo "📦 Installing frontend dependencies..."
npm install

echo "✅ Frontend setup complete!"

# Create environment file if it doesn't exist
cd ..
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your AWS account details and OAuth credentials"
fi

echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Configure AWS credentials: aws configure"
echo "3. Install AWS CDK CLI: npm install -g aws-cdk"
echo "4. Start development:"
echo "   - Infrastructure: cd infrastructure && npm run watch"
echo "   - Frontend: cd frontend && npm run dev"
echo "   - Backend: cd backend && python -m pytest"
echo ""
echo "For detailed setup instructions, see README.md"