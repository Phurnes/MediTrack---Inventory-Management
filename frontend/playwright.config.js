
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",

  // Run tests in parallel when possible.
  fullyParallel: true,

  // CI should fail if test.only is accidentally committed.
  forbidOnly: !!process.env.CI,

  // Retry failed tests on GitHub Actions.
  retries: process.env.CI ? 2 : 0,

  // Keep output readable in the terminal.
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Playwright starts the React development server automatically.
  webServer: {
    command: "npm run dev -- --host 127.0.0.1",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
