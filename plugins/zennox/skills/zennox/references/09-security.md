# 09 — Security: Threat Model, Code Vulnerabilities, Platform Hardening

Security is a gate in Review and Ship, and a habit in Build. This file is defensive guidance
for apps you own or are authorised to work on.

## Contents
1. Ten-minute threat model
2. Web/API vulnerability checklist
3. Auth, sessions, secrets
4. Desktop hardening (Electron, Tauri)
5. Mobile hardening (iOS, Android, hybrid)
6. Supply chain and CI
7. Tooling by layer
8. Reporting format

Standards to align with (check current editions): OWASP Top 10, OWASP ASVS (web), OWASP
MASVS/MASTG (mobile), OWASP API Security Top 10, CWE Top 25.

---

## 1. Ten-minute threat model

1. Draw data flow: client(s) → API → services → stores → third parties.
2. Mark trust boundaries (every arrow that crosses one needs authn, authz and validation).
3. For each boundary, run STRIDE quickly: Spoofing, Tampering, Repudiation, Information
   disclosure, Denial of service, Elevation of privilege.
4. List the top 5 risks with likelihood × impact; each gets a mitigation and a test.
5. Save as `docs/threat-model.md`; revisit when a boundary changes.

## 2. Web/API checklist

| Risk | Do |
|---|---|
| Broken access control / IDOR | Check ownership server-side on every object access; deny by default; test with a second user |
| Injection (SQL/NoSQL/command/LDAP) | Parameterised queries / ORM bindings; never build shell commands from input; allow-list arguments |
| XSS | Framework auto-escaping; no `innerHTML`/`dangerouslySetInnerHTML`/`v-html` with untrusted data, or sanitise with DOMPurify; strict CSP |
| CSRF | SameSite cookies + CSRF token for cookie-auth state changes |
| SSRF | Allow-list outbound hosts; block private/link-local ranges and metadata IPs; don't follow redirects blindly |
| Insecure deserialisation | Don't deserialise untrusted data into objects (pickle, Java serialisation, YAML `load`) |
| Mass assignment | Explicit DTO/schema of writable fields |
| File upload | Validate type by content, size limits, random names, store outside web root/object store, scan if needed |
| Rate limiting / brute force | Per-IP and per-account limits on login, OTP, password reset, expensive endpoints |
| Security misconfig | No debug mode or stack traces in prod; minimal CORS (no `*` with credentials); remove default creds |
| Sensitive data exposure | TLS everywhere, HSTS; encrypt sensitive columns; minimise what you log |
| Logging & monitoring | Log authn/authz failures and admin actions (without secrets/PII); alert on spikes |

Headers baseline: `Content-Security-Policy` (start from `default-src 'self'`; avoid
`unsafe-inline`/`unsafe-eval`), `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
`Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` limiting camera/mic/geo,
`frame-ancestors` in CSP to prevent clickjacking.

Validation: one schema (zod/valibot/pydantic) per input, in `core`, used on server *and*
client. Client validation is UX; server validation is security.

## 3. Auth, sessions, secrets

- Use a proven provider or library; don't hand-roll crypto or password storage. If you must
  store passwords: Argon2id (or bcrypt/scrypt) with per-user salt.
- OIDC Authorization Code + PKCE for SPAs and native apps; system browser for login on mobile
  and desktop (not embedded webviews).
- Prefer passkeys/WebAuthn; offer TOTP MFA; protect recovery flows as strongly as login.
- Web sessions: `HttpOnly; Secure; SameSite=Lax` (or Strict) cookies. Tokens in JS-readable
  storage are exposed to any XSS.
- Native: tokens in Keychain / Keystore / Credential Manager / libsecret via the secure
  storage adapter.
- Secrets: env vars or a secret manager; never in repo, client bundles, mobile binaries or
  desktop resources (they *will* be extracted). Anything shipped to a device is public.
  Third-party API keys that must be secret belong behind your own API.
- Rotate keys; scope them minimally; revoke on employee offboarding.

## 4. Desktop hardening

**Electron**
- `contextIsolation: true`, `sandbox: true`, `nodeIntegration: false` (these are defaults in
  modern Electron — don't turn them off).
- Expose a minimal API via `contextBridge` in preload; never expose `ipcRenderer` wholesale.
- Validate `event.senderFrame` origin in every `ipcMain.handle`; validate arguments with a schema.
- Block unexpected navigation and windows: `will-navigate` and `setWindowOpenHandler` → deny
  or open externally with an allow-list (`shell.openExternal` only for validated https URLs).
- `session.setPermissionRequestHandler` to deny by default.
- Strict CSP for local content; load app content from a custom protocol or file, not remote.
- Use Electron Fuses to disable `RunAsNode`, enable ASAR integrity, etc.
- Keep Electron current; Chromium security fixes ship through Electron releases.

**Tauri 2**
- Capabilities: grant each window only the permissions it needs (`assets/tauri.capabilities.json`).
- Scope filesystem and shell plugins tightly (specific dirs, specific commands).
- Validate all `#[tauri::command]` arguments in Rust; treat the webview as untrusted.
- Set a CSP in `tauri.conf.json`; consider the isolation pattern for apps loading
  third-party content.

