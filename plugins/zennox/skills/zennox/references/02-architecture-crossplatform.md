# 02 — Cross-Platform Architecture, OS Dependencies & System Design

## Contents
1. Stack decision matrix
2. Decision questions (ask in this order)
3. Monorepo layout and code reuse
4. Platform adapter pattern
5. OS-specific dependencies (how to declare them per ecosystem)
6. Per-OS toolchain and build prerequisites
7. System design checklist
8. Anti-patterns

Framework versions move fast. Before pinning a version or claiming a feature, check the
project's current docs or changelog (web search if available).

---

## 1. Stack decision matrix

| Stack | Targets | Share with web | Binary / install size | Native access | Pick when | Avoid when |
|---|---|---|---|---|---|---|
| Responsive web + PWA | All browsers; installable on Android, desktop, iOS (Home Screen) | 100% | None (cached) | Web APIs only; iOS PWA limits on background work | Content, tools, internal apps, MVPs | Needs deep background tasks, Bluetooth on iOS, store-only distribution |
| Tauri 2 | Win, macOS, Linux, iOS, Android | Web UI 100%, Rust backend | Small (uses system webview) | Rust + plugins, capability-scoped | Desktop app from a web app; security-sensitive desktop | Need identical rendering across OSes (webviews differ) |
| Electron | Win, macOS, Linux | Web UI 100%, Node main process | Large (bundles Chromium) | Full Node.js | Need Chromium everywhere, heavy Node ecosystem | Size- or memory-sensitive users |
| Capacitor | iOS, Android (+ web) | ~100% of web code | Medium | Native plugins | Wrap an existing web app for stores | Complex native-feeling UI, heavy animation |
| React Native (Expo) | iOS, Android, (web via RN Web), Win/macOS via community | Logic and some UI | Medium | Native modules, Expo modules | JS/TS team, native UI feel, OTA updates | Pixel-identical custom rendering needs |
| Flutter | iOS, Android, web, Win, macOS, Linux | Dart only (not your React web) | Medium | Platform channels / FFI | One custom-designed UI everywhere | You need SEO web or to reuse an existing web codebase |
| Kotlin Multiplatform (+ Compose MP) | Android, iOS, desktop, web (wasm) | Logic; UI optional | Small–medium | expect/actual, full native | Native UI per platform with shared logic | Team has no Kotlin |
| Native (Swift / Kotlin) | One platform each | None | Smallest | Total | Platform showcase, top performance | Small team, many platforms |

## 2. Decision questions (in this order)

1. **Is a store listing required?** No → start with web/PWA. Yes → continue.
2. **Is there already a web codebase?** Yes → Capacitor (mobile) / Tauri or Electron (desktop).
3. **Does the UI need to feel native per platform, or look identical everywhere?** Native
   feel → React Native or KMP/native. Identical → Flutter or web-based.
4. **What does the team know?** Prefer the stack the team can debug at 2am.
5. **Hard native needs?** (background location, BLE, widgets, CarPlay, health data) → check
   the stack's plugin support *before* committing; write the ADR with the evidence.
6. **Size/memory constraints?** Prefer Tauri over Electron; native over everything.

Record the result in `docs/adr/0001-stack.md`.

## 3. Monorepo layout and code reuse

```
repo/
├── packages/
│   ├── core/          # types, schemas (zod/valibot), business rules, state machines, API client
│   ├── ui/            # design tokens + shared components (web/RN as applicable)
│   ├── adapters/      # interfaces + per-platform implementations
│   └── config/        # eslint, tsconfig, prettier shared presets
├── apps/
│   ├── web/           # Next.js / Vite / SvelteKit / Astro
│   ├── desktop/       # Tauri (src-tauri/) or Electron (main/, preload/)
│   └── mobile/        # Expo / Capacitor / Flutter / native shells
├── e2e/               # Playwright specs shared across web + desktop
├── docs/adr/
├── DESIGN.md
└── SPEC.md
```

Reuse rules:
- `core` imports nothing platform-specific (no `window`, `fs`, `react-native`, `@tauri-apps`).
  `project_graph.py` reports violations as **layer violations**.
- Validation schemas live once in `core` and are used both client- and server-side.
- Design tokens are generated from DESIGN.md into CSS variables, a TS object, and (if needed)
  Swift/Kotlin/Dart constants. One source, many outputs.
- Workspace tool: pnpm workspaces (+ Turborepo or Nx for caching) for JS; Cargo workspaces
  for Rust; Gradle multi-module for KMP; Melos or pub workspaces for Flutter.

## 4. Platform adapter pattern

Define the capability once, implement per platform, inject at the app edge.

```ts
// packages/adapters/src/storage.ts
export interface KeyValueStore {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
}

// packages/adapters/src/storage.web.ts      -> IndexedDB (idb-keyval) or localStorage for tiny data
// packages/adapters/src/storage.tauri.ts    -> @tauri-apps/plugin-store
// packages/adapters/src/storage.native.ts   -> expo-secure-store / MMKV
// apps/*/src/platform.ts picks one and passes it to core
```

Typical adapters: storage, secure storage (keychain/keystore/DPAPI), notifications, file
picker/FS, clipboard, share sheet, deep links, biometrics, background tasks, haptics,
camera, geolocation, in-app purchase, updater. Each adapter gets a fake for tests.

Secrets/tokens go to the **secure** adapter only: Keychain (Apple), Keystore (Android),
Credential Manager / DPAPI (Windows), Secret Service / libsecret (Linux). Never to
localStorage or plain files.

## 5. OS-specific dependencies — how to declare them

Declare platform-conditional dependencies with the ecosystem's own mechanism instead of
runtime `if (os === ...)` imports that drag every platform's code into every build.

