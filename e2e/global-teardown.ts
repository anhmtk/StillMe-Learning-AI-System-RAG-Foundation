import { chromium, FullConfig } from '@playwright/test';

/**
 * Global teardown for Playwright tests
 * Runs after all tests to clean up the environment
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global teardown for NicheRadar v1.5 tests...');
  
  // Start browser for cleanup tasks
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Clean up test data if needed
    console.log('🧹 Cleaning up test data...');
    const cleanupUrl = 'http://localhost:5000/api/cleanup-test-data';
    
    try {
      const response = await page.goto(cleanupUrl, { timeout: 5000 });
      if (response?.status() === 200) {
        console.log('✅ Test data cleaned up');
      } else {
        console.log('⚠️ Test data cleanup endpoint not available');
      }
    } catch (error) {
      console.log('⚠️ Test data cleanup endpoint not available');
    }
    
    // Generate test summary
    console.log('📊 Generating test summary...');
    
    // Check if test reports were generated
    const reportPaths = [
      'reports/test_report.html',
      'reports/coverage/index.html',
      'reports/playwright-report/index.html'
    ];
    
    for (const reportPath of reportPaths) {
      try {
        const response = await page.goto(`file://${process.cwd()}/${reportPath}`, { timeout: 2000 });
        if (response?.status() === 200) {
          console.log(`✅ Report generated: ${reportPath}`);
        }
      } catch (error) {
        console.log(`⚠️ Report not found: ${reportPath}`);
      }
    }
    
    // Log test completion
    console.log('✅ Global teardown completed successfully');
    console.log('📋 Test artifacts available in reports/ directory');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw error in teardown to avoid masking test failures
  } finally {
    await browser.close();
  }
}

export default globalTeardown;
