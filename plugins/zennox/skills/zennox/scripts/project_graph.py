#!/usr/bin/env python3
"""Build a lightweight import graph of a repo and write .zennox/GRAPH_REPORT.md + graph.json.

Usage:
  python3 project_graph.py <repo>                 # build/refresh (hash-cached)
  python3 project_graph.py <repo> --neighbors F   # what F imports and what imports F
  python3 project_graph.py <repo> --core-dirs core,shared,domain

Languages: JS/TS (+jsx/tsx/mjs/cjs/vue/svelte), Python, Go, Rust, Dart, Kotlin, Swift.
Regex-based by design: fast, dependency-free, good enough to orient. Not a type checker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import state_dir, iter_files, read_text, rel, write_json  # noqa: E402

LANG = {".js": "js", ".jsx": "js", ".ts": "js", ".tsx": "js", ".mjs": "js", ".cjs": "js",
        ".vue": "js", ".svelte": "js", ".py": "py", ".go": "go", ".rs": "rs", ".dart": "dart",
        ".kt": "kt", ".kts": "kt", ".swift": "swift"}
JS_EXTS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"]

PATTERNS = {
    "js": [re.compile(r"""(?:import|export)\s[^'"]*?from\s*['"]([^'"]+)['"]"""),
           re.compile(r"""import\s*['"]([^'"]+)['"]"""),
           re.compile(r"""(?:require|import)\s*\(\s*['"]([^'"]+)['"]\s*\)""")],
    "py": [re.compile(r"^\s*from\s+(\.*[\w.]*)\s+import\s", re.M),
           re.compile(r"^\s*import\s+([\w.]+(?:\s*,\s*[\w.]+)*)", re.M)],
    "go": [re.compile(r'^\s*import\s+(?:\w+\s+)?"([^"]+)"', re.M),
           re.compile(r'^\s*(?:\w+\s+)?"([^"]+)"\s*$', re.M)],
    "rs": [re.compile(r"^\s*(?:pub\s+)?use\s+((?:crate|super|self)(?:::\w+)+)", re.M),
           re.compile(r"^\s*(?:pub\s+)?mod\s+(\w+)\s*;", re.M)],
    "dart": [re.compile(r"""^\s*(?:import|export|part)\s+['"]([^'"]+)['"]""", re.M)],
    "kt": [re.compile(r"^\s*import\s+([\w.]+)", re.M)],
    "swift": [re.compile(r"^\s*(?:@testable\s+)?import\s+(\w+)", re.M)],
}

PLATFORM_MODULES = re.compile(
    r"^(react-native|react-dom|electron|@tauri-apps/|expo|@capacitor/|@ionic/|node:|fs$|path$|"
    r"os$|child_process$|UIKit$|AppKit$|SwiftUI$|WatchKit$|android\.|androidx\.|dart:io|"
    r"dart:html|dart:ui|package:flutter/|tkinter|winreg|win32|ctypes|"
    r"(std::)?os::(windows|unix|macos))")
DOM_GLOBAL = re.compile(r"\b(window|document|localStorage|navigator)\.")
ENTRY_HINT = re.compile(r"(^|/)(index|main|app|App|page|layout|route|server|cli|setup|"
                        r"__init__|mod|lib|build|vite\.config|next\.config|.*\.config|"
                        r".*\.(test|spec|stories)|test_.*|.*_test)\.\w+$")


def parse_imports(text: str, lang: str) -> list[str]:
    if lang == "go":  # only lines inside import blocks or single imports
        blocks = re.findall(r"^import\s*\((.*?)\)", text, re.S | re.M)
        out = re.findall(r'"([^"]+)"', "\n".join(blocks))
        return out + PATTERNS["go"][0].findall(text)
    found: list[str] = []
    for pat in PATTERNS[lang]:
        for m in pat.findall(text):
            if lang == "py" and "," in m:
                found.extend(x.strip() for x in m.split(","))
            else:
                found.append(m)
    return found


