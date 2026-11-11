# Using Zennox

Zennox can be used three ways: **all at once** (one command runs the whole lifecycle),
**separately** (call any single mode, or chain a few), or **standalone** (run the scripts and
templates yourself, with or without an AI agent).

## Contents
1. Talking to Zennox
2. All at once: `zennox full`
3. Separately: every mode, with example prompts
4. Chaining modes
5. Standalone scripts (no AI needed)
6. Using one part on its own (references and templates)
7. Files Zennox creates in your project
8. Tips per surface (Claude.ai, Claude Code, Cowork, other agents)

---

## 1. Talking to Zennox

You never have to use a command. Zennox switches on whenever you ask for cross-platform app
work ("build a notes app for Android, iPhone and Windows"). To pick a mode yourself, start your
message with `zennox <mode>`. In Claude Code, `/zennox <mode>` works too.

```
zennox help                      → shows every mode with an example
zennox audit                     → one mode
zennox design + test             → two modes in order
zennox full                      → everything, start to finish
```

## 2. All at once: `zennox full`

`full` takes you from an idea to a shipped app, running every phase with its quality gate:

| Step | Mode | What you get | Pauses for you? |
|---|---|---|---|
| 1 | `init` | Machine check, project map, past decisions loaded | No |
| 2 | `spec` | Up to 5 questions → `SPEC.md` | **Yes — approve the spec** |
| 3 | `plan` | Stack decision (ADR), architecture, threat model, slices → `PLAN.md` | **Yes — approve the plan** |
| 4 | `design` | Design Read, dials, `DESIGN.md` with tokens (skipped for backend-only work) | No |
| 5 | `build` → `test` → `review` per slice | Working code, tests, security + design scans | Stops if anything is red |
| 6 | `harden` + `optimize` | HIGH findings fixed, performance budgets checked | No |
| 7 | `ship` | CI matrix, signing, release checklist | **Yes — before any production deploy** |
| 8 | `remember` + `gain` | Decisions and shortcuts saved, summary of what was saved | No |

Example:

```
zennox full
I want a habit tracker that works offline on iPhone, Android, Windows and Mac.
Free, no accounts at first, sync later. I know React and TypeScript.
```

Say **"no pauses"** to let it run steps 2–7 on stated assumptions. It will still ask before
deploying to production.

```
zennox full, no pauses — internal inventory tool, web + Windows desktop, Postgres backend
```

If a session ends mid-way, start a new one with `zennox full, continue` — it reads `SPEC.md`,
`PLAN.md` and project memory to pick up where it stopped.

## 3. Separately: every mode

Use any mode on its own. If a mode needs something that doesn't exist yet (for example `build`
with no plan), it does the minimum of the missing step and tells you.

### Plan

| Mode | Use it to | Example |
|---|---|---|
| `init` | Get oriented in a new or existing repo | `zennox init` |
| `spec` | Turn an idea into a one-page SPEC.md | `zennox spec a recipe app for families` |
| `plan` | Choose the stack and break work into slices | `zennox plan — should this be Tauri, Electron or a PWA?` |

### Design

| Mode | Use it to | Example |
|---|---|---|
| `design` | Create new UI from a brief | `zennox design the onboarding screens, calm and editorial` |
| `study` | Turn a screenshot or URL you like into a DESIGN.md (principles only, never a copy) | `zennox study` + attach image |
| `redesign` | Keep the content, change the look and structure | `zennox redesign the pricing page` |
| `polish` | Final craft pass: spacing, type, states | `zennox polish the settings screen` |
| `3d` | Rebuild an object from an image as Three.js code | `zennox 3d` + attach a photo of a lamp |

Design sub-commands work inside `design`/`polish`: `distill`, `bolder`, `quieter`,
`colorize`, `typeset`, `animate`, `adapt`, `harden`, `critique`
(e.g. `zennox polish — make it quieter`).

### Build and fix

| Mode | Use it to | Example |
|---|---|---|
| `build` | Implement one slice with the least new code | `zennox build slice 3` or `zennox build a share button` |
| `debug` | Find the root cause of a bug or slowness | `zennox debug — login fails only on iOS Safari` |
| `optimize` | Cut bundle size, load time, tokens or model cost | `zennox optimize the startup time` |

### Check

| Mode | Use it to | Example |
|---|---|---|
| `test` | Write and run tests across browsers and devices | `zennox test the checkout flow on mobile` |
| `review` | Five-axis review of a change before merging | `zennox review my last commit` |
| `audit` | Score everything (code, design, security, performance) — **never edits** | `zennox audit` |
| `harden` | Fix security problems | `zennox harden the Electron app` |

### Release and remember

| Mode | Use it to | Example |
|---|---|---|
| `ship` | Set up CI/CD, signing, store release | `zennox ship to TestFlight and the Microsoft Store` |
| `remember` | Save or recall a decision | `zennox remember we use pnpm and UTC dates` |
| `debt` | List shortcuts you postponed | `zennox debt` |
| `gain` | See what Zennox saved you (lines, files read, cost) | `zennox gain` |
| `help` | Show the menu | `zennox help` |

## 4. Chaining modes

