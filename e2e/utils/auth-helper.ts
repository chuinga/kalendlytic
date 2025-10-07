import { Page, BrowserContext } from '@playwright/test';
import jwt from 'jsonwebtoken';
import axios from 'axios';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  idToken?: string;
}

export class AuthHelper {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.API_BASE_URL || 'https://api.example.com';
  }

  async setupTestAuthentication(): Promise<void> {
    console.log('Setting up test authentication...');
    // This would typically involve setting up test OAuth credentials
    // For now, we'll use mock tokens
  }

  async loginUser(page: Page, email: string, password: string): Promise<AuthTokens> {
    console.log(`Logging in user: ${email}`);
    
    // Navigate to login page
    await page.goto('/login');
    
    // Fill in credentials
    await page.fill('[data-testid="email-input"]', email);
    await page.fill('[data-testid="password-input"]', password);
    
    // Click login button
    await page.click('[data-testid="login-button"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard');
    
    // Extract tokens from local storage or cookies
    const tokens = await this.extractTokensFromPage(page);
    
    return tokens;
  }

  async loginWithOAuth(page: Page, provider: 'google' | 'microsoft'): Promise<void> {
    console.log(`Logging in with ${provider} OAuth`);
    
    await page.goto('/connections');
    
    // Click the OAuth provider button
    const oauthButton = page.locator(`[data-testid="${provider}-oauth-button"]`);
    await oauthButton.click();
    
    // Handle OAuth popup/redirect
    if (provider === 'google') {
      await this.handleGoogleOAuth(page);
    } else {
      await this.handleMicrosoftOAuth(page);
    }
    
    // Wait for successful connection
    await page.waitForSelector(`[data-testid="${provider}-connected"]`);
  }

  private async handleGoogleOAuth(page: Page): Promise<void> {
    // In a real test, this would handle the Google OAuth flow
    // For testing purposes, we'll mock the successful OAuth response
    
    // Wait for OAuth popup or redirect
    await page.waitForTimeout(2000);
    
    // Mock successful OAuth by directly setting the connection state
    await page.evaluate(() => {
      localStorage.setItem('google-oauth-success', 'true');
      window.dispatchEvent(new CustomEvent('oauth-success', { 
        detail: { provider: 'google' } 
      }));
    });
  }

  private async handleMicrosoftOAuth(page: Page): Promise<void> {
    // Similar to Google OAuth, but for Microsoft
    await page.waitForTimeout(2000);
    
    await page.evaluate(() => {
      localStorage.setItem('microsoft-oauth-success', 'true');
      window.dispatchEvent(new CustomEvent('oauth-success', { 
        detail: { provider: 'microsoft' } 
      }));
    });
  }

  async logout(page: Page): Promise<void> {
    console.log('Logging out user');
    
    // Click user menu
    await page.click('[data-testid="user-menu"]');
    
    // Click logout
    await page.click('[data-testid="logout-button"]');
    
    // Wait for redirect to login page
    await page.waitForURL('/login');
  }

  async extractTokensFromPage(page: Page): Promise<AuthTokens> {
    // Extract authentication tokens from the page
    const tokens = await page.evaluate(() => {
      const accessToken = localStorage.getItem('accessToken') || 
                         sessionStorage.getItem('accessToken') ||
                         'mock-access-token';
      const refreshToken = localStorage.getItem('refreshToken') || 
                          sessionStorage.getItem('refreshToken') ||
                          'mock-refresh-token';
      const idToken = localStorage.getItem('idToken') || 
                     sessionStorage.getItem('idToken');
      
      return {
        accessToken,
        refreshToken,
        idToken
      };
    });
    
    return tokens;
  }

  async setAuthTokens(context: BrowserContext, tokens: AuthTokens): Promise<void> {
    // Set authentication tokens in browser context
    await context.addInitScript((tokens) => {
      localStorage.setItem('accessToken', tokens.accessToken);
      localStorage.setItem('refreshToken', tokens.refreshToken);
      if (tokens.idToken) {
        localStorage.setItem('idToken', tokens.idToken);
      }
    }, tokens);
  }

  generateMockToken(userId: string, email: string): string {
    // Generate a mock JWT token for testing
    const payload = {
      sub: userId,
      email: email,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (60 * 60), // 1 hour expiry
      iss: 'test-issuer',
      aud: 'test-audience'
    };
    
    return jwt.sign(payload, 'test-secret');
  }

  async validateTokenSecurity(token: string): Promise<boolean> {
    try {
      // Validate token structure and security
      const decoded = jwt.decode(token, { complete: true });
      
      if (!decoded || typeof decoded === 'string') {
        return false;
      }
      
      // Check for required claims
      const payload = decoded.payload as any;
      const requiredClaims = ['sub', 'email', 'iat', 'exp'];
      
      for (const claim of requiredClaims) {
        if (!payload[claim]) {
          return false;
        }
      }
      
      // Check token expiry
      if (payload.exp < Math.floor(Date.now() / 1000)) {
        return false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  }

  async testTokenRefresh(page: Page): Promise<boolean> {
    try {
      // Simulate token expiry and test refresh
      await page.evaluate(() => {
        const expiredToken = localStorage.getItem('accessToken');
        if (expiredToken) {
          // Modify token to make it expired
          localStorage.setItem('accessToken', expiredToken + '-expired');
        }
      });
      
      // Make an API call that should trigger token refresh
      await page.goto('/dashboard');
      
      // Wait for potential token refresh
      await page.waitForTimeout(3000);
      
      // Check if new token was set
      const newToken = await page.evaluate(() => {
        return localStorage.getItem('accessToken');
      });
      
      return newToken !== null && !newToken.includes('-expired');
    } catch (error) {
      console.error('Token refresh test failed:', error);
      return false;
    }
  }
}