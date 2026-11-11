#!/usr/bin/env python3
"""Scan UI code for generic-AI design tells and basic a11y/UX defects.

Usage: python3 slop_check.py <path> [--fail-on-high] [--json]
Scans .html .htm .css .scss .sass .less .jsx .tsx .vue .svelte .astro
Writes .zennox/slop-report.json. Findings are prompts for judgement, not verdicts.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import state_dir, iter_files, line_of, read_text, rel, write_json  # noqa: E402

EXTS = [".html", ".htm", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx", ".vue", ".svelte", ".astro"]
MARKUP = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro"}
TOKEN_FILE = re.compile(r"(token|theme|variables|vars|palette|design|colors?)\.", re.I)

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]")
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
GRAD = re.compile(r"(linear|radial|conic)-gradient\(([^;{}]*)\)", re.I)
TW_GRAD = re.compile(r"\b(?:from|via|to)-(purple|violet|indigo|fuchsia|pink)-\d{2,3}\b")
SLOP_WORDS = re.compile(r"\b(unlock|elevate|seamless(ly)?|supercharge|revolutioni[sz]e|empower|unleash|"
                        r"next[- ]level|game[- ]chang\w*|cutting[- ]edge|effortless(ly)?)\b", re.I)
HEADING = re.compile(r"<(h1|h2|h3|title)\b[^>]*>(.*?)</\1>", re.I | re.S)
IMG_NO_ALT = re.compile(r"<img\b(?![^>]*\balt\s*=)[^>]*>", re.I)
IMG_NO_DIMS = re.compile(r"<img\b(?![^>]*\b(width|height)\s*=)(?![^>]*aspect)[^>]*>", re.I)
BUTTON = re.compile(r"<button\b([^>]*)>(.*?)</button>", re.I | re.S)
OUTLINE_NONE = re.compile(r"outline\s*:\s*(none|0)\b|\boutline-none\b", re.I)
FOCUS_STYLE = re.compile(r":focus-visible|:focus\b|focus-visible:|focus:ring|focus:outline|focus-ring", re.I)
ZOOM_BLOCK = re.compile(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b", re.I)
ANIM = re.compile(r"@keyframes|\banimation\s*:|\btransition\s*:|\banimate-\w+|\btransition-\w+", re.I)
REDUCED = re.compile(r"prefers-reduced-motion|motion-reduce:|motion-safe:|useReducedMotion|reducedMotion", re.I)
MOTION_LIB = re.compile(r"""from\s+['"](motion/react|framer-motion|motion)['"]""")
FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;}{]+)|fontFamily\s*:\s*[{\[]?([^}\]\n]+)", re.I)
GENERIC_FONTS = {"inter", "roboto", "arial", "helvetica", "helvetica neue", "sans-serif", "serif",
                 "system-ui", "-apple-system", "blinkmacsystemfont", "segoe ui", "ui-sans-serif",
                 "monospace", "ui-monospace", "inherit", "var", "apple color emoji", "noto sans"}
LOREM = re.compile(r"lorem ipsum", re.I)
VH100 = re.compile(r"\b100vh\b|\bh-screen\b|\bmin-h-screen\b")
RADIUS = re.compile(r"border-radius\s*:\s*(\d+(?:\.\d+)?)px", re.I)
SMALL_TW_TARGET = re.compile(r"<(button|a)\b[^>]*class(?:Name)?=[\"'{`][^\"'`]*\b(?:h|size)-(\d+(?:\.5)?)\b", re.I)
CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
SIZE_DECL = re.compile(r"(?:^|;)\s*(?:min-)?(height|width)\s*:\s*(\d+(?:\.\d+)?)px", re.I)
INLINE_STYLE = re.compile(r"\bstyle\s*=\s*(\{\{|\")")
TEXT_CENTER_P = re.compile(r"<p\b[^>]*class(?:Name)?=[\"'][^\"']*\btext-center\b", re.I)


def hue_of(hexcode: str) -> tuple[float, float, float]:
    h = hexcode.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ss, ll


