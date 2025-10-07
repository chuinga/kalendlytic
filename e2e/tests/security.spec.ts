import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login-page';
import { DashboardPage } from '../pages/dashboard-page';
import { ConnectionsPage } from '../pages/connections-page';
import { TestDataManager } from '../utils/test-data-manager';
import { AuthHelper } from '../utils/auth-helper';

test.describe('Security Testing @security', () => {
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

  test('Authentication security validation', async ({ page }) => {
    const loginPage = new LoginPage(page);
    
    // Test SQL Injection attempts
    await loginPage.goto();
    
    const sqlInjectionAttempts = [
      "admin'; DROP TABLE users; --",
      "' OR '1'='1",
      "admin'/*",
      "' UNION SELECT * FROM users --"
    ];
    
    for (const injection of sqlInjectionAttempts) {
      await loginPage.clearForm();
      await loginPage.login(injection, 'password');
      
      expect(await loginPage.hasError()).toBe(true);
      await expect(page).not.toHaveURL(/dashboard/);
    }
    
    // Test XSS attempts in login form
    const xssAttempts = [
      "<script>alert('xss')</script>",
      "javascript:alert('xss')",
      "<img src=x onerror=alert('xss')>"
    ];
    
    for (const xss of xssAttempts) {
      await loginPage.clearForm();
      await loginPage.login(xss, 'password');
      
      expect(await loginPage.hasError()).toBe(true);
    }
  });

  test('Session management security', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    // Valid login and token extraction
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    const tokens = await authHelper.extractTokensFromPage(page);
    expect(tokens.accessToken).toBeTruthy();
    
    // Token validation
    const isValidToken = await authHelper.validateTokenSecurity(tokens.accessToken);
    expect(isValidToken).toBe(true);
    
    // Logout security
    await dashboardPage.logout();
    
    const tokensAfterLogout = await authHelper.extractTokensFromPage(page);
    expect(tokensAfterLogout.accessToken).toBeFalsy();
  });

  test('Data protection and privacy', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    // Check for sensitive data in DOM
    const pageContent = await page.content();
    
    const sensitivePatterns = [
      /password\s*[:=]\s*["'][^"']+["']/i,
      /secret\s*[:=]\s*["'][^"']+["']/i,
      /private[_-]?key\s*[:=]\s*["'][^"']+["']/i
    ];
    
    for (const pattern of sensitivePatterns) {
      expect(pageContent).not.toMatch(pattern);
    }
    
    // Local storage security
    const localStorageData = await page.evaluate(() => {
      const data: { [key: string]: string } = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          data[key] = localStorage.getItem(key) || '';
        }
      }
      return data;
    });
    
    for (const [key, value] of Object.entries(localStorageData)) {
      if (key.toLowerCase().includes('password')) {
        expect(value).toBe('');
      }
    }
  });

  test('Input validation and sanitization', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    
    await loginPage.goto();
    await loginPage.loginAndWaitForDashboard(testUsers[0].email, testUsers[0].password);
    
    await dashboardPage.navigateToPreferences();
    
    const xssPayloads = [
      "<script>alert('xss')</script>",
      "<img src=x onerror=alert('xss')>",
      "javascript:alert('xss')"
    ];
    
    for (const payload of xssPayloads) {
      await page.fill('[data-testid="name-input"]', payload);
      await page.click('[data-testid="save-preferences"]');
      
      await page.waitForTimeout(1000);
      
      const savedValue = await page.inputValue('[data-testid="name-input"]');
      expect(savedValue).not.toContain('<script>');
      expect(savedValue).not.toContain('javascript:');
    }
  });

  test('Authorization and access control', async ({ page }) => {
    const protectedRoutes = [
      '/dashboard',
      '/connections', 
      '/preferences',
      '/audit'
    ];
    
    // Test unauthorized access
    for (const route of protectedRoutes) {
      await page.goto(route);
      
      const currentUrl = page.url();
      const isProtected = currentUrl.includes('/login') || 
                         currentUrl.includes('/error');
      expect(isProtected).toBe(true);
    }
  });
});