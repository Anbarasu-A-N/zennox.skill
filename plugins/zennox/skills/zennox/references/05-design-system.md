# 05 — Design System: Taste, Structure, Tokens, Slop Gates

Goal: UIs that look *made*, not *generated*. This merges five approaches — a brief-first
design read with dials, macrostructure-before-styling, deep craft references across seven
dimensions, a searchable style/palette/type library, and portable DESIGN.md files — into one
flow.

## Contents
1. Verbs (what the user can ask for)
2. The design flow
3. Dials
4. Macrostructure library
5. Style library (pick one register, commit to it)
6. Type pairings
7. Colour system (OKLCH)
8. Spacing, layout, responsive
9. Interaction & UX writing
10. DESIGN.md format and `study`
11. Slop gates (pre-ship checklist)
12. Craft commands (polish, distill, bolder, quieter …)

---

## 1. Verbs

| Verb | Behaviour |
|---|---|
| *(default)* build | New UI from a brief → full flow below |
| `study <image or URL>` | Extract design DNA (macrostructure, type pairing, colour anchor, density, motion) into DESIGN.md. Capture *principles*, not pixels: never clone a brand's logo, wordmark, illustrations or proprietary assets, and don't recreate paid templates. |
| `redesign` | Keep copy and information architecture; change macrostructure and visual fingerprint |
| `audit` | Score against slop gates + a11y; ranked punch list; **no edits** |
| `polish` / `distill` / `bolder` / `quieter` / `colorize` / `animate` / `adapt` / `harden` | Focused craft passes (§12) |
| `init` | Write PRODUCT.md (audience, register, voice, anti-references) and DESIGN.md |

If the user attaches an image or URL without a verb, ask once: *study it, or use it as loose
reference for a fresh build?*

Implementation safety rail: in an existing project, touch only the files in scope. Don't swap
the CSS framework, rename components, or restyle unrelated pages.

## 2. The design flow

1. **Pre-scan.** Read DESIGN.md, PRODUCT.md, existing tokens/theme files, component library,
   and `.zennox/design-log.json` (previous runs). If DESIGN.md exists, it is the source of
   truth; deviate only when the user asks.
2. **Context gate.** You need: product, audience, register (*brand* vs *product* surface),
   platforms, stack. Ask for anything missing that changes the outcome; assume the rest.
3. **Design Read** (say it): `Design Read: invoicing tool for freelancers, product surface,
   calm Swiss-editorial, Next.js + Tailwind.`
4. **Dials** (say them): `Variance 4 · Motion 3 · Density 7.`
5. **Macrostructure** from §4. Don't repeat the one logged for the previous run in this project
   unless the user wants consistency across pages (then reuse on purpose).
6. **Style register** from §5 + **type pairing** from §6 + **colour anchor** from §7.
7. **Write tokens into DESIGN.md** (`assets/DESIGN.template.md`). Generate CSS variables /
   Tailwind theme / platform constants from it.
8. **Build** with real content (no lorem ipsum in hero, headings or buttons). Include empty,
   loading and error states for every data view.
9. **Gate:** run `python3 scripts/slop_check.py <path>`; fix all HIGH; justify any MEDIUM you
   keep. Walk §11 by eye for what the scanner can't see.
10. **Log** the macrostructure, register and dials in `.zennox/design-log.json` (append
    `{"date","page","macrostructure","register","dials"}`).

Brand surfaces (landing, portfolio, campaign) get more variance and motion. Product surfaces
(dashboards, settings, tools, data tables) get restraint, density and speed — personality
lives in type, colour and microcopy, not layout tricks.

## 3. Dials

| Dial | 1–3 | 4–7 | 8–10 |
|---|---|---|---|
| **Variance** (layout risk) | Conventional grid, predictable | Asymmetry, one surprising section | Broken grid, overlap, editorial scale jumps |
| **Motion** | State feedback only | Entrance choreography, hover depth | Scroll-driven scenes, physics, 3D |
| **Density** | Airy, one idea per screen | Balanced | Information-dense (pro tools, trading, admin) |

Reduced-motion users always get Motion ≤ 2 regardless of the dial.

## 4. Macrostructure library

Pick the skeleton before any colour. Examples (not templates — adapt):

