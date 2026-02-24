import { test, expect } from "@playwright/test";
import { LoginPage, RegisterPage } from "./pages/AuthPage";

const UNIQUE = Date.now();
const USER = { username: `e2e${UNIQUE}`, email: `e2e${UNIQUE}@test.com`, password: "password123" };

test.describe("Authentication", () => {
  test("register → redirect to dashboard", async ({ page }) => {
    const reg = new RegisterPage(page);
    await reg.goto();
    await reg.register(USER.username, USER.email, USER.password);
    await page.waitForURL("/");
    await expect(page.locator("h1, [class*='heading']")).toContainText("sessions");
  });

  test("login with username → redirect to dashboard", async ({ page }) => {
    // Register first
    const reg = new RegisterPage(page);
    await reg.goto();
    await reg.register(`l${UNIQUE}`, `l${UNIQUE}@t.com`, USER.password);
    // Logout
    await page.click("button:has-text('Sign out')");
    // Login
    const login = new LoginPage(page);
    await login.goto();
    await login.login(`l${UNIQUE}`, USER.password);
    await page.waitForURL("/");
    await expect(page).toHaveURL("/");
  });

  test("wrong password shows error", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.login("nobody@nowhere.com", "wrongpass");
    await expect(page.locator("[class*='error']")).toBeVisible();
  });

  test("unauthenticated / redirects to /login", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL(/\/login/);
  });
});