| Ecosystem | Mechanism | Example |
|---|---|---|
| npm | `os` / `cpu` fields in a package + `optionalDependencies` (prebuilt-binary pattern) | Publish `mylib-win32-x64`, `mylib-darwin-arm64`… each with `"os": ["win32"]`; main package lists them as optional deps |
| npm (code) | `exports` conditions | `"exports": {".": {"react-native": "./native.js", "browser": "./web.js", "node": "./node.js"}}` |
| React Native | File extensions | `Button.ios.tsx`, `Button.android.tsx`, `Button.native.tsx`, `Button.web.tsx` |
| Python | PEP 508 markers | `pywin32; sys_platform == "win32"`, `uvloop; sys_platform != "win32"` |
| Rust / Tauri | Target tables + cfg | `[target.'cfg(target_os = "macos")'.dependencies]` and `#[cfg(windows)]` |
| Dart / Flutter | Conditional imports | `import 'stub.dart' if (dart.library.io) 'io.dart' if (dart.library.js_interop) 'web.dart';` |
| Kotlin MP | `expect` / `actual` + source sets | `commonMain`, `androidMain`, `iosMain`, `desktopMain` |
| Swift | Compiler conditions | `#if os(iOS)`, `#if canImport(UIKit)`, `#if targetEnvironment(macCatalyst)` |
| Go | Build tags / filename suffix | `file_windows.go`, `//go:build darwin` |
| .NET | TFMs + conditional ItemGroups | `<ItemGroup Condition="$(TargetFramework.Contains('android'))">` |

Native Node modules: prefer packages that ship N-API prebuilds; otherwise every Windows dev
needs MSVC Build Tools and every Linux CI image needs a compiler. Rebuild Electron natives
against Electron's ABI (`@electron/rebuild`).

Cross-OS hygiene in code: `path.join`/`pathlib` not string concatenation; never assume
case-sensitive (Linux) or case-insensitive (Windows/macOS default) filesystems; normalise line
endings with `.gitattributes` (`* text=auto eol=lf`); use the OS's app-data dirs
(`app.getPath('userData')`, Tauri `appDataDir`, `platformdirs` in Python) not `~/.myapp`.

## 6. Per-OS toolchain and build prerequisites

Run `scripts/detect_env.py` to see which of these exist on the current machine.

| Target | Build host | Prerequisites | Gotchas |
|---|---|---|---|
| Web | Any | Node LTS | Test Safari/WebKit; it's the most common source of "works on my machine" |
| Windows | Windows (or CI windows runner) | MSVC Build Tools; WebView2 runtime (Tauri; preinstalled on Win 11) | Authenticode signing for SmartScreen; long-path setting; antivirus false positives on unsigned builds |
| macOS | macOS only | Xcode / Command Line Tools | Notarization required for distribution outside the App Store; universal (arm64 + x86_64) builds; hardened runtime + entitlements |
| Linux | Linux | Tauri: webkit2gtk-4.1, libssl, librsvg, appindicator dev packages; Electron: none extra for build | Package formats (AppImage, deb, rpm, Flatpak, Snap); build on the oldest glibc you support |
| iOS | macOS only | Xcode, Apple Developer account, signing identity + provisioning profile | Simulator ≠ device (push, background, camera); App Review guidelines |
| Android | Any | JDK 17 (check current AGP requirement), Android SDK, NDK if native code | minSdk vs feature use; Play target-API deadlines; 64-bit requirement |

If the machine can't build a target (e.g. iOS from Linux), say so and route that target to CI
(`assets/ci-matrix.yml`).

## 7. System design checklist

Work through this for any app with a backend. Keep answers in SPEC.md or ADRs.

- **Clients & trust boundaries:** every client is untrusted. Authz is server-side.
- **API style:** REST + OpenAPI for public/multi-client; tRPC or GraphQL when one team owns
  client and server and the schema changes often. Version from day one (`/v1`).
- **Auth:** OIDC Authorization Code + PKCE for native and SPA; passkeys (WebAuthn) where
  possible; short-lived access tokens, rotating refresh tokens in secure storage.
- **Data:** Postgres by default server-side; SQLite on device for offline. Migrations are
  versioned and reversible (`13-extra-capabilities.md`).
- **Sync model:** online-only → simple. Offline-capable → choose last-write-wins per field,
  server-authoritative merge, or CRDTs (Yjs/Automerge) for collaborative text
  (`12-networking-performance.md`).
- **Realtime:** SSE for server→client streams; WebSockets for bidirectional; push
  notifications (APNs/FCM/Web Push) when the app is closed.
- **Files/media:** object storage + signed URLs + CDN; never stream big files through the app
  server.
- **Async work:** queue (SQS, Cloud Tasks, Redis streams, or Postgres-based) for email,
  image processing, webhooks. Idempotency keys on every retried operation.
- **Scaling path:** stateless app servers behind a load balancer; cache (CDN → HTTP cache →
  Redis) before sharding; read replicas before rewrites.
- **Observability:** structured logs, error tracking, traces across client → API → DB,
  uptime checks. Decide this before launch, not after the first outage.
- **Cost:** estimate monthly cost at 1×, 10× and 100× expected users; note the line item that
  grows fastest.

## 8. Anti-patterns

- Choosing a framework for its demo, not for the hardest native requirement in the spec.
- `if (Platform.OS === 'ios')` scattered through business logic instead of adapters.
- Separate codebases per platform "for now" with no shared core.
- Storing tokens in localStorage / AsyncStorage / plain files.
- Building iOS locally on a borrowed Mac with no CI equivalent.
- Shipping Electron with `nodeIntegration: true` or without `contextIsolation`.
