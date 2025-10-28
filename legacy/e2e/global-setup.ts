import { chromium, FullConfig } from '@playwright/test';

/**
 * Global setup for Playwright tests
 * Runs before all tests to prepare the environment
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup for NicheRadar v1.5 tests...');
  
  // Start browser for setup tasks
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Check if backend is running
    console.log('🔍 Checking backend status...');
    const backendUrl = 'http://localhost:5000/health';
    
    try {
      const response = await page.goto(backendUrl, { timeout: 10000 });
      if (response?.status() === 200) {
        console.log('✅ Backend is running');
      } else {
        console.log('❌ Backend is not responding properly');
        throw new Error('Backend health check failed');
      }
    } catch (error) {
      console.log('❌ Backend is not running. Please start the backend first.');
      throw new Error('Backend is not available');
    }
    
    // Check if frontend is running
    console.log('🔍 Checking frontend status...');
    const frontendUrl = 'http://localhost:3000';
    
    try {
      const response = await page.goto(frontendUrl, { timeout: 10000 });
      if (response?.status() === 200) {
        console.log('✅ Frontend is running');
      } else {
        console.log('❌ Frontend is not responding properly');
        throw new Error('Frontend health check failed');
      }
    } catch (error) {
      console.log('❌ Frontend is not running. Please start the frontend first.');
      throw new Error('Frontend is not available');
    }
    
    // Verify staging configuration
    console.log('🔍 Verifying staging configuration...');
    const stagingUrl = 'http://localhost:3000?profile=staging';
    
    try {
      await page.goto(stagingUrl, { timeout: 10000 });
      console.log('✅ Staging profile is accessible');
    } catch (error) {
      console.log('❌ Staging profile is not accessible');
      throw new Error('Staging profile check failed');
    }
    
    // Check if test data is available
    console.log('🔍 Checking test data availability...');
    const testDataUrl = 'http://localhost:5000/api/test-data';
    
    try {
      const response = await page.goto(testDataUrl, { timeout: 5000 });
      if (response?.status() === 200) {
        console.log('✅ Test data is available');
      } else {
        console.log('⚠️ Test data endpoint not available (this is optional)');
      }
    } catch (error) {
      console.log('⚠️ Test data endpoint not available (this is optional)');
    }
    
    console.log('✅ Global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
