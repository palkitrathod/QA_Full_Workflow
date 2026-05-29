import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async navigate() {
    await this.page.goto('https://dev.dmerocket.com/insurance');
  }

  async enterUsername(username: string) {
    await this.page.fill('[data-test="username"]', username);
  }

  async enterPassword(password: string) {
    await this.page.fill('[data-test="password"]', password);
  }

  async clickLogin() {
    await this.page.click('[data-test="login-button"]');
  }

  async getErrorMessage() {
    return this.page.locator('[data-test="error"]').textContent();
  }

  async isAppConfigVisible() {
    return this.page.locator('text=App Config').isVisible();
  }
}
