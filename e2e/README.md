# End-to-End Testing Suite

This directory contains the comprehensive end-to-end testing suite for the AWS Meeting Scheduling Agent. The test suite covers complete user journeys, performance benchmarks, and security validation.

## Overview

The E2E testing suite is built using Playwright and provides:

- **Complete User Journey Testing**: Full workflow from registration to meeting scheduling
- **Performance Testing**: Load times, concurrent users, and large dataset handling
- **Security Testing**: Authentication, authorization, and data protection validation

## Test Structure

```
e2e/
├── tests/
│   ├── user-journey.spec.ts    # Complete user workflow tests
│   ├── performance.spec.ts     # Performance and load testing
│   └── security.spec.ts        # Security vulnerability testing
├── pages/
│   ├── base-page.ts           # Base page object model
│   ├── login-page.ts          # Login page interactions
│   ├── dashboard-page.ts      # Dashboard page interactions
│   └── connections-page.ts    # Connections page interactions
├── utils/
│   ├── test-data-manager.ts   # Test data creation and cleanup
│   ├── auth-helper.ts         # Authentication utilities
│   ├── performance-monitor.ts # Performance metrics collection
│   └── security-scanner.ts    # Security vulnerability scanning
├── playwright.config.ts       # Playwright configuration
├── global-setup.ts           # Global test setup
├── global-teardown.ts        # Global test cleanup
└── run-tests.sh              # Test execution script
```

## Prerequisites

1. **Node.js** (v18 or higher)
2. **npm** or **yarn**
3. **Running application** (frontend and backend)

## Installation

1. Navigate to the e2e directory:
```bash
cd e2e
```

2. Install dependencies:
```bash
npm install
```

3. Install Playwright browsers:
```bash
npx playwright install
```

## Running Tests

### Quick Start

Run all tests:
```bash
npm test
```

Or use the test runner script:
```bash
./run-tests.sh all
```

### Specific Test Suites

**User Journey Tests:**
```bash
npm run test:user-journey
# or
./run-tests.sh user-journey
```

**Performance Tests:**
```bash
npm run test:performance
# or
./run-tests.sh performance
```

**Security Tests:**
```bash
npm run test:security
# or
./run-tests.sh security
```

### Browser-Specific Testing

Run tests on specific browsers:
```bash
./run-tests.sh all chromium
./run-tests.sh all firefox
./run-tests.sh all webkit
```

### Headed Mode (Visual Testing)

Run tests with browser UI visible:
```bash
npm run test:headed
# or
./run-tests.sh all chromium true
```

### Debug Mode

Run tests in debug mode:
```bash
npm run test:debug
```

## Test Categories

### 1. User Journey Tests (@user-journey)

Tests the complete user workflow:

- **Registration and Login**: User account creation and authentication
- **Calendar Connections**: OAuth integration with Google and Microsoft
- **Meeting Scheduling**: Creating and managing calendar events
- **Conflict Resolution**: Agent-driven conflict detection and resolution
- **Preferences Management**: User preference configuration
- **Audit Trail**: Decision tracking and rationale viewing
- **Error Handling**: Recovery from various error scenarios
- **Accessibility**: Keyboard navigation and screen reader compatibility

### 2. Performance Tests (@performance)

Validates system performance under various conditions:

- **Page Load Performance**: Load time benchmarks for all pages
- **Large Dataset Handling**: Performance with 1000+ calendar events
- **Concurrent Users**: Simulation of multiple simultaneous users
- **Memory Usage**: Memory leak detection and resource monitoring
- **API Response Times**: Backend performance validation
- **Network Conditions**: Testing under slow/intermittent connectivity

**Performance Thresholds:**
- Page load time: < 3 seconds
- Authentication time: < 5 seconds
- Dashboard load: < 4 seconds
- Large dataset (1000 events): < 15 seconds
- Memory usage: < 50MB growth
- API response time: < 2 seconds average

### 3. Security Tests (@security)

Comprehensive security validation:

- **Authentication Security**: SQL injection, XSS, brute force protection
- **Session Management**: Token validation, refresh, and cleanup
- **Data Protection**: Sensitive data exposure prevention
- **Input Validation**: XSS, command injection, path traversal protection
- **Authorization**: Access control and role-based permissions
- **OAuth Security**: State parameter validation, CSRF protection
- **Content Security Policy**: CSP header validation
- **Data Encryption**: Secure data transmission and storage

