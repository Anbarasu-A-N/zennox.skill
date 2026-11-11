# 10 — Testing Strategy & Playwright

## Contents
1. Test pyramid for cross-platform apps
2. Playwright setup (cross-browser + devices)
3. Writing resilient tests
4. Network, auth, offline
5. Visual regression
6. Accessibility tests
7. Desktop (Electron, Tauri) and native mobile
8. Debugging failures
9. CI

---

## 1. Pyramid

| Layer | Scope | Tools | Runs |
|---|---|---|---|
| Unit | Pure logic in `core` | Vitest/Jest, pytest, `cargo test`, XCTest, JUnit | Every save |
| Component | One UI component with fakes | Vitest + Testing Library, Playwright component testing, Storybook tests | Every commit |
| Integration | Adapter ↔ real dependency (DB, storage, IPC) | Testcontainers, real SQLite, Tauri command tests | Every PR |
| E2E | User flows across real browsers/devices | Playwright; Detox/Maestro for native | Every PR (smoke) + nightly (full) |

Aim for many fast unit tests and a *small* number of high-value E2E flows (sign-up, core task,
payment, offline/sync). Every bug fix gets a regression test that failed before the fix.

## 2. Playwright setup

Start from `assets/playwright.config.ts`. Key ideas:

```ts
projects: [
  { name: "chromium",      use: { ...devices["Desktop Chrome"] } },
  { name: "firefox",       use: { ...devices["Desktop Firefox"] } },
  { name: "webkit",        use: { ...devices["Desktop Safari"] } },
  { name: "mobile-safari", use: { ...devices["iPhone 13"] } },
  { name: "mobile-chrome", use: { ...devices["Pixel 7"] } },
],
webServer: { command: "pnpm --filter web preview", url: "http://localhost:4173", reuseExistingServer: !process.env.CI },
use: { trace: "on-first-retry", screenshot: "only-on-failure" },
```

Install: `npm i -D @playwright/test && npx playwright install --with-deps`. Device names
come from Playwright's registry; list them with
`node -e "console.log(Object.keys(require('playwright').devices))"`.

Mobile emulation covers viewport, touch, user agent and DPR — not real device performance or
native APIs. Use real devices (cloud farms or local) for those.

## 3. Resilient tests

- Locate by role and label: `page.getByRole("button", { name: "Save" })`, `getByLabel`,
  `getByText`. Use `data-testid` only when no accessible name exists (and consider adding one).
- Rely on web-first assertions which auto-wait: `await expect(locator).toBeVisible()`.
  Never `waitForTimeout` in committed tests.
- Each test is independent: own data, own user (fixtures or API seeding), no ordering.
- Page Object or "screen helper" functions only once a flow is reused in 3+ tests.
- Keep E2E tests about behaviour, not implementation details.

```ts
test("creates a note offline and syncs", async ({ page, context }) => {
  await page.goto("/notes");
  await context.setOffline(true);
  await page.getByRole("button", { name: "New note" }).click();
  await page.getByLabel("Title").fill("Offline idea");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Saved on this device")).toBeVisible();
  await context.setOffline(false);
  await expect(page.getByText("Synced")).toBeVisible();
});
```

## 4. Network, auth, offline

- Mock or shape responses: `await page.route("**/api/notes", r => r.fulfill({ json: [] }))`.
  Test error paths: 500s, timeouts (`route.abort("timedout")`), slow responses.
- Auth once per worker with `storageState` saved by a setup project; don't log in via UI in
  every test.
- Offline: `context.setOffline(true)`; service-worker behaviour needs `serviceWorkers: "allow"`.
- Geolocation, permissions, locale, timezone, colour scheme and reduced motion are context
  options — test RTL locales and dark mode for key screens.

## 5. Visual regression

```ts
await expect(page).toHaveScreenshot("dashboard.png", { fullPage: true, maxDiffPixelRatio: 0.01 });
```
- Generate baselines in the same OS/browser as CI (use the official Playwright Docker image)
  or diffs will be noise.
- Mask dynamic regions (`mask: [page.getByTestId("clock")]`), disable animations
  (`animations: "disabled"`), use fixed fonts.
- Snapshot the design system's components rather than every page.

## 6. Accessibility tests

```ts
import AxeBuilder from "@axe-core/playwright";
test("home has no detectable a11y violations", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations).toEqual([]);
});
```
Automated checks catch roughly a third of issues; also test keyboard-only navigation
(`page.keyboard.press("Tab")` and assert focus) and screen reader labels on key flows.

## 7. Desktop and native mobile

- **Electron:** `import { _electron as electron } from "playwright"`; `const app = await
  electron.launch({ args: ["."] }); const win = await app.firstWindow();` then use normal
  locators. You can evaluate in the main process with `app.evaluate`.
- **Tauri:** test the web UI with Playwright against the dev server for most flows; for the
  packaged app use WebDriver via `tauri-driver` (supported on Linux and Windows; check docs for
  macOS status). Unit-test Rust commands with `cargo test`.
- **React Native:** Detox or Maestro for E2E; Jest + React Native Testing Library for components.
- **Flutter:** `flutter test` (widget) and `integration_test`; Patrol for native dialogs.
- **Native:** XCUITest (iOS/macOS), Espresso / Compose UI tests (Android).
- **Capacitor:** web layer with Playwright; native plugins on device with Appium or Maestro.

## 8. Debugging failures

1. Re-run with `--trace on` and open `npx playwright show-trace trace.zip` (DOM snapshots,
   network, console per step).
2. `--headed --debug` or `await page.pause()` locally; `npx playwright codegen <url>` to
   discover locators.
3. Flaky? Look for: missing awaits, assertions on non-auto-waiting values, shared test data,
   animations, time-dependent code (use `page.clock`).
4. Only-in-CI? Compare browser version, viewport, fonts, timezone, CPU speed (use the
   Playwright Docker image locally).

## 9. CI

- Smoke E2E (chromium + one mobile project) on every PR; full matrix nightly and before release.
- Shard large suites: `--shard=1/4`.
- Upload the HTML report and traces as artifacts on failure.
- Retries: 2 in CI, 0 locally. Treat any test that needed a retry as a bug to fix.
