#!/usr/bin/env python3
"""Detect host OS, toolchains and the project's stack; say which targets are buildable here.

Usage: python3 detect_env.py [project_path] [--json]
Writes .zennox/env.json in the project.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import state_dir, read_text, write_json  # noqa: E402

TOOLS = {
    "node": ["node", "--version"], "npm": ["npm", "--version"], "pnpm": ["pnpm", "--version"],
    "yarn": ["yarn", "--version"], "bun": ["bun", "--version"], "deno": ["deno", "--version"],
    "python": [sys.executable, "--version"], "rustc": ["rustc", "--version"],
    "cargo": ["cargo", "--version"], "go": ["go", "version"], "java": ["java", "-version"],
    "flutter": ["flutter", "--version"], "dart": ["dart", "--version"],
    "dotnet": ["dotnet", "--version"], "xcodebuild": ["xcodebuild", "-version"],
    "swift": ["swift", "--version"], "adb": ["adb", "version"], "docker": ["docker", "--version"],
    "git": ["git", "--version"], "gh": ["gh", "--version"],
}

JS_MARKERS = {
    "react": "React", "next": "Next.js", "vite": "Vite", "vue": "Vue", "nuxt": "Nuxt",
    "svelte": "Svelte", "@sveltejs/kit": "SvelteKit", "astro": "Astro", "solid-js": "Solid",
    "@angular/core": "Angular", "electron": "Electron", "@tauri-apps/api": "Tauri",
    "@tauri-apps/cli": "Tauri", "expo": "Expo", "react-native": "React Native",
    "@capacitor/core": "Capacitor", "three": "Three.js", "@react-three/fiber": "React Three Fiber",
    "motion": "Motion", "framer-motion": "Framer Motion", "@playwright/test": "Playwright",
    "tailwindcss": "Tailwind", "vitest": "Vitest", "jest": "Jest", "zod": "Zod",
    "@anthropic-ai/sdk": "Anthropic SDK", "openai": "OpenAI SDK", "workbox-window": "Workbox/PWA",
    "vite-plugin-pwa": "Workbox/PWA", "turbo": "Turborepo", "nx": "Nx",
}


def run(cmd: list[str], versions: bool = True) -> str | None:
    # shutil.which finds Windows .cmd/.bat shims (npm.cmd, pnpm.cmd) that bare names can't launch
    exe = cmd[0] if os.path.isabs(cmd[0]) else shutil.which(cmd[0])
    if not exe:
        return None
    if not versions:
        return "present"
    try:
        # Tools print in whatever code page they like (e.g. cp1252 "©" on Windows): never crash on it
        proc = subprocess.Popen([exe, *cmd[1:]], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return "present (version check failed)"
    try:
        out, err = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        # Don't communicate() again: a .cmd shim's grandchild can hold the pipes open forever.
        proc.kill()
        return "present (version check timed out)"
    lines = (out or err).strip().splitlines()
    return lines[0][:120] if lines else "present"


def detect_stack(root: Path) -> dict:
    stack: set[str] = set()
    notes: list[str] = []
    pkgs = [p for p in root.glob("**/package.json") if "node_modules" not in p.parts][:50]
    for pkg in pkgs:
        try:
            data = json.loads(read_text(pkg) or "{}")
        except json.JSONDecodeError:
            continue
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        stack.update(label for dep, label in JS_MARKERS.items() if dep in deps)
        if data.get("workspaces"):
            stack.add("npm/yarn workspaces")
    checks = {
        "pnpm-workspace.yaml": "pnpm workspaces", "pubspec.yaml": "Flutter/Dart",
        "Cargo.toml": "Rust", "go.mod": "Go", "pyproject.toml": "Python",
        "requirements.txt": "Python", "Package.swift": "Swift Package",
        "settings.gradle.kts": "Gradle", "settings.gradle": "Gradle",
        "capacitor.config.ts": "Capacitor", "capacitor.config.json": "Capacitor",
        "app.json": None, "DESIGN.md": "DESIGN.md present", "SPEC.md": "SPEC.md present",
    }
    for name, label in checks.items():
        if label and any(p for p in root.glob(f"**/{name}") if "node_modules" not in p.parts):
            stack.add(label)
    if any(root.glob("**/src-tauri/tauri.conf.json")):
        stack.add("Tauri")
    if any(root.glob("**/*.xcodeproj")) or any(root.glob("**/*.xcworkspace")):
        stack.add("Xcode project")
    gradle_files = [p for p in root.glob("**/build.gradle*") if "node_modules" not in p.parts][:30]
    if any("multiplatform" in read_text(p) for p in gradle_files):
        stack.add("Kotlin Multiplatform")
    if not stack:
        notes.append("No known stack markers found (new project?)")
    return {"stack": sorted(stack), "notes": notes}


def buildable(os_name: str, tools: dict, env: dict) -> dict:
    has = lambda k: bool(tools.get(k))  # noqa: E731
    android_sdk = env.get("ANDROID_HOME") or env.get("ANDROID_SDK_ROOT")
    t = {
        "web/PWA": has("node") or has("bun") or has("deno"),
        "desktop (this OS)": has("node") or has("cargo"),
        "android": has("java") and bool(android_sdk),
        "ios": os_name == "Darwin" and has("xcodebuild"),
        "macos": os_name == "Darwin",
        "windows": os_name == "Windows",
        "linux": os_name == "Linux",
        "flutter targets": has("flutter"),
    }
    reasons = {}
    if not t["ios"]:
        reasons["ios"] = "needs macOS + Xcode (use a macOS CI runner)" if os_name != "Darwin" else "install Xcode"
    if not t["android"]:
        reasons["android"] = "needs JDK + Android SDK (set ANDROID_HOME)"
    if not has("cargo"):
        reasons["desktop (this OS)"] = "Tauri needs Rust (rustup); Electron needs only Node"
    if not has("flutter"):
        reasons["flutter targets"] = "install the Flutter SDK if the project uses Flutter"
    for other in ("macos", "windows", "linux"):
        if not t[other]:
            reasons[other] = "build on that OS or in a CI runner for it"
    return {"targets": t, "reasons": reasons}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="print JSON instead of a summary")
    ap.add_argument("--no-versions", action="store_true", help="only check tools exist (fastest)")
    args = ap.parse_args()
    root = Path(args.path).resolve()

    os_name = platform.system()
    with ThreadPoolExecutor(max_workers=8) as pool:  # probe in parallel: worst case ~one timeout, not twenty
        found = pool.map(lambda kv: (kv[0], run(kv[1], not args.no_versions)), TOOLS.items())
    tools = dict(found)
    tools = {k: v for k, v in tools.items() if v}
    env = {k: os.environ[k] for k in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "JAVA_HOME", "CI") if k in os.environ}
    result = {
        "host": {"os": os_name, "release": platform.release(), "arch": platform.machine(),
                 "python": platform.python_version()},
        "tools": tools, "env": env, **detect_stack(root), **buildable(os_name, tools, env),
    }
    if root.is_dir():
        write_json(state_dir(root) / "env.json", result)

    if args.json:
        print(json.dumps(result, indent=2))
        return
    h = result["host"]
    print(f"Host: {h['os']} {h['release']} ({h['arch']}), Python {h['python']}")
    print("Tools: " + (", ".join(f"{k}" for k in tools) or "none detected"))
    print("Stack: " + (", ".join(result["stack"]) or "none detected"))
    print("Buildable here:")
    for target, ok in result["targets"].items():
        why = "" if ok else f"  — {result['reasons'].get(target, '')}"
        print(f"  [{'x' if ok else ' '}] {target}{why}")
    if root.is_dir():
        print(f"Details: {root / '.zennox' / 'env.json'}")


if __name__ == "__main__":
    import signal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles/CI
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped to head
    main()
