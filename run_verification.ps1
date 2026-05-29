$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runFolder = "run_insurance_verification_$timestamp"
$runPath = Join-Path $PWD $runFolder

Write-Host "=== Creating output folder: $runFolder ==="
New-Item -ItemType Directory -Path $runPath -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "tmp") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "allure-report") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runPath "allure-results") -Force | Out-Null

# Clean previous run artifacts
Remove-Item -Recurse -Force ".tmp" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "generated_test_cases.md" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "playwright-results.json" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "tests" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "allure-report" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "allure-results" -ErrorAction SilentlyContinue

# Set env vars for DME Rocket
$env:TARGET_APP_URL = "https://dev.dmerocket.com/insurance"
$env:USERNAME = "admin@selectortho.net"
$env:PASSWORD = "Password123!"
$env:LOCAL_BUGS_FILE = Join-Path $runPath "bugs.md"

# Remove existing bugs file if it exists
Remove-Item -Force $env:LOCAL_BUGS_FILE -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================"
Write-Host "STEP 1: Run pipeline with local bug filing"
Write-Host "============================================"
Write-Host "Target URL: $env:TARGET_APP_URL"
Write-Host "Local bugs: $env:LOCAL_BUGS_FILE"
Write-Host ""

python main.py --document "BUG_Retest_Insurance_Name_Truncation.md" --regression 2>&1

# Recreate tests/specs dir for verification
New-Item -ItemType Directory -Path "tests/specs" -Force | Out-Null
New-Item -ItemType Directory -Path "tests/pages" -Force | Out-Null

# Re-create the verification spec file (it was deleted by pipeline cleanup)
$verificationSpec = @'
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.TARGET_APP_URL || 'https://dev.dmerocket.com/insurance';
const USERNAME = process.env.USERNAME || 'admin@selectortho.net';
const PASSWORD = process.env.PASSWORD || 'Password123!';

const LONG_NAME = 'BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)';
const UPDATED_NAME = 'BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) UPDATED';
const SHORT_NAME = 'TEST INSURANCE SHORT';
const SPECIAL_NAME = 'BCBS TPA (MID-LEVEL) & ASSOCIATES \u2014 SOUTHWEST';
const FIFTY_CHARS = 'A'.repeat(50);
const FIFTY_ONE_CHARS = 'A'.repeat(51);

