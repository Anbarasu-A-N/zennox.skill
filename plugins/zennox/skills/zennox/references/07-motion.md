# 07 — Motion (Framer Motion → Motion)

Framer Motion is now published as **Motion** (`motion` package, React API under
`motion/react`). The old `framer-motion` package name still works in many projects; match
what the repo already uses. Check motion.dev for current API before using newer features.

## Contents
1. When to animate (and when CSS is enough)
2. Timing and easing tokens
3. Core patterns (React)
4. Layout and shared-element transitions
5. Scroll-linked motion
6. Gestures
7. Performance and bundle size
8. Accessibility
9. Native equivalents

---

## 1. When to animate

Motion must explain something: where an element came from, what changed, what is
interactive, or what to look at. If it explains nothing, delete it.

Ladder first: CSS transitions, `@starting-style` (enter animations), CSS scroll-driven
animations and the View Transitions API cover a lot with zero JS. Reach for Motion when you
need exit animations, layout animation, gesture physics, orchestration or springs.

## 2. Timing and easing tokens (defaults; tune per DESIGN.md)

| Token | Value | Use |
|---|---|---|
| `--dur-instant` | 100ms | Hover colour, press feedback |
| `--dur-fast` | 150–200ms | Small UI: toggles, tooltips, menus |
| `--dur-base` | 250–300ms | Panels, cards, modals entering |
| `--dur-slow` | 400–500ms | Page-level, large surfaces |
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | Entering |
| `--ease-in` | `cubic-bezier(0.64, 0, 0.78, 0)` | Exiting (exit ≈ 70–80% of enter duration) |
| spring snappy | `{ type: "spring", stiffness: 500, damping: 30 }` | Buttons, toggles |
| spring smooth | `{ type: "spring", stiffness: 260, damping: 26 }` | Panels, layout |
| spring bouncy | `{ type: "spring", bounce: 0.35, duration: 0.6 }` | Playful brands only |

Stagger lists by 30–60ms per item, capped at ~8 items (then animate the rest together).

## 3. Core patterns

```tsx
import { motion, AnimatePresence, MotionConfig } from "motion/react";

// Respect OS reduced-motion setting app-wide
<MotionConfig reducedMotion="user">{children}</MotionConfig>

// Enter / exit
<AnimatePresence>
  {open && (
    <motion.div
      key="panel"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 4 }}
      transition={{ type: "spring", stiffness: 260, damping: 26 }}
    />
  )}
</AnimatePresence>

// Orchestrated list
const list = { show: { transition: { staggerChildren: 0.04 } } };
const item = { hidden: { opacity: 0, y: 6 }, show: { opacity: 1, y: 0 } };
<motion.ul variants={list} initial="hidden" animate="show">
  {items.map(i => <motion.li key={i.id} variants={item}>{i.name}</motion.li>)}
</motion.ul>
```

## 4. Layout and shared elements

```tsx
<motion.div layout />                       // animates size/position changes automatically
<motion.div layoutId={`card-${id}`} />      // shared element between list and detail views
```
Wrap siblings that change together in `<LayoutGroup>`. Use `layout="position"` when only
position should animate (avoids text stretching). Add `layout` to children whose aspect ratio
changes, or scale-correct with `layoutDependency`.

## 5. Scroll-linked motion

```tsx
import { useScroll, useTransform, motion } from "motion/react";
const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
const y = useTransform(scrollYProgress, [0, 1], [40, -40]);
<motion.section ref={ref} style={{ y }} />

<motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true, amount: 0.3 }} />
```
Keep parallax subtle (≤ 40px) on product surfaces; never scroll-jack.

## 6. Gestures

```tsx
<motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} />
<motion.div drag="x" dragConstraints={{ left: -120, right: 0 }} dragElastic={0.1}
            onDragEnd={(_, info) => info.offset.x < -80 && onDelete()} />
```
Hover effects only on devices that hover: guard with `@media (hover: hover)` in CSS or check
pointer type. Every drag gesture needs a non-drag alternative (button) for accessibility.

## 7. Performance and bundle size

- Animate `transform` and `opacity` only; avoid animating `width/height/top/left` (use `layout`).
- Use `LazyMotion` with `domAnimation` and the lightweight `m` component to cut bundle size
  when you only need basic animations; load `domMax` only for layout/drag.
- Prefer motion values (`useMotionValue`, `useTransform`) for high-frequency updates; they
  bypass React re-renders.
- Profile on a mid-range Android phone, not your laptop. Target 60fps; drop effects that don't
  hold it.

## 8. Accessibility

- `MotionConfig reducedMotion="user"` globally, plus `useReducedMotion()` for bespoke cases:
  replace movement with opacity or nothing.
- No flashing more than 3 times per second.
- Never hide essential information behind motion (content must be present without animation).
- Autoplaying motion longer than 5 seconds needs a pause control.

## 9. Native equivalents

| Platform | Tooling |
|---|---|
| SwiftUI | `withAnimation(.spring(...))`, `matchedGeometryEffect`, `PhaseAnimator`, `KeyframeAnimator`, `.contentTransition`, SF Symbol effects |
| Jetpack Compose | `animate*AsState`, `AnimatedVisibility`, `updateTransition`, shared element transitions |
| React Native | Reanimated (worklets on UI thread), Moti for a Motion-like API, Layout Animations |
| Flutter | Implicit animations (`AnimatedContainer`), `Hero`, `flutter_animate` |
