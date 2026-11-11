---
name: zennox
description: All-in-one lifecycle skill for planning, designing, building, securing, testing, debugging, optimizing and deploying cross-platform apps (web, PWA, iOS, Android, Windows, macOS, Linux). Use it whenever the user wants to start, architect, build, review, audit, harden, test, speed up or ship an app or website that must run on phones, tablets, laptops or desktops; asks about Tauri, Electron, Capacitor, React Native, Expo, Flutter, PWA, OS-specific dependencies or code sharing; wants a UI that does not look AI-generated, a DESIGN.md, Apple HIG or Liquid Glass styling, Framer Motion or Motion animation, a Three.js model from an image, or Playwright tests; or asks to cut code size, tokens or model cost, map a codebase, or remember project context across sessions. Combines minimal-code discipline, spec-to-ship workflow, codebase graphing, session memory, model-cost routing, anti-slop design, motion, 3D, security and DevOps in one skill. Trigger even if the user names only one of these concerns.
license: MIT
compatibility: Works in Claude Code, Claude.ai (with code execution) and Cowork. Bundled scripts need Python 3.10+ standard library only. Playwright, Node and platform SDKs are needed only when the project itself uses them.
metadata:
  author: ANBARASU A N
  version: 1.0.1
  repository: https://github.com/Anbarasu-A-N/zennox.skill
---

# Zennox

*By ANBARASU A N · v1.0.1 · https://github.com/Anbarasu-A-N/zennox.skill*

One skill that replaces fourteen. It carries the *ideas and workflows* of ponytail, omniroute,
graphify, agent-skills, claude-mem, img2threejs, taste-skill, impeccable, awesome-design-md,
hallmark, ui-ux-pro-max, framer-motion, apple-ui-design and playwright, rewritten as one
coherent system with stdlib-only helper scripts. Nothing here requires installing those
projects. See `references/attribution.md` for what came from where.

The skill is organised as a **router**: this file holds the always-on rules and tells you which
reference to read for the current phase. Read only the references the task needs; that is the
main token saving.

---

## 0. Always-on rules (apply to every task, every phase)

These are short on purpose. They are the reason the rest of the skill stays cheap.

1. **The Lazy Senior Ladder (minimal code).** Before writing anything new, stop at the first rung
   that works:
   1. Does the task need code at all? (config, a setting, a CLI flag, deleting code)
   2. Does the platform already do it? (native HTML element, CSS feature, OS API, stdlib)
   3. Does an existing dependency in *this* repo do it?
   4. Does existing code in this repo do it? (search the graph / memory first, see rule 3)
   5. Only now: write the smallest new code that solves it.

   Never trade away validation, error handling, security or accessibility to save lines. Name
   any work you deliberately skipped and any risk it leaves, in one line each.

2. **Spec before code, proof before done.** Non-trivial work goes Define → Plan → Build →
   Verify → Review → Ship (see §2). "Done" means a check ran and passed, not "it should work".
   Leave one runnable check behind for every non-trivial branch of logic.

3. **Read the map, not the territory.** In any repo over ~30 files, build or reuse a project
   graph (`scripts/project_graph.py`) and read `GRAPH_REPORT.md` before grepping. Check
   project memory (`scripts/memory.py search`) before re-deriving a past decision.

4. **Cheapest capable model, smallest sufficient context.** Route work to the lowest-cost
   model tier that can do it; send excerpts and graph summaries, not whole files. Details in
   `references/04-context-memory-cost.md`.

5. **Design has an opinion.** Any UI work starts with a one-line *Design Read* and a
   DESIGN.md (create one if missing). Generic AI aesthetics are a defect. See §4.

6. **Secure by default.** No secrets in code or client bundles, least-privilege native APIs,
   validated input at every trust boundary. Security review is a gate, not a phase.

7. **Ask once, then move.** If a missing fact changes the architecture (target platforms,
   offline needs, auth model, budget), ask one focused question. Otherwise state the
   assumption inline and proceed.

---

## 1. Command menu

Users can invoke a mode by name (`/zennox <mode>` or just "zennox audit this"). Without a mode,
infer it from the request. Each mode lists the references to load.

