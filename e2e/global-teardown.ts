import { FullConfig } from '@playwright/test';
import { TestDataManager } from './utils/test-data-manager';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global E2E test teardown...');
  
  try {
    // Clean up test data
    const testDataManager = new TestDataManager();
    await testDataManager.cleanup();
    
    console.log('✅ Global teardown completed successfully');
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  }
}

export default globalTeardown;