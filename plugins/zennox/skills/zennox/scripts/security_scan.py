#!/usr/bin/env python3
"""Fast first-pass security scan for cross-platform app repos (defensive use on your own code).

Usage: python3 security_scan.py <path> [--fail-on-high] [--json] [--include-build]
Checks: hard-coded secrets, dangerous sinks, injection-prone queries, Electron/Tauri misconfig,
mobile cleartext, weak crypto, permissive CORS, TLS verification off, CI workflow risks,
.env files not ignored. Writes .zennox/security-report.json.
This is triage, not a SAST/dependency audit — follow up with Semgrep/CodeQL/osv-scanner.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import SKIP_DIRS, state_dir, iter_files, line_of, read_text, rel, write_json  # noqa: E402

EXTS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".py", ".go", ".rs", ".dart",
        ".kt", ".java", ".swift", ".rb", ".php", ".json", ".yml", ".yaml", ".toml", ".xml", ".plist",
        ".html", ".env", ".properties", ".gradle", ".kts", ".sh", ".ps1", ".tf", ".conf", ".ini", ".map"]
PLACEHOLDER = re.compile(r"example|xxx+|your[_-]?|changeme|dummy|placeholder|<[^>]+>|\$\{|process\.env|"
                         r"os\.environ|getenv|import\.meta\.env|\*\*\*|test|fake|sample", re.I)

# (severity, rule, regex, message, languages or None for all)
RULES: list[tuple[str, str, re.Pattern, str, set | None]] = [
    ("HIGH", "secret-aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key ID", None),
    ("HIGH", "secret-private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY"), "Private key material", None),
    ("HIGH", "secret-github", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "GitHub token", None),
    ("HIGH", "secret-anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}"), "Anthropic API key", None),
    ("HIGH", "secret-openai", re.compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{32,}"), "OpenAI-style API key", None),
    ("HIGH", "secret-stripe", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{20,}"), "Stripe live secret key", None),
    ("HIGH", "secret-slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token", None),
    ("MEDIUM", "secret-google", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "Google API key (ok only if restricted and meant to be public)", None),
    ("MEDIUM", "secret-generic", re.compile(r"""(?i)\b(api[_-]?key|secret|passw(or)?d|auth[_-]?token|access[_-]?token|client[_-]?secret)\b["']?\s*[:=]\s*["']([^"'\s]{12,})["']"""),
     "Hard-coded credential-like value", None),

    ("HIGH", "electron-node-integration", re.compile(r"nodeIntegration\s*:\s*true"), "Electron nodeIntegration enabled", {"js"}),
    ("HIGH", "electron-context-isolation", re.compile(r"contextIsolation\s*:\s*false"), "Electron contextIsolation disabled", {"js"}),
    ("HIGH", "electron-sandbox", re.compile(r"sandbox\s*:\s*false"), "Electron renderer sandbox disabled", {"js"}),
    ("HIGH", "electron-websecurity", re.compile(r"webSecurity\s*:\s*false|allowRunningInsecureContent\s*:\s*true"), "Electron web security disabled", {"js"}),
    ("MEDIUM", "electron-open-external", re.compile(r"shell\.openExternal\(\s*[a-zA-Z_$][\w.$]*\s*\)"), "shell.openExternal with unvalidated input — allow-list https URLs", {"js"}),
    ("MEDIUM", "tauri-csp-null", re.compile(r'"csp"\s*:\s*null'), "Tauri CSP disabled", {"json"}),
    ("MEDIUM", "tauri-broad-scope", re.compile(r'"path"\s*:\s*"(\*\*|\$HOME/\*\*|/\*\*)"'), "Tauri filesystem scope is very broad", {"json"}),
    ("MEDIUM", "tauri-shell", re.compile(r'"shell:(default|allow-execute|allow-spawn)"'), "Tauri shell execution permission — scope commands tightly", {"json"}),
    ("MEDIUM", "tauri-asset-csp", re.compile(r"dangerousDisableAssetCspModification|dangerousRemoteDomainIpcAccess"), "Tauri 'dangerous' option enabled", {"json"}),

    ("HIGH", "eval", re.compile(r"(?<![\w.])(eval|new\s+Function)\s*\("), "eval/new Function — code injection risk", {"js"}),
    ("MEDIUM", "xss-sink", re.compile(r"dangerouslySetInnerHTML|\.innerHTML\s*=|\.outerHTML\s*=|\bv-html\b|document\.write\(|insertAdjacentHTML\(|\{@html\s"),
     "Raw HTML sink — sanitise untrusted data (DOMPurify) or avoid", {"js"}),
    ("MEDIUM", "token-in-localstorage", re.compile(r"localStorage\.setItem\(\s*['\"][^'\"]*(token|jwt|auth|session)[^'\"]*['\"]", re.I),
     "Auth token in localStorage is readable by any XSS — prefer HttpOnly cookies or secure storage", {"js"}),
    ("MEDIUM", "insecure-random", re.compile(r"Math\.random\(\)[^\n;]{0,40}(token|secret|password|nonce|otp|salt|key)|(token|secret|password|nonce|otp|salt)\w*\s*=\s*[^\n;]{0,40}Math\.random\(\)", re.I),
     "Math.random for security values — use crypto.getRandomValues/randomUUID", {"js"}),
    ("HIGH", "sql-concat", re.compile(r"""(?i)(query|execute|exec|raw|prepare)\s*\(\s*(f["']|`[^`]*\$\{|["'][^"']*(select|insert|update|delete)\b[^"']*["']\s*(\+|%\s|\.format))"""),
     "SQL built from strings — use parameterised queries", None),
    ("HIGH", "tls-verify-off", re.compile(r"rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=?\s*['\"]?0|verify\s*=\s*False|InsecureSkipVerify\s*:\s*true|danger_accept_invalid_certs\(true\)"),
     "TLS certificate verification disabled", None),
    ("HIGH", "jwt-none", re.compile(r"""(?i)algorithms?\s*[:=]\s*\[?\s*["']none["']|verify_signature["']?\s*:\s*False"""), "JWT signature verification disabled", None),
    ("MEDIUM", "py-deserialize", re.compile(r"\bpickle\.loads?\(|\byaml\.load\((?![^)]*SafeLoader)|\bmarshal\.loads\("), "Unsafe deserialisation", {"py"}),
    ("HIGH", "py-shell", re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True|\bos\.system\(|\bos\.popen\("), "Shell command execution — avoid shell=True, pass arg lists", {"py"}),
    ("MEDIUM", "node-exec", re.compile(r"child_process['\"]?\)?\.exec(Sync)?\(|\bexec(Sync)?\(\s*`[^`]*\$\{"), "child_process.exec with interpolation — prefer execFile with arg arrays", {"js"}),
    ("LOW", "weak-hash", re.compile(r"createHash\(\s*['\"](md5|sha1)['\"]|hashlib\.(md5|sha1)\(|MessageDigest\.getInstance\(\"(MD5|SHA-?1)\""), "MD5/SHA-1 — fine for checksums, not for passwords/signatures", None),
    ("MEDIUM", "cors-wildcard", re.compile(r"""Access-Control-Allow-Origin['"]?\s*[,:]\s*['"]\*['"]|origin\s*:\s*['"]\*['"]|origin\s*:\s*true|CORS_ALLOW_ALL_ORIGINS\s*=\s*True|allow_origins\s*=\s*\[\s*["']\*["']"""),
     "Wildcard CORS — restrict origins (never with credentials)", None),
    ("LOW", "debug-on", re.compile(r"^\s*DEBUG\s*=\s*True\b|app\.run\([^)]*debug\s*=\s*True", re.M), "Debug mode enabled — ensure it's off in production", {"py"}),
    ("MEDIUM", "android-cleartext", re.compile(r'usesCleartextTraffic\s*=\s*"true"|cleartextTrafficPermitted\s*=\s*"true"'), "Android cleartext HTTP allowed", {"xml"}),
    ("MEDIUM", "ios-ats", re.compile(r"<key>NSAllowsArbitraryLoads</key>\s*<true\s*/>"), "iOS App Transport Security disabled", {"plist", "xml"}),
    ("LOW", "android-debuggable", re.compile(r'android:debuggable\s*=\s*"true"'), "debuggable=true in manifest", {"xml"}),
    ("LOW", "android-exported", re.compile(r"<(activity|service|receiver|provider)\b(?![^>]*android:exported)[^>]*>"), "Component without explicit android:exported", {"xml"}),
    ("LOW", "cleartext-url", re.compile(r"""["'`]http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|10\.|192\.168\.|\[::1\]|example\.|schemas\.|www\.w3\.org|ns\.adobe|xmlns)[^\s"'`]+"""), "Cleartext http:// URL", None),

    ("MEDIUM", "gha-pr-target", re.compile(r"^\s*pull_request_target\s*:", re.M), "pull_request_target runs with secrets — never check out untrusted PR code", {"yml"}),
    ("MEDIUM", "gha-write-all", re.compile(r"permissions\s*:\s*write-all"), "Workflow has write-all permissions", {"yml"}),
    ("LOW", "gha-unpinned", re.compile(r"uses\s*:\s*(?!actions/|github/|\./)[\w.-]+/[\w./-]+@(main|master|v?\d+(\.\d+)*)\s*$", re.M), "Third-party action pinned to a tag/branch — pin to a commit SHA", {"yml"}),
    ("HIGH", "gha-secret-echo", re.compile(r"echo\s+[^\n]*\$\{\{\s*secrets\."), "Secret echoed in workflow logs", {"yml"}),
]

LANG_OF = {".js": "js", ".jsx": "js", ".ts": "js", ".tsx": "js", ".mjs": "js", ".cjs": "js", ".vue": "js",
           ".svelte": "js", ".html": "js", ".py": "py", ".json": "json", ".yml": "yml", ".yaml": "yml",
           ".xml": "xml", ".plist": "plist"}


def redact(s: str) -> str:
    s = s.strip()
    return s if len(s) < 12 else s[:6] + "…[redacted]"


def scan(root: Path, include_build: bool) -> tuple[list[dict], int]:
    skip = set(SKIP_DIRS) - ({"dist", "build", "out"} if include_build else set())
    findings: list[dict] = []
    files = list(iter_files(root, EXTS + [".env"], skip_dirs=skip))
    for p in files:
        f = rel(p, root)
        lang = LANG_OF.get(p.suffix.lower())
        if p.suffix == ".map":
            if include_build:
                findings.append({"severity": "LOW", "file": f, "line": 0, "rule": "sourcemap",
                                 "message": "Source map in build output — upload privately to error tracker, don't serve publicly unless intended", "match": ""})
            continue
        t = read_text(p)
        minified = p.name.endswith((".min.js", ".bundle.js")) or (t.count("\n") < 3 and len(t) > 5000)
        for sev, rule, rx, msg, langs in RULES:
            if langs and lang not in langs:
                continue
            for m in rx.finditer(t):
                snippet = m.group(0)
                if rule == "secret-generic" and PLACEHOLDER.search(m.group(0)):
                    continue
                if rule.startswith("secret") and re.search(r"\.(test|spec)\.|fixtures?/|__mocks__", f):
                    sev_eff = "LOW"
                else:
                    sev_eff = "INFO" if minified else sev
                findings.append({"severity": sev_eff, "file": f, "line": line_of(t, m.start()), "rule": rule,
                                 "message": msg + (" (minified/vendor file — check if reachable)" if minified else ""),
                                 "match": redact(snippet) if rule.startswith("secret") else snippet.strip()[:80]})
                if len([x for x in findings if x["file"] == f and x["rule"] == rule]) >= 5:
                    break
    # .env files committed without being ignored
    gi = read_text(root / ".gitignore") if root.is_dir() else ""
    for env in (root.glob("**/.env*") if root.is_dir() else []):
        if any(part in SKIP_DIRS for part in env.relative_to(root).parts[:-1]) or env.name.endswith((".example", ".sample", ".template")):
            continue
        if not re.search(r"^\s*\.env(\*|\b)", gi, re.M):
            findings.append({"severity": "HIGH", "file": rel(env, root), "line": 0, "rule": "env-not-ignored",
                             "message": ".env file present but .env not in .gitignore", "match": ""})
    return findings, len(files)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--fail-on-high", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-build", action="store_true", help="also scan dist/build/out (use on release artifacts)")
    a = ap.parse_args()
    root = Path(a.path).resolve()
    findings, n = scan(root, a.include_build)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    findings.sort(key=lambda x: (order[x["severity"]], x["file"], x["line"]))
    counts = defaultdict(int)
    for x in findings:
        counts[x["severity"]] += 1
    write_json(state_dir(root) / "security-report.json", {"files_scanned": n, "counts": counts, "findings": findings})
    if a.json:
        print(json.dumps(findings, indent=2))
    else:
        print(f"Scanned {n} files — HIGH {counts['HIGH']} · MEDIUM {counts['MEDIUM']} · LOW {counts['LOW']} · INFO {counts['INFO']}")
        for x in findings[:80]:
            loc = f"{x['file']}:{x['line']}" if x["line"] else x["file"]
            extra = f"  [{x['match']}]" if x["match"] else ""
            print(f"[{x['severity']}] {loc}  {x['rule']} — {x['message']}{extra}")
        if len(findings) > 80:
            print(f"… {len(findings) - 80} more in .zennox/security-report.json")
    if a.fail_on_high and counts["HIGH"]:
        sys.exit(2)


if __name__ == "__main__":
    import signal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles/CI
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped to head
    main()