test.describe('Insurance Name Truncation Fix \u2014 Acceptance Criteria Verification', () => {

  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
  });

  async function login(page) {
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 60000 });
    const url = page.url();
    if (url.includes('auth0.com') || url.includes('login')) {
      await page.waitForSelector('input[name="username"], input[type="email"], input#username', { timeout: 20000 });
      const userInput = page.locator('input[name="username"], input[type="email"], input#username').first();
      await userInput.fill(USERNAME);
      const continueBtn = page.locator('button:has-text("Continue"), button:has-text("Next"), button[type="submit"]').first();
      if (await continueBtn.isVisible({ timeout: 3000 })) {
        await continueBtn.click();
        await page.waitForTimeout(1500);
      }
      const passInput = page.locator('input[name="password"], input[type="password"], input#password').first();
      await passInput.fill(PASSWORD);
      const loginBtn = page.locator('button:has-text("Login"), button:has-text("Sign In"), button[type="submit"]').first();
      await loginBtn.click();
    }
    await page.waitForLoadState('networkidle', { timeout: 60000 });
  }

  async function navigateToInsurance(page) {
    const appConfig = page.locator('text=App Config').first();
    if (await appConfig.isVisible({ timeout: 8000 })) {
      await appConfig.click();
      await page.waitForTimeout(1000);
    }
    const insuranceLink = page.locator('text=Insurance').first();
    if (await insuranceLink.isVisible({ timeout: 8000 })) {
      await insuranceLink.click();
    }
    await page.waitForLoadState('networkidle', { timeout: 30000 });
  }

  function getLastRecordName(page) {
    return page.locator('table tr:nth-child(1) td:nth-child(2), .table tr:nth-child(1) td:nth-child(2), [class*="row"]:nth-child(1) [class*="name"]').first();
  }

  async function clickAddNew(page) {
    const addBtn = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create"), [aria-label="Add"], a:has-text("Add")').first();
    if (await addBtn.isVisible({ timeout: 5000 })) {
      await addBtn.click();
      await page.waitForLoadState('networkidle', { timeout: 30000 });
    }
  }

  async function fillAndSave(page, name) {
    const nameField = page.locator('input[name="name"], input#name, [label="Name"] input, input[placeholder*="name" i]').first();
    await nameField.waitFor({ state: 'visible', timeout: 15000 });
    await nameField.fill(name);
    const saveBtn = page.locator('button:has-text("Save"), button:has-text("Submit"), button[type="submit"]').first();
    await saveBtn.click();
    await page.waitForLoadState('networkidle', { timeout: 30000 });
  }

  test('TC-004: Create insurance with long name saves without truncation', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    await clickAddNew(page);
    await fillAndSave(page, LONG_NAME);
    const error = page.locator('.error, .alert-danger, [role="alert"]');
    expect(await error.count()).toBe(0);
  });

  test('TC-005: Saved insurance name is exactly the full name on create', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    const nameCell = getLastRecordName(page);
    await expect(nameCell).toContainText(LONG_NAME, { timeout: 15000 });
    const savedText = await nameCell.textContent();
    expect(savedText.trim()).toBe(LONG_NAME);
    expect(savedText.trim()).not.toBe('BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEV)');
  });

  test('TC-006: Full insurance name appears in listing after create', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    const nameCell = page.locator('text=${LONG_NAME}').first();
    await expect(nameCell).toBeVisible({ timeout: 15000 });
  });

  test('TC-007: Name is not truncated/hidden in listing UI', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    const nameCell = page.locator('text=${LONG_NAME}').first();
    await expect(nameCell).toBeVisible({ timeout: 15000 });
    const text = await nameCell.textContent();
    expect(text.trim()).toBe(LONG_NAME);
  });

  test('TC-010: Edit insurance with long name saves without truncation', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    const editBtn = page.locator('button:has-text("Edit"), [aria-label="Edit"], a:has-text("Edit")').first();
    await editBtn.waitFor({ state: 'visible', timeout: 15000 });
    await editBtn.click();
    await page.waitForLoadState('networkidle', { timeout: 30000 });
    await fillAndSave(page, UPDATED_NAME);
    const error = page.locator('.error, .alert-danger, [role="alert"]');
    expect(await error.count()).toBe(0);
  });

  test('TC-011: Updated insurance name is persisted correctly after edit', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    const nameCell = getLastRecordName(page);
    await expect(nameCell).toContainText(UPDATED_NAME, { timeout: 15000 });
    const text = await nameCell.textContent();
    expect(text.trim()).toBe(UPDATED_NAME);
  });

  test('TC-015: Name above 50-character limit saves correctly', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    await clickAddNew(page);
    await fillAndSave(page, FIFTY_ONE_CHARS);
    const error = page.locator('.error, .alert-danger, [role="alert"]');
    expect(await error.count()).toBe(0);
  });

  test('TC-016: Short insurance name saves without regression', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    await clickAddNew(page);
    await fillAndSave(page, SHORT_NAME);
    const error = page.locator('.error, .alert-danger, [role="alert"]');
    expect(await error.count()).toBe(0);
  });

  test('TC-017: Name with special characters saves correctly', async ({ page }) => {
    test.setTimeout(180000);
    await login(page);
    await navigateToInsurance(page);
    await clickAddNew(page);
    await fillAndSave(page, SPECIAL_NAME);
    const error = page.locator('.error, .alert-danger, [role="alert"]');
    expect(await error.count()).toBe(0);
  });

});
'@

Set-Content -Path "tests/specs/insurance_name_verification.spec.ts" -Value $verificationSpec -Encoding UTF8
Write-Host "[FILE] Re-created verification spec."

Write-Host ""
Write-Host "============================================"
Write-Host "STEP 2: Run Acceptance Criteria Verification"
Write-Host "============================================"

npx playwright test tests/specs/insurance_name_verification.spec.ts --reporter=json,line 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Some verification tests failed (expected for unreachable site)"
}

Write-Host ""
Write-Host "============================================"
Write-Host "STEP 3: Copy outputs to run folder"
Write-Host "============================================"

# Copy all outputs
if (Test-Path ".tmp/context.json") { Copy-Item ".tmp/context.json" (Join-Path $runPath "tmp/context.json") -Force }
if (Test-Path "generated_test_cases.md") { Copy-Item "generated_test_cases.md" (Join-Path $runPath "generated_test_cases.md") -Force }
if (Test-Path "playwright-results.json") { Copy-Item "playwright-results.json" (Join-Path $runPath "playwright-results.json") -Force }
if (Test-Path "deep_evaluation_report.html") { Copy-Item "deep_evaluation_report.html" (Join-Path $runPath "deep_evaluation_report.html") -Force }
if (Test-Path "allure-report") { Copy-Item -Recurse "allure-report/*" (Join-Path $runPath "allure-report") -Force }
if (Test-Path "allure-results") { Copy-Item -Recurse "allure-results/*" (Join-Path $runPath "allure-results") -Force }

Write-Host ""
Write-Host "============================================"
Write-Host "DONE - All outputs saved to:"
Write-Host "  $runPath"
Write-Host "============================================"
