# 11 — DevOps, Release & Deployment

## Contents
1. Environments and branching
2. CI matrix (build every target on every merge)
3. Versioning and changelogs
4. Signing and notarization per platform
5. Distribution channels
6. Updates (desktop, mobile OTA, web)
7. Backend deploy and infrastructure as code
8. Rollout, rollback, observability
9. Cost hygiene

---

## 1. Environments and branching

- `dev` (local) → `preview` (per-PR deploy) → `staging` (prod-like data shape, fake data) →
  `production`.
- Trunk-based: short-lived branches, merge to `main` behind feature flags. Release by tag.
- Config by environment variables; one build artifact promoted through environments for
  backends and web. Mobile/desktop builds differ per channel only in config, not code.

## 2. CI matrix

Template: `assets/ci-matrix.yml` (GitHub Actions). Shape:

```
lint + typecheck + unit (ubuntu)              ── every push
web build + Playwright smoke                  ── every PR
desktop build: ubuntu / windows / macos       ── every PR to main (unsigned), tags (signed)
android build (ubuntu), ios build (macos)     ── every PR to main (debug), tags (release)
security: secret scan, dep audit, SAST        ── every PR
```

Cache aggressively (pnpm store, Cargo registry + target, Gradle, CocoaPods/SPM, Turborepo
remote cache). iOS and macOS jobs need macOS runners; they're the slowest and most expensive,
so run them on PRs touching native code or on `main` only.

Action hygiene: pin third-party actions to SHAs, `permissions: contents: read` by default,
secrets only in release jobs, OIDC for cloud deploy.

## 3. Versioning and changelogs

- SemVer for apps and packages. Conventional Commits (`feat:`, `fix:`, `perf:`, `BREAKING
  CHANGE:`) → automated changelog (Changesets for monorepos, or release-please).
- Mobile needs two numbers: marketing version (1.4.0) and a monotonically increasing build
  number (CFBundleVersion / versionCode) — derive the build number from CI run number.
- Tag releases `v1.4.0`; the tag triggers signed builds.

## 4. Signing and notarization

| Platform | What | Notes |
|---|---|---|
| Windows | Authenticode code signing (certificate from a CA or a cloud signing service) | Unsigned or newly signed apps trigger SmartScreen warnings until reputation builds; sign installers *and* executables |
| macOS (outside App Store) | Developer ID Application cert + hardened runtime + notarization (`notarytool`) + stapling | Required for Gatekeeper to open the app without warnings; build universal binaries |
| macOS / iOS App Store | Apple Distribution cert + provisioning profiles | fastlane `match` or Xcode Cloud to manage certs in CI |
| Android | Upload key (yours) + Play App Signing (Google holds the app signing key) | Back up the upload key; losing it requires a reset request |
| Linux | GPG-sign repos/packages; Flatpak and Snap stores sign their builds | AppImage can embed a signature |
| Updates | Tauri updater requires its own signing key pair; electron-updater verifies code signature on Windows/macOS | Keep update private keys in CI secrets only |

## 5. Distribution channels

| Platform | Channels |
|---|---|
| Web | CDN static hosting (Cloudflare Pages, Vercel, Netlify, S3+CloudFront) or containers for SSR |
| PWA | Same as web + manifest + service worker; optionally wrap for stores (Trusted Web Activity on Android) |
| Windows | Direct download (MSI/NSIS/MSIX), Microsoft Store, winget manifest |
| macOS | Notarized DMG/ZIP, Mac App Store, Homebrew cask |
| Linux | AppImage, deb/rpm, Flathub, Snap Store |
| iOS | TestFlight → App Store |
| Android | Play internal → closed → open testing → production; optionally F-Droid or direct APK |

Store submissions need privacy labels / data-safety forms, screenshots per device class,
age rating and review notes with a demo account. Plan a review buffer of days for iOS.

## 6. Updates

- **Desktop:** Tauri updater plugin or electron-updater against a static JSON/feed on your
  CDN or GitHub Releases; signed updates only; staged rollout via a percentage field or
  separate channels (beta/stable).
- **Mobile OTA:** Expo EAS Update / similar can ship JS and asset changes without store review,
  within store policy limits (no changing the app's primary purpose; native code still needs a
  store build). Use runtime versions so OTA bundles only reach compatible binaries.
- **Web/PWA:** hashed asset filenames + long cache; HTML short cache; service worker prompts
  "New version available — reload" rather than silently swapping mid-session.
- **Minimum supported version:** API returns a min client version; old clients show an
  upgrade screen instead of breaking.

## 7. Backend deploy and IaC

- Containers (Docker, multi-stage, non-root user, distroless/slim base) to a managed runtime
  (Cloud Run, Fly.io, ECS/Fargate, Azure Container Apps), or serverless/edge functions for
  spiky, stateless work.
- Managed Postgres with automated backups and point-in-time recovery; test a restore.
- Infrastructure as code (Terraform/OpenTofu, Pulumi, or the platform's config files) checked
  into the repo; plan on PR, apply on merge.
- DB migrations run as a separate step before the new app version; write them
  backward-compatible (expand → migrate → contract) so rollback doesn't need a down-migration.

## 8. Rollout, rollback, observability

- Feature flags for risky changes; kill switch for every new integration.
- Staged rollout: internal → 1–5% → 25% → 100%, watching crash-free rate and error budget
  between steps. Store consoles support phased releases for mobile.
- Rollback: web/backend redeploy previous artifact (keep N previous); desktop push previous
  version to the update feed; mobile can't roll back binaries — use flags and OTA.
- Observability before launch:
  - Errors: Sentry (or similar) on every client and server, with release tags and source maps
    (upload source maps privately; don't serve them publicly unless intended).
  - Traces/metrics: OpenTelemetry → your backend of choice.
  - Uptime and synthetic checks on key flows (a Playwright smoke test against prod works).
  - SLOs: e.g. 99.9% successful API requests, p95 latency < 300ms; alert on burn rate, not
    on every blip.

## 9. Cost hygiene

- Preview environments auto-delete when PRs close.
- macOS CI minutes are the priciest: path filters on native jobs.
- Set budget alerts on cloud accounts on day one.
- Cache CDN aggressively; serve images via an image CDN in modern formats (AVIF/WebP).
- Turn off idle staging databases outside working hours where possible.
