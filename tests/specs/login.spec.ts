import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

const validUsername = process.env.USERNAME;
const validPassword = process.env.PASSWORD;

test('Successful Application Load', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await expect(page).toBeVisible('[data-test="inventory-container"]');
});

test('Application Load with Invalid URL', async ({ page }) => {
  await page.goto('https://dev.dmerocket.com/invalid-url');
  await expect(page).toHaveURL(/.*404/);
});

test('Application Load with Invalid Credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterCredentials('invalidUser', 'invalidPass');
  const errorMessage = await loginPage.getErrorMessage();
  expect(errorMessage).toContain('Username and password do not match any user in this service.');
});

test('Application Load with No Credentials', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterCredentials('', '');
  const errorMessage = await loginPage.getErrorMessage();
  expect(errorMessage).toContain('Username is required');
});

test('Successful Admin User Login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterCredentials(validUsername, validPassword);
  await expect(page).toBeVisible('[data-test="inventory-container"]');
});

test('Admin User Login with Incorrect Password', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterCredentials(validUsername, 'wrongPassword');
  const errorMessage = await loginPage.getErrorMessage();
  expect(errorMessage).toContain('Username and password do not match any user in this service.');
});

test('Admin User Login with Incorrect Username', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.navigate();
  await loginPage.enterCredentials('wrongUser', validPassword);
  const errorMessage = await loginPage.getErrorMessage();
  expect(errorMessage).toContain('Username and password do not match any user in this service.');
});
