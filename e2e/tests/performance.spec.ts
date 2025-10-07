import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { ConnectionsPage } from '../pages/connections-page';
import { TestDataManager } from '../utils/test-data-manager';
import { AuthHelper } from '../utils/auth-helper';

test.describe('Performance Testing @performance', () => {
  let testDataManager: TestDataManager;
  let authHelper: AuthHelper;
  let testUsers: any[];

  test.beforeAll(async () => {
    testDataManager = new TestDataManager();
    authHelper = new AuthHelper();
    await testDataManager.initialize();
    testUsers = await testDataManager.createTestUsers();
  });

  test.afterAll(async () => {
    await testDataManager.cleanup();
  });

  test('Page load performance benchmarks', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Test 1: Login page load time
    const loginStartTime = Date.now();
    await loginPage.goto();
    await loginPage.waitForPageLoad();
    const loginLoadTime = Date.now() - loginStartTime;
    
    console.log(`Login page load time: ${loginLoadTime}ms`);
    expect(loginLoadTime).toBeLessThan(3000); // Should load within 3 seconds
    
    // Test 2: Authentication performance
    const authStartTime = Date.now();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    const authTime = Date.now() - authStartTime;
    
    console.log(`Authentication time: ${authTime}ms`);
    expect(authTime).toBeLessThan(5000); // Should authenticate within 5 seconds
    
    // Test 3: Dashboard load time with data
    const dashboardStartTime = Date.now();
    await dashboardPage.waitForDashboardLoad();
    const dashboardLoadTime = Date.now() - dashboardStartTime;
    
    console.log(`Dashboard load time: ${dashboardLoadTime}ms`);
    expect(dashboardLoadTime).toBeLessThan(4000); // Should load within 4 seconds
    
    // Test 4: Calendar data rendering performance
    await testDataManager.createTestCalendarData();
    
    const refreshStartTime = Date.now();
    await dashboardPage.refreshDashboard();
    const refreshTime = Date.now() - refreshStartTime;
    
    console.log(`Dashboard refresh time: ${refreshTime}ms`);
    expect(refreshTime).toBeLessThan(6000); // Should refresh within 6 seconds
  });

  test('Large dataset performance', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Login first
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    // Test 1: Large calendar dataset (1000 events)
    console.log('Creating large dataset with 1000 events...');
    const largeDataset = await testDataManager.createLargeDataset(1000);
    expect(largeDataset.length).toBe(1000);
    
    const largeDataStartTime = Date.now();
    await dashboardPage.refreshDashboard();
    const largeDataLoadTime = Date.now() - largeDataStartTime;
    
    console.log(`Large dataset load time (1000 events): ${largeDataLoadTime}ms`);
    expect(largeDataLoadTime).toBeLessThan(15000); // Should handle large dataset within 15 seconds
    
    // Verify dashboard still functions correctly
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    expect(await dashboardPage.isCalendarViewVisible()).toBe(true);
    
    // Test 2: Conflict detection performance with large dataset
    const conflictDetectionStartTime = Date.now();
    const hasConflicts = await dashboardPage.hasConflicts();
    const conflictDetectionTime = Date.now() - conflictDetectionStartTime;
    
    console.log(`Conflict detection time: ${conflictDetectionTime}ms`);
    expect(conflictDetectionTime).toBeLessThan(3000); // Should detect conflicts within 3 seconds
    
    // Test 3: Agent processing performance
    const agentStartTime = Date.now();
    const agentActions = await dashboardPage.getAgentActions();
    const agentProcessingTime = Date.now() - agentStartTime;
    
    console.log(`Agent processing time: ${agentProcessingTime}ms`);
    expect(agentProcessingTime).toBeLessThan(5000); // Agent should process within 5 seconds
    expect(agentActions.length).toBeGreaterThan(0);
  });

  test('Concurrent user simulation', async ({ browser }) => {
    const concurrentUsers = 5;
    const userSessions: Promise<void>[] = [];
    
    console.log(`Simulating ${concurrentUsers} concurrent users...`);
    
    // Create concurrent user sessions
    for (let i = 0; i < concurrentUsers; i++) {
      const userSession = simulateUserSession(browser, testUsers[i % testUsers.length], i);
      userSessions.push(userSession);
    }
    
    // Wait for all sessions to complete
    const startTime = Date.now();
    await Promise.all(userSessions);
    const totalTime = Date.now() - startTime;
    
    console.log(`All ${concurrentUsers} concurrent sessions completed in: ${totalTime}ms`);
    expect(totalTime).toBeLessThan(30000); // All sessions should complete within 30 seconds
  });

  test('Memory and resource usage', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Login and load dashboard
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    // Get initial memory usage
    const initialMetrics = await page.evaluate(() => {
      return {
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0,
        totalJSHeapSize: (performance as any).memory?.totalJSHeapSize || 0,
        jsHeapSizeLimit: (performance as any).memory?.jsHeapSizeLimit || 0
      };
    });
    
    console.log('Initial memory usage:', initialMetrics);
    
    // Load large dataset and perform operations
    await testDataManager.createLargeDataset(500);
    await dashboardPage.refreshDashboard();
    
    // Perform multiple operations to stress test
    for (let i = 0; i < 10; i++) {
      await dashboardPage.refreshDashboard();
      await page.waitForTimeout(1000);
    }
    
    // Get final memory usage
    const finalMetrics = await page.evaluate(() => {
      return {
        usedJSHeapSize: (performance as any).memory?.usedJSHeapSize || 0,
        totalJSHeapSize: (performance as any).memory?.totalJSHeapSize || 0,
        jsHeapSizeLimit: (performance as any).memory?.jsHeapSizeLimit || 0
      };
    });
    
    console.log('Final memory usage:', finalMetrics);
    
    // Check for memory leaks (memory usage shouldn't grow excessively)
    const memoryGrowth = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize;
    const memoryGrowthMB = memoryGrowth / (1024 * 1024);
    
    console.log(`Memory growth: ${memoryGrowthMB.toFixed(2)} MB`);
    expect(memoryGrowthMB).toBeLessThan(50); // Memory growth should be less than 50MB
  });

  test('API response time benchmarks', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    const connectionsPage = new ConnectionsPage(page);
    
    // Track API response times
    const apiTimes: { [key: string]: number[] } = {};
    
    page.on('response', response => {
      const url = response.url();
      const timing = response.timing();
      
      if (url.includes('/api/')) {
        const endpoint = url.split('/api/')[1].split('?')[0];
        if (!apiTimes[endpoint]) {
          apiTimes[endpoint] = [];
        }
        apiTimes[endpoint].push(timing.responseEnd);
      }
    });
    
    // Perform various operations to trigger API calls
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    await dashboardPage.navigateToConnections();
    await connectionsPage.refreshConnections();
    
    await dashboardPage.goto();
    await dashboardPage.refreshDashboard();
    
    await dashboardPage.navigateToAudit();
    
    // Wait for all API calls to complete
    await page.waitForTimeout(5000);
    
    // Analyze API performance
    console.log('API Response Times:');
    for (const [endpoint, times] of Object.entries(apiTimes)) {
      if (times.length > 0) {
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const maxTime = Math.max(...times);
        
        console.log(`${endpoint}: avg=${avgTime.toFixed(2)}ms, max=${maxTime.toFixed(2)}ms`);
        
        // API endpoints should respond within reasonable time
        expect(avgTime).toBeLessThan(2000); // Average response time < 2s
        expect(maxTime).toBeLessThan(5000); // Max response time < 5s
      }
    }
  });

  test('Network conditions simulation', async ({ page, context }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Test 1: Slow 3G network simulation
    await context.route('**/*', async route => {
      // Simulate slow network by adding delay
      await new Promise(resolve => setTimeout(resolve, 100));
      await route.continue();
    });
    
    const slowNetworkStartTime = Date.now();
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    const slowNetworkTime = Date.now() - slowNetworkStartTime;
    
    console.log(`Slow network login time: ${slowNetworkTime}ms`);
    expect(slowNetworkTime).toBeLessThan(15000); // Should work even on slow network within 15s
    
    // Remove network simulation
    await context.unroute('**/*');
    
    // Test 2: Intermittent connectivity
    let requestCount = 0;
    await context.route('**/*', async route => {
      requestCount++;
      // Fail every 5th request to simulate intermittent connectivity
      if (requestCount % 5 === 0) {
        await route.abort();
      } else {
        await route.continue();
      }
    });
    
    // Should handle intermittent failures gracefully
    await dashboardPage.refreshDashboard();
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    await context.unroute('**/*');
  });
});

async function simulateUserSession(browser: any, user: any, sessionId: number): Promise<void> {
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log(`Starting session ${sessionId} for user ${user.email}`);
    
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Login
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(user.email, user.password);
    
    // Perform typical user actions
    await dashboardPage.waitForDashboardLoad();
    await dashboardPage.refreshDashboard();
    
    // Navigate between pages
    await dashboardPage.navigateToConnections();
    await page.waitForTimeout(2000);
    
    await dashboardPage.navigateToPreferences();
    await page.waitForTimeout(2000);
    
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardLoad();
    
    // Logout
    await dashboardPage.logout();
    
    console.log(`Session ${sessionId} completed successfully`);
  } catch (error) {
    console.error(`Session ${sessionId} failed:`, error);
    throw error;
  } finally {
    await context.close();
  }
}