Join modes with `+` or "then". Each one runs with its own gate, in order.

```
zennox audit + harden            → score first, then fix security issues
zennox design + test             → build the UI, then test it on all browsers
zennox review then ship          → review the branch, then prepare the release
zennox plan + design + build     → the first half of `full`, without shipping
```

## 5. Standalone scripts (no AI needed)

The scripts are plain Python 3.10+ with no installs. Run them from a terminal or in your own
CI. Replace `$Z` with the skill's folder (in this repo:
`plugins/zennox/skills/zennox`). On Windows use `python` instead of `python3`.

```bash
# What can this machine build? (writes .zennox/env.json)
python3 $Z/scripts/detect_env.py .
python3 $Z/scripts/detect_env.py . --no-versions   # fastest: only checks which tools exist

# Map the codebase: hot files, cycles, unused files, layer violations
python3 $Z/scripts/project_graph.py .
python3 $Z/scripts/project_graph.py . --neighbors src/api/client.ts
python3 $Z/scripts/project_graph.py . --core-dirs core,shared,domain

# Design check (exit code 2 on HIGH findings with --fail-on-high)
python3 $Z/scripts/slop_check.py apps/web --fail-on-high

# Security first pass (add --include-build to scan release output)
python3 $Z/scripts/security_scan.py . --fail-on-high
python3 $Z/scripts/security_scan.py dist --include-build

# Project memory
python3 $Z/scripts/memory.py add --type decision --title "Use Tauri 2" --body "Smaller binaries." --tags desktop
python3 $Z/scripts/memory.py search "desktop"
python3 $Z/scripts/memory.py get <id> --summary
python3 $Z/scripts/memory.py list --type debt
python3 $Z/scripts/memory.py compact
```

Every script supports `--help` and `--json`. Reports go to `.zennox/` in the scanned project.

Use them as gates in your own CI:

```yaml
- name: Zennox security gate
  run: python3 zennox/scripts/security_scan.py . --fail-on-high
- name: Zennox design gate
  run: python3 zennox/scripts/slop_check.py apps/web --fail-on-high
```

## 6. Using one part on its own

Every reference file is self-contained, so you can take just the part you need:

| I only want… | Take this file |
|---|---|
| The spec → ship workflow | `references/01-lifecycle.md` |
| Help choosing Tauri / Electron / RN / Flutter / PWA | `references/02-architecture-crossplatform.md` |
| Less code from my agent | `references/03-minimal-code.md` |
| Lower token and model costs | `references/04-context-memory-cost.md` |
| UI that doesn't look AI-generated | `references/05-design-system.md` + `assets/DESIGN.template.md` |
| Apple / Liquid Glass look | `references/06-apple-platform.md` |
| Good animation | `references/07-motion.md` |
| Image → 3D model | `references/08-3d-threejs.md` |
| A security checklist | `references/09-security.md` |
| Playwright tests | `references/10-testing-playwright.md` + `assets/playwright.config.ts` |
| CI/CD and store release | `references/11-devops-deploy.md` + `assets/ci-matrix.yml` |
| Offline, sync, performance, debugging | `references/12-networking-performance.md` |
| Accessibility, i18n, privacy | `references/13-extra-capabilities.md` |

Ways to use a single file: attach it to a chat; paste it into your project's `CLAUDE.md` or
`AGENTS.md`; or drop it into Cursor rules (`.cursor/rules/zennox-design.mdc`). The templates in
`assets/` can be copied straight into a project.

## 7. Files Zennox creates in your project

| File | Created by | Commit it? |
|---|---|---|
| `SPEC.md`, `PLAN.md`, `DESIGN.md` | `spec`, `plan`, `design` | Yes |
| `docs/adr/NNNN-*.md`, `docs/threat-model.md` | `plan`, `harden` | Yes |
| `.zennox/memory.jsonl` | `memory.py` | Yes, if you want shared team memory |
| `.zennox/GRAPH_REPORT.md`, `graph.json`, `graph-cache.json` | `project_graph.py` | No (regenerate) |
| `.zennox/*-report.json`, `env.json` | scanners, `detect_env.py` | No |

Suggested `.gitignore` lines if you keep memory but not reports:

```
.zennox/*
!.zennox/memory.jsonl
```

## 8. Tips per surface

**Claude.ai / Claude app** — turn on code execution so Zennox can run its scripts. Upload your
project files (or a zip) for `audit`, `review` and `init`. Without code execution, every mode
still works from the guides; only the automatic scans are skipped.

**Claude Code** — the best fit: Zennox can read your repo, run the scripts and your tests
directly. Add one line to your project's `CLAUDE.md` so every session starts mapped:
`Before exploring, read .zennox/GRAPH_REPORT.md (run zennox init if missing).`

**Cowork** — same as Claude Code for files on your machine; good for `audit`, `ship`
checklists and documents.

**Other agents (Cursor, Codex, Gemini CLI, Copilot…)** — most read the `SKILL.md` format or
an `AGENTS.md` file. Copy the `zennox` folder into the agent's skills directory, or paste
`SKILL.md` into its rules file; the scripts run the same everywhere.
