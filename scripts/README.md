# Demo and Testing Scripts

This directory contains comprehensive demo and testing scripts for the AWS Meeting Scheduling Agent. These scripts validate deployment, generate test data, perform load testing, and demonstrate key functionality.

## Scripts Overview

### 1. `demo.py` - End-to-End Demo Script
Interactive demonstration of all key features including:
- OAuth calendar connections (simulated)
- Unified availability aggregation
- AI-powered conflict detection and resolution
- Meeting prioritization
- Automated email communication
- Agent decision audit trails
- Performance metrics

**Usage:**
```bash
# Set environment variables
export DEMO_API_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com"
export DEMO_USER_EMAIL="demo@example.com"
export DEMO_USER_PASSWORD="DemoPass123!"

# Run the demo
python3 scripts/demo.py
```

### 2. `generate_test_data.py` - Test Data Generator
Creates realistic test data for demonstration and testing:
- Demo user accounts with profiles
- Calendar events across multiple providers
- User preferences and scheduling rules
- OAuth connection records
- Agent execution logs and audit trails

**Usage:**
```bash
# Generate test data for 5 users
python3 scripts/generate_test_data.py --users 5 --region us-east-1

# Generate and write to DynamoDB
python3 scripts/generate_test_data.py --users 10 --write-db --export-json test_data.json

# Options:
#   --users N          Number of demo users (default: 5)
#   --region REGION    AWS region (default: us-east-1)
#   --write-db         Write data to DynamoDB tables
#   --export-json FILE Export data to JSON file
```

### 3. `performance_test.py` - Performance and Load Testing
Comprehensive performance testing suite:
- Load testing with concurrent users
- Stress testing with increasing load
- Endurance testing for memory leaks
- Response time analysis and reporting

**Usage:**
```bash
# Basic load test
python3 scripts/performance_test.py \
    --api-url "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com" \
    --test-type load \
    --users 50 \
    --requests 10 \
    --duration 60

# Stress test
python3 scripts/performance_test.py \
    --api-url "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com" \
    --test-type stress

# All tests
python3 scripts/performance_test.py \
    --api-url "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com" \
    --test-type all \
    --output performance_report.json

# Options:
#   --api-url URL      API Gateway base URL (required)
#   --auth-token TOKEN Authentication token
#   --test-type TYPE   load|stress|endurance|all (default: load)
#   --users N          Concurrent users for load test (default: 50)
#   --requests N       Requests per user (default: 10)
#   --duration N       Test duration in seconds (default: 60)
#   --output FILE      Output file for results (default: performance_report.json)
```

### 4. `deployment_verification.py` - Deployment Verification
Automated verification of deployed AWS resources:
- CloudFormation stack status
- DynamoDB table health
- Lambda function deployment
- API Gateway accessibility
- Cognito User Pool configuration
- S3 and CloudFront setup
- Secrets Manager configuration
- Bedrock model access

**Usage:**
```bash
# Basic verification
python3 scripts/deployment_verification.py

# Custom configuration
python3 scripts/deployment_verification.py \
    --region us-west-2 \
    --stack-prefix MyMeetingScheduler \
    --output verification_report.json

# Options:
#   --region REGION       AWS region (default: us-east-1)
#   --stack-prefix PREFIX CloudFormation stack prefix (default: MeetingScheduler)
#   --output FILE         Output file for verification report
```

### 5. `run_all_tests.sh` - Master Test Runner
Runs all testing scripts in sequence for complete validation:

**Usage:**
```bash
# Set environment variables
export DEMO_API_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com"
export DEMO_USER_EMAIL="demo@example.com"
export AWS_REGION="us-east-1"
export STACK_PREFIX="MeetingScheduler"

# Make executable and run
chmod +x scripts/run_all_tests.sh
./scripts/run_all_tests.sh
```

## Prerequisites

### Python Dependencies
Install required Python packages:
```bash
pip install boto3 requests aiohttp
```

### AWS Configuration
Ensure AWS credentials are configured:
```bash
aws configure
# OR set environment variables:
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Environment Variables
Set the following environment variables for testing:

```bash
# Required for demo and performance testing
export DEMO_API_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com"
export DEMO_USER_EMAIL="demo@example.com"
export DEMO_USER_PASSWORD="DemoPass123!"

# Optional AWS configuration
export AWS_REGION="us-east-1"
export STACK_PREFIX="MeetingScheduler"
```

## Test Scenarios

### Quick Validation
For rapid deployment validation:
```bash
python3 scripts/deployment_verification.py
```

### Performance Baseline
For establishing performance baselines:
```bash
python3 scripts/performance_test.py \
    --api-url "$DEMO_API_URL" \
    --test-type load \
    --users 20 \
    --duration 120
```

### Complete Demo
For comprehensive feature demonstration:
```bash
python3 scripts/demo.py
```

### Full Test Suite
For complete validation before production:
```bash
./scripts/run_all_tests.sh
```

## Output Files

The scripts generate various output files:

- `test_data_YYYYMMDD_HHMMSS.json` - Generated test data
- `performance_results_YYYYMMDD_HHMMSS.json` - Performance test results
- `verification_report.json` - Deployment verification report

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   ```
   Solution: Configure AWS CLI or set environment variables
   ```

2. **API Gateway URL Not Set**
   ```
   Solution: Set DEMO_API_URL environment variable
   ```

3. **Permission Denied Errors**
   ```
   Solution: Ensure IAM user has required permissions for all AWS services
   ```

4. **Bedrock Access Denied**
   ```
   Solution: Enable Bedrock model access in AWS console
   ```

### Debug Mode
Add verbose logging to any script:
```bash
export PYTHONPATH="."
python3 -v scripts/demo.py
```

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Verify Deployment
  run: python3 scripts/deployment_verification.py --output verification.json

- name: Run Performance Tests
  run: python3 scripts/performance_test.py --api-url $API_URL --test-type load

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: "*.json"
```

## Contributing

When adding new test scripts:
1. Follow the existing naming convention
2. Include comprehensive error handling
3. Add usage documentation to this README
4. Ensure scripts are idempotent and safe to run multiple times