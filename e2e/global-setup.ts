import { chromium, FullConfig } from '@playwright/test';
import { TestDataManager } from './utils/test-data-manager';
import { AuthHelper } from './utils/auth-helper';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Initialize test data manager
    const testDataManager = new TestDataManager();
    await testDataManager.initialize();
    
    // Create test users and data
    await testDataManager.createTestUsers();
    await testDataManager.createTestCalendarData();
    
    // Setup authentication tokens for tests
    const authHelper = new AuthHelper();
    await authHelper.setupTestAuthentication();
    
    console.log('✅ Global setup completed successfully');
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await context.close();
    await browser.close();
  }
}

export default globalSetup;