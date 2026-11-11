# Attribution — where each idea came from

Zennox is written and maintained by **ANBARASU A N** (https://github.com/Anbarasu-A-N/zennox.skill).

Zennox is an original synthesis. It re-expresses the *ideas* of the projects below in new
words and new stdlib scripts; it does not bundle their code or text. If you want the full
original behaviour (hooks, dashboards, larger databases, live browser modes), install the
original project. Licences listed are as reported by the projects at time of writing — check
each repository before redistributing anything from it.

| Source | What Zennox took | Where it lives here |
|---|---|---|
| ponytail (DietrichGebert/ponytail, MIT) | Reuse-first "laziest senior dev" ladder; keep safety guards; review/audit/debt/gain verbs | SKILL.md rule 1, `03-minimal-code.md`, `memory.py --type debt` |
| OmniRoute (diegosouzapw/OmniRoute, MIT) | One gateway endpoint, cost-optimised routing, fallback combos, circuit breaker / key cooldown / model lockout, compression | `04-context-memory-cost.md` §3 (legitimate routing concepts only) |
| graphify (Graphify-Labs/graphify) | Build a queryable graph of the repo and read its report before grepping; god nodes and communities; hash cache | `project_graph.py`, `04-context-memory-cost.md` §1 |
| agent-skills (addyosmani/agent-skills) | Define → Plan → Build → Verify → Review → Ship with gates; five-axis review; Prove-It bug pattern | SKILL.md §2, `01-lifecycle.md` |
| claude-mem (thedotmack/claude-mem) | Persistent cross-session memory with progressive, three-layer, token-aware retrieval | `memory.py`, `04-context-memory-cost.md` §2 |
| img2threejs (img2threejs/img2threejs) | Suitability gate, spec before code, pass-by-pass procedural sculpting, vision review loop, Group factory output | `08-3d-threejs.md` |
| taste-skill (Leonxlnx/taste-skill, MIT) | Brief-first "Design Read", explicit dials, anti-slop ban list, distinct style registers | `05-design-system.md` §2–3, §5, §11 |
| impeccable (pbakaus/impeccable, Apache-2.0) | Seven craft dimensions (type, colour/contrast in OKLCH, spatial, motion, interaction, responsive, UX writing); polish/distill/bolder/quieter… commands; project design context | `05-design-system.md` §6–9, §12 |
| awesome-design-md (VoltAgent/awesome-design-md) | DESIGN.md as portable, agent-readable design system; nine-section format | `05-design-system.md` §10, `assets/DESIGN.template.md` |
| hallmark (Nutlope/hallmark, MIT) | Default/audit/redesign/study verbs; macrostructure before theme; pre-ship slop gates; design log to avoid repeating structures; implementation safety rail | `05-design-system.md` §1–2, §4, §11 |
| ui-ux-pro-max-skill (nextlevelbuilder, MIT) | Style, palette, font-pairing and product-type reasoning library; master + page-override design system | `05-design-system.md` §5–7 |
| Framer Motion / Motion (motion.dev) | Animation API patterns, springs, layout animation, reduced motion, LazyMotion | `07-motion.md` |
| Apple HIG / Liquid Glass design skills (e.g. apple-hig-expert and Liquid Glass skills) | HIG principles, Liquid Glass control-layer rules, platform navigation, HIG audit with confidence tags | `06-apple-platform.md` |
| Playwright (microsoft/playwright) | Cross-browser + device projects, web-first assertions, traces, visual and a11y testing, Electron automation | `10-testing-playwright.md`, `assets/playwright.config.ts` |
| Anthropic frontend-design skill | The original "avoid generic AI aesthetics" brief that several of the above build on | `05-design-system.md` |
