import { Page } from '@playwright/test';

export interface SecurityIssue {
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  description: string;
  location: string;
  recommendation: string;
}

export class SecurityScanner {
  private page: Page;
  private issues: SecurityIssue[] = [];

  constructor(page: Page) {
    this.page = page;
  }

  async scanPage(): Promise<SecurityIssue[]> {
    this.issues = [];
    
    await this.checkSecurityHeaders();
    await this.checkContentSecurityPolicy();
    await this.checkSensitiveDataExposure();
    await this.checkInputValidation();
    await this.checkAuthenticationSecurity();
    await this.checkSessionManagement();
    
    return this.issues;
  }

  private async checkSecurityHeaders(): Promise<void> {
    const response = await this.page.waitForResponse(response => 
      response.url().includes(this.page.url())
    ).catch(() => null);
    
    if (!response) return;
    
    const headers = response.headers();
    
    // Check for missing security headers
    const requiredHeaders = [
      { name: 'x-frame-options', severity: 'medium' as const },
      { name: 'x-content-type-options', severity: 'medium' as const },
      { name: 'x-xss-protection', severity: 'medium' as const },
      { name: 'strict-transport-security', severity: 'high' as const },
      { name: 'content-security-policy', severity: 'high' as const }
    ];
    
    for (const header of requiredHeaders) {
      if (!headers[header.name]) {
        this.issues.push({
          severity: header.severity,
          type: 'Missing Security Header',
          description: `Missing ${header.name} header`,
          location: 'HTTP Response Headers',
          recommendation: `Add ${header.name} header to prevent security vulnerabilities`
        });
      }
    }
    
    // Check HSTS header value
    const hstsHeader = headers['strict-transport-security'];
    if (hstsHeader && !hstsHeader.includes('max-age=')) {
      this.issues.push({
        severity: 'medium',
        type: 'Weak HSTS Configuration',
        description: 'HSTS header missing max-age directive',
        location: 'HTTP Response Headers',
        recommendation: 'Include max-age directive in HSTS header'
      });
    }
  }

  private async checkContentSecurityPolicy(): Promise<void> {
    const cspHeader = await this.page.evaluate(() => {
      const metaCSP = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
      return metaCSP ? metaCSP.getAttribute('content') : null;
    });
    
    if (!cspHeader) {
      this.issues.push({
        severity: 'high',
        type: 'Missing CSP',
        description: 'No Content Security Policy found',
        location: 'HTML Meta Tags',
        recommendation: 'Implement Content Security Policy to prevent XSS attacks'
      });
      return;
    }
    
    // Check for unsafe CSP directives
    const unsafeDirectives = [
      "'unsafe-eval'",
      "'unsafe-inline'",
      "data:",
      "*"
    ];
    
    for (const directive of unsafeDirectives) {
      if (cspHeader.includes(directive)) {
        this.issues.push({
          severity: 'medium',
          type: 'Unsafe CSP Directive',
          description: `CSP contains unsafe directive: ${directive}`,
          location: 'Content Security Policy',
          recommendation: `Remove or restrict ${directive} directive in CSP`
        });
      }
    }
  }

