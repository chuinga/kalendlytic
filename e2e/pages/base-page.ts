import { Page, Locator } from '@playwright/test';

export abstract class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto(path: string = ''): Promise<void> {
    await this.page.goto(path);
  }

  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
  }

  async getPageTitle(): Promise<string> {
    return await this.page.title();
  }

  async isElementVisible(selector: string): Promise<boolean> {
    try {
      await this.page.waitForSelector(selector, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickElement(selector: string): Promise<void> {
    await this.page.click(selector);
  }

  async fillInput(selector: string, value: string): Promise<void> {
    await this.page.fill(selector, value);
  }

  async getText(selector: string): Promise<string> {
    return await this.page.textContent(selector) || '';
  }

  async waitForElement(selector: string, timeout: number = 10000): Promise<Locator> {
    return this.page.waitForSelector(selector, { timeout });
  }

  async waitForUrl(url: string | RegExp, timeout: number = 10000): Promise<void> {
    await this.page.waitForURL(url, { timeout });
  }

  async getErrorMessages(): Promise<string[]> {
    const errorElements = await this.page.locator('[data-testid*="error"], .error, .alert-error').all();
    const messages: string[] = [];
    
    for (const element of errorElements) {
      const text = await element.textContent();
      if (text) {
        messages.push(text.trim());
      }
    }
    
    return messages;
  }

  async hasNoErrors(): Promise<boolean> {
    const errors = await this.getErrorMessages();
    return errors.length === 0;
  }
}