| Macrostructure | Fits |
|---|---|
| Editorial long-read: oversized headline, narrow measure, pull quotes, margin notes | Essays, studios, thought leadership |
| Split-screen persistent: left fixed narrative, right scrolling proof | Product launches, case studies |
| Index/catalogue: dense typographic list, hover previews | Portfolios, archives, directories |
| Bento with hierarchy: one dominant tile, deliberate size steps (not equal cards) | Feature overviews |
| Product-first theatre: live interactive demo above the fold | Dev tools, editors, calculators |
| Document/spec sheet: numbered sections, tables, mono accents | Technical products, APIs |
| Timeline/narrative: vertical story with sticky chapter markers | Company, history, onboarding |
| Command-centre: sidebar + toolbar + dense panes | Dashboards, admin, pro tools |
| Inbox / master-detail | Messaging, CRM, mail, tickets |
| Canvas + inspector | Editors, design/3D tools |
| Feed + composer | Social, notes, activity |
| Wizard / focused flow: one task per screen, progress | Onboarding, checkout, forms |

The generic fallback (centered hero → logo strip → three equal feature cards → testimonial
carousel → pricing → CTA) is allowed only if the user explicitly asks for it.

## 5. Style library

Commit to one register; mixing three is how slop happens.

| Register | Signals | Good for |
|---|---|---|
| Swiss / International | Strict grid, grotesk, flush-left, red or black accent | Tools, agencies, data |
| Editorial serif | Large serif display, generous measure, rules, small caps | Media, writing, premium services |
| Quiet minimal | Near-monochrome, one accent, lots of space, fine borders | SaaS product surfaces |
| Industrial / brutalist | Mono type, visible structure, hard edges, raw colour blocks | Dev tools, hardware, music |
| Warm tactile | Paper tones, grain, soft shadows, rounded humanist type | Consumer, wellness, food |
| Technical dark | Deep neutral, mono accents, crisp 1px lines, sparse glow | Infra, security, AI tools |
| Playful geometric | Bold primaries, shapes, chunky radius, bouncy motion | Kids, games, creative tools |
| Luxury restraint | High contrast serif, black/ivory, tiny UI, slow motion | Fashion, hospitality |
| Bento modern | Tiles of varied size, strong hierarchy, subtle depth | Feature showcases |
| Glass / material (Apple-like) | Translucent chrome over content, system type | Apple-platform apps (see 06) |
| Neo-retro | Pixel or 80s/90s type, CRT or print artefacts — used with restraint | Games, nostalgia brands |
| Data-dense pro | Tabular numerals, compact rows, muted palette, colour = meaning | Finance, analytics, ops |

Industry hints (starting points, not rules): health → calm, high-legibility, trustworthy
blues/greens, never alarming reds except for alerts; finance → restraint, tabular figures,
strong contrast; kids → high saturation, large targets; dev tools → dark-friendly, mono
accents, dense; luxury → space and type over colour.

## 6. Type pairings

Free (Google Fonts / open licences). Use `font-display: swap`, subset, and self-host for
performance and privacy. Always give a system fallback stack.

| Display | Text | Mood |
|---|---|---|
| Fraunces | Inter Tight or Source Sans 3 | Warm editorial |
| Instrument Serif | Instrument Sans | Elegant, modern |
| Space Grotesk | IBM Plex Sans | Technical, friendly |
| Bricolage Grotesque | Figtree | Playful-confident |
| DM Serif Display | DM Sans | Classic contrast |
| Syne | Manrope | Art/creative |
| Newsreader | Public Sans | News, civic |
| Archivo (expanded weights) | Archivo | Industrial |
| JetBrains Mono / IBM Plex Mono | (as accent) | Dev tools |
| Playfair Display | Lato | Luxury (use sparingly; very common) |
| System UI stack | — | Product surfaces where speed matters |

Rules: modular scale (1.2–1.333 for product, 1.414–1.618 for brand); body 16–18px; measure
45–75ch; line-height 1.4–1.6 body, 1.0–1.15 display; tighten tracking on large display text;
`font-variant-numeric: tabular-nums` for numbers in tables. Two families maximum.

## 7. Colour system (OKLCH)

- Define colours in OKLCH so lightness steps are perceptually even; generate ramps by varying
  L with modest C.
- **Tinted neutrals:** give greys a hint of the brand hue (C ≈ 0.005–0.02) instead of pure grey.
- Roles, not names: `--bg`, `--surface`, `--surface-2`, `--text`, `--text-muted`, `--border`,
  `--accent`, `--accent-contrast`, `--success`, `--warning`, `--danger`, `--focus`.
- One accent, used for primary action and focus. Semantic colours only for meaning.
- Contrast: WCAG AA minimum (4.5:1 body, 3:1 large text and UI components). Check both themes.
- Dark mode is its own palette, not an inversion: raise surface lightness for elevation,
  reduce accent chroma slightly, avoid pure black backgrounds for long reading.

```css
:root {
  --bg: oklch(98.5% 0.006 85);  --text: oklch(22% 0.015 85);
  --accent: oklch(58% 0.16 35); --focus: oklch(62% 0.18 250);
}
@media (prefers-color-scheme: dark) {
  :root { --bg: oklch(17% 0.01 85); --text: oklch(93% 0.01 85); --accent: oklch(70% 0.14 35); }
}
```

