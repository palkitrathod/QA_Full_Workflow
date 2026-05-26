import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

const validUsername = process.env.USERNAME;
const validPassword = process.env.PASSWORD;

test.describe('Login Page Tests', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.navigate();
  });

  test('Verify presence of Login Page elements', async () => {
    expect(await loginPage.usernameInput.isVisible()).toBe(true);
    expect(await loginPage.passwordInput.isVisible()).toBe(true);
    expect(await loginPage.loginButton.isVisible()).toBe(true);
  });

  test('Verify absence of Login Page elements', async () => {
    const nonExistentElement = page.locator('[data-test="non-existent"]');
    expect(await nonExistentElement.count()).toBe(0);
  });

  test('Validate Username field with valid input', async () => {
    await loginPage.enterUsername(validUsername);
    expect(await loginPage.usernameInput.inputValue()).toBe(validUsername);
  });

  test('Validate Username field with empty input', async () => {
    await loginPage.enterUsername('');
    await loginPage.clickLogin();
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
  });

  test('Validate Password field with valid input', async () => {
    await loginPage.enterPassword(validPassword);
    expect(await loginPage.passwordInput.inputValue()).toBe(validPassword);
  });

  test('Validate Password field with empty input', async () => {
    await loginPage.enterPassword('');
    await loginPage.clickLogin();
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
  });

  test('Test Login button functionality with valid credentials', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    expect(await loginPage.isInventoryVisible()).toBe(true);
  });

  test('Verify successful login', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    expect(await loginPage.isInventoryVisible()).toBe(true);
  });

  test('Check error messages for invalid username', async () => {
    await loginPage.enterUsername('invalid_user');
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
  });

  test('Check error messages for invalid password', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword('invalid_password');
    await loginPage.clickLogin();
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
  });

  test('Verify session management after page refresh', async () => {
    await loginPage.enterUsername(validUsername);
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    await page.reload();
    expect(await loginPage.isInventoryVisible()).toBe(true);
  });

  test('Verify access restriction for locked users', async () => {
    await loginPage.enterUsername('locked_user');
    await loginPage.enterPassword(validPassword);
    await loginPage.clickLogin();
    expect(await loginPage.isErrorMessageVisible()).toBe(true);
  });

});
