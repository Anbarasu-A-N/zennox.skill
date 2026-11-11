# Changelog

All notable changes to Zennox are listed here. Versions follow [SemVer](https://semver.org).

## [1.0.1] — 2026-11-11

- Fix CI on Windows: manifest check moved from an inline shell command (broke in PowerShell) into the Python tests.
- Fix `security_scan.py` skipping the `.env` check when the project sits inside a parent folder named like `build`, `env`, `out` or `vendor`.
- Fix `detect_env.py` crashing on Windows when a tool prints non-UTF-8 text (for example
  `©` in a Windows code page) — this was the cause of the failing Windows CI jobs.
- `detect_env.py` now probes tools in parallel with a 5-second limit, resolves Windows `.cmd`
  shims (`npm`, `pnpm`, `yarn`), can't be hung by a slow tool, and has a `--no-versions` flag.
- Add `tools/build_skill.py`: builds a byte-identical `zennox.skill` on any OS, and
  `--check` reports whether the committed package is out of date. CI uses it.
- Add `.gitattributes` so files keep LF line endings on Windows checkouts.
- Add tests for manifests, SKILL.md front matter, reference links, the `.env` fix, CRLF line
  endings, misbehaving tools, and the committed package staying in sync (14 tests).

## [1.0.0] — 2026-11-11

First public release by ANBARASU A N.

- One skill combining the workflows of 14 popular agent skills (see `references/attribution.md`).
- 21 modes, including `full` (whole lifecycle in one run) and `help`; modes can be chained.
- 13 reference guides: lifecycle, cross-platform architecture and OS-specific dependencies,
  minimal code, context/memory/cost, design system, Apple HIG and Liquid Glass, Motion,
  image-to-Three.js, security, Playwright testing, DevOps, networking/performance, extras
  (accessibility, i18n, privacy, data, analytics, AI features).
- 5 stdlib-only Python scripts: `detect_env`, `project_graph`, `memory`, `slop_check`, `security_scan`.
- 6 templates: DESIGN.md, SPEC.md, ADR, CI matrix, Playwright config, Tauri capabilities.
- Claude Code plugin marketplace manifest; self-tests on Windows, macOS and Linux.