## 8. Spacing, layout, responsive

- 4px base, scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, 128. Use fewer steps, used consistently.
- Proximity shows grouping: space inside a group < space between groups.
- Mobile-first CSS; fluid type and space with `clamp()`; container queries for components.
- Breakpoints from content, not devices; typically ~640 / 960 / 1280.
- Touch targets ≥ 44×44 pt (Apple) / 48×48 dp (Material); 8px between adjacent targets.
- Safe areas on phones (`env(safe-area-inset-*)`); thumb zone for primary mobile actions.
- Desktop: keyboard shortcuts for frequent actions, hover states, right-click where native.

## 9. Interaction & UX writing

- Every interactive element: default, hover, active, focus-visible, disabled, loading.
- Focus: visible ring with ≥ 3:1 contrast, never `outline: none` without a replacement.
- Forms: label above field, inline validation on blur, error text says how to fix it.
- Loading: skeletons for layout-stable content; spinners only for < 1s unknown waits;
  optimistic UI for safe actions.
- Empty states: explain what goes here and offer the first action.
- Buttons say what happens ("Send invoice"), not "Submit"/"OK". Errors: what happened, why,
  what to do. No blame, no jargon, no exclamation marks.
- Confirm destructive actions, or better: make them undoable.

## 10. DESIGN.md format and `study`

DESIGN.md is a plain-markdown design system that any coding agent can follow. Use the nine
sections in `assets/DESIGN.template.md`:

1. Visual theme & atmosphere 2. Colour palette & roles 3. Typography 4. Component styling
5. Layout principles 6. Depth & elevation 7. Do's and don'ts 8. Responsive behaviour
9. Agent prompt guide (how to ask for new screens in this style).

Community collections of DESIGN.md files describing well-known products' design languages
exist (e.g. the awesome-design-md repo). Use them as *inspiration for principles* — density,
type contrast, colour restraint — then write your own tokens. Don't ship another company's
brand identity as yours.

`study` procedure: identify macrostructure → measure type scale and pairing → sample palette
and derive roles → note radius, border, shadow language → note motion style → write DESIGN.md
in your own words with your own token values.

## 11. Slop gates (pre-ship)

`slop_check.py` catches the starred items automatically; check the rest by eye.

Visual
- ★ Purple/indigo-to-pink or blue-to-purple gradient as the main brand move
- ★ Emoji used as icons in UI chrome (use an icon set: Lucide, Phosphor, SF Symbols)
- ★ Inter/Roboto/Arial as the *only* font with no deliberate pairing
- Equal-size three-card feature grid as the default section
- Glassmorphism or glow everywhere instead of in one place
- Drop shadows on everything; inconsistent radii (e.g. 4, 6, 8, 12, 16 all in use)
- Centred text for paragraphs longer than two lines
- Stock "abstract 3D blob" hero art

Copy
- "Unlock", "Elevate", "Seamless", "Supercharge", "Revolutionize", "Empower" in headlines
- Fake metrics and testimonials; lorem ipsum in visible places
- Em-dash-heavy, rule-of-three marketing cadence in every sentence

Interaction & a11y
- ★ `outline: none` without a focus replacement
- ★ Animations with no `prefers-reduced-motion` handling
- ★ Tap targets under 44px; ★ `user-scalable=no` / `maximum-scale=1`
- ★ Images without `alt`; icon-only buttons without accessible names
- Hover-only affordances on touch devices
- Missing empty / loading / error states

Engineering
- ★ Inline `style=` sprawl instead of tokens; hard-coded hex values outside the token file
- Layout shift from late-loading fonts/images (reserve space: `width`/`height`, `aspect-ratio`)
- Huge JS for static content

## 12. Craft commands

| Command | Do |
|---|---|
| `polish` | Fix alignment, spacing rhythm, type scale steps, optical sizes, states; no structural change |
| `distill` | Remove elements until each screen has one primary job; cut decoration that carries no meaning |
| `bolder` | Increase scale contrast, stronger accent use, more decisive layout |
| `quieter` | Reduce colour, motion and weight; more space; fewer competing focal points |
| `colorize` | Introduce or rework palette from a single anchor hue in OKLCH |
| `typeset` | Rework type pairing, scale, measure, leading |
| `animate` | Add purposeful motion per `07-motion.md` |
| `adapt` | Make it work across breakpoints, input types (touch/mouse/keyboard) and platforms |
| `harden` | States, errors, edge-case content (long names, RTL, 0/1/1000 items), a11y |
| `critique` | Opinionated review: what works, what doesn't, top 3 changes — no edits |
