import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

const validUsername = process.env.USERNAME;
const validPassword = process.env.PASSWORD;

test('Successful Application Load', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await expect(page).toHaveURL('https://dev.dmerocket.com/insurance');
});

test('Application Load with Invalid URL', async ({ page }) => {
  await page.goto('https://dev.dmerocket.com/invalid-url');
  await expect(page).toHaveURL(/.*404/);
});

test('Application Load without Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await expect(loginPage.isAppConfigVisible()).toBe(false);
});

test('Admin User Successful Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterUsername(validUsername);
  await loginPage.enterPassword(validPassword);
  await loginPage.clickLogin();
  await expect(page).toHaveURL('https://dev.dmerocket.com/insurance/dashboard');
});

test('Admin User Login with Invalid Credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterUsername(validUsername);
  await loginPage.enterPassword('wrongpassword');
  await loginPage.clickLogin();
  const errorMessage = await loginPage.getErrorMessage();
  await expect(errorMessage).toContain('Invalid credentials');
});

test('Display App Config Menu After Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterUsername(validUsername);
  await loginPage.enterPassword(validPassword);
  await loginPage.clickLogin();
  await expect(loginPage.isAppConfigVisible()).toBe(true);
});

test('App Config Menu Not Displayed Without Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await expect(loginPage.isAppConfigVisible()).toBe(false);
});

test('Navigate to Insurance Listing Page', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterUsername(validUsername);
  await loginPage.enterPassword(validPassword);
  await loginPage.clickLogin();
  await page.click('text=App Config');
  await expect(page).toHaveURL('https://dev.dmerocket.com/insurance/listing');
});

test('Navigate to Insurance Listing Page Without Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await expect(loginPage.isAppConfigVisible()).toBe(false);
});
