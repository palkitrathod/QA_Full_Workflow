import { test } from '@playwright/test';

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

test('Diagnose DME Rocket Insurance Page Structure', async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 900 });
  await login(page);
  await page.waitForTimeout(3000);

  // Dump all buttons
  console.log('\n=== ALL BUTTONS ===');
  const buttons = page.locator('button, a[role="button"], [class*="btn"], a:has-text("New"), a:has-text("Edit"), a:has-text("Add")');
  const btnCount = await buttons.count();
  for (let i = 0; i < btnCount; i++) {
    const text = await buttons.nth(i).textContent();
    const tag = await buttons.nth(i).evaluate(el => el.tagName);
    const cls = await buttons.nth(i).getAttribute('class');
    const id = await buttons.nth(i).getAttribute('id');
    const href = await buttons.nth(i).getAttribute('href');
    console.log(`  [${i}] <${tag}> text="${text?.trim()}" class="${cls}" id="${id}" href="${href}"`);
  }

  // Dump all input fields
  console.log('\n=== ALL INPUTS ===');
  const inputs = page.locator('input, select, textarea');
  const inpCount = await inputs.count();
  for (let i = 0; i < inpCount; i++) {
    const name = await inputs.nth(i).getAttribute('name');
    const id = await inputs.nth(i).getAttribute('id');
    const ph = await inputs.nth(i).getAttribute('placeholder');
    const label = await inputs.nth(i).getAttribute('aria-label');
    const type = await inputs.nth(i).getAttribute('type');
    const cls = await inputs.nth(i).getAttribute('class');
    console.log(`  [${i}] name="${name}" id="${id}" type="${type}" placeholder="${ph}" aria-label="${label}" class="${cls}"`);
  }

  // Dump table headers if there's a table
  console.log('\n=== TABLE HEADERS ===');
  const tables = page.locator('table, [role="table"], [class*="table"], [class*="grid"]');
  const tblCount = await tables.count();
  for (let t = 0; t < tblCount; t++) {
    const ths = tables.nth(t).locator('th, [role="columnheader"]');
    const thCount = await ths.count();
    console.log(`  Table [${t}]: ${thCount} columns`);
    for (let i = 0; i < thCount; i++) {
      const text = await ths.nth(i).textContent();
      console.log(`    Col ${i}: "${text?.trim()}"`);
    }
  }

  // Dump any visible links
  console.log('\n=== ALL LINKS ===');
  const links = page.locator('a');
  const lnkCount = await links.count();
  for (let i = 0; i < lnkCount; i++) {
    const text = await links.nth(i).textContent();
    const href = await links.nth(i).getAttribute('href');
    const cls = await links.nth(i).getAttribute('class');
    if (text?.trim() || (href && !href.startsWith('#'))) {
      console.log(`  [${i}] text="${text?.trim()}" href="${href}" class="${cls}"`);
    }
  }

  // Dump page heading
  console.log('\n=== PAGE HEADING ===');
  const h1 = page.locator('h1');
  const h1text = await h1.textContent();
  console.log(`  h1: "${h1text?.trim()}"`);

  // Check main content area
  console.log('\n=== MAIN CONTENT CLASSES ===');
  const main = page.locator('main, [role="main"], .container, .content, .page');
  const mc = await main.count();
  for (let i = 0; i < mc; i++) {
    const cls = await main.nth(i).getAttribute('class');
    const tag = await main.nth(i).evaluate(el => el.tagName);
    console.log(`  [${i}] <${tag}> class="${cls}"`);
  }

  console.log('\n=== DONE ===');
});