class Resolver:
    def __init__(self, root: Path, files: list[Path]):
        self.root = root
        self.rels = {rel(f, root) for f in files}
        self.by_stem: dict[str, list[str]] = defaultdict(list)
        for r in self.rels:
            self.by_stem[Path(r).stem].append(r)
        self.dart_pkg = self._dart_package()
        self.go_mod = self._go_module()
        self.kt_index = {}  # "pkg.Class" -> file

    def _dart_package(self) -> str | None:
        pub = self.root / "pubspec.yaml"
        m = re.search(r"^name:\s*(\S+)", read_text(pub), re.M) if pub.exists() else None
        return m.group(1) if m else None

    def _go_module(self) -> str | None:
        gm = self.root / "go.mod"
        m = re.search(r"^module\s+(\S+)", read_text(gm), re.M) if gm.exists() else None
        return m.group(1) if m else None

    def index_kotlin(self, path: str, text: str) -> None:
        m = re.search(r"^\s*package\s+([\w.]+)", text, re.M)
        if m:
            self.kt_index[f"{m.group(1)}.{Path(path).stem}"] = path

    def _try(self, base: str, exts: list[str]) -> str | None:
        base = base.rstrip("/")
        cands = [base] + [base + e for e in exts] + [f"{base}/index{e}" for e in exts]
        return next((c for c in cands if c in self.rels), None)

    def resolve(self, src: str, imp: str, lang: str) -> str | None:
        here = Path(src).parent
        if lang == "js":
            if imp.startswith("."):
                base = _norm(here / imp)
                found = self._try(base, JS_EXTS)
                if not found and re.search(r"\.(m|c)?js$", base):  # TS ESM: './x.js' -> x.ts
                    found = self._try(re.sub(r"\.(m|c)?js$", "", base), JS_EXTS)
                return found
            for prefix in ("@/", "~/", "src/"):
                if imp.startswith(prefix):
                    return self._try("src/" + imp[len(prefix):], JS_EXTS)
            return None
        if lang == "py":
            if imp.startswith("."):
                dots = len(imp) - len(imp.lstrip("."))
                base = here
                for _ in range(dots - 1):
                    base = base.parent
                mod = imp.lstrip(".").replace(".", "/")
                p = (base / mod).as_posix() if mod else base.as_posix()
            else:
                p = imp.replace(".", "/")
            for cand in (p + ".py", p + "/__init__.py", "src/" + p + ".py", "src/" + p + "/__init__.py"):
                cand = cand.lstrip("./") if cand.startswith("./") else cand
                if cand in self.rels:
                    return cand
            return None
        if lang == "dart":
            if imp.startswith("package:") and self.dart_pkg and imp.startswith(f"package:{self.dart_pkg}/"):
                return self._try("lib/" + imp.split("/", 1)[1], [])
            if not imp.startswith(("package:", "dart:")):
                return self._try(_norm(here / imp), [])
            return None
        if lang == "rs":
            if "::" not in imp:  # mod x;
                for c in (_norm(here / f"{imp}.rs"), _norm(here / imp / "mod.rs")):
                    if c in self.rels:
                        return c
                return None
            parts = imp.split("::")
            if parts[0] == "crate":
                crate_root = next((Path(r).parent for r in self.rels
                                   if r.endswith(("src/lib.rs", "src/main.rs")) and src.startswith(str(Path(r).parent))), Path("src"))
                segs = parts[1:]
                for n in range(len(segs), 0, -1):
                    base = crate_root.joinpath(*segs[:n])
                    for c in (_norm(base) + ".rs", _norm(base / "mod.rs")):
                        if c in self.rels:
                            return c
            return None
        if lang == "kt":
            return self.kt_index.get(imp)
        if lang == "go" and self.go_mod and imp.startswith(self.go_mod):
            d = imp[len(self.go_mod):].strip("/")
            return next((r for r in sorted(self.rels) if Path(r).parent.as_posix() == d and r.endswith(".go")), None)
        return None


