# Zennox

**One skill to plan, design, build, secure, test and ship cross-platform apps — web, PWA,
iOS, Android, Windows, macOS and Linux.**

Created by **ANBARASU A N** · MIT licence · v1.0.1

Zennox gives an AI coding agent (Claude and others that read `SKILL.md` files) a complete,
senior-level way of working: it writes the least code that solves the problem, follows a
spec → plan → build → test → review → ship workflow with real quality gates, keeps a map and a
memory of your project to save tokens, and produces interfaces that don't look AI-generated.

It brings together the ideas of 14 popular agent skills — ponytail, OmniRoute, graphify,
agent-skills, claude-mem, img2threejs, taste-skill, impeccable, awesome-design-md, hallmark,
ui-ux-pro-max, Framer Motion, Apple HIG design skills and Playwright — rewritten as **one**
skill, so you install one thing instead of fourteen. See
[attribution](plugins/zennox/skills/zennox/references/attribution.md).

---

## What it can do

| Area | What you get |
|---|---|
| Planning | One-page SPEC.md from a short interview, architecture decisions (ADRs), vertical slices |
| Cross-platform | Stack choice (PWA, Tauri, Electron, Capacitor, React Native/Expo, Flutter, KMP, native), monorepo layout, platform adapters, OS-specific dependency rules for 10 ecosystems |
| Minimal code | A "reuse first" ladder: platform features → existing deps → existing code → new code |
| Tokens & cost | Codebase graph, cross-session project memory, model routing and budgets |
| Design | Design Read + dials, macrostructures, style registers, type pairings, OKLCH colour, DESIGN.md, anti-"AI slop" checks |
| Apple & motion | Apple HIG and Liquid Glass rules, Motion (Framer Motion) patterns with reduced-motion support |
| 3D | Rebuild an object from one image as editable, procedural Three.js code |
| Security | Threat model, OWASP-aligned checklists, Electron/Tauri/mobile hardening, supply chain |
| Testing | Playwright across Chromium, WebKit, Firefox and mobile devices; visual and accessibility tests |
| DevOps | CI matrix for every platform, signing/notarization, stores, auto-update, rollout and rollback |
| Extras | Accessibility (WCAG 2.2), i18n/RTL, privacy and store compliance, data and migrations, AI-feature safety |

Plus **5 helper scripts** (Python 3.10+, standard library only — nothing to install) and
**6 templates** (DESIGN.md, SPEC.md, ADR, CI matrix, Playwright config, Tauri capabilities).

---

## Install

### Claude.ai or the Claude desktop/mobile app

1. Download `zennox.skill` from the [latest release](https://github.com/Anbarasu-A-N/zennox.skill/releases/latest)
   or [straight from the repo](https://github.com/Anbarasu-A-N/zennox.skill/raw/main/zennox.skill)
   (it's a ZIP file; rename to `zennox.zip` if your browser needs it).
2. Make sure **Code execution and file creation** is on in **Settings → Capabilities**.
3. Go to **Customize → Skills**, click **+**, choose **Create skill → Upload a skill**, and
   upload the file.

Skill settings move occasionally; if these menus look different, see
[Anthropic's skills help page](https://support.claude.com/en/articles/12512180-using-skills-in-claude).

### Claude Code — as a plugin (recommended, easy updates)

```
/plugin marketplace add Anbarasu-A-N/zennox.skill
/plugin install zennox@zennox
```

Update later with `/plugin marketplace update zennox`.

### Claude Code — as a plain skill

```bash
git clone https://github.com/Anbarasu-A-N/zennox.skill.git
# for all your projects:
cp -r zennox.skill/plugins/zennox/skills/zennox ~/.claude/skills/zennox
# or just one project:
cp -r zennox.skill/plugins/zennox/skills/zennox .claude/skills/zennox
```

On Windows (PowerShell): `Copy-Item -Recurse zennox.skill\plugins\zennox\skills\zennox $HOME\.claude\skills\zennox`

### Other agents (Cursor, Codex, Gemini CLI, Copilot, OpenCode…)

```bash
npx skills add Anbarasu-A-N/zennox.skill
```

The skills CLI looks for `SKILL.md` files anywhere in the repo. If your agent or CLI version doesn't pick it up, copy the `plugins/zennox/skills/zennox` folder into the agent's skills directory.

---

## Quick start

Zennox switches on by itself for cross-platform app work. To choose a mode, start your message
with `zennox`:

```
zennox help                         # list every mode
zennox full                         # the whole lifecycle: idea → shipped app
zennox audit                        # score code, design, security, performance (no edits)
zennox design + test                # chain modes
```

**Use everything at once** with `zennox full`: it interviews you, writes the spec and plan,
designs, builds slice by slice with tests and reviews, hardens, and prepares the release —
pausing for your approval on the spec, the plan, and any production deploy.

**Use parts separately** with any of the 21 modes:

| Plan | Design | Build | Check | Release |
|---|---|---|---|---|
| `init` `spec` `plan` | `design` `study` `redesign` `polish` `3d` | `build` `debug` `optimize` | `test` `review` `audit` `harden` | `ship` `remember` `debt` `gain` |

Full guide with examples for every mode, chaining, and standalone script use:
**[docs/USAGE.md](docs/USAGE.md)**

---

## Scripts (work without any AI)

```bash
Z=plugins/zennox/skills/zennox
python3 $Z/scripts/detect_env.py .                 # what can this machine build?
python3 $Z/scripts/project_graph.py .              # code map: hot files, cycles, dead code, layer leaks
python3 $Z/scripts/slop_check.py apps/web          # design and accessibility tells
python3 $Z/scripts/security_scan.py .              # secrets, unsafe settings, injection risks
python3 $Z/scripts/memory.py search "auth"         # project memory
```

All accept `--help`; scanners accept `--fail-on-high` for CI gates. Reports are written to
`.zennox/` inside the scanned project.

---

## Repository layout

```
zennox.skill/
├── .claude-plugin/marketplace.json        # lets Claude Code install from this repo
├── plugins/zennox/
│   ├── .claude-plugin/plugin.json
│   └── skills/zennox/                     # ← the skill itself
│       ├── SKILL.md                       # router: rules, modes, index
│       ├── references/                    # 13 guides + attribution
│       ├── scripts/                       # 5 stdlib Python helpers
│       └── assets/                        # 6 templates
├── docs/USAGE.md
├── tests/test_scripts.py                  # self-tests (Windows, macOS, Linux in CI)
├── tools/build_skill.py                   # builds zennox.skill on any OS
├── zennox.skill                           # ready-to-upload package for Claude.ai
├── .github/workflows/test.yml
├── CHANGELOG.md · CONTRIBUTING.md · LICENSE
└── README.md
```

---

## Development

```bash
python -m unittest discover -s tests -v     # 14 self-tests
python tools/build_skill.py                 # rebuild zennox.skill after changing the skill
python tools/build_skill.py --check         # is the committed zennox.skill up to date?
```

The tests fail if the committed `zennox.skill` doesn't match the source, so you can't forget
to rebuild it.

CI runs the tests on Windows, macOS and Linux with Python 3.10 and 3.13, then builds
`zennox.skill` as a downloadable artifact. Contributions are welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Notes

- Zennox's scanners are fast first-pass checks, not a replacement for a full security audit
  or SAST tools; it says so in its reports.
- Framework details change quickly; Zennox tells the agent to check current docs before
  pinning versions or quoting prices.
- Zennox is an independent project and is not affiliated with Anthropic or with the authors
  of the projects that inspired it.

## Licence

[MIT](LICENSE) © 2026 ANBARASU A N
