"""Self-tests for the Zennox helper scripts. Stdlib only.

Run from the repo root:  python -m unittest discover -s tests -v
Each test builds a tiny throwaway project with known problems planted in it and checks that
the matching script finds them.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "zennox" / "skills" / "zennox" / "scripts"

FIXTURE = {
    "package.json": '{"name":"demo","workspaces":["apps/*","packages/*"]}',
    "apps/web/package.json": '{"dependencies":{"react":"18","motion":"11"}}',
    "packages/core/src/index.ts": 'export * from "./notes";\nexport { validate } from "./validate.js";\n',
    "packages/core/src/notes.ts": 'import { validate } from "./validate";\nimport fs from "fs";\n'
                                  'export const save = (n: string) => { localStorage.setItem("authToken", n); return validate(n); };\n',
    "packages/core/src/validate.ts": 'import { save } from "./notes";\nexport const validate = (s: string) => s.length > 0;\n',
    "packages/adapters/src/unused.ts": "export const nothing = 1;\n",
    "apps/web/src/Hero.tsx": '<section className="bg-gradient-to-r from-purple-500 via-pink-500">\n'
                             "<h1>Unlock your potential</h1>\n<img src=\"/a.png\" />\n<button><svg/></button>\n</section>\n",
    "apps/web/src/styles.css": "body{font-family:Inter,sans-serif}\n.btn{height:32px;outline:none;transition:all .2s}\n",
    "apps/desktop/main.ts": "new BrowserWindow({ webPreferences: { nodeIntegration: true, contextIsolation: false } });\n"
                            'const q = db.query(`SELECT * FROM notes WHERE id = ${id}`);\n',
    "apps/api/server.py": "import subprocess\nsubprocess.run(cmd, shell=True)\n",
    ".gitignore": "node_modules\n",
    ".env": "SECRET=1\n",
}


def run(script: str, *args: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONUTF8": "1", **(extra_env or {})}
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)


def make_fixture(root: Path, newline: str = "\n") -> None:
    """Write FIXTURE with exact line endings (bytes, so the OS can't translate them)."""
    for rel, text in FIXTURE.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.replace("\n", newline).encode("utf-8"))


def rules(report: Path) -> set[str]:
    return {f["rule"] for f in json.loads(report.read_text(encoding="utf-8"))["findings"]}


class ZennoxScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        make_fixture(cls.root)
        cls.state = cls.root / ".zennox"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_detect_env(self):
        r = run("detect_env.py", str(self.root), "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("React", data["stack"])
        self.assertIn("web/PWA", data["targets"])

    def test_project_graph(self):
        r = run("project_graph.py", str(self.root))
        self.assertEqual(r.returncode, 0, r.stderr)
        g = json.loads((self.state / "graph.json").read_text(encoding="utf-8"))
        self.assertTrue(any("notes.ts" in "".join(c) for c in g["cycles"]), "cycle notes<->validate not found")
        self.assertTrue(any("platform module 'fs'" in v for v in g["layer_violations"]))
        self.assertIn("packages/adapters/src/unused.ts", g["orphans"])
        self.assertTrue((self.state / "GRAPH_REPORT.md").exists())

    def test_slop_check(self):
        r = run("slop_check.py", str(self.root), "--fail-on-high")
        self.assertEqual(r.returncode, 2, "HIGH findings should fail the run")
        rules = {f["rule"] for f in json.loads((self.state / "slop-report.json").read_text(encoding="utf-8"))["findings"]}
        for expected in ("img-alt", "icon-button-name", "reduced-motion", "purple-gradient", "slop-copy", "small-target"):
            self.assertIn(expected, rules)

    def test_security_scan(self):
        r = run("security_scan.py", str(self.root), "--fail-on-high")
        self.assertEqual(r.returncode, 2, "HIGH findings should fail the run")
        rules = {f["rule"] for f in json.loads((self.state / "security-report.json").read_text(encoding="utf-8"))["findings"]}
        for expected in ("electron-node-integration", "electron-context-isolation", "sql-concat", "py-shell",
                         "env-not-ignored", "token-in-localstorage"):
            self.assertIn(expected, rules)

    def test_memory_roundtrip_and_secret_guard(self):
        root = str(self.root)
        self.assertEqual(run("memory.py", "--root", root, "add", "--type", "decision",
                             "--title", "Use Tauri for desktop", "--body", "Smaller binaries.").returncode, 0)
        hit = run("memory.py", "--root", root, "search", "tauri desktop")
        self.assertIn("Use Tauri for desktop", hit.stdout)
        blocked = run("memory.py", "--root", root, "add", "--title", "oops",
                      "--body", "sk-ant-api03-abcdefghijklmnopqrstuvwxyz012345")
        self.assertNotEqual(blocked.returncode, 0, "secret should be refused")


class RepoIntegrity(unittest.TestCase):
    """Checks that used to be an inline CI command (fragile in PowerShell on Windows)."""
    REPO = Path(__file__).resolve().parents[1]
    SKILL = REPO / "plugins" / "zennox" / "skills" / "zennox"

    def test_manifests_are_valid_json_and_consistent(self):
        market = json.loads((self.REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        plugin = json.loads((self.REPO / "plugins" / "zennox" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "zennox")
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertEqual(market["plugins"][0]["version"], plugin["version"])
        self.assertTrue((self.REPO / market["plugins"][0]["source"]).is_dir())

    def test_skill_frontmatter(self):
        text = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"))
        head = text.split("---", 2)[1]
        self.assertIn("name: zennox", head)
        self.assertEqual(self.SKILL.name, "zennox")
        desc = next(l for l in head.splitlines() if l.startswith("description:"))
        self.assertLessEqual(len(desc) - len("description: "), 1024)
        self.assertNotIn("<", desc)

    def test_every_reference_in_index_exists(self):
        text = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        import re
        for ref in set(re.findall(r"references/[\w.\-]+\.md", text)):
            self.assertTrue((self.SKILL / ref).exists(), ref)


class PackagedSkill(unittest.TestCase):
    """zennox.skill in the repo root is what users download; it must match the source."""

    def test_committed_package_is_up_to_date(self):
        if not (RepoIntegrity.REPO / "zennox.skill").exists():
            self.skipTest("no zennox.skill committed in repo root")
        r = subprocess.run([sys.executable, str(RepoIntegrity.REPO / "tools" / "build_skill.py"), "--check"],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_build_is_reproducible_and_valid(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for d in (a, b):
                subprocess.run([sys.executable, str(RepoIntegrity.REPO / "tools" / "build_skill.py"), d], check=True,
                               capture_output=True)
            pa, pb = Path(a) / "zennox.skill", Path(b) / "zennox.skill"
            self.assertEqual(pa.read_bytes(), pb.read_bytes(), "build must be byte-identical")
            import zipfile
            names = zipfile.ZipFile(pa).namelist()
            self.assertIn("zennox/SKILL.md", names)        # folder name must equal skill name
            self.assertFalse([n for n in names if "__pycache__" in n or n.endswith(".pyc")])


class EnvFileInsideSkippedParent(unittest.TestCase):
    def test_env_check_ignores_parent_directory_names(self):
        with tempfile.TemporaryDirectory() as d:
            proj = Path(d) / "build" / "app"          # parent dir is named like a skipped dir
            proj.mkdir(parents=True)
            (proj / ".env").write_text("A=1\n", encoding="utf-8")
            (proj / ".gitignore").write_text("node_modules\n", encoding="utf-8")
            run("security_scan.py", str(proj))
            rep = json.loads((proj / ".zennox" / "security-report.json").read_text(encoding="utf-8"))
            self.assertIn("env-not-ignored", {f["rule"] for f in rep["findings"]})



class WindowsLineEndings(unittest.TestCase):
    """Git on Windows often checks files out with CRLF. Results must not change."""

    def test_crlf_gives_same_findings_as_lf(self):
        with tempfile.TemporaryDirectory() as lf, tempfile.TemporaryDirectory() as crlf:
            make_fixture(Path(lf), "\n")
            make_fixture(Path(crlf), "\r\n")
            for script, report in (("slop_check.py", "slop-report.json"),
                                   ("security_scan.py", "security-report.json")):
                run(script, lf)
                run(script, crlf)
                self.assertEqual(rules(Path(lf) / ".zennox" / report),
                                 rules(Path(crlf) / ".zennox" / report), script)
            run("project_graph.py", lf)
            run("project_graph.py", crlf)
            g_lf = json.loads((Path(lf) / ".zennox" / "graph.json").read_text(encoding="utf-8"))
            g_crlf = json.loads((Path(crlf) / ".zennox" / "graph.json").read_text(encoding="utf-8"))
            for key in ("edges", "cycles", "orphans", "layer_violations"):
                self.assertEqual(g_lf[key], g_crlf[key], key)


class MisbehavingTools(unittest.TestCase):
    """Windows runners have tools that print non-UTF-8 text (cp1252 '\u00a9') or hang.
    detect_env.py must report them, not crash or stall."""

    @staticmethod
    def _fake_tool(bindir: Path, name: str, body: str) -> None:
        impl = bindir / f"{name}_impl.py"
        impl.write_text(body, encoding="utf-8")
        if os.name == "nt":  # like npm.cmd / pnpm.cmd shims
            (bindir / f"{name}.cmd").write_bytes(f'@"{sys.executable}" "{impl}" %*\r\n'.encode())
        else:
            launcher = bindir / name
            launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{impl}" "$@"\n', encoding="utf-8")
            launcher.chmod(0o755)

    def test_non_utf8_output_and_hung_tool(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            bindir = Path(d) / "bin"
            proj = Path(d) / "proj"
            bindir.mkdir()
            proj.mkdir()
            self._fake_tool(bindir, "java", "import sys\nsys.stderr.buffer.write(b'java version \\xa9 Oracle\\n')\n")
            self._fake_tool(bindir, "dotnet", "import time\ntime.sleep(12)\n")
            start = time.monotonic()
            r = run("detect_env.py", str(proj), "--json",
                    extra_env={"PATH": str(bindir) + os.pathsep + os.environ.get("PATH", "")})
            elapsed = time.monotonic() - start
            self.assertEqual(r.returncode, 0, r.stderr)
            tools = json.loads(r.stdout)["tools"]
            self.assertIn("Oracle", tools["java"])
            self.assertIn("timed out", tools["dotnet"])
            self.assertLess(elapsed, 11, "a hung tool must not stall detect_env")

    def test_no_versions_flag(self):
        with tempfile.TemporaryDirectory() as d:
            r = run("detect_env.py", d, "--json", "--no-versions")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(all(v == "present" for v in json.loads(r.stdout)["tools"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
