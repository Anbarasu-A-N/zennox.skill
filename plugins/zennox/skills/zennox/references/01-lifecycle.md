# 01 — Lifecycle: Define → Plan → Build → Verify → Review → Ship

Most agents skip straight to code. This file is the antidote. Each phase has an output and a
gate; you may move fast through a phase, but you may not skip its gate silently.

## Contents
1. Define (interview + SPEC.md)
2. Plan (architecture + slices + ADRs)
3. Build (incremental, vertical slices)
4. Verify (prove it)
5. Review (five axes)
6. Ship (release checklist)
7. Sizing the process to the task

---

## 1. Define

Ask only what changes the design. A good first interview is at most five questions, asked one
at a time if the user seems unsure, or all at once if they are clearly technical:

1. Who uses it and on which devices? (phone / tablet / laptop / desktop; iOS / Android /
   Windows / macOS / Linux / browser)
2. What is the single job it must do well on day one?
3. Does it need to work offline, or with flaky networks?
4. Does it handle accounts, payments, health, location or other sensitive data?
5. Constraints: budget, deadline, team skills, existing backend, store presence required?

Write `SPEC.md` from `assets/SPEC.template.md`: problem, users, platforms, core flows, data,
non-goals, success metric, risks. One page. If the user won't answer, write the spec with
explicit `ASSUMPTION:` lines and move on.

**Gate:** user acknowledges the spec, or assumptions are listed at the top.

## 2. Plan

1. Pick the architecture (`02-architecture-crossplatform.md`). Write one ADR per irreversible
   choice (framework, database, auth provider, sync model, hosting). Template:
   `assets/ADR.template.md`. Keep ADRs to ~15 lines.
2. Sketch the system: clients → API/edge → services → data stores → third parties. Name the
   trust boundaries; each one gets validation and auth.
3. Break into **vertical slices**. A slice cuts through UI, logic and data for one user-visible
   behaviour, and is small enough to review in one sitting (rule of thumb: < 200 changed lines,
   < 1 day). Order slices so the riskiest assumption is tested first.
4. For each slice write: goal, files likely touched, acceptance check (a test name or a manual
   step), and platforms affected.

Plan file shape (`PLAN.md`):

```
## Slice 3 — Offline note editing
Goal: edit a note with no network; syncs on reconnect
Touches: packages/core/sync.ts, apps/web/src/notes/Editor.tsx, adapters/storage
Check: e2e/offline-edit.spec.ts passes on chromium, webkit, mobile-safari
Risk: conflict resolution; using last-write-wins per field (ADR-004)
```

**Gate:** every slice has a check; risky slices come first.

## 3. Build

- One slice at a time. Don't start slice N+1 while N is red.
- Apply the Lazy Senior Ladder (`03-minimal-code.md`) before each new file or dependency.
- Shared logic in `packages/core`; platform specifics behind adapters. Never import a
  platform module from core (the graph script flags this).
- Commit per slice with a conventional message: `feat(sync): offline note editing`.
- If you take a shortcut, log it: `memory.py add --type debt "..."`.

## 4. Verify

"Tests are proof." For each slice:

- Unit tests for pure logic in core (fast, run on every save).
- Integration tests at adapter boundaries (storage, network, native bridges).
- E2E with Playwright for user flows on Chromium, WebKit, Firefox + one mobile emulation.
- For native shells: run the platform runner (XCTest / Espresso / `cargo test` for Tauri
  commands) at least in CI.
- The **Prove-It pattern** for bugs: write the failing test first, see it fail, fix, see it
  pass. Never claim a bug is fixed without this.

**Gate:** green, or an exception the user explicitly approved and that is logged as debt.

## 5. Review (five axes)

Ask, for every diff: *would a staff engineer approve this?*

| Axis | Questions |
|---|---|
| Correctness | Does it meet the slice's acceptance check? Edge cases: empty, huge, unicode, offline, slow, concurrent, timezone? |
| Simplicity | Could the ladder have stopped earlier? Any new dependency that a platform feature covers? Dead code, speculative abstraction? |
| Security | Input validated at the boundary? Authz checked server-side? Secrets out of code and bundles? `security_scan.py` clean? |
| Performance | N+1 queries, unbounded lists, main-thread blocking, bundle growth, re-render storms? |
| Accessibility & UX | Keyboard, focus, labels, contrast, reduced motion, touch targets, error and empty states? `slop_check.py` clean? |

Output a ranked punch list: `[HIGH] file:line — problem — fix`. Highs block merge.

## 6. Ship

Short checklist (details in `11-devops-deploy.md`):

- [ ] CI matrix green for every target
- [ ] Version bumped, changelog generated from commits
- [ ] Artifacts signed (and notarized on macOS)
- [ ] Secrets only in CI secret store; none in artifacts (`security_scan.py dist/`)
- [ ] Feature flags for risky paths; staged rollout (e.g. 5% → 25% → 100%)
- [ ] Error tracking and basic metrics live before rollout starts
- [ ] Rollback path tested (previous build re-deployable, DB migration reversible)
- [ ] Store metadata, privacy labels and screenshots updated if store release

"Faster is safer": small, frequent releases with good rollback beat big careful ones.

## 7. Sizing the process

| Task size | What to do |
|---|---|
| Typo / one-liner | Just do it. Verify. |
| Small feature (< 1 day) | 3-line spec in the reply, one slice, test, review checklist mentally. |
| Feature (days) | SPEC.md section + PLAN.md slices + ADR if irreversible. |
| New product | Full flow, interview first. |

Don't bury a user who asked for a button in process. Do insist on the gate checks.