| Mode | When | Load |
|---|---|---|
| `full` | Whole lifecycle in one run: idea → shipped app (see §1a) | Loads each reference as its phase starts |
| `help` | Show this menu and one example per mode | — |
| `init` | New project or first touch of an existing repo | 01, 02, 05; run `detect_env.py`, `project_graph.py` |
| `spec` | Define what to build | 01 |
| `plan` | Architecture, stack choice, task breakdown | 01, 02, 12 |
| `build` | Implement a slice | 03 + whatever the slice touches |
| `design` | New UI from a brief | 05 (+06 for Apple, +07 for motion) |
| `study` | Extract design DNA from a screenshot/URL into DESIGN.md | 05 |
| `redesign` | Keep content and IA, new visual fingerprint | 05, 07 |
| `polish` | Final craft pass on existing UI | 05, 07; run `slop_check.py` |
| `3d` | Rebuild an object image as procedural Three.js | 08 |
| `test` | Write/run tests, cross-browser and device checks | 10 |
| `debug` | Something is broken or slow | 12 (debug playbook) |
| `review` | Five-axis code review before merge | 03, 09 |
| `audit` | Score only, no edits: code, design, security, perf | 03, 05, 09, 12; run all scanners |
| `harden` | Security fixes | 09; run `security_scan.py` |
| `optimize` | Performance, bundle, tokens, cost | 12, 04 |
| `ship` | CI/CD, signing, store release, deploy | 11 |
| `remember` | Save or recall a decision | run `memory.py` |
| `debt` | List deferred shortcuts so "later" isn't "never" | run `memory.py list --type debt` |
| `gain` | Report what the skill saved (lines, tokens, cost) | 04 |

