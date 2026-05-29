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

test('Diagnose New Insurance Form', async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 900 });
  await login(page);
  await page.waitForTimeout(2000);

  // Click New Insurance
  await page.locator('button:has-text("New Insurance")').click();
  await page.waitForTimeout(2000);

  console.log('\n=== NEW INSURANCE FORM: ALL INPUTS ===');
  const inputs = page.locator('input, select, textarea, label');
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const tag = await inputs.nth(i).evaluate(el => el.tagName);
    const text = await inputs.nth(i).textContent();
    const name = await inputs.nth(i).getAttribute('name');
    const id = await inputs.nth(i).getAttribute('id');
    const ph = await inputs.nth(i).getAttribute('placeholder');
    const type = await inputs.nth(i).getAttribute('type');
    const aria = await inputs.nth(i).getAttribute('aria-label');
    const forAttr = await inputs.nth(i).getAttribute('for');
    const cls = await inputs.nth(i).getAttribute('class');
    if (tag === 'LABEL' || name || id || ph || type === 'text') {
      console.log(`  [${i}] <${tag}> text="${text?.trim()}" name="${name}" id="${id}" placeholder="${ph}" type="${type}" for="${forAttr}" aria="${aria}"`);
    }
  }

  console.log('\n=== ALL BUTTONS on FORM ===');
  const btns = page.locator('button');
  const bcnt = await btns.count();
  for (let i = 0; i < bcnt; i++) {
    const txt = await btns.nth(i).textContent();
    const cls = await btns.nth(i).getAttribute('class');
    if (txt?.trim()) {
      console.log(`  [${i}] "${txt?.trim()}" class="${cls}"`);
    }
  }

  console.log('\n=== HEADING on FORM ===');
  const h1 = page.locator('h1');
  console.log(`  h1: "${(await h1.textContent())?.trim()}"`);
  const h2 = page.locator('h2');
  const h2count = await h2.count();
  for (let i = 0; i < h2count; i++) {
    console.log(`  h2[${i}]: "${(await h2.nth(i).textContent())?.trim()}"`);
  }
});

test('Diagnose View/Edit Detail Page', async ({ page }) => {
  test.setTimeout(120000);
  await page.setViewportSize({ width: 1280, height: 900 });
  await login(page);
  await page.waitForTimeout(2000);

  // Click the first "View" button
  const viewBtn = page.locator('button:has-text("View")').first();
  await viewBtn.waitFor({ state: 'visible', timeout: 10000 });
  await viewBtn.click();
  await page.waitForTimeout(3000);

  console.log('\n=== VIEW DETAIL PAGE: HEADINGS ===');
  const h1 = page.locator('h1');
  console.log(`  h1: "${(await h1.textContent())?.trim()}"`);
  const h2 = page.locator('h2');
  const h2count = await h2.count();
  for (let i = 0; i < h2count; i++) {
    console.log(`  h2[${i}]: "${(await h2.nth(i).textContent())?.trim()}"`);
  }

  console.log('\n=== VIEW DETAIL: ALL INPUTS ===');
  const inputs = page.locator('input, select, textarea, label');
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const tag = await inputs.nth(i).evaluate(el => el.tagName);
    const text = await inputs.nth(i).textContent();
    const name = await inputs.nth(i).getAttribute('name');
    const id = await inputs.nth(i).getAttribute('id');
    const ph = await inputs.nth(i).getAttribute('placeholder');
    const type = await inputs.nth(i).getAttribute('type');
    const forAttr = await inputs.nth(i).getAttribute('for');
    if (tag === 'LABEL' || name || id || ph) {
      console.log(`  [${i}] <${tag}> text="${text?.trim()}" name="${name}" id="${id}" placeholder="${ph}" type="${type}" for="${forAttr}"`);
    }
  }

  console.log('\n=== VIEW DETAIL: ALL BUTTONS ===');
  const btns = page.locator('button');
  const bcnt = await btns.count();
  for (let i = 0; i < bcnt; i++) {
    const txt = await btns.nth(i).textContent();
    const cls = await btns.nth(i).getAttribute('class');
    if (txt?.trim()) {
      console.log(`  [${i}] "${txt?.trim()}" class="${cls}"`);
    }
  }
});
