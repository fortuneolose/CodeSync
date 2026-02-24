import { test, expect } from "@playwright/test";
import { RegisterPage } from "./pages/AuthPage";

const TS = Date.now();

async function registerAndLogin(page: any, suffix: string) {
  const reg = new RegisterPage(page);
  await reg.goto();
  await reg.register(`sess${TS}${suffix}`, `sess${TS}${suffix}@t.com`, "password123");
  await page.waitForURL("/");
}

test.describe("Sessions", () => {
  test("create session → opens editor", async ({ page }) => {
    await registerAndLogin(page, "a");
    await page.click("button:has-text('New session')");
    await page.fill("input[placeholder*='Untitled'], input[value='Untitled']", "My E2E Session");
    await page.click("button:has-text('Create')");
    await page.waitForURL(/\/editor\//);
    await expect(page.locator("[class*='sessionTitle']")).toContainText("My E2E Session");
  });

  test("session appears on dashboard", async ({ page }) => {
    await registerAndLogin(page, "b");
    await page.click("button:has-text('New session')");
    await page.fill("input[placeholder*='Untitled'], input[value='Untitled']", "ListTest");
    await page.click("button:has-text('Create')");
    await page.goto("/");
    await expect(page.locator("[class*='cardTitle']").first()).toContainText("ListTest");
  });

  test("editor toolbar shows AI and Snapshots buttons", async ({ page }) => {
    await registerAndLogin(page, "c");
    await page.click("button:has-text('New session')");
    await page.fill("input[placeholder*='Untitled'], input[value='Untitled']", "EditorTest");
    await page.click("button:has-text('Create')");
    await page.waitForURL(/\/editor\//);
    await expect(page.locator("button:has-text('AI')")).toBeVisible();
    await expect(page.locator("button:has-text('📸')")).toBeVisible();
  });
});
