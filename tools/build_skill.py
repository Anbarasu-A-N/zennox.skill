#!/usr/bin/env python3
"""Build zennox.skill (the ZIP that Claude.ai uploads) from plugins/zennox/skills/zennox.

Usage (from the repo root, any OS):
  python tools/build_skill.py              # writes ./zennox.skill
  python tools/build_skill.py dist/        # writes dist/zennox.skill
  python tools/build_skill.py --check      # exit 1 if ./zennox.skill is out of date

The archive is reproducible: same source files give a byte-identical zip (fixed timestamps,
sorted entries, LF line endings for text), so git only sees a change when the skill changed.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "plugins" / "zennox" / "skills" / "zennox"
EXCLUDE_DIRS = {"__pycache__", ".zennox", "node_modules"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}
TEXT = {".md", ".py", ".json", ".yml", ".yaml", ".ts", ".txt", ".toml"}
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def entries() -> list[tuple[str, bytes]]:
    out = []
    for p in sorted(SKILL.rglob("*")):
        rel = p.relative_to(SKILL.parent)
        if p.is_dir() or EXCLUDE_DIRS & set(rel.parts) or p.name in EXCLUDE_NAMES or p.suffix == ".pyc":
            continue
        data = p.read_bytes()
        if p.suffix in TEXT:  # Windows checkouts may have CRLF; the package always uses LF
            data = data.replace(b"\r\n", b"\n")
        out.append((rel.as_posix(), data))
    return out


def build(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in entries():
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".py") else 0o644) << 16
            z.writestr(info, data)
    return dest


def up_to_date(pkg: Path) -> tuple[bool, str]:
    if not pkg.exists():
        return False, f"{pkg.name} not found"
    with zipfile.ZipFile(pkg) as z:
        packed = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    source = dict(entries())
    if packed.keys() != source.keys():
        diff = sorted(packed.keys() ^ source.keys())
        return False, "file list differs: " + ", ".join(diff[:5])
    changed = [n for n in source if packed[n].replace(b"\r\n", b"\n") != source[n]]
    return (not changed), ("changed: " + ", ".join(changed[:5])) if changed else "up to date"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", default=str(REPO), help="output directory (default: repo root)")
    ap.add_argument("--check", action="store_true", help="only verify the existing zennox.skill")
    a = ap.parse_args()
    pkg = Path(a.out) / "zennox.skill"
    if a.check:
        ok, msg = up_to_date(pkg)
        print(f"{pkg}: {msg}" + ("" if ok else " — run: python tools/build_skill.py"))
        sys.exit(0 if ok else 1)
    build(pkg)
    print(f"built {pkg} ({pkg.stat().st_size // 1024} KB, {len(entries())} files)")


if __name__ == "__main__":
    main()
