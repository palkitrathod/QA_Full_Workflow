import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { CartPage } from '../pages/CartPage';
import { CheckoutPage } from '../pages/CheckoutPage';


test.describe('E2E default flow', () => {
  let pageObj: any;
  test.beforeEach(async ({ page }) => {
    pageObj = new LoginPage(page);
    await pageObj.navigate();
  });


  test('Cart step', async () => {
    pageObj = new CartPage(pageObj.page);
    await pageObj.navigate();
    // add assertions specific to this page if needed
  });


  test('Checkout step', async () => {
    pageObj = new CheckoutPage(pageObj.page);
    await pageObj.navigate();
    // add assertions specific to this page if needed
  });


});