## Configuration

### Environment Variables

Set these environment variables for test configuration:

```bash
# Application URLs
export BASE_URL="http://localhost:3000"
export API_BASE_URL="http://localhost:8000"

# Test Configuration
export CI="false"                    # Set to "true" for CI environments
export PLAYWRIGHT_BROWSERS_PATH=""   # Custom browser installation path
```

### Playwright Configuration

The `playwright.config.ts` file contains:

- **Browser Configuration**: Chrome, Firefox, Safari, Mobile browsers
- **Test Timeouts**: Global and action-specific timeouts
- **Retry Logic**: Automatic retry on failure
- **Reporting**: HTML, JSON, and JUnit reports
- **Screenshots/Videos**: Capture on failure
- **Parallel Execution**: Optimized test execution

## Test Data Management

The test suite uses the `TestDataManager` class to:

- **Create Test Users**: Generate users with different roles and permissions
- **Generate Calendar Data**: Create realistic calendar events and conflicts
- **Large Dataset Creation**: Generate performance testing datasets
- **Cleanup**: Automatic cleanup after test completion

### Test Users

The suite creates these test users:
- `test.user1@example.com` - Regular user (America/New_York)
- `test.user2@example.com` - Regular user (America/Los_Angeles)
- `admin@example.com` - Admin user (UTC)

## Performance Monitoring

The `PerformanceMonitor` class tracks:

- **Core Web Vitals**: LCP, FID, CLS metrics
- **Load Times**: Page and resource loading performance
- **Memory Usage**: JavaScript heap size monitoring
- **Custom Metrics**: Application-specific performance indicators

## Security Scanning

The `SecurityScanner` class validates:

- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Content Security Policy**: Unsafe directive detection
- **Sensitive Data Exposure**: Password, token, key exposure
- **Input Validation**: Missing validation attributes
- **Session Security**: Cookie security attributes

## Reporting

Test results are generated in multiple formats:

- **HTML Report**: Interactive report with screenshots and videos
- **JSON Report**: Machine-readable test results
- **JUnit Report**: CI/CD integration format
- **Console Output**: Real-time test execution feedback

### Viewing Reports

After test execution:
```bash
npx playwright show-report
```

Or open `playwright-report/index.html` in a browser.

## CI/CD Integration

For continuous integration:

```yaml
# Example GitHub Actions workflow
- name: Run E2E Tests
  run: |
    cd e2e
    npm install
    npx playwright install --with-deps
    ./run-tests.sh all
  env:
    BASE_URL: ${{ secrets.BASE_URL }}
    API_BASE_URL: ${{ secrets.API_BASE_URL }}
    CI: true
```

## Troubleshooting

### Common Issues

1. **Browser Installation Failures**:
   ```bash
   npx playwright install-deps
   npx playwright install
   ```

2. **Test Timeouts**:
   - Increase timeout values in `playwright.config.ts`
   - Check application performance
   - Verify network connectivity

3. **Authentication Failures**:
   - Verify test user credentials
   - Check OAuth configuration
   - Validate API endpoints

4. **Performance Test Failures**:
   - Check system resources
   - Verify application optimization
   - Review performance thresholds

### Debug Mode

For detailed debugging:
```bash
npx playwright test --debug
```

This opens the Playwright Inspector for step-by-step debugging.

### Verbose Logging

Enable verbose logging:
```bash
DEBUG=pw:api npx playwright test
```

## Best Practices

1. **Test Independence**: Each test should be independent and not rely on others
2. **Data Cleanup**: Always clean up test data after execution
3. **Stable Selectors**: Use `data-testid` attributes for reliable element selection
4. **Performance Baselines**: Regularly update performance thresholds based on improvements
5. **Security Updates**: Keep security tests updated with latest vulnerability patterns

## Contributing

When adding new tests:

1. Follow the existing page object model pattern
2. Add appropriate test tags (@user-journey, @performance, @security)
3. Include proper error handling and cleanup
4. Update this README with new test descriptions
5. Ensure tests pass in all supported browsers

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Playwright documentation
3. Check application logs for errors
4. Contact the development team