  private async checkSensitiveDataExposure(): Promise<void> {
    // Check page source for sensitive data
    const pageContent = await this.page.content();
    
    const sensitivePatterns = [
      { pattern: /password\s*[:=]\s*["'][^"']+["']/gi, type: 'Password Exposure' },
      { pattern: /api[_-]?key\s*[:=]\s*["'][^"']+["']/gi, type: 'API Key Exposure' },
      { pattern: /secret\s*[:=]\s*["'][^"']+["']/gi, type: 'Secret Exposure' },
      { pattern: /private[_-]?key\s*[:=]\s*["'][^"']+["']/gi, type: 'Private Key Exposure' },
      { pattern: /token\s*[:=]\s*["'][A-Za-z0-9+/]{20,}["']/gi, type: 'Token Exposure' }
    ];
    
    for (const { pattern, type } of sensitivePatterns) {
      const matches = pageContent.match(pattern);
      if (matches) {
        this.issues.push({
          severity: 'critical',
          type: type,
          description: `Sensitive data found in page source: ${matches[0].substring(0, 50)}...`,
          location: 'HTML Source',
          recommendation: 'Remove sensitive data from client-side code'
        });
      }
    }
    
    // Check localStorage and sessionStorage
    const storageData = await this.page.evaluate(() => {
      const data: { [key: string]: any } = {};
      
      // Check localStorage
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          data[`localStorage.${key}`] = localStorage.getItem(key);
        }
      }
      
      // Check sessionStorage
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key) {
          data[`sessionStorage.${key}`] = sessionStorage.getItem(key);
        }
      }
      
      return data;
    });
    
    for (const [key, value] of Object.entries(storageData)) {
      if (typeof value === 'string') {
        if (key.toLowerCase().includes('password') && value.length > 0) {
          this.issues.push({
            severity: 'critical',
            type: 'Password in Storage',
            description: `Password stored in ${key}`,
            location: 'Browser Storage',
            recommendation: 'Never store passwords in browser storage'
          });
        }
        
        if (key.toLowerCase().includes('secret') && value.length > 0) {
          this.issues.push({
            severity: 'high',
            type: 'Secret in Storage',
            description: `Secret stored in ${key}`,
            location: 'Browser Storage',
            recommendation: 'Avoid storing secrets in browser storage'
          });
        }
      }
    }
  }

  private async checkInputValidation(): Promise<void> {
    // Find all input fields
    const inputs = await this.page.locator('input, textarea, select').all();
    
    for (let i = 0; i < inputs.length; i++) {
      const input = inputs[i];
      const tagName = await input.evaluate(el => el.tagName.toLowerCase());
      const type = await input.getAttribute('type') || 'text';
      const name = await input.getAttribute('name') || `input-${i}`;
      
      // Check for missing input validation attributes
      if (type === 'email') {
        const pattern = await input.getAttribute('pattern');
        if (!pattern) {
          this.issues.push({
            severity: 'low',
            type: 'Missing Input Validation',
            description: `Email input ${name} missing pattern validation`,
            location: `Input field: ${name}`,
            recommendation: 'Add pattern attribute for email validation'
          });
        }
      }
      
      // Check for missing maxlength on text inputs
      if (['text', 'textarea'].includes(type)) {
        const maxLength = await input.getAttribute('maxlength');
        if (!maxLength) {
          this.issues.push({
            severity: 'low',
            type: 'Missing Input Length Limit',
            description: `Text input ${name} missing maxlength attribute`,
            location: `Input field: ${name}`,
            recommendation: 'Add maxlength attribute to prevent buffer overflow attacks'
          });
        }
      }
      
      // Check for autocomplete on sensitive fields
      if (name.toLowerCase().includes('password') || name.toLowerCase().includes('secret')) {
        const autocomplete = await input.getAttribute('autocomplete');
        if (autocomplete !== 'off' && autocomplete !== 'new-password') {
          this.issues.push({
            severity: 'medium',
            type: 'Insecure Autocomplete',
            description: `Sensitive input ${name} allows autocomplete`,
            location: `Input field: ${name}`,
            recommendation: 'Set autocomplete="off" for sensitive fields'
          });
        }
      }
    }
  }

  private async checkAuthenticationSecurity(): Promise<void> {
    // Check for login form security
    const loginForm = await this.page.locator('form').first();
    
    if (await loginForm.isVisible()) {
      const method = await loginForm.getAttribute('method');
      if (method && method.toLowerCase() !== 'post') {
        this.issues.push({
          severity: 'high',
          type: 'Insecure Form Method',
          description: 'Login form uses GET method',
          location: 'Login Form',
          recommendation: 'Use POST method for login forms'
        });
      }
      
      const action = await loginForm.getAttribute('action');
      if (action && action.startsWith('http://')) {
        this.issues.push({
          severity: 'critical',
          type: 'Insecure Form Action',
          description: 'Login form submits to HTTP URL',
          location: 'Login Form',
          recommendation: 'Use HTTPS for form submission'
        });
      }
    }
  }

  private async checkSessionManagement(): Promise<void> {
    // Check for session cookies
    const cookies = await this.page.context().cookies();
    
    for (const cookie of cookies) {
      if (cookie.name.toLowerCase().includes('session') || 
          cookie.name.toLowerCase().includes('auth') ||
          cookie.name.toLowerCase().includes('token')) {
        
        if (!cookie.secure) {
          this.issues.push({
            severity: 'high',
            type: 'Insecure Cookie',
            description: `Session cookie ${cookie.name} not marked as secure`,
            location: 'HTTP Cookies',
            recommendation: 'Mark session cookies as secure'
          });
        }
        
        if (!cookie.httpOnly) {
          this.issues.push({
            severity: 'medium',
            type: 'Cookie Accessible via JavaScript',
            description: `Session cookie ${cookie.name} not marked as httpOnly`,
            location: 'HTTP Cookies',
            recommendation: 'Mark session cookies as httpOnly'
          });
        }
        
        if (cookie.sameSite === 'None' || !cookie.sameSite) {
          this.issues.push({
            severity: 'medium',
            type: 'Missing SameSite Protection',
            description: `Session cookie ${cookie.name} missing SameSite attribute`,
            location: 'HTTP Cookies',
            recommendation: 'Set SameSite attribute to Strict or Lax'
          });
        }
      }
    }
  }

  getIssuesBySeverity(severity: 'low' | 'medium' | 'high' | 'critical'): SecurityIssue[] {
    return this.issues.filter(issue => issue.severity === severity);
  }

  getCriticalIssues(): SecurityIssue[] {
    return this.getIssuesBySeverity('critical');
  }

  getHighIssues(): SecurityIssue[] {
    return this.getIssuesBySeverity('high');
  }

  hasSecurityIssues(): boolean {
    return this.issues.length > 0;
  }

  hasCriticalIssues(): boolean {
    return this.getCriticalIssues().length > 0;
  }

  generateReport(): string {
    if (this.issues.length === 0) {
      return 'No security issues found.';
    }
    
    let report = 'Security Scan Report\n';
    report += '===================\n\n';
    
    const severityOrder = ['critical', 'high', 'medium', 'low'] as const;
    
    for (const severity of severityOrder) {
      const severityIssues = this.getIssuesBySeverity(severity);
      if (severityIssues.length > 0) {
        report += `${severity.toUpperCase()} ISSUES (${severityIssues.length}):\n`;
        report += '-'.repeat(20) + '\n';
        
        for (const issue of severityIssues) {
          report += `Type: ${issue.type}\n`;
          report += `Description: ${issue.description}\n`;
          report += `Location: ${issue.location}\n`;
          report += `Recommendation: ${issue.recommendation}\n\n`;
        }
      }
    }
    
    return report;
  }
}