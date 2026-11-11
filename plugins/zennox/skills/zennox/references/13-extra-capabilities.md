# 13 — Extra Capabilities (gaps the 14 source skills didn't cover)

These were added because a cross-platform app usually fails on them late and expensively.

## Contents
1. Accessibility (WCAG 2.2 AA)
2. Internationalisation and localisation
3. Privacy and compliance
4. Data modelling and migrations
5. Analytics and product metrics
6. AI features inside the app
7. Documentation that stays useful

---

## 1. Accessibility

Target WCAG 2.2 AA on every platform.
- Semantic structure first: landmarks, headings in order, real buttons and links, labels on
  every input. Native components before ARIA; ARIA only to fill gaps.
- Keyboard: everything reachable and operable; visible focus; no traps; logical order; skip
  link on content sites. Focus moves into dialogs and returns on close.
- Contrast: 4.5:1 text, 3:1 large text and UI parts; don't convey meaning by colour alone.
- Target size: at least 24×24 CSS px (WCAG 2.2 minimum), 44pt/48dp on touch platforms.
- Motion: honour reduced motion; no autoplay without pause.
- Media: captions, transcripts, alt text that describes purpose.
- Mobile: VoiceOver/TalkBack labels, traits/roles, grouping; Dynamic Type / font scaling
  without truncating key content.
- Test: axe in Playwright (`10-testing-playwright.md`), keyboard-only pass, one screen-reader
  pass per release on each platform family.

## 2. Internationalisation and localisation

- Externalise every user-facing string from day one; ICU MessageFormat for plurals, gender
  and select (`{count, plural, one {# file} other {# files}}`). Libraries: FormatJS/i18next
  (web/RN), Flutter `intl`/ARB, Apple String Catalogs, Android string resources.
- Never concatenate translated fragments; translators need whole sentences.
- `Intl.DateTimeFormat`, `Intl.NumberFormat` (currency, units), `Intl.Collator` for sorting.
  Store times in UTC; display in the user's zone.
- RTL: use CSS logical properties (`margin-inline-start`, `inset-inline-end`), `dir="auto"`
  on user content, mirror directional icons only.
- Text expansion: allow ~30–40% longer strings (German, Finnish); test with pseudo-locales.
- Locale-aware input: names with any script, addresses without assuming US format, phone
  numbers via libphonenumber.

## 3. Privacy and compliance

Not legal advice — flag these for the user to confirm with counsel where relevant.
- Data minimisation: collect only what the spec needs; set retention periods.
- Consent: analytics/ads cookies need opt-in in many jurisdictions (GDPR/ePrivacy); honour
  Global Privacy Control where required.
- User rights: export and delete data. App Store and Google Play both require in-app account
  deletion for apps that let users create accounts (check current policy text).
- Children: COPPA (US) and age-appropriate design codes change what you may collect.
- Health, finance, education data may fall under HIPAA, PCI DSS, FERPA or local equivalents —
  use compliant vendors (e.g. a payment provider so card data never touches your servers).
- Store disclosures: Apple privacy nutrition labels + privacy manifest; Google Play data safety
  form. Keep them in sync with actual SDK behaviour (third-party SDKs count).
- Privacy policy and terms linked in-app and on the store listing.

## 4. Data modelling and migrations

- Model from the core flows in SPEC.md; name tables/collections after domain nouns.
- IDs: UUIDv7 or ULID (sortable, safe to generate offline) for anything created on devices.
- Every table: `created_at`, `updated_at`; soft delete (`deleted_at`) when sync or undo matters.
- Migrations versioned in the repo (Prisma, Drizzle, Alembic, Flyway, sqlx). Expand →
  migrate → contract for zero-downtime. On-device SQLite schemas migrate on app start with a
  tested upgrade path from every released version.
- Indexes for every foreign key and every frequent `WHERE`/`ORDER BY`; check query plans for
  hot paths.
- Backups + tested restore (`11-devops-deploy.md`).

## 5. Analytics and product metrics

- Define 3–5 metrics from the SPEC's success metric (activation, retention, task success,
  time-to-value). Track events that answer them; skip the rest.
- Event naming: `object_action` (`note_created`, `invoice_sent`) with a typed schema in `core`.
- Privacy-friendly options (self-hosted or cookie-less analytics) reduce consent burden.
- Never send PII or secrets in event properties.
- Separate product analytics from error tracking and performance monitoring.

## 6. AI features inside the app

- Server-side only for keys and calls; route by task and budget (`04-context-memory-cost.md`).
- Treat model output as untrusted input: validate structured output against a schema, escape
  before rendering, never execute it.
- Prompt injection: content from users, web pages, files or emails can contain instructions.
  Keep tools least-privilege, require user confirmation for consequential actions, and keep
  system instructions separate from retrieved content.
- Stream responses (SSE) for perceived speed; show stop/regenerate controls.
- Log prompts/outputs only with consent and with PII redaction; set retention.
- Evaluate with a fixed set of test prompts before changing models or prompts.

## 7. Documentation that stays useful

- `README.md`: what it is, how to run each target, how to test, how to release — kept true
  by running the commands in CI where possible.
- `SPEC.md`, `DESIGN.md`, `docs/adr/`, `docs/threat-model.md`: short, current, linked.
- `CLAUDE.md` / `AGENTS.md`: project conventions for coding agents (stack, commands, rules,
  "read `.zennox/GRAPH_REPORT.md` before exploring"). Keep it under ~100 lines.
- Generated API docs from the schema, not hand-written.