def _norm(p: Path) -> str:
    parts: list[str] = []
    for part in p.as_posix().split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def tarjan(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    index, low, stack, on, out, i = {}, {}, [], set(), [], [0]
    sys.setrecursionlimit(max(10000, len(nodes) * 4))

    def visit(v: str) -> None:
        index[v] = low[v] = i[0]; i[0] += 1
        stack.append(v); on.add(v)
        for w in adj.get(v, ()):
            if w not in index:
                visit(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                out.append(sorted(comp))

    for n in nodes:
        if n not in index:
            visit(n)
    return out


def cluster_of(path: str) -> str:
    parts = path.split("/")
    if len(parts) > 2 and parts[0] in ("apps", "packages", "src", "lib", "libs", "services", "modules"):
        return "/".join(parts[:2])
    return parts[0] if len(parts) > 1 else "(root)"


def build(root: Path, core_dirs: set[str]) -> dict:
    files = list(iter_files(root, LANG.keys()))
    fdir = state_dir(root)
    cache_path = fdir / "graph-cache.json"
    try:
        cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    except json.JSONDecodeError:
        cache = {}
    res = Resolver(root, files)
    parsed, new_cache = {}, {}
    for f in files:
        r = rel(f, root)
        text = read_text(f)
        h = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
        lang = LANG[f.suffix.lower()]
        if lang == "kt":
            res.index_kotlin(r, text)
        entry = cache.get(r)
        if not entry or entry.get("h") != h:
            entry = {"h": h, "imports": parse_imports(text, lang), "loc": text.count("\n") + 1,
                     "dom": bool(lang == "js" and DOM_GLOBAL.search(text))}
        new_cache[r] = entry
        parsed[r] = (lang, entry)
    write_json(cache_path, new_cache)

    adj: dict[str, set[str]] = defaultdict(set)
    external: Counter = Counter()
    violations: list[str] = []
    for r, (lang, entry) in parsed.items():
        in_core = any(seg in core_dirs for seg in r.split("/")[:-1])
        for imp in entry["imports"]:
            target = res.resolve(r, imp, lang)
            if target and target != r:
                adj[r].add(target)
                if in_core and not any(s in core_dirs for s in target.split("/")[:-1]) \
                        and target.split("/")[0] in ("apps", "platform", "native", "desktop", "mobile", "web"):
                    violations.append(f"{r} → {target} (core imports app/platform code)")
            elif not imp.startswith((".", "/")):
                name = imp.split("/")[0] if not imp.startswith("@") else "/".join(imp.split("/")[:2])
                if lang in ("py", "kt", "swift"):
                    name = imp.split(".")[0]
                external[name] += 1
                if in_core and PLATFORM_MODULES.match(imp):
                    violations.append(f"{r} imports platform module '{imp}'")
        if in_core and entry.get("dom"):
            violations.append(f"{r} uses DOM/browser globals (window/document/localStorage/navigator)")

    nodes = sorted(parsed)
    indeg = Counter(t for ts in adj.values() for t in ts)
    outdeg = {n: len(adj.get(n, ())) for n in nodes}
    cycles = tarjan(nodes, adj)
    orphans = [n for n in nodes if indeg[n] == 0 and not ENTRY_HINT.search(n)]
    clusters: dict[str, dict] = defaultdict(lambda: {"files": 0, "intra": 0, "inter": 0})
    for n in nodes:
        clusters[cluster_of(n)]["files"] += 1
    for a, ts in adj.items():
        for b in ts:
            key = "intra" if cluster_of(a) == cluster_of(b) else "inter"
            clusters[cluster_of(a)][key] += 1
    langs = Counter(parsed[n][0] for n in nodes)
    return {
        "root": str(root), "files": len(nodes), "edges": sum(len(v) for v in adj.values()),
        "languages": dict(langs),
        "nodes": [{"id": n, "lang": parsed[n][0], "loc": parsed[n][1]["loc"],
                   "in": indeg[n], "out": outdeg[n]} for n in nodes],
        "adjacency": {k: sorted(v) for k, v in adj.items()},
        "external": dict(external.most_common(40)),
        "god_nodes": [(n, indeg[n]) for n, _ in indeg.most_common(12)],
        "hubs": sorted(((n, d) for n, d in outdeg.items() if d), key=lambda x: -x[1])[:10],
        "cycles": cycles[:15], "orphans": orphans,
        "clusters": dict(sorted(clusters.items(), key=lambda kv: -kv[1]["files"])),
        "layer_violations": sorted(set(violations)),
    }


def report(g: dict) -> str:
    L = [f"# GRAPH_REPORT", "",
         f"{g['files']} files · {g['edges']} internal import edges · languages: "
         + ", ".join(f"{k}={v}" for k, v in g["languages"].items()), "",
         "Read god nodes first; open neighbours with `project_graph.py <repo> --neighbors <file>`.", "",
         "## God nodes (most imported)"]
    L += [f"- `{n}` ← {d}" for n, d in g["god_nodes"]] or ["- (none)"]
    L += ["", "## Hubs (import the most)"] + ([f"- `{n}` → {d}" for n, d in g["hubs"]] or ["- (none)"])
    L += ["", "## Clusters", "| cluster | files | intra edges | outgoing inter edges |", "|---|---|---|---|"]
    L += [f"| {c} | {v['files']} | {v['intra']} | {v['inter']} |" for c, v in list(g["clusters"].items())[:20]]
    L += ["", f"## Layer violations ({len(g['layer_violations'])})"]
    L += [f"- {v}" for v in g["layer_violations"][:30]] or ["- none"]
    L += ["", f"## Import cycles ({len(g['cycles'])})"]
    L += [f"- {' → '.join(c[:6])}{' …' if len(c) > 6 else ''}" for c in g["cycles"]] or ["- none"]
    L += ["", f"## Orphans — not imported, not an obvious entry point ({len(g['orphans'])})"]
    L += [f"- `{o}`" for o in g["orphans"][:30]] or ["- none"]
    if len(g["orphans"]) > 30:
        L.append(f"- … {len(g['orphans']) - 30} more in graph.json")
    L += ["", "## Top external dependencies (by import count)"]
    L += [", ".join(f"`{k}` {v}" for k, v in list(g["external"].items())[:25]) or "none"]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--neighbors", metavar="FILE", help="show imports/importers of FILE (substring ok)")
    ap.add_argument("--core-dirs", default="core,shared,domain,common",
                    help="comma-separated dir names that must stay platform-agnostic")
    a = ap.parse_args()
    root = Path(a.path).resolve()
    g = build(root, {d.strip() for d in a.core_dirs.split(",") if d.strip()})
    fdir = state_dir(root)
    write_json(fdir / "graph.json", g)
    (fdir / "GRAPH_REPORT.md").write_text(report(g), encoding="utf-8")

    if a.neighbors:
        matches = [n["id"] for n in g["nodes"] if a.neighbors in n["id"]]
        if not matches:
            print(f"No file matching '{a.neighbors}'"); return
        for m in matches[:5]:
            importers = sorted(k for k, v in g["adjacency"].items() if m in v)
            print(f"{m}\n  imports:   {', '.join(g['adjacency'].get(m, [])) or '-'}\n  importers: {', '.join(importers) or '-'}")
        return
    print(f"{g['files']} files, {g['edges']} edges, {len(g['cycles'])} cycles, "
          f"{len(g['layer_violations'])} layer violations, {len(g['orphans'])} orphans")
    print(f"Report: {fdir / 'GRAPH_REPORT.md'}")


if __name__ == "__main__":
    import signal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles/CI
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped to head
    main()
