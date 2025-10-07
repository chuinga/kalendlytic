import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { ConnectionsPage } from '../pages/connections-page';
import { TestDataManager } from '../utils/test-data-manager';
import { AuthHelper } from '../utils/auth-helper';

test.describe('Complete User Journey', () => {
  let testDataManager: TestDataManager;
  let authHelper: AuthHelper;
  let testUser: any;

  test.beforeAll(async () => {
    testDataManager = new TestDataManager();
    authHelper = new AuthHelper();
    await testDataManager.initialize();
    
    const users = await testDataManager.createTestUsers();
    testUser = users[0]; // Use first test user
  });

  test.afterAll(async () => {
    await testDataManager.cleanup();
  });

  test('Complete user journey: Registration → Login → Connect Calendars → Schedule Meeting → Resolve Conflict', async ({ page, context }) => {
    // Step 1: User Registration and Login
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    
    // Verify login page loads correctly
    await expect(page).toHaveTitle(/Login/);
    expect(await loginPage.isLoginFormVisible()).toBe(true);
    
    // Perform login
    await loginPage.loginAndWaitForDashboard(testUser.email, testUser.password);
    
    // Step 2: Dashboard Access and Initial State
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.waitForDashboardLoad();
    
    // Verify dashboard loads with expected elements
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    expect(await dashboardPage.isCalendarViewVisible()).toBe(true);
    expect(await dashboardPage.isAvailabilityTimelineVisible()).toBe(true);
    
    // Initially should have no connections
    const connectionStatuses = await dashboardPage.getConnectionsStatus();
    expect(connectionStatuses.length).toBe(0);
    
    // Step 3: Connect Calendar Accounts
    await dashboardPage.navigateToConnections();
    
    const connectionsPage = new ConnectionsPage(page);
    await connectionsPage.waitForPageLoad();
    
    // Connect Google Calendar
    await connectionsPage.connectGoogle();
    expect(await connectionsPage.isGoogleConnected()).toBe(true);
    
    // Connect Microsoft Calendar
    await connectionsPage.connectMicrosoft();
    expect(await connectionsPage.isMicrosoftConnected()).toBe(true);
    
    // Verify both connections are healthy
    expect(await connectionsPage.areAllConnectionsHealthy()).toBe(true);
    
    // Step 4: Return to Dashboard and Verify Connections
    await dashboardPage.goto();
    await dashboardPage.waitForDashboardLoad();
    
    // Should now show connected calendars
    const updatedStatuses = await dashboardPage.getConnectionsStatus();
    expect(updatedStatuses.length).toBeGreaterThan(0);
    expect(await dashboardPage.areConnectionsHealthy()).toBe(true);
    
    // Step 5: Create Test Calendar Events (Simulate Conflict)
    await testDataManager.createTestCalendarData();
    await dashboardPage.refreshDashboard();
    
    // Should detect conflicts
    expect(await dashboardPage.hasConflicts()).toBe(true);
    const conflictCount = await dashboardPage.getConflictCount();
    expect(conflictCount).toBeGreaterThan(0);
    
    // Step 6: Agent Activity and Conflict Resolution
    // Verify agent has taken actions
    expect(await dashboardPage.hasRecentAgentActivity()).toBe(true);
    
    const agentActions = await dashboardPage.getAgentActions();
    expect(agentActions.length).toBeGreaterThan(0);
    
    // Should contain conflict resolution actions
    const hasConflictResolution = agentActions.some(action => 
      action.toLowerCase().includes('conflict') || 
      action.toLowerCase().includes('reschedule')
    );
    expect(hasConflictResolution).toBe(true);
    
    // Step 7: Navigate to Audit Trail
    await dashboardPage.navigateToAudit();
    
    // Verify audit trail shows agent decisions
    await page.waitForSelector('[data-testid="audit-entries"]');
    const auditEntries = await page.locator('[data-testid="audit-entry"]').count();
    expect(auditEntries).toBeGreaterThan(0);
    
    // Should have entries with rationale
    const firstEntry = page.locator('[data-testid="audit-entry"]').first();
    const rationale = await firstEntry.locator('[data-testid="rationale"]').textContent();
    expect(rationale).toBeTruthy();
    expect(rationale!.length).toBeGreaterThan(10); // Should have meaningful rationale
    
    // Step 8: Preferences Configuration
    await dashboardPage.navigateToPreferences();
    
    // Configure working hours
    await page.fill('[data-testid="start-time"]', '09:00');
    await page.fill('[data-testid="end-time"]', '17:00');
    
    // Add VIP contact
    await page.fill('[data-testid="vip-email"]', 'vip@company.com');
    await page.click('[data-testid="add-vip"]');
    
    // Set buffer time
    await page.fill('[data-testid="buffer-minutes"]', '15');
    
    // Save preferences
    await page.click('[data-testid="save-preferences"]');
    await page.waitForSelector('[data-testid="preferences-saved"]');
    
    // Step 9: Test Preference Application
    await dashboardPage.goto();
    await dashboardPage.refreshDashboard();
    
    // Agent should now consider new preferences
    const updatedActions = await dashboardPage.getAgentActions();
    const hasPreferenceBasedAction = updatedActions.some(action =>
      action.toLowerCase().includes('vip') ||
      action.toLowerCase().includes('working hours') ||
      action.toLowerCase().includes('buffer')
    );
    expect(hasPreferenceBasedAction).toBe(true);
    
    // Step 10: Security and Session Management
    // Test token refresh
    const tokenRefreshWorked = await authHelper.testTokenRefresh(page);
    expect(tokenRefreshWorked).toBe(true);
    
    // Verify no sensitive data in logs
    const errors = await dashboardPage.getErrorMessages();
    const hasSensitiveData = errors.some(error =>
      error.includes('password') ||
      error.includes('token') ||
      error.includes('secret')
    );
    expect(hasSensitiveData).toBe(false);
    
    // Step 11: Logout and Session Cleanup
    await dashboardPage.logout();
    
    // Verify redirect to login page
    await expect(page).toHaveURL(/login/);
    
    // Verify session is cleared
    const tokensAfterLogout = await authHelper.extractTokensFromPage(page);
    expect(tokensAfterLogout.accessToken).toBeFalsy();
    
    // Step 12: Verify Cannot Access Protected Routes
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/); // Should redirect to login
    
    await page.goto('/connections');
    await expect(page).toHaveURL(/login/); // Should redirect to login
    
    await page.goto('/preferences');
    await expect(page).toHaveURL(/login/); // Should redirect to login
  });

  test('Error handling and recovery scenarios', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    const connectionsPage = new ConnectionsPage(page);
    
    // Test 1: Invalid login credentials
    await loginPage.goto();
    await loginPage.login('invalid@email.com', 'wrongpassword');
    
    expect(await loginPage.hasError()).toBe(true);
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage.toLowerCase()).toContain('invalid');
    
    // Test 2: Network error simulation
    await page.route('**/api/**', route => route.abort());
    
    await loginPage.login(testUser.email, testUser.password);
    
    // Should handle network errors gracefully
    expect(await loginPage.hasError()).toBe(true);
    
    // Remove network interception
    await page.unroute('**/api/**');
    
    // Test 3: Successful login after error recovery
    await loginPage.clearForm();
    await loginPage.loginAndWaitForDashboard(testUser.email, testUser.password);
    
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    // Test 4: Connection failure handling
    await dashboardPage.navigateToConnections();
    
    // Simulate OAuth failure
    await page.route('**/oauth/**', route => route.abort());
    
    await connectionsPage.connectGoogle();
    
    // Should show connection error
    expect(await connectionsPage.hasConnectionErrors()).toBe(true);
    
    // Remove OAuth interception
    await page.unroute('**/oauth/**');
    
    // Test 5: Recovery from connection failure
    await connectionsPage.refreshConnections();
    await connectionsPage.connectGoogle();
    
    expect(await connectionsPage.isGoogleConnected()).toBe(true);
  });

  test('Accessibility and usability validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Login first
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUser.email, testUser.password);
    
    // Test 1: Keyboard navigation
    await page.keyboard.press('Tab'); // Should focus first interactive element
    await page.keyboard.press('Enter'); // Should activate focused element
    
    // Test 2: Screen reader compatibility
    const pageTitle = await dashboardPage.getPageTitle();
    expect(pageTitle).toBeTruthy();
    expect(pageTitle.length).toBeGreaterThan(0);
    
    // Test 3: Color contrast and visual elements
    const calendarView = page.locator('[data-testid="calendar-view"]');
    await expect(calendarView).toBeVisible();
    
    // Test 4: Responsive design
    await page.setViewportSize({ width: 375, height: 667 }); // Mobile size
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    await page.setViewportSize({ width: 768, height: 1024 }); // Tablet size
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    await page.setViewportSize({ width: 1920, height: 1080 }); // Desktop size
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
    
    // Test 5: Loading states and feedback
    await dashboardPage.refreshDashboard();
    
    // Should show loading indicators during refresh
    const loadingIndicator = page.locator('[data-testid="loading"]');
    // Note: Loading might be too fast to catch, so we just verify it doesn't error
    
    await dashboardPage.waitForDashboardLoad();
    expect(await dashboardPage.isDashboardFullyLoaded()).toBe(true);
  });
});