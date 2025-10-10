#!/bin/bash
"""
Master Test Runner for AWS Meeting Scheduling Agent

This script runs all demo and testing scripts in sequence to provide
comprehensive validation of the deployed system.
"""

set -e  # Exit on any error

echo "🚀 AWS Meeting Scheduling Agent - Complete Testing Suite"
echo "======================================================="

# Configuration
API_URL=${DEMO_API_URL:-"https://your-api-gateway-url.execute-api.eu-west-1.amazonaws.com"}
DEMO_USER_EMAIL=${DEMO_USER_EMAIL:-"demo@example.com"}
AWS_REGION=${AWS_REGION:-"eu-west-1"}
STACK_PREFIX=${STACK_PREFIX:-"MeetingScheduler"}

echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Demo User: $DEMO_USER_EMAIL"
echo "  AWS Region: $AWS_REGION"
echo "  Stack Prefix: $STACK_PREFIX"
echo "======================================================="

# Step 1: Deployment Verification
echo ""
echo "📋 Step 1: Deployment Verification"
echo "-----------------------------------"
python3 scripts/deployment_verification.py \
    --region "$AWS_REGION" \
    --stack-prefix "$STACK_PREFIX"

if [ $? -ne 0 ]; then
    echo "❌ Deployment verification failed. Stopping test suite."
    exit 1
fi

# Step 2: Generate Test Data
echo ""
echo "📊 Step 2: Generate Test Data"
echo "------------------------------"
python3 scripts/generate_test_data.py \
    --users 5 \
    --region "$AWS_REGION" \
    --export-json "test_data_$(date +%Y%m%d_%H%M%S).json"

# Step 3: Performance Testing
echo ""
echo "⚡ Step 3: Performance Testing"
echo "------------------------------"
python3 scripts/performance_test.py \
    --api-url "$API_URL" \
    --test-type load \
    --users 10 \
    --requests 5 \
    --duration 30 \
    --output "performance_results_$(date +%Y%m%d_%H%M%S).json"

# Step 4: End-to-End Demo
echo ""
echo "🎬 Step 4: End-to-End Demo"
echo "---------------------------"
python3 scripts/demo.py

echo ""
echo "✅ All tests completed successfully!"
echo "======================================================="
echo "📊 Test Results Summary:"
echo "  - Deployment verification: PASSED"
echo "  - Test data generation: COMPLETED"
echo "  - Performance testing: COMPLETED"
echo "  - End-to-end demo: COMPLETED"
echo ""
echo "🎉 Your AWS Meeting Scheduling Agent is fully validated!"