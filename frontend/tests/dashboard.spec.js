
import { test, expect } from "@playwright/test";

test("MediTrack dashboard opens successfully", async ({ page }) => {
  await page.goto("/");

  // Check that the page loaded.
  await expect(page.locator("body")).toBeVisible();

  // Check for the application name somewhere on the page.
  await expect(page.locator("body")).toContainText(/MediTrack/i);

  // Save a screenshot for reference.
  await page.screenshot({
    path: "test-results/meditrack-dashboard.png",
    fullPage: true,
  });
});
