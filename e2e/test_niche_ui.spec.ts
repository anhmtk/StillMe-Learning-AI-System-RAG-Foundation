/**
 * E2E UI tests for NicheRadar v1.5 - Playwright
 * Tests Niche Radar tab, Top 10 table, Generate Playbook, Sources modal
 */

import { test, expect } from '@playwright/test';

test.describe('NicheRadar UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app with staging profile
    await page.goto('http://localhost:3000?profile=staging');
    
    // Wait for app to load
    await page.waitForSelector('[data-testid="app-layout"]', { timeout: 10000 });
  });

  test('Niche Radar tab displays Top 10 table', async ({ page }) => {
    // Click on Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    
    // Wait for Top 10 table to load
    await page.waitForSelector('[data-testid="niche-top10-table"]', { timeout: 15000 });
    
    // Check table headers
    await expect(page.locator('[data-testid="table-header-score"]')).toBeVisible();
    await expect(page.locator('[data-testid="table-header-confidence"]')).toBeVisible();
    await expect(page.locator('[data-testid="table-header-sources"]')).toBeVisible();
    
    // Check table has rows
    const tableRows = page.locator('[data-testid="niche-table-row"]');
    await expect(tableRows).toHaveCountGreaterThan(0);
    
    // Check each row has required columns
    const firstRow = tableRows.first();
    await expect(firstRow.locator('[data-testid="niche-score"]')).toBeVisible();
    await expect(firstRow.locator('[data-testid="niche-confidence"]')).toBeVisible();
    await expect(firstRow.locator('[data-testid="niche-sources"]')).toBeVisible();
  });

  test('Generate Playbook button creates playbook', async ({ page }) => {
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Click Generate Playbook for first niche
    const firstRow = page.locator('[data-testid="niche-table-row"]').first();
    await firstRow.locator('[data-testid="generate-playbook-btn"]').click();
    
    // Wait for snackbar/toast notification
    await page.waitForSelector('[data-testid="playbook-generated-toast"]', { timeout: 10000 });
    
    // Check toast message
    const toast = page.locator('[data-testid="playbook-generated-toast"]');
    await expect(toast).toContainText('Playbook generated successfully');
    
    // Check files are created (this would be verified in real implementation)
    // For now, we'll check the UI feedback
    await expect(toast).toBeVisible();
  });

  test('Sources modal displays source information', async ({ page }) => {
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Click View Sources for first niche
    const firstRow = page.locator('[data-testid="niche-table-row"]').first();
    await firstRow.locator('[data-testid="view-sources-btn"]').click();
    
    // Wait for sources modal to open
    await page.waitForSelector('[data-testid="sources-modal"]', { timeout: 5000 });
    
    // Check modal is visible
    const modal = page.locator('[data-testid="sources-modal"]');
    await expect(modal).toBeVisible();
    
    // Check modal title
    await expect(modal.locator('[data-testid="modal-title"]')).toContainText('Sources');
    
    // Check source information is displayed
    const sourceItems = modal.locator('[data-testid="source-item"]');
    await expect(sourceItems).toHaveCountGreaterThan(0);
    
    // Check each source item has required fields
    const firstSource = sourceItems.first();
    await expect(firstSource.locator('[data-testid="source-name"]')).toBeVisible();
    await expect(firstSource.locator('[data-testid="source-time"]')).toBeVisible();
    await expect(firstSource.locator('[data-testid="source-domain"]')).toBeVisible();
    await expect(firstSource.locator('[data-testid="source-url"]')).toBeVisible();
    
    // Check source URL is clickable
    const sourceUrl = firstSource.locator('[data-testid="source-url"]');
    await expect(sourceUrl).toHaveAttribute('href');
    
    // Close modal
    await modal.locator('[data-testid="close-modal-btn"]').click();
    await expect(modal).not.toBeVisible();
  });

  test('Start Experiment button creates experiment', async ({ page }) => {
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Click Start Experiment for first niche
    const firstRow = page.locator('[data-testid="niche-table-row"]').first();
    await firstRow.locator('[data-testid="start-experiment-btn"]').click();
    
    // Wait for experiment creation confirmation
    await page.waitForSelector('[data-testid="experiment-created-toast"]', { timeout: 10000 });
    
    // Check toast message
    const toast = page.locator('[data-testid="experiment-created-toast"]');
    await expect(toast).toContainText('Experiment started');
    
    // Check experiment checklist is displayed
    await page.waitForSelector('[data-testid="experiment-checklist"]', { timeout: 5000 });
    
    // Check checklist items
    const checklistItems = page.locator('[data-testid="checklist-item"]');
    await expect(checklistItems).toHaveCountGreaterThan(0);
    
    // Check first item is checked (repo created)
    const firstItem = checklistItems.first();
    await expect(firstItem.locator('[data-testid="checklist-checkbox"]')).toBeChecked();
  });

  test('Attribution and Confidence are displayed correctly', async ({ page }) => {
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Check first row has score and confidence
    const firstRow = page.locator('[data-testid="niche-table-row"]').first();
    
    // Check score is displayed and is a number
    const scoreElement = firstRow.locator('[data-testid="niche-score"]');
    await expect(scoreElement).toBeVisible();
    const scoreText = await scoreElement.textContent();
    expect(scoreText).toMatch(/^\d+\.\d+$/); // Should be a decimal number
    
    // Check confidence is displayed and is a percentage
    const confidenceElement = firstRow.locator('[data-testid="niche-confidence"]');
    await expect(confidenceElement).toBeVisible();
    const confidenceText = await confidenceElement.textContent();
    expect(confidenceText).toMatch(/^\d+%$/); // Should be a percentage
    
    // Check sources count is displayed
    const sourcesElement = firstRow.locator('[data-testid="niche-sources"]');
    await expect(sourcesElement).toBeVisible();
    const sourcesText = await sourcesElement.textContent();
    expect(sourcesText).toMatch(/^\d+ sources$/); // Should be "X sources"
  });

  test('Table sorting works correctly', async ({ page }) => {
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Click on Score header to sort
    await page.click('[data-testid="table-header-score"]');
    
    // Wait for table to re-render
    await page.waitForTimeout(1000);
    
    // Check scores are in descending order
    const scoreElements = page.locator('[data-testid="niche-score"]');
    const scores = await scoreElements.allTextContents();
    
    // Convert to numbers and check descending order
    const scoreNumbers = scores.map(score => parseFloat(score));
    for (let i = 0; i < scoreNumbers.length - 1; i++) {
      expect(scoreNumbers[i]).toBeGreaterThanOrEqual(scoreNumbers[i + 1]);
    }
    
    // Click on Confidence header to sort
    await page.click('[data-testid="table-header-confidence"]');
    
    // Wait for table to re-render
    await page.waitForTimeout(1000);
    
    // Check confidence values are in descending order
    const confidenceElements = page.locator('[data-testid="niche-confidence"]');
    const confidences = await confidenceElements.allTextContents();
    
    // Convert to numbers and check descending order
    const confidenceNumbers = confidences.map(conf => parseFloat(conf.replace('%', '')));
    for (let i = 0; i < confidenceNumbers.length - 1; i++) {
      expect(confidenceNumbers[i]).toBeGreaterThanOrEqual(confidenceNumbers[i + 1]);
    }
  });

  test('Error handling for failed data loading', async ({ page }) => {
    // Mock network failure
    await page.route('**/api/niche-radar/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    
    // Wait for error message
    await page.waitForSelector('[data-testid="error-message"]', { timeout: 10000 });
    
    // Check error message is displayed
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Failed to load niche data');
    
    // Check retry button is available
    const retryButton = page.locator('[data-testid="retry-button"]');
    await expect(retryButton).toBeVisible();
    
    // Click retry button
    await retryButton.click();
    
    // Wait for loading state
    await page.waitForSelector('[data-testid="loading-spinner"]', { timeout: 5000 });
  });

  test('Responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Navigate to Niche Radar tab
    await page.click('[data-testid="niche-radar-tab"]');
    await page.waitForSelector('[data-testid="niche-top10-table"]');
    
    // Check table is responsive
    const table = page.locator('[data-testid="niche-top10-table"]');
    await expect(table).toBeVisible();
    
    // Check table scrolls horizontally on mobile
    const tableContainer = page.locator('[data-testid="table-container"]');
    await expect(tableContainer).toHaveCSS('overflow-x', 'auto');
    
    // Check buttons are touch-friendly
    const generateButton = page.locator('[data-testid="generate-playbook-btn"]').first();
    const buttonBox = await generateButton.boundingBox();
    expect(buttonBox.height).toBeGreaterThanOrEqual(44); // Minimum touch target size
  });
});
