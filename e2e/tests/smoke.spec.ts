import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Smoke Tests', () => {
  let testDataManager: TestDataManager;
  let testUser: any;

  test.beforeAll(async () => {
    testDataManager = new TestDataManager();
    await testDataManager.initialize();
    const users = await testDataManager.createTestUsers();
    testUser = users[0];
  });

  test.afterAll(async () => {
    await testDataManager.cleanup();
  });

  test('Application loads and basic navigation works', async ({ page }) => {
    // Test 1: Login page loads
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    await expect(page).toHaveTitle(/Login/);
    expect(await loginPage.isLoginFormVisible()).toBe(true);
    
    // Test 2: Successful login
    await loginPage.loginAndWaitForDashboard(testUser.email, testUser.password);
    
    // Test 3: Dashboard loads
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.waitForDashboardLoad();
    
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    // Test 4: Basic navigation works
    await dashboardPage.navigateToConnections();
    await expect(page).toHaveURL(/connections/);
    
    await dashboardPage.navigateToPreferences();
    await expect(page).toHaveURL(/preferences/);
    
    await dashboardPage.goto();
    await expect(page).toHaveURL(/dashboard/);
    
    // Test 5: Logout works
    await dashboardPage.logout();
    await expect(page).toHaveURL(/login/);
  });

  test('API health check', async ({ page }) => {
    // Test API connectivity
    const response = await page.request.get('/api/health');
    expect(response.status()).toBe(200);
    
    const healthData = await response.json();
    expect(healthData.status).toBe('healthy');
  });

  test('Critical user flows work', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Login
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUser.email, testUser.password);
    
    // Verify core functionality is accessible
    expect(await dashboardPage.isCalendarViewVisible()).toBe(true);
    expect(await dashboardPage.isAvailabilityTimelineVisible()).toBe(true);
    
    // Verify no critical errors
    expect(await dashboardPage.hasNoErrors()).toBe(true);
  });
});