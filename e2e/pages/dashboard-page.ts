import { Page, Locator } from '@playwright/test';
import { BasePage } from './base-page';

export class DashboardPage extends BasePage {
  private userMenu: Locator;
  private logoutButton: Locator;
  private calendarView: Locator;
  private conflictIndicators: Locator;
  private availabilityTimeline: Locator;
  private connectionsStatus: Locator;
  private agentActions: Locator;
  private preferencesLink: Locator;
  private connectionsLink: Locator;
  private auditLink: Locator;

  constructor(page: Page) {
    super(page);
    this.userMenu = page.locator('[data-testid="user-menu"]');
    this.logoutButton = page.locator('[data-testid="logout-button"]');
    this.calendarView = page.locator('[data-testid="calendar-view"]');
    this.conflictIndicators = page.locator('[data-testid="conflict-indicator"]');
    this.availabilityTimeline = page.locator('[data-testid="availability-timeline"]');
    this.connectionsStatus = page.locator('[data-testid="connections-status"]');
    this.agentActions = page.locator('[data-testid="agent-actions"]');
    this.preferencesLink = page.locator('[data-testid="preferences-link"]');
    this.connectionsLink = page.locator('[data-testid="connections-link"]');
    this.auditLink = page.locator('[data-testid="audit-link"]');
  }

  async goto(): Promise<void> {
    await super.goto('/dashboard');
    await this.waitForPageLoad();
  }

  async logout(): Promise<void> {
    await this.userMenu.click();
    await this.logoutButton.click();
    await this.waitForUrl('/login');
  }

  async isCalendarViewVisible(): Promise<boolean> {
    return await this.calendarView.isVisible();
  }

  async getConflictCount(): Promise<number> {
    return await this.conflictIndicators.count();
  }

  async hasConflicts(): Promise<boolean> {
    const count = await this.getConflictCount();
    return count > 0;
  }

  async isAvailabilityTimelineVisible(): Promise<boolean> {
    return await this.availabilityTimeline.isVisible();
  }

  async getConnectionsStatus(): Promise<string[]> {
    const connections = await this.connectionsStatus.locator('[data-testid="connection-item"]').all();
    const statuses: string[] = [];
    
    for (const connection of connections) {
      const status = await connection.getAttribute('data-status');
      if (status) {
        statuses.push(status);
      }
    }
    
    return statuses;
  }

  async areConnectionsHealthy(): Promise<boolean> {
    const statuses = await this.getConnectionsStatus();
    return statuses.every(status => status === 'connected');
  }

  async getAgentActions(): Promise<string[]> {
    const actions = await this.agentActions.locator('[data-testid="agent-action"]').all();
    const actionTexts: string[] = [];
    
    for (const action of actions) {
      const text = await action.textContent();
      if (text) {
        actionTexts.push(text.trim());
      }
    }
    
    return actionTexts;
  }

  async hasRecentAgentActivity(): Promise<boolean> {
    const actions = await this.getAgentActions();
    return actions.length > 0;
  }

  async navigateToPreferences(): Promise<void> {
    await this.preferencesLink.click();
    await this.waitForUrl('/preferences');
  }

  async navigateToConnections(): Promise<void> {
    await this.connectionsLink.click();
    await this.waitForUrl('/connections');
  }

  async navigateToAudit(): Promise<void> {
    await this.auditLink.click();
    await this.waitForUrl('/audit');
  }

  async waitForDashboardLoad(): Promise<void> {
    await this.waitForElement('[data-testid="dashboard-loaded"]');
  }

  async refreshDashboard(): Promise<void> {
    await this.page.reload();
    await this.waitForDashboardLoad();
  }

  async getWelcomeMessage(): Promise<string> {
    const welcomeElement = this.page.locator('[data-testid="welcome-message"]');
    return await welcomeElement.textContent() || '';
  }

  async isDashboardFullyLoaded(): Promise<boolean> {
    const requiredElements = [
      this.calendarView,
      this.availabilityTimeline,
      this.connectionsStatus
    ];

    for (const element of requiredElements) {
      if (!(await element.isVisible())) {
        return false;
      }
    }

    return true;
  }
}