import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TARGET_APP_URL || 'https://dev.dmerocket.com/insurance';
const USERNAME = process.env.USERNAME || 'admin@selectortho.net';
const PASSWORD = process.env.PASSWORD || 'Password123!';

const LONG_NAME = 'BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)';
const UPDATED_NAME = 'BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) UPDATED';
const SHORT_NAME = 'TEST INSURANCE SHORT';
const SPECIAL_NAME = 'BCBS TPA (MID-LEVEL) & ASSOCIATES — SOUTHWEST';
const FIFTY_ONE_CHARS = 'A'.repeat(51);

async function login(page) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 60000 });
  const url = page.url();
  if (url.includes('auth0.com') || url.includes('login')) {
    await page.waitForSelector('input[name="username"], input[type="email"], input#username', { timeout: 20000 });
    await page.locator('input[name="username"], input[type="email"], input#username').first().fill(USERNAME);
    const continueBtn = page.locator('button:has-text("Continue"), button:has-text("Next"), button[type="submit"]').first();
    if (await continueBtn.isVisible({ timeout: 3000 })) { await continueBtn.click(); await page.waitForTimeout(1500); }
    await page.locator('input[name="password"], input[type="password"], input#password').first().fill(PASSWORD);
    await page.locator('button:has-text("Login"), button:has-text("Sign In"), button[type="submit"]').first().click();
    await page.waitForLoadState('networkidle', { timeout: 60000 });
  }
}

async function searchInsurance(page, name) {
  await page.locator('input[placeholder="Search name"]').fill(name);
  await page.locator('button:has-text("Search Insurances")').click();
  await page.waitForTimeout(2000);
}

async function findRow(page, name) {
  let maxPages = 50;
  while (maxPages-- > 0) {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    for (let i = 0; i < count; i++) {
      const cell = rows.nth(i).locator('td').first();
      const text = (await cell.textContent()) || '';
      if (text.trim() === name.trim()) {
        return { row: rows.nth(i), cell };
      }
    }
    const nextBtn = page.locator('button:has-text("Next Page")');
    const cls = await nextBtn.getAttribute('class');
    if (cls && cls.includes('cursor-not-allowed')) break;
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
      await page.waitForTimeout(1500);
    } else {
      break;
    }
  }
  return null;
}

test.describe('Insurance Name Truncation Fix — Acceptance Criteria Verification', () => {

  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
  });

  test('TC-004: Create insurance with long name saves without truncation', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await page.locator('button:has-text("New Insurance")').click();
    await page.waitForSelector('input#name', { timeout: 10000 });
    await page.locator('input#name').fill(LONG_NAME);
    await page.locator('button:has-text("Save and Close")').click();
    await page.waitForTimeout(3000);
  });

  test('TC-005: Saved insurance name is exactly the full name on create', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await searchInsurance(page, LONG_NAME);
    const result = await findRow(page, LONG_NAME);
    expect(result).not.toBeNull();
    const savedText = await result.cell.textContent();
    expect(savedText.trim()).toBe(LONG_NAME);
  });

  test('TC-006: Full insurance name appears in listing after create', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await searchInsurance(page, LONG_NAME);
    const result = await findRow(page, LONG_NAME);
    expect(result).not.toBeNull();
    const savedText = await result.cell.textContent();
    expect(savedText.trim()).toBe(LONG_NAME);
  });

  test('TC-010: Edit insurance with long name saves without truncation', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await searchInsurance(page, LONG_NAME);
    const result = await findRow(page, LONG_NAME);
    expect(result).not.toBeNull();
    const viewBtn = result.row.locator('button:has-text("View")');
    await viewBtn.waitFor({ state: 'visible', timeout: 10000 });
    await viewBtn.click();
    await page.waitForTimeout(2000);

    await page.locator('button:has-text("Edit")').click();
    await page.waitForSelector('input#name', { timeout: 10000 });
    await page.locator('input#name').fill(UPDATED_NAME);
    await page.locator('button:has-text("Save and Close")').click();
    await page.waitForTimeout(3000);
  });

  test('TC-011: Updated insurance name is persisted correctly after edit', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await searchInsurance(page, UPDATED_NAME);
    const result = await findRow(page, UPDATED_NAME);
    expect(result).not.toBeNull();
    const savedText = await result.cell.textContent();
    expect(savedText.trim()).toBe(UPDATED_NAME);
  });

  test('TC-015: Name above 50-character limit saves correctly', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await page.locator('button:has-text("New Insurance")').click();
    await page.waitForSelector('input#name', { timeout: 10000 });
    await page.locator('input#name').fill(FIFTY_ONE_CHARS);
    await page.locator('button:has-text("Save and Close")').click();
    await page.waitForTimeout(3000);
  });

  test('TC-016: Short insurance name saves without regression', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await page.locator('button:has-text("New Insurance")').click();
    await page.waitForSelector('input#name', { timeout: 10000 });
    await page.locator('input#name').fill(SHORT_NAME);
    await page.locator('button:has-text("Save and Close")').click();
    await page.waitForTimeout(3000);
  });

  test('TC-017: Name with special characters saves correctly', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await page.locator('button:has-text("New Insurance")').click();
    await page.waitForSelector('input#name', { timeout: 10000 });
    await page.locator('input#name').fill(SPECIAL_NAME);
    await page.locator('button:has-text("Save and Close")').click();
    await page.waitForTimeout(3000);
  });
});
