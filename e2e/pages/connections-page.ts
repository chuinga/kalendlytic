import { Page, Locator } from '@playwright/test';
import { BasePage } from './base-page';

export class ConnectionsPage extends BasePage {
  private googleConnectButton: Locator;
  private microsoftConnectButton: Locator;
  private googleDisconnectButton: Locator;
  private microsoftDisconnectButton: Locator;
  private googleStatus: Locator;
  private microsoftStatus: Locator;
  private connectionHealth: Locator;
  private refreshButton: Locator;
  private testConnectionButton: Locator;

  constructor(page: Page) {
    super(page);
    this.googleConnectButton = page.locator('[data-testid="google-oauth-button"]');
    this.microsoftConnectButton = page.locator('[data-testid="microsoft-oauth-button"]');
    this.googleDisconnectButton = page.locator('[data-testid="google-disconnect-button"]');
    this.microsoftDisconnectButton = page.locator('[data-testid="microsoft-disconnect-button"]');
    this.googleStatus = page.locator('[data-testid="google-status"]');
    this.microsoftStatus = page.locator('[data-testid="microsoft-status"]');
    this.connectionHealth = page.locator('[data-testid="connection-health"]');
    this.refreshButton = page.locator('[data-testid="refresh-connections"]');
    this.testConnectionButton = page.locator('[data-testid="test-connection"]');
  }

  async goto(): Promise<void> {
    await super.goto('/connections');
    await this.waitForPageLoad();
  }

  async connectGoogle(): Promise<void> {
    await this.googleConnectButton.click();
    // Handle OAuth flow (mocked in test environment)
    await this.page.waitForTimeout(2000);
    await this.page.evaluate(() => {
      localStorage.setItem('google-oauth-success', 'true');
      window.dispatchEvent(new CustomEvent('oauth-success', { 
        detail: { provider: 'google' } 
      }));
    });
    await this.waitForElement('[data-testid="google-connected"]');
  }

  async connectMicrosoft(): Promise<void> {
    await this.microsoftConnectButton.click();
    // Handle OAuth flow (mocked in test environment)
    await this.page.waitForTimeout(2000);
    await this.page.evaluate(() => {
      localStorage.setItem('microsoft-oauth-success', 'true');
      window.dispatchEvent(new CustomEvent('oauth-success', { 
        detail: { provider: 'microsoft' } 
      }));
    });
    await this.waitForElement('[data-testid="microsoft-connected"]');
  }

  async disconnectGoogle(): Promise<void> {
    await this.googleDisconnectButton.click();
    // Confirm disconnection if modal appears
    const confirmButton = this.page.locator('[data-testid="confirm-disconnect"]');
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }
    await this.waitForElement('[data-testid="google-disconnected"]');
  }

  async disconnectMicrosoft(): Promise<void> {
    await this.microsoftDisconnectButton.click();
    // Confirm disconnection if modal appears
    const confirmButton = this.page.locator('[data-testid="confirm-disconnect"]');
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }
    await this.waitForElement('[data-testid="microsoft-disconnected"]');
  }

  async isGoogleConnected(): Promise<boolean> {
    const status = await this.googleStatus.getAttribute('data-status');
    return status === 'connected';
  }

  async isMicrosoftConnected(): Promise<boolean> {
    const status = await this.microsoftStatus.getAttribute('data-status');
    return status === 'connected';
  }

  async getGoogleConnectionStatus(): Promise<string> {
    return await this.googleStatus.textContent() || '';
  }

  async getMicrosoftConnectionStatus(): Promise<string> {
    return await this.microsoftStatus.textContent() || '';
  }

  async getConnectionHealth(): Promise<string> {
    return await this.connectionHealth.textContent() || '';
  }

  async refreshConnections(): Promise<void> {
    await this.refreshButton.click();
    await this.page.waitForTimeout(2000); // Wait for refresh to complete
  }

  async testConnection(provider: 'google' | 'microsoft'): Promise<boolean> {
    const testButton = this.page.locator(`[data-testid="test-${provider}-connection"]`);
    await testButton.click();
    
    // Wait for test result
    await this.page.waitForTimeout(3000);
    
    const resultElement = this.page.locator(`[data-testid="${provider}-test-result"]`);
    const result = await resultElement.getAttribute('data-result');
    
    return result === 'success';
  }

  async areAllConnectionsHealthy(): Promise<boolean> {
    const health = await this.getConnectionHealth();
    return health.includes('All connections healthy') || health.includes('✓');
  }

  async getLastSyncTime(provider: 'google' | 'microsoft'): Promise<string> {
    const syncElement = this.page.locator(`[data-testid="${provider}-last-sync"]`);
    return await syncElement.textContent() || '';
  }

  async hasConnectionErrors(): Promise<boolean> {
    const errorElements = await this.page.locator('[data-testid*="connection-error"]').count();
    return errorElements > 0;
  }

  async getConnectionErrors(): Promise<string[]> {
    const errorElements = await this.page.locator('[data-testid*="connection-error"]').all();
    const errors: string[] = [];
    
    for (const element of errorElements) {
      const text = await element.textContent();
      if (text) {
        errors.push(text.trim());
      }
    }
    
    return errors;
  }

  async waitForConnectionStatus(provider: 'google' | 'microsoft', status: 'connected' | 'disconnected'): Promise<void> {
    await this.waitForElement(`[data-testid="${provider}-${status}"]`);
  }
}