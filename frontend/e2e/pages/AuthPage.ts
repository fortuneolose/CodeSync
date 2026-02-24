import type { Page, Locator } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly identifierInput: Locator;
  readonly passwordInput: Locator;
  readonly submitBtn: Locator;
  readonly errorMsg: Locator;

  constructor(page: Page) {
    this.page = page;
    this.identifierInput = page.locator('input').first();
    this.passwordInput = page.locator('input[type="password"]');
    this.submitBtn = page.locator('button[type="submit"]');
    this.errorMsg = page.locator("p.error, [class*='error']").first();
  }

  async goto() { await this.page.goto("/login"); }

  async login(identifier: string, password: string) {
    await this.identifierInput.fill(identifier);
    await this.passwordInput.fill(password);
    await this.submitBtn.click();
  }
}

export class RegisterPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitBtn: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('input').nth(0);
    this.emailInput = page.locator('input[type="email"]');
    this.passwordInput = page.locator('input[type="password"]');
    this.submitBtn = page.locator('button[type="submit"]');
  }

  async goto() { await this.page.goto("/register"); }

  async register(username: string, email: string, password: string) {
    await this.usernameInput.fill(username);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitBtn.click();
  }
}
