import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TARGET_APP_URL || 'https://dev.dmerocket.com/insurance';
const USERNAME = process.env.USERNAME || 'admin@selectortho.net';
const PASSWORD = process.env.PASSWORD || 'Password123!';

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

test('Debug table structure after search', async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 900 });
  await login(page);
  await page.waitForTimeout(2000);

  // Search for a record
  await page.locator('input[placeholder="Search name"]').fill('BCBS');
  await page.locator('button:has-text("Search Insurances")').click();
  await page.waitForTimeout(3000);

  // Check all table/row-related elements
  console.log('\n=== TABLE ELEMENTS ===');
  for (const sel of ['table', '[role="table"]', '[class*="table"]', '.dataTable']) {
    const count = await page.locator(sel).count();
    console.log(`  ${sel}: ${count} found`);
  }

  // Check for thead/tbody
  console.log('\n=== THEAD/TBODY ===');
  let thCount = await page.locator('thead').count();
  console.log(`  thead: ${thCount}`);
  thCount = await page.locator('tbody').count();
  console.log(`  tbody: ${thCount}`);

  // Try different row selectors
  console.log('\n=== ROW SELECTORS ===');
  for (const sel of ['table tbody tr', 'table tr', 'tr', '[role="row"]', '[class*="row"]']) {
    const count = await page.locator(sel).count();
    console.log(`  ${sel}: ${count}`);
    if (count > 0 && count < 20) {
      for (let i = 0; i < count; i++) {
        const text = await page.locator(sel).nth(i).textContent();
        console.log(`    [${i}]: "${text?.trim().substring(0, 100)}"`);
      }
    }
  }

  // Check the rows in the table
  const table = page.locator('table').first();
  const rows = table.locator('tr');
  const rc = await rows.count();
  console.log(`\n=== TABLE ROWS: ${rc} ===`);
  for (let i = 0; i < rc; i++) {
    const cells = rows.nth(i).locator('td, th');
    const cc = await cells.count();
    const texts: string[] = [];
    for (let j = 0; j < cc; j++) {
      texts.push((await cells.nth(j).textContent())?.trim() || '');
    }
    console.log(`  Row ${i} (${cc} cells): ${texts.join(' | ')}`);
  }
});
