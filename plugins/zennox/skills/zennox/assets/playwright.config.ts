// Zennox Playwright template. Adjust webServer and baseURL to your app.
import { defineConfig, devices } from "@playwright/test";

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 2 : undefined,
  reporter: isCI ? [["html", { open: "never" }], ["github"]] : "list",
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:4173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01, animations: "disabled" } },
  projects: [
    { name: "setup", testMatch: /.*\.setup\.ts/ },                    // logs in once, saves storageState
    { name: "chromium", use: { ...devices["Desktop Chrome"], storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
    { name: "firefox", use: { ...devices["Desktop Firefox"], storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
    { name: "webkit", use: { ...devices["Desktop Safari"], storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
    { name: "mobile-safari", use: { ...devices["iPhone 13"], storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
    { name: "mobile-chrome", use: { ...devices["Pixel 7"], storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
    { name: "dark-reduced-motion", use: { ...devices["Desktop Chrome"], colorScheme: "dark", reducedMotion: "reduce", storageState: "e2e/.auth/user.json" }, dependencies: ["setup"] },
  ],
  webServer: {
    command: "pnpm --filter web build && pnpm --filter web preview --port 4173",
    url: "http://localhost:4173",
    reuseExistingServer: !isCI,
    timeout: 120_000,
  },
});