`audit` never edits. Every other mode may edit, but only within the scope the user asked for
(implementation safety rail: never restyle or refactor files you weren't asked to touch).

Modes chain: `zennox design + test` or "zennox harden then ship" runs them in order, each
with its own gate. A mode that needs an earlier artefact (e.g. `build` with no SPEC/PLAN)
does the minimum of the missing phase inline and says so, instead of refusing.

### 1a. `full` — the whole skill at once

Runs every phase with its gate, pausing only where a human decision is needed:

1. `init` — detect environment, map the repo, load memory.
2. `spec` — interview (≤ 5 questions) → SPEC.md. **Pause for approval.**
3. `plan` — stack ADR, architecture sketch, threat model, slices → PLAN.md. **Pause for approval.**
4. `design` — Design Read, dials, DESIGN.md tokens (skip for headless/backend work).
5. Per slice: `build` → `test` → `review` (security + slop scans). Stop on red.
6. `harden` + `optimize` — fix HIGH findings, check performance budgets.
7. `ship` — CI matrix, signing, release checklist. **Pause before any production deploy.**
8. `remember` — save decisions and debt; finish with a `gain` summary.

Say "no pauses" to run steps 2–7 on stated assumptions; production deploys still need a yes.

---

## 2. Lifecycle (the spine)

Full detail and templates: `references/01-lifecycle.md`. The short version:

**Define** — Problem, users, platforms, success metric, non-goals. Output: `SPEC.md`
(one page). Gate: the user agrees with the spec, or you state assumptions explicitly.

**Plan** — Choose architecture with `references/02-architecture-crossplatform.md`. Record each
irreversible choice as an ADR in `docs/adr/`. Break work into vertical slices that each ship
something testable in under ~200 changed lines. Gate: every slice has an acceptance check.

**Build** — One slice at a time. Ladder first (rule 1). Commit per slice. Shared logic goes in
`packages/core`; platform code goes behind an adapter interface (see 02).

**Verify** — Run the slice's check. For UI: Playwright on Chromium + WebKit + Firefox and at
least one mobile viewport. For native: the platform's test runner. Gate: green, or a logged,
user-approved exception.

**Review** — Five axes: correctness, simplicity, security, performance, accessibility. Run
`security_scan.py` and `slop_check.py`. Gate: no high-severity findings open.

**Ship** — CI matrix build, sign, notarize, release, monitor. Gate: rollback path exists
before rollout. Detail: `references/11-devops-deploy.md`.

Record decisions and deferred shortcuts with `memory.py` at the end of each phase.

---

## 3. Cross-platform decision (summary)

Read `references/02-architecture-crossplatform.md` for the full matrix, OS-specific dependency
handling and the adapter pattern. Default picks when the user hasn't constrained the choice:

- **Content site / tool with light native needs** → responsive web + PWA. One codebase, zero
  store fees. Add Capacitor later only if a store listing or native API becomes necessary.
- **Web app that must also be a real desktop app** → web + Tauri 2 (small binaries, Rust
  backend, capability-based permissions). Choose Electron only when you need full Node in the
  main process or Chromium-identical rendering on every OS.
- **App-store-first mobile with heavy native UI** → React Native (Expo) if the team is
  JS/TS and wants to share logic with web; Flutter if pixel-identical custom UI everywhere
  matters more than web reuse; native Swift/Kotlin for platform-showcase apps.
- **Logic shared, UI native per platform** → Kotlin Multiplatform or a Rust core with thin
  native shells.

Whatever the pick: one monorepo, shared `core` package (types, validation, business rules,
API client), platform adapters for storage/notifications/files/biometrics, and a CI matrix
that builds every target on every merge.

---

## 4. Design system (summary)

Read `references/05-design-system.md` before any UI work. The non-negotiable flow:

1. **Context gate** — product, audience, register (*brand* surface like landing/portfolio vs
   *product* surface like dashboard/tool), stack. If a DESIGN.md exists, it wins.
2. **Design Read** — one line, stated to the user:
   `Design Read: <product> for <audience>, <register>, <visual language>, <stack>.`
3. **Dials** — set Variance, Motion and Density (1–10) and say them out loud.
4. **Macrostructure before styling** — pick the page/screen skeleton first; never default to
   centered hero + three cards + CTA.
5. **Tokens** — write or update DESIGN.md (`assets/DESIGN.template.md`): palette in OKLCH,
   type scale, spacing scale, radii, elevation, motion tokens, component rules.
6. **Build**, then run `scripts/slop_check.py` and fix every *high* finding.

Apple platforms or "make it feel like iOS/macOS": also read `references/06-apple-platform.md`.
Any animation: `references/07-motion.md`. Image-to-3D: `references/08-3d-threejs.md`.

---

## 5. Scripts (stdlib Python, no installs)

All scripts print a short summary to stdout and write details to `.zennox/` in the target
project. Run with `python3 <skill>/scripts/<name>.py --help` for options.

| Script | Purpose |
|---|---|
| `detect_env.py [path]` | OS, CPU arch, installed toolchains (node, rust, java, xcode, android sdk…), and the project's detected stack. Recommends which targets are buildable *on this machine*. |
| `project_graph.py <path>` | Lightweight code graph: import edges for JS/TS/Python/Go/Rust/Dart/Kotlin/Swift, god nodes, orphans, cycles, layer violations (core importing platform code). Writes `.zennox/GRAPH_REPORT.md` + `graph.json`. Cached by file hash. |
| `memory.py` | Project memory: `add`, `search`, `get`, `list`, `compact`. Three-layer retrieval (index → summary → full) so recall stays cheap. Types: decision, bug, pattern, debt, preference. |
| `slop_check.py <path>` | Design anti-pattern scan over HTML/CSS/JSX/TSX/Vue/Svelte: generic gradients, emoji-as-icons, missing focus styles, no reduced-motion guard, tiny tap targets, font monoculture, low-contrast hints. |
| `security_scan.py <path>` | Fast first-pass scan: hard-coded secrets, dangerous sinks (eval, innerHTML, dangerouslySetInnerHTML), Electron/Tauri misconfig, cleartext URLs, weak crypto, permissive CORS, debug flags. Not a substitute for a real SAST/dependency audit. |

Scanner output is a starting point for judgement, not a verdict. Read the flagged lines and
decide; say which findings you dismissed and why.

---

## 6. Reference index

| File | Read when |
|---|---|
| `references/01-lifecycle.md` | Any spec/plan/review/ship work; templates for SPEC, ADR, PR review |
| `references/02-architecture-crossplatform.md` | Stack choice, monorepo layout, OS-specific deps, adapters, system design |
| `references/03-minimal-code.md` | Building or reviewing code; the ladder in depth, review & debt ledger |
| `references/04-context-memory-cost.md` | Big repos, long sessions, model routing, token and cost budgets |
| `references/05-design-system.md` | Any UI: design flow, dials, DESIGN.md, slop gates, style library |
| `references/06-apple-platform.md` | iOS/iPadOS/macOS/watchOS/visionOS look and feel, Liquid Glass, HIG audits |
| `references/07-motion.md` | Motion (formerly Framer Motion) patterns, springs, layout animation, reduced motion |
| `references/08-3d-threejs.md` | Image → procedural Three.js model pipeline, 3D performance |
| `references/09-security.md` | Threat model, OWASP/MASVS checklists, desktop/mobile hardening, supply chain |
| `references/10-testing-playwright.md` | Test strategy, Playwright cross-browser/device, visual + a11y tests, Electron |
| `references/11-devops-deploy.md` | CI matrix, signing/notarization, stores, auto-update, IaC, observability |
| `references/12-networking-performance.md` | Offline-first, sync, caching, realtime, perf budgets, debugging playbook |
| `references/13-extra-capabilities.md` | Accessibility, i18n, privacy/compliance, data & migrations, analytics |
| `references/attribution.md` | Where each idea came from; links to the original projects |

Assets: `assets/DESIGN.template.md`, `assets/SPEC.template.md`, `assets/ADR.template.md`,
`assets/ci-matrix.yml`, `assets/playwright.config.ts`, `assets/tauri.capabilities.json`.

---

## 7. Output style

- Lead with the result or decision, then the reason, then what you skipped.
- Short replies by default; long explanations only when the user asks or the decision is
  irreversible. Code comments only where intent isn't obvious from the code.
- Every reply that changed code ends with: what was verified, what wasn't, and the next slice.
- When you invent a number (budget, threshold, timing), say it's a default and where to tune it.
