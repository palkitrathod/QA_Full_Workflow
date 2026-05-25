import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

dotenv.config({ quiet: true });

export default defineConfig({
  testDir: './tests/specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['json', { outputFile: 'playwright-results.json' }],
    ['line'],
    ['allure-playwright', { resultsDir: 'allure-results' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: process.env.TARGET_APP_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
