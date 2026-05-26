import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

const validUsername = process.env.USERNAME || '';
const validPassword = process.env.PASSWORD || '';

test.describe('Login Page Tests', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigate();
  });

  test('Elements are visible on the login page', async () => {
    await expect(loginPage.usernameInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('Non‑existent element should not be present', async ({ page }) => {
    const nonExistent = page.locator('[data-test="non-existent"]');
    await expect(nonExistent).toHaveCount(0);
  });

  test('Valid username input', async () => {
    await loginPage.enterUsername(validUsername);
    await expect(loginPage.usernameInput).toHaveValue(validUsername);
  });

  test('Empty username shows error', async () => {
    await loginPage.enterUsername('');
    await loginPage.clickLogin();
    await expect(loginPage.isErrorMessageVisible()).toBeTruthy();
  });

  test('Valid password input', async () => {
    await loginPage.enterPassword(validPassword);
    await expect(loginPage.passwordInput).toHaveValue(validPassword);
  });

  test('Empty password shows error', async () => {
    await loginPage.enterPassword('');
    await loginPage.clickLogin();
    await expect(loginPage.isErrorMessageVisible()).toBeTruthy();
  });

  test('Successful login with valid credentials', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    await expect(loginPage.isInventoryVisible()).toBeTruthy();
  });

  test('Invalid username shows error', async () => {
    await loginPage.enterUsername('invalid_user');
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    await expect(loginPage.isErrorMessageVisible()).toBeTruthy();
  });

  test('Invalid password shows error', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword('invalid_password');
    await loginPage.clickLogin();
    await expect(loginPage.isErrorMessageVisible()).toBeTruthy();
  });

  test('Session persists after page refresh', async ({ page }) => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    await page.reload();
    await expect(loginPage.isInventoryVisible()).toBeTruthy();
  });

  test('Locked user cannot log in', async () => {
    await loginPage.enterUsername('locked_user');
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    await expect(loginPage.isErrorMessageVisible()).toBeTruthy();
  });
});
