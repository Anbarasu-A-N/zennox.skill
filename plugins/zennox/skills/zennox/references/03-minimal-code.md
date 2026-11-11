# 03 — Minimal Code, Maximum Output

The cheapest line of code is the one you don't write: no tokens to generate, no bugs, nothing
to review, test, secure or maintain. This file expands rule 1 of SKILL.md.

## Contents
1. The Lazy Senior Ladder, in depth
2. Platform-first replacements (web, mobile, desktop)
3. Over-build traps
4. What you must never cut
5. Reuse: finding existing code before writing new
6. Review mode (diff-level) and audit mode (repo-level)
7. Debt ledger
8. Measuring gain

---

## 1. The ladder, in depth

| Rung | Question | Typical answer |
|---|---|---|
| 0 | Does this need doing? | The feature already exists behind a flag; the bug is a config value; the user wants a setting, not a system. |
| 1 | Config, not code? | A build flag, an env var, a lint rule, a framework option. |
| 2 | Does the platform do it? | Native HTML/CSS, Web APIs, OS APIs, the language stdlib. |
| 3 | Does an installed dependency do it? | Check `package.json` / `Cargo.toml` / `pubspec.yaml` before adding a new one. |
| 4 | Does code in this repo do it? | Search the graph (`GRAPH_REPORT.md`), then `memory.py search`, then grep. |
| 5 | Smallest new code | Inline > function > module > package. No abstraction until the third use. |

State which rung you stopped at when it's not obvious: *"Used `<dialog>` (rung 2) instead of a
modal library."*

## 2. Platform-first replacements

Web:
| Instead of | Use |
|---|---|
| Date-picker library | `<input type="date">` / `type="datetime-local"` |
| Modal library | `<dialog>` with `showModal()` |
| Tooltip/popover library | Popover API (`popover` attribute) + CSS anchor positioning where supported, with a fallback |
| Accordion component | `<details>` / `<summary>` |
| Form validation library (simple forms) | Constraint validation: `required`, `pattern`, `type="email"`, `:user-invalid` |
| JS scroll-snap carousel | CSS `scroll-snap-type` |
| JS sticky header | `position: sticky` |
| Resize listeners for layout | Container queries, `clamp()`, grid `auto-fit` |
| Lodash for one function | Native `structuredClone`, `Object.groupBy`, `Array.prototype.at`, `Intl.*` |
| Moment.js | `Intl.DateTimeFormat`, `Intl.RelativeTimeFormat`; Temporal where available |
| Animation library for fades | CSS transitions, `@starting-style`, View Transitions API |
| Lazy-load library | `loading="lazy"` on images and iframes |
| UUID package | `crypto.randomUUID()` |
| Fetch wrapper | `fetch` + `AbortController` + a 20-line helper |

Mobile / desktop:
| Instead of | Use |
|---|---|
| Custom share UI | System share sheet (Web Share API, `Share` in RN, `ShareLink` in SwiftUI) |
| Custom file dialogs | OS file picker via the framework's dialog plugin |
| Hand-rolled secure storage | Keychain / Keystore / Credential Manager via an existing plugin |
| Custom auth UI for OAuth | System browser session (ASWebAuthenticationSession / Custom Tabs) |
| Bespoke updater | Tauri updater plugin / electron-updater / store updates |

## 3. Over-build traps

Stop and simplify when you notice:
- A config system for a value that has one setting.
- A plugin architecture with one plugin.
- A generic `Repository<T>` wrapping one table.
- State management library for state that lives in one component.
- An "abstraction layer" over a library you use in one place.
- Retry/backoff/circuit-breaker logic around a call that runs once at startup.
- Writing a component the design system already has.

## 4. Never cut

Lazy means *less code*, not *less care*. Keep, always:
- Input validation at trust boundaries and error handling that tells the user what happened.
- Authz checks, output encoding, CSRF protection, secure storage of secrets.
- Accessibility: labels, focus order, keyboard support, contrast, reduced motion.
- One runnable check for each non-trivial branch.
- Cleanup of listeners, timers, subscriptions (memory leaks are bugs).

## 5. Reuse before writing

1. Read `.zennox/GRAPH_REPORT.md` (build it with `project_graph.py` if stale). God nodes are
   where shared utilities usually live.
2. `memory.py search "<concept>"` for past decisions ("we chose zod", "dates are UTC").
3. Grep for the verb, not the noun: `format`, `parse`, `validate`, `fetch`, `debounce`.
4. If two near-duplicates exist, extend the better one; don't add a third.

## 6. Review and audit modes

**Review (a diff):** for each hunk ask — could a higher rung have done this? Output:
```
[TRIM]  src/utils/date.ts:1-48  — replace with Intl.DateTimeFormat (rung 2), −45 lines
[KEEP]  src/api/client.ts:30    — retry needed: endpoint is flaky (ADR-007)
[RISK]  src/forms/Signup.tsx    — removed lib also did email normalisation; add .trim().toLowerCase()
```

**Audit (the repo):** rank the biggest wins: unused dependencies (`depcheck`, `knip`,
`cargo udeps`), dead exports (graph orphans), duplicated helpers, components that re-implement
native elements, oversized bundles. Report only; don't edit in audit mode.

## 7. Debt ledger

Every deliberate shortcut gets logged the moment you take it:
```
python3 scripts/memory.py add --type debt --title "No pagination on /notes" \
  --body "Fine below ~500 notes. Add cursor pagination before public launch." --tags api,perf
```
`/zennox debt` lists them (`memory.py list --type debt`). Review the ledger before each `ship`.

## 8. Measuring gain

When the user asks what was saved (`/zennox gain`), report honestly with what you can measure:
lines added vs a reasonable naive approach (state it's an estimate), dependencies avoided,
bundle size delta (from the build), files read vs. files in repo (context saved). Don't invent
percentages.
