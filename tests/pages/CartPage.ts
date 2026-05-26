import { Page } from '@playwright/test';

export class CartPage {
  constructor(private page: Page) {}

  get cartItems() {
    return this.page.locator('[data-test="cart-item"]');
  }

  get checkoutButton() {
    return this.page.locator('[data-test="checkout-button"]');
  }

  async navigate() {
    await this.page.goto(`${process.env.BASE_URL ?? ''}/cart`);
  }

  async addItemToCart(itemName: string) {
    const item = this.page.locator(`[data-test="product-${itemName}"]`);
    await item.click();
  }

  async proceedToCheckout() {
    await this.checkoutButton.click();
  }
}
