"""Shared helpers for Zennox scripts (stdlib only)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Iterator

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "dist", "build", "out",
    ".next", ".nuxt", ".svelte-kit", ".astro", ".output", ".vercel", ".turbo", ".cache",
    "coverage", "target", "Pods", "DerivedData", ".gradle", ".dart_tool", ".pub-cache",
    ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
    ".zennox", ".idea", ".vscode", "vendor", ".expo",
}
MAX_FILE_BYTES = 1_000_000


def iter_files(root: Path, exts: Iterable[str], skip_dirs: set[str] | None = None) -> Iterator[Path]:
    """Yield files under root with one of the given extensions, skipping heavy/generated dirs."""
    exts = {e.lower() for e in exts}
    skip = SKIP_DIRS if skip_dirs is None else skip_dirs
    if root.is_file():
        if root.suffix.lower() in exts:
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d == ".github" or (d not in skip and not d.startswith("."))]
        for name in filenames:
            p = Path(dirpath, name)
            if p.suffix.lower() in exts or name in exts:
                try:
                    if p.stat().st_size <= MAX_FILE_BYTES:
                        yield p
                except OSError:
                    continue


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def state_dir(root: Path) -> Path:
    base = root if root.is_dir() else root.parent
    d = base / ".zennox"
    d.mkdir(exist_ok=True)
    return d


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def rel(p: Path, root: Path) -> str:
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()