def purple_pink(hexes: list[str]) -> bool:
    hits = [h for h in hexes if (lambda x: 250 <= x[0] <= 335 and x[1] > 0.35 and 0.25 < x[2] < 0.85)(hue_of(h))]
    return len(hits) >= 1 and len(hexes) >= 2


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path")
    ap.add_argument("--fail-on-high", action="store_true", help="exit 2 if any HIGH finding")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    root = Path(a.path).resolve()
    findings: list[dict] = []
    add = lambda sev, f, line, rule, msg: findings.append(  # noqa: E731
        {"severity": sev, "file": f, "line": line, "rule": rule, "message": msg})

    any_anim = any_reduced = any_focus = False
    motion_files: list[str] = []
    fonts: set[str] = set()
    radii: set[str] = set()
    outline_hits: list[tuple[str, int]] = []
    files = list(iter_files(root, EXTS))
    for p in files:
        t = read_text(p)
        f = rel(p, root)
        ext = p.suffix.lower()
        any_anim |= bool(ANIM.search(t))
        any_reduced |= bool(REDUCED.search(t))
        any_focus |= bool(FOCUS_STYLE.search(t))
        if MOTION_LIB.search(t):
            motion_files.append(f)
        for m in OUTLINE_NONE.finditer(t):
            outline_hits.append((f, line_of(t, m.start())))
        for m in ZOOM_BLOCK.finditer(t):
            add("HIGH", f, line_of(t, m.start()), "zoom-blocked", "Viewport blocks pinch-zoom; remove user-scalable=no / maximum-scale=1")
        for m in FONT_FAMILY.finditer(t):
            for fam in re.split(r"[,\[\]]", (m.group(1) or m.group(2) or "")):
                fam = fam.strip().strip("'\"` ").lower()
                if fam and not fam.startswith(("var(", "$", "theme(")):
                    fonts.add(fam)
        radii.update(RADIUS.findall(t))

        grads = list(GRAD.finditer(t))
        for m in grads:
            if purple_pink(HEX.findall(m.group(2))) or re.search(r"\b(purple|violet|indigo|fuchsia|magenta|pink)\b", m.group(2), re.I):
                add("MEDIUM", f, line_of(t, m.start()), "purple-gradient", "Purple/indigo/pink gradient — the most common AI-default brand move")
        tw = TW_GRAD.findall(t)
        if len(tw) >= 2:
            add("MEDIUM", f, line_of(t, TW_GRAD.search(t).start()), "purple-gradient", f"Tailwind purple/pink gradient stops ({', '.join(sorted(set(tw)))})")

        if not TOKEN_FILE.search(p.name):
            hexes = HEX.findall(t)
            if len(hexes) > 20:
                add("MEDIUM", f, 1, "hardcoded-colors", f"{len(hexes)} hard-coded hex colours; move to tokens (DESIGN.md → CSS vars)")
        for m in VH100.finditer(t):
            add("LOW", f, line_of(t, m.start()), "100vh", "100vh/h-screen jumps on mobile browsers; prefer 100dvh/100svh (min-h-dvh)")
            break

        if ext in {".css", ".scss", ".sass", ".less"} or "<style" in t:
            for rm in CSS_RULE.finditer(t):
                sel, body = rm.group(1), rm.group(2)
                if re.search(r"button|\.btn|icon-?button|\[role=.?button|\.chip|\.tab\b", sel, re.I):
                    for dm in SIZE_DECL.finditer(body):
                        if float(dm.group(2)) < 44:
                            add("MEDIUM", f, line_of(t, rm.start()), "small-target",
                                f"{sel.strip()[:40]} {dm.group(1)} {dm.group(2)}px < 44px touch target")
                            break

        if ext in MARKUP:
            for m in IMG_NO_ALT.finditer(t):
                add("HIGH", f, line_of(t, m.start()), "img-alt", "<img> without alt (use alt=\"\" for decorative images)")
            for m in IMG_NO_DIMS.finditer(t):
                add("LOW", f, line_of(t, m.start()), "img-dimensions", "<img> without width/height → layout shift (CLS)")
            for m in BUTTON.finditer(t):
                attrs, inner = m.group(1), m.group(2)
                text_only = re.sub(r"<[^>]+>", "", inner).strip()
                if "{" in inner or re.search(r"aria-label|aria-labelledby|title\s*=", attrs, re.I):
                    continue
                if not text_only:
                    add("HIGH", f, line_of(t, m.start()), "icon-button-name", "Icon-only button without aria-label")
            for m in SMALL_TW_TARGET.finditer(t):
                if float(m.group(2)) * 4 < 40:
                    add("MEDIUM", f, line_of(t, m.start()), "small-target", f"<{m.group(1)}> h/size-{m.group(2)} ≈ {float(m.group(2))*4:g}px < 44px touch target")
            for m in HEADING.finditer(t):
                w = SLOP_WORDS.search(re.sub(r"<[^>]+>", "", m.group(2)))
                if w:
                    add("MEDIUM", f, line_of(t, m.start()), "slop-copy", f"Generic marketing verb in heading: '{w.group(0)}'")
            for m in LOREM.finditer(t):
                add("MEDIUM", f, line_of(t, m.start()), "lorem", "Lorem ipsum in shipped markup"); break
            emo = [(line_of(t, m.start()), m.group(0)) for m in EMOJI.finditer(t)]
            if emo:
                add("MEDIUM", f, emo[0][0], "emoji-icons", f"{len(emo)} emoji in UI markup (e.g. {''.join(e for _, e in emo[:5])}); use an icon set")
            n_inline = len(INLINE_STYLE.findall(t))
            if n_inline > 15:
                add("LOW", f, 1, "inline-styles", f"{n_inline} inline style attributes; prefer tokens/classes")
            for m in TEXT_CENTER_P.finditer(t):
                add("LOW", f, line_of(t, m.start()), "centered-paragraph", "Centred paragraph text; keep long text left-aligned"); break

    if outline_hits and not any_focus:
        for f, ln in outline_hits[:10]:
            add("HIGH", f, ln, "focus-removed", "Focus outline removed and no :focus-visible/focus: style anywhere in the project")
    elif outline_hits:
        add("LOW", outline_hits[0][0], outline_hits[0][1], "focus-check", f"{len(outline_hits)} outline removals; confirm each has a visible focus replacement")
    if any_anim and not any_reduced:
        add("HIGH", "(project)", 0, "reduced-motion", "Animations/transitions found but no prefers-reduced-motion handling anywhere")
    if motion_files and not any_reduced:
        add("MEDIUM", motion_files[0], 1, "reduced-motion", "Motion/Framer Motion used without MotionConfig reducedMotion=\"user\" or useReducedMotion")
    custom = {x for x in fonts if x not in GENERIC_FONTS}
    if fonts and not custom:
        add("MEDIUM", "(project)", 0, "font-monoculture", f"Only generic fonts in use ({', '.join(sorted(fonts)[:5])}); choose a deliberate pairing")
    if len(radii) > 5:
        add("LOW", "(project)", 0, "radius-sprawl", f"{len(radii)} distinct border-radius values ({', '.join(sorted(radii, key=float))}px); consolidate to a scale")

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings.sort(key=lambda x: (order[x["severity"]], x["file"], x["line"]))
    counts = defaultdict(int)
    for x in findings:
        counts[x["severity"]] += 1
    out_dir = state_dir(root)
    write_json(out_dir / "slop-report.json", {"files_scanned": len(files), "counts": counts, "findings": findings})

    if a.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        print(f"Scanned {len(files)} UI files — HIGH {counts['HIGH']} · MEDIUM {counts['MEDIUM']} · LOW {counts['LOW']}")
        for x in findings[:60]:
            loc = f"{x['file']}:{x['line']}" if x["line"] else x["file"]
            print(f"[{x['severity']}] {loc}  {x['rule']} — {x['message']}")
        if len(findings) > 60:
            print(f"… {len(findings) - 60} more in .zennox/slop-report.json")
    if a.fail_on_high and counts["HIGH"]:
        sys.exit(2)


if __name__ == "__main__":
    import signal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles/CI
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped to head
    main()