**Both:** sign binaries, verify update signatures, serve updates over HTTPS only.

## 5. Mobile hardening

- Transport: iOS App Transport Security on (no arbitrary loads); Android
  `network_security_config` with cleartext disabled. Certificate pinning only with a backup pin
  and a rotation plan (or skip it — a broken pin bricks the app).
- Storage: secrets in Keychain/Keystore; no sensitive data in logs, screenshots of sensitive
  screens obscured in the app switcher where appropriate, no PII in `UserDefaults`/
  `SharedPreferences` unencrypted.
- Deep links / universal links / app links: validate every parameter; never perform an action
  purely from a link without confirmation.
- WebViews (Capacitor, RN WebView): disable file access and JS bridges you don't need;
  allow-list navigation.
- Android: `exported` set explicitly on components; minimal permissions; `android:allowBackup`
  considered; Play Integrity / App Attest for high-risk apps (defence in depth, not a lock).
- Treat root/jailbreak detection and obfuscation as speed bumps; the server must enforce rules.

## 6. Supply chain and CI

- Commit lockfiles; use `npm ci` / `pnpm install --frozen-lockfile` in CI.
- Audit dependencies: `npm audit` / `pnpm audit`, `osv-scanner`, `cargo audit`, `pip-audit`;
  automate updates (Dependabot or Renovate) with CI gates.
- Before adding a dependency: maintenance activity, download count, install scripts,
  typosquat check (exact name), licence.
- GitHub Actions: pin third-party actions to a commit SHA; `permissions:` least privilege
  (default `contents: read`); never echo secrets; OIDC to cloud instead of long-lived keys;
  don't run untrusted PR code with secrets (`pull_request_target` caution).
- Generate an SBOM (CycloneDX/SPDX) for releases; sign artifacts and provenance where the
  platform supports it.
- Secret scanning: gitleaks or trufflehog in pre-commit and CI.

## 7. Tooling by layer

| Layer | Tools |
|---|---|
| First pass (this skill) | `scripts/security_scan.py` |
| SAST | Semgrep (community rules for JS/TS, Python, Go, Swift, Kotlin), CodeQL, ESLint security plugins, Bandit (Python), `cargo clippy` |
| Dependencies | osv-scanner, npm/pnpm audit, cargo audit, pip-audit, Snyk/Dependabot |
| Secrets | gitleaks, trufflehog |
| DAST | OWASP ZAP baseline scan against staging |
| Mobile | MobSF static analysis; MASTG test cases |
| Containers/IaC | Trivy, Checkov, tfsec |

## 8. Reporting format

```
[HIGH]  api/notes.ts:42  CWE-639 IDOR — note fetched by id without owner check
        Fix: add `where: { id, ownerId: session.userId }`; test: e2e/authz-notes.spec.ts
[MED]   desktop/main.ts:18  Electron window opens arbitrary URLs from renderer
        Fix: setWindowOpenHandler allow-list
[INFO]  security_scan.py flagged `eval` in vendor/legacy.min.js — third-party, not reachable; dismissed
```
HIGH = exploitable now or exposes data/credentials; blocks merge and release.
