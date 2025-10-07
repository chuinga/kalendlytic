import { Page } from '@playwright/test';

export interface PerformanceMetrics {
  loadTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  memoryUsage: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

export class PerformanceMonitor {
  private page: Page;
  private metrics: PerformanceMetrics[] = [];

  constructor(page: Page) {
    this.page = page;
  }

  async startMonitoring(): Promise<void> {
    // Inject performance monitoring script
    await this.page.addInitScript(() => {
      // Monitor Core Web Vitals
      window.addEventListener('load', () => {
        // Record performance metrics
        const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        (window as any).performanceMetrics = {
          loadTime: perfData.loadEventEnd - perfData.loadEventStart,
          domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
          firstContentfulPaint: 0,
          largestContentfulPaint: 0,
          cumulativeLayoutShift: 0,
          firstInputDelay: 0
        };
      });

      // Monitor FCP
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            (window as any).performanceMetrics.firstContentfulPaint = entry.startTime;
          }
        }
      }).observe({ entryTypes: ['paint'] });

      // Monitor LCP
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        (window as any).performanceMetrics.largestContentfulPaint = lastEntry.startTime;
      }).observe({ entryTypes: ['largest-contentful-paint'] });

      // Monitor CLS
      let clsValue = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        (window as any).performanceMetrics.cumulativeLayoutShift = clsValue;
      }).observe({ entryTypes: ['layout-shift'] });

      // Monitor FID
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          (window as any).performanceMetrics.firstInputDelay = (entry as any).processingStart - entry.startTime;
        }
      }).observe({ entryTypes: ['first-input'] });
    });
  }

  async collectMetrics(): Promise<PerformanceMetrics> {
    const metrics = await this.page.evaluate(() => {
      const perfMetrics = (window as any).performanceMetrics || {};
      
      // Get memory usage
      const memory = (performance as any).memory || {};
      
      return {
        loadTime: perfMetrics.loadTime || 0,
        domContentLoaded: perfMetrics.domContentLoaded || 0,
        firstContentfulPaint: perfMetrics.firstContentfulPaint || 0,
        largestContentfulPaint: perfMetrics.largestContentfulPaint || 0,
        cumulativeLayoutShift: perfMetrics.cumulativeLayoutShift || 0,
        firstInputDelay: perfMetrics.firstInputDelay || 0,
        memoryUsage: {
          usedJSHeapSize: memory.usedJSHeapSize || 0,
          totalJSHeapSize: memory.totalJSHeapSize || 0,
          jsHeapSizeLimit: memory.jsHeapSizeLimit || 0
        }
      };
    });

    this.metrics.push(metrics);
    return metrics;
  }

  async measurePageLoad(url: string): Promise<PerformanceMetrics> {
    const startTime = Date.now();
    
    await this.page.goto(url);
    await this.page.waitForLoadState('networkidle');
    
    const endTime = Date.now();
    const loadTime = endTime - startTime;
    
    const metrics = await this.collectMetrics();
    metrics.loadTime = loadTime;
    
    return metrics;
  }

  async measureAction(action: () => Promise<void>): Promise<number> {
    const startTime = Date.now();
    await action();
    const endTime = Date.now();
    
    return endTime - startTime;
  }

  getAverageMetrics(): PerformanceMetrics {
    if (this.metrics.length === 0) {
      throw new Error('No metrics collected');
    }

    const avg = this.metrics.reduce((acc, metric) => {
      acc.loadTime += metric.loadTime;
      acc.domContentLoaded += metric.domContentLoaded;
      acc.firstContentfulPaint += metric.firstContentfulPaint;
      acc.largestContentfulPaint += metric.largestContentfulPaint;
      acc.cumulativeLayoutShift += metric.cumulativeLayoutShift;
      acc.firstInputDelay += metric.firstInputDelay;
      acc.memoryUsage.usedJSHeapSize += metric.memoryUsage.usedJSHeapSize;
      acc.memoryUsage.totalJSHeapSize += metric.memoryUsage.totalJSHeapSize;
      acc.memoryUsage.jsHeapSizeLimit += metric.memoryUsage.jsHeapSizeLimit;
      return acc;
    }, {
      loadTime: 0,
      domContentLoaded: 0,
      firstContentfulPaint: 0,
      largestContentfulPaint: 0,
      cumulativeLayoutShift: 0,
      firstInputDelay: 0,
      memoryUsage: {
        usedJSHeapSize: 0,
        totalJSHeapSize: 0,
        jsHeapSizeLimit: 0
      }
    });

    const count = this.metrics.length;
    
    return {
      loadTime: avg.loadTime / count,
      domContentLoaded: avg.domContentLoaded / count,
      firstContentfulPaint: avg.firstContentfulPaint / count,
      largestContentfulPaint: avg.largestContentfulPaint / count,
      cumulativeLayoutShift: avg.cumulativeLayoutShift / count,
      firstInputDelay: avg.firstInputDelay / count,
      memoryUsage: {
        usedJSHeapSize: avg.memoryUsage.usedJSHeapSize / count,
        totalJSHeapSize: avg.memoryUsage.totalJSHeapSize / count,
        jsHeapSizeLimit: avg.memoryUsage.jsHeapSizeLimit / count
      }
    };
  }

  validatePerformance(metrics: PerformanceMetrics): { passed: boolean; issues: string[] } {
    const issues: string[] = [];
    
    // Core Web Vitals thresholds
    if (metrics.largestContentfulPaint > 2500) {
      issues.push(`LCP too slow: ${metrics.largestContentfulPaint}ms (should be < 2500ms)`);
    }
    
    if (metrics.firstInputDelay > 100) {
      issues.push(`FID too slow: ${metrics.firstInputDelay}ms (should be < 100ms)`);
    }
    
    if (metrics.cumulativeLayoutShift > 0.1) {
      issues.push(`CLS too high: ${metrics.cumulativeLayoutShift} (should be < 0.1)`);
    }
    
    // Custom thresholds
    if (metrics.loadTime > 5000) {
      issues.push(`Page load too slow: ${metrics.loadTime}ms (should be < 5000ms)`);
    }
    
    if (metrics.memoryUsage.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
      issues.push(`Memory usage too high: ${(metrics.memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB (should be < 50MB)`);
    }
    
    return {
      passed: issues.length === 0,
      issues
    };
  }

  reset(): void {
    this.metrics = [];
  }
}