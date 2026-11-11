# DESIGN.md — <Product name>

> Source of truth for how this product looks and feels. Coding agents: follow this file for
> every new screen; propose changes here before deviating.

Design Read: <product> for <audience>, <brand|product> surface, <visual language>, <stack>.
Dials: Variance <1-10> · Motion <1-10> · Density <1-10>

## 1. Visual theme & atmosphere
<!-- 3–5 sentences: mood, references in words (not brands to copy), what it must never feel like. -->

## 2. Colour palette & roles
| Role | Light (OKLCH) | Dark (OKLCH) | Use |
|---|---|---|---|
| --bg | oklch(98.5% 0.006 85) | oklch(17% 0.01 85) | Page background |
| --surface | oklch(100% 0 0) | oklch(21% 0.012 85) | Cards, panels |
| --text | oklch(22% 0.015 85) | oklch(93% 0.01 85) | Body text |
| --text-muted | oklch(45% 0.015 85) | oklch(72% 0.012 85) | Secondary text |
| --border | oklch(90% 0.008 85) | oklch(30% 0.01 85) | Hairlines |
| --accent | oklch(58% 0.16 35) | oklch(70% 0.14 35) | Primary action, links |
| --focus | oklch(62% 0.18 250) | oklch(72% 0.15 250) | Focus ring |
| --success / --warning / --danger | … | … | Meaning only |

## 3. Typography
- Display: <family>, weights <…>; Text: <family>; Mono: <family>
- Scale (ratio <1.25>): 12 · 14 · 16 · 20 · 25 · 31 · 39 · 49
- Body 16–18px, line-height 1.5, measure 60–72ch; display line-height 1.05, tracking -0.02em
- Numbers in tables: tabular-nums

## 4. Component styling
- Buttons: <radius>, <height 40/44>, primary = accent fill, secondary = border, tertiary = text
- Inputs: label above, 44px height, 1px border, focus ring 2px --focus offset 2px
- Cards: <border vs shadow>, radius <…>, padding <…>
- Icons: <Lucide/Phosphor/SF Symbols>, <1.5px> stroke, sized to text cap height
- States: hover, active, focus-visible, disabled, loading for every interactive element

## 5. Layout principles
- Macrostructure: <from library>
- Grid: <12-col / 4-col mobile>, max content width <1200px>, gutters <24px>
- Spacing scale: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96

## 6. Depth & elevation
- Level 0 flat · Level 1 hairline border · Level 2 soft shadow (popover) · Level 3 modal + scrim
- Radii: <small 6 · medium 10 · large 16> (concentric when nested)

## 7. Do's and don'ts
- Do: <…>
- Don't: purple-pink gradients, emoji icons, equal three-card grids by default, centered long paragraphs, glow everywhere

## 8. Responsive behaviour
- Mobile-first; breakpoints ~640 / 960 / 1280 (content-driven)
- Touch targets ≥ 44px; primary mobile action in thumb zone; safe areas respected
- Desktop: keyboard shortcuts for frequent actions; hover reveals are enhancements only

## 9. Agent prompt guide
- "Build <screen> following DESIGN.md: <macrostructure>, density <n>, use existing components from packages/ui."
- Motion tokens: fast 180ms, base 260ms, ease-out cubic-bezier(0.22,1,0.36,1); honour reduced motion.
