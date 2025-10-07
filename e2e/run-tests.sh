#!/bin/bash

# E2E Test Runner Script for AWS Meeting Scheduling Agent
# This script runs the comprehensive E2E testing suite

set -e

echo "🚀 Starting E2E Test Suite for AWS Meeting Scheduling Agent"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing E2E test dependencies..."
    npm install
    print_success "Dependencies installed successfully"
fi

# Install Playwright browsers if not already installed
print_status "Installing Playwright browsers..."
npx playwright install
print_success "Playwright browsers installed"

# Set environment variables
export BASE_URL=${BASE_URL:-"http://localhost:3000"}
export API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
export CI=${CI:-"false"}

print_status "Environment Configuration:"
echo "  Base URL: $BASE_URL"
echo "  API Base URL: $API_BASE_URL"
echo "  CI Mode: $CI"

# Function to run specific test suite
run_test_suite() {
    local suite_name=$1
    local test_pattern=$2
    
    print_status "Running $suite_name tests..."
    
    if npx playwright test --grep "$test_pattern" --reporter=html,json; then
        print_success "$suite_name tests completed successfully"
        return 0
    else
        print_error "$suite_name tests failed"
        return 1
    fi
}

# Parse command line arguments
TEST_SUITE=${1:-"all"}
BROWSER=${2:-"chromium"}
HEADED=${3:-"false"}

# Set Playwright options based on arguments
PLAYWRIGHT_OPTS=""
if [ "$HEADED" = "true" ]; then
    PLAYWRIGHT_OPTS="$PLAYWRIGHT_OPTS --headed"
fi

if [ "$BROWSER" != "all" ]; then
    PLAYWRIGHT_OPTS="$PLAYWRIGHT_OPTS --project=$BROWSER"
fi

print_status "Test Configuration:"
echo "  Test Suite: $TEST_SUITE"
echo "  Browser: $BROWSER"
echo "  Headed Mode: $HEADED"

# Create results directory
mkdir -p test-results
mkdir -p screenshots

# Run tests based on suite selection
case $TEST_SUITE in
    "user-journey")
        print_status "Running User Journey Tests..."
        npx playwright test --grep "@user-journey" $PLAYWRIGHT_OPTS
        ;;
    "performance")
        print_status "Running Performance Tests..."
        npx playwright test --grep "@performance" $PLAYWRIGHT_OPTS
        ;;
    "security")
        print_status "Running Security Tests..."
        npx playwright test --grep "@security" $PLAYWRIGHT_OPTS
        ;;
    "smoke")
        print_status "Running Smoke Tests..."
        npx playwright test --grep "smoke" $PLAYWRIGHT_OPTS
        ;;
    "all")
        print_status "Running All E2E Tests..."
        
        # Run user journey tests first
        if run_test_suite "User Journey" "@user-journey"; then
            USER_JOURNEY_PASSED=true
        else
            USER_JOURNEY_PASSED=false
        fi
        
        # Run performance tests
        if run_test_suite "Performance" "@performance"; then
            PERFORMANCE_PASSED=true
        else
            PERFORMANCE_PASSED=false
        fi
        
        # Run security tests
        if run_test_suite "Security" "@security"; then
            SECURITY_PASSED=true
        else
            SECURITY_PASSED=false
        fi
        
        # Print summary
        echo ""
        print_status "Test Suite Summary:"
        echo "=================="
        
        if [ "$USER_JOURNEY_PASSED" = true ]; then
            print_success "✓ User Journey Tests: PASSED"
        else
            print_error "✗ User Journey Tests: FAILED"
        fi
        
        if [ "$PERFORMANCE_PASSED" = true ]; then
            print_success "✓ Performance Tests: PASSED"
        else
            print_error "✗ Performance Tests: FAILED"
        fi
        
        if [ "$SECURITY_PASSED" = true ]; then
            print_success "✓ Security Tests: PASSED"
        else
            print_error "✗ Security Tests: FAILED"
        fi
        
        # Overall result
        if [ "$USER_JOURNEY_PASSED" = true ] && [ "$PERFORMANCE_PASSED" = true ] && [ "$SECURITY_PASSED" = true ]; then
            print_success "🎉 All E2E tests passed successfully!"
            exit 0
        else
            print_error "❌ Some E2E tests failed. Check the reports for details."
            exit 1
        fi
        ;;
    *)
        print_error "Unknown test suite: $TEST_SUITE"
        echo "Available test suites: all, user-journey, performance, security, smoke"
        exit 1
        ;;
esac

# Generate and open test report
if [ -f "playwright-report/index.html" ]; then
    print_status "Test report generated: playwright-report/index.html"
    
    if [ "$CI" != "true" ]; then
        print_status "Opening test report in browser..."
        npx playwright show-report
    fi
fi

print_success "E2E test execution completed!"