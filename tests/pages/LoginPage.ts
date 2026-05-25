import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  get usernameInput() {
    return this.page.locator('[data-test="username"]');
  }

  get passwordInput() {
    return this.page.locator('[data-test="password"]');
  }

  get loginButton() {
    return this.page.locator('[data-test="login-button"]');
  }

  get errorMessage() {
    return this.page.locator('[data-test="error"]');
  }

  get inventoryContainer() {
    return this.page.locator('[data-test="inventory-container"]');
  }

  async navigate() {
    await this.page.goto(process.env.URL);
  }

  async enterUsername(username: string) {
    await this.usernameInput.fill(username);
  }

  async enterPassword(password: string) {
    await this.passwordInput.fill(password);
  }

  async clickLogin() {
    await this.loginButton.click();
  }

  async isErrorMessageVisible() {
    return await this.errorMessage.isVisible();
  }

  async isInventoryVisible() {
    return await this.inventoryContainer.isVisible();
  }
}
