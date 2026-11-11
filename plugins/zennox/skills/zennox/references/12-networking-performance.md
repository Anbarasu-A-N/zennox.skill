# 12 — Networking, Offline, Performance & Debugging

## Contents
1. Network layer design
2. Caching layers
3. Offline-first and sync
4. Realtime
5. Performance budgets
6. Web performance techniques
7. Mobile and desktop performance
8. Debugging playbook

---

## 1. Network layer design

- One API client in `core` (typed from OpenAPI/tRPC/GraphQL schema). Every call gets:
  timeout (default 10s; tune per endpoint), `AbortController` cancellation, retry with
  exponential backoff + jitter **only for idempotent requests** (GET, or writes with an
  idempotency key), and typed error results.
- Respect `Retry-After` on 429/503.
- Compress responses (Brotli/gzip); paginate with cursors, not offsets, for growing lists.
- HTTP/2 or HTTP/3 at the edge; keep payloads small (select fields, avoid over-fetching).
- Detect connectivity via failed requests, not only `navigator.onLine` (it lies on captive
  portals).
- Mobile: batch background requests; avoid waking the radio for tiny frequent calls.

## 2. Caching layers

| Layer | Tool | Rule |
|---|---|---|
| Browser HTTP cache | `Cache-Control` | Hashed assets: `public, max-age=31536000, immutable`; HTML: `no-cache` (revalidate) |
| CDN | Edge cache | Cache public GETs; `stale-while-revalidate`; purge on deploy |
| Service worker | Workbox or hand-written | App shell cache-first; API network-first with fallback; never cache auth'd responses in shared caches |
| Client data cache | TanStack Query / SWR / Apollo | Stale times per resource; invalidate on mutation |
| Server cache | Redis / in-memory | Cache expensive reads; key by everything that changes the answer (user, locale, version) |

Use ETags/`If-None-Match` for cheap revalidation of medium-size resources.

## 3. Offline-first and sync

Decide the model in an ADR:

| Model | How | Fits |
|---|---|---|
| Online-only + optimistic UI | Mutate UI immediately, roll back on failure | Most CRUD apps |
| Queue & replay | Store mutations in IndexedDB/SQLite outbox; replay on reconnect with idempotency keys | Forms, field apps, notes |
| Last-write-wins per field | Track `updatedAt` per field; server merges | Simple personal data |
| Server-authoritative merge | Client sends ops; server resolves and returns canonical state | Shared business data |
| CRDT | Yjs / Automerge documents synced via a provider | Collaborative text/whiteboards |
| Sync engine | Local-first DBs (e.g. PowerSync, ElectricSQL, Replicache-style) | Data-heavy offline apps |

Always: show sync status ("Saved on this device" / "Synced"), handle conflicts visibly when
they can lose user work, and test offline → edit → reconnect in E2E.

## 4. Realtime

- **SSE** for server→client streams (notifications, LLM token streaming); auto-reconnects,
  works over HTTP/2, simple to scale.
- **WebSockets** for bidirectional low-latency (chat, multiplayer, collaboration). Heartbeats,
  reconnect with backoff, resubscribe and fetch missed events by cursor after reconnect.
- **Push** (APNs, FCM, Web Push) when the app isn't open; payload minimal, fetch details on open.
- Scale with a pub/sub backbone (Redis, NATS, managed services); sticky sessions or a
  shared state store for socket servers.

## 5. Performance budgets (defaults — tune per product)

| Metric | Target |
|---|---|
| LCP | ≤ 2.5s (p75, mobile) |
| INP | ≤ 200ms |
| CLS | ≤ 0.1 |
| Initial JS (compressed) | ≤ 170KB for app routes; far less for content pages |
| Desktop cold start | ≤ 1.5s to interactive window |
| Mobile cold start | ≤ 2s on a mid-range Android device |
| API p95 | ≤ 300ms for interactive endpoints |
| Memory (desktop idle) | Tauri apps typically far below Electron; set a number and track it |

Measure in CI (Lighthouse CI, bundle-size checks like size-limit) and in the field (web-vitals
→ analytics, crash/perf tools on mobile).

## 6. Web performance techniques

- Ship less JS: server rendering / static generation for content; islands or partial
  hydration; route-level code splitting; remove unused deps (`03-minimal-code.md`).
- Images: correct `width`/`height` or `aspect-ratio`, `srcset`/`sizes`, AVIF/WebP,
  `loading="lazy"` below the fold, `fetchpriority="high"` for the LCP image.
- Fonts: self-host, subset, `font-display: swap`, preload the one or two critical files,
  size-adjust fallbacks to prevent layout shift.
- Avoid long tasks: break work with `scheduler.yield()`/`setTimeout`, move heavy work to Web
  Workers, virtualise long lists (TanStack Virtual).
- React: memoise only after profiling; colocate state; avoid context for high-frequency values.
- Preconnect to critical origins; prefetch likely next routes on hover/visibility.

## 7. Mobile and desktop performance

- RN: Hermes engine; FlashList for long lists; Reanimated for animations on the UI thread;
  avoid large JSON over the bridge; use the New Architecture where libraries support it.
- Flutter: `const` widgets, avoid rebuilding large subtrees, `ListView.builder`, profile in
  profile mode (not debug).
- Native: Instruments (iOS/macOS), Android Studio profiler, Baseline Profiles on Android.
- Electron: keep the main process light (no sync IPC, no heavy work); lazy-load windows;
  measure with `--inspect` and Chrome DevTools performance panel.
- Tauri: heavy work in Rust commands (async), stream large data via events or channels rather
  than giant JSON payloads.

## 8. Debugging playbook

1. **Reproduce** with the smallest steps; note platform, OS version, build, network.
2. **Write the failing test** (Prove-It) — unit if possible, E2E if it's a flow.
3. **Bisect**: `git bisect` with the test as the oracle; for regressions this is fastest.
4. **Observe, don't guess**: logs with correlation IDs, Playwright trace, browser DevTools
   (Network, Performance, Memory), `chrome://inspect` for Android WebViews, Safari Web
   Inspector for iOS WebViews, Flipper/React Native DevTools, Xcode/Android Studio debuggers,
   `RUST_LOG=debug` for Tauri.
5. **Form one hypothesis at a time**; change one thing; re-run the test.
6. **Fix the root cause**, not the symptom. If you must patch the symptom, log debt.
7. **Record** in memory: `memory.py add --type bug --title "..." --body "symptom → cause → fix → test"`.

Common cross-platform culprits: WebKit-only CSS/JS differences, timezone/locale parsing,
path separators and case sensitivity, CRLF line endings, file permission differences, different
webview versions (Tauri on older Windows/Linux), iOS Safari 100vh/safe areas, Android back
button handling, keyboard covering inputs on mobile, high-DPI scaling on Windows.
