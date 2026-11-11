# 06 — Apple Platforms: HIG, Liquid Glass, Native Feel

Use for iOS, iPadOS, macOS, watchOS, tvOS, visionOS, and for web/cross-platform apps that
should *feel* at home on Apple devices. HIG content changes with each OS release; when a claim
matters (an API, a size, a review rule), verify against developer.apple.com/design/human-interface-guidelines.

## Contents
1. Principles
2. Liquid Glass (iOS 26 / macOS Tahoe generation)
3. Layout, sizes, typography
4. Navigation per platform
5. Platform-specific must-haves
6. Approximating Apple feel on web / cross-platform
7. HIG audit procedure

---

## 1. Principles

- **Hierarchy:** content first; controls and chrome recede and float above it.
- **Harmony:** shapes and motion echo the hardware (concentric corners, fluid motion).
- **Consistency:** use system components and behaviours; users already know them.
- Earlier HIG vocabulary still applies: clarity, deference, depth.

## 2. Liquid Glass

A translucent, refractive material for the **navigation/control layer** (tab bars, toolbars,
sidebars, sheets, floating buttons) that sits over content.

Rules:
- Glass goes on the control layer only. Never put glass on content (cards, list rows, body
  text containers).
- Don't stack glass on glass; group nearby glass elements so they can blend and morph.
- Keep legibility: test text and symbols over bright, dark and busy content; let the system
  handle vibrancy. Respect Reduce Transparency and Increase Contrast settings.
- Use the regular variant for most UI; the clear variant only over media where content must
  show through, with a dimming layer if needed.

SwiftUI (iOS 26+; check current docs for exact signatures):
```swift
Button("Add", systemImage: "plus") { add() }
    .buttonStyle(.glass)              // or .glassProminent for primary

GlassEffectContainer(spacing: 16) {   // lets nearby glass shapes blend/morph
    HStack { toolA.glassEffect(); toolB.glassEffect() }
}

Image("hero").backgroundExtensionEffect()   // extend content under sidebars/inspectors
```
UIKit: `UIGlassEffect` with `UIVisualEffectView`; AppKit: `NSGlassEffectView`. Standard bars,
tab views, sheets and toolbars adopt the material automatically when built with the new SDK —
prefer that over custom glass.

## 3. Layout, sizes, typography

- Minimum hit target **44×44 pt** (iOS/iPadOS); visionOS targets are larger (about 60 pt);
  watchOS uses full-width rows.
- Respect safe areas and layout margins; support every size class and both orientations on iPad.
- System font (SF Pro / SF Compact / New York) via text styles, never fixed sizes: use
  `.font(.body)`, `.headline`, `.largeTitle`… so **Dynamic Type** works. Test at the largest
  accessibility sizes.
- **SF Symbols** for icons, with matching weight to adjacent text; use symbol rendering modes
  (monochrome, hierarchical, palette) rather than custom PNGs.
- Semantic colours (`.primary`, `.secondary`, `Color(.systemBackground)`, tint) so light/dark
  and high-contrast work automatically.
- Corner radii should be concentric with the container/device.

## 4. Navigation per platform

| Platform | Primary pattern |
|---|---|
| iPhone | Tab bar (≤ 5 tabs) for top-level sections; navigation stack for drill-down; sheets for focused tasks |
| iPad | Sidebar (`NavigationSplitView`) that can collapse to tabs; multiple columns; pointer and keyboard support |
| macOS | Sidebar + content + optional inspector; full menu bar with standard menus and shortcuts; toolbar; resizable windows; Settings window (⌘,) |
| watchOS | Vertical page lists, Digital Crown scrolling, glanceable content, complications |
| visionOS | Windows, volumes, ornaments; gaze + pinch; keep content within comfortable field of view |
| tvOS | Focus engine, large type, top tab bar, remote-friendly |

## 5. Platform must-haves

- Dark mode, Dynamic Type, VoiceOver labels and traits, Reduce Motion, Reduce Transparency.
- Haptics for meaningful feedback only (`sensoryFeedback` in SwiftUI).
- macOS: every action reachable from the menu bar; standard shortcuts (⌘N, ⌘O, ⌘S, ⌘W, ⌘Z,
  ⌘F, ⌘,); drag and drop; undo.
- iOS: swipe-back gesture never blocked; pull-to-refresh where lists update; system share
  sheet; Sign in with Apple if you offer other third-party sign-in (check current App Review
  guideline wording).
- Privacy: purpose strings for every permission, asked at the moment of need, plus the app's
  privacy manifest and App Store privacy labels.

## 6. Approximating Apple feel on web / cross-platform

You can evoke the feel; don't copy Apple's trademarks or ship SF fonts outside Apple platforms
(their licence restricts that). Use the system stack, which renders SF on Apple devices:

```css
:root { font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }

.glass-bar {
  background: color-mix(in oklch, var(--bg) 60%, transparent);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid color-mix(in oklch, var(--text) 10%, transparent);
}
@supports not (backdrop-filter: blur(1px)) { .glass-bar { background: var(--surface); } }
@media (prefers-reduced-transparency: reduce) { .glass-bar { background: var(--surface); backdrop-filter: none; } }
```

- Springy, interruptible motion (see `07-motion.md`, spring presets).
- Large titles that collapse on scroll; grouped inset lists; sheets with detents on mobile.
- Respect platform conventions per OS in cross-platform apps: Material patterns on Android,
  Fluent/Win32 conventions on Windows (e.g. window controls on the right, Ctrl shortcuts),
  Apple patterns on Apple platforms. React Native and Flutter both expose the current platform
  so adapters can switch components.

## 7. HIG audit procedure

1. List screens and the platform(s) each targets.
2. For each: navigation pattern correct? hit targets ≥ 44 pt? Dynamic Type at max size?
   dark mode? contrast? VoiceOver order and labels? glass only on controls? reduced
   motion/transparency honoured?
3. Tag each finding with confidence: **verified** (measured in code/tool), **needs device
   test**, or **assumed**.
4. Output a ranked punch list with the HIG section to read for each.
