#!/usr/bin/env python3
"""Project memory with cheap three-layer recall. Stored in <root>/.zennox/memory.jsonl.

  add     --type decision|bug|pattern|debt|preference|note --title T [--body B] [--tags a,b]
          [--files f1,f2] [--supersedes ID]
  search  QUERY [--type T] [--limit N]     layer 1: index lines only (id, type, date, title)
  get     ID [--summary]                   layer 2 (--summary) or layer 3 (full entry)
  list    [--type T] [--limit N]           most recent first
  compact                                  drop superseded entries, merge exact duplicates

Global: --root PATH (default: current dir, or $ZENNOX_ROOT).
Refuses to store text that looks like a secret.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

TYPES = ("decision", "bug", "pattern", "debt", "preference", "note")
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|"
                    r"sk-ant-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9]{32,}|sk_live_[0-9A-Za-z]{20,}|"
                    r"xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_\-]{35})")
WORD = re.compile(r"[a-z0-9]+")


def store(root: Path) -> Path:
    d = root / ".zennox"
    d.mkdir(parents=True, exist_ok=True)
    return d / "memory.jsonl"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def save_all(path: Path, entries: list[dict]) -> None:
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")


def active(entries: list[dict]) -> list[dict]:
    superseded = {e["supersedes"] for e in entries if e.get("supersedes")}
    return [e for e in entries if e["id"] not in superseded]


def summarize(body: str, title: str) -> str:
    text = (body or title).strip().replace("\n", " ")
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return first[:160] + ("…" if len(first) > 160 else "")


def tokens(s: str) -> list[str]:
    return WORD.findall(s.lower())


def score(entries: list[dict], query: str) -> list[tuple[float, dict]]:
    q = tokens(query)
    if not q:
        return []
    docs = []
    for e in entries:
        fields = {"title": tokens(e["title"]), "tags": tokens(" ".join(e.get("tags", []))),
                  "body": tokens(e.get("body", "") + " " + " ".join(e.get("files", [])))}
        docs.append((e, fields))
    n = len(docs) or 1
    df = Counter()
    for _, f in docs:
        df.update(set(f["title"] + f["tags"] + f["body"]))
    results = []
    for e, f in docs:
        s = 0.0
        for t in q:
            idf = math.log(1 + n / (1 + df[t]))
            s += idf * (3 * f["title"].count(t) + 2 * f["tags"].count(t) + min(f["body"].count(t), 5))
        if s > 0:
            age_days = (time.time() - e.get("ts", 0)) / 86400
            results.append((s * (1 + 0.15 / (1 + age_days / 30)), e))  # slight recency boost
    return sorted(results, key=lambda x: -x[0])


def fmt_index(e: dict, s: float | None = None) -> str:
    date = time.strftime("%Y-%m-%d", time.localtime(e.get("ts", 0)))
    sc = f" {s:5.1f}" if s is not None else ""
    return f"{e['id']} | {e['type']:<10} | {date} |{sc} {e['title']}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.environ.get("ZENNOX_ROOT", "."))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--type", choices=TYPES, default="note")
    a.add_argument("--title", required=True)
    a.add_argument("--body", default="")
    a.add_argument("--tags", default="")
    a.add_argument("--files", default="")
    a.add_argument("--supersedes")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--type", choices=TYPES)
    s.add_argument("--limit", type=int, default=8)
    g = sub.add_parser("get"); g.add_argument("id"); g.add_argument("--summary", action="store_true")
    li = sub.add_parser("list"); li.add_argument("--type", choices=TYPES); li.add_argument("--limit", type=int, default=15)
    sub.add_parser("compact")
    args = ap.parse_args()

    path = store(Path(args.root).resolve())
    entries = load(path)

    if args.cmd == "add":
        blob = f"{args.title}\n{args.body}"
        if SECRET.search(blob):
            sys.exit("Refused: text looks like it contains a secret/credential. Store a reference instead.")
        ts = time.time()
        e = {"id": hashlib.sha1(f"{ts}{args.title}".encode()).hexdigest()[:8], "ts": ts, "type": args.type,
             "title": args.title.strip(), "summary": summarize(args.body, args.title), "body": args.body.strip(),
             "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
             "files": [f.strip() for f in args.files.split(",") if f.strip()]}
        if args.supersedes:
            if not any(x["id"] == args.supersedes for x in entries):
                sys.exit(f"No entry {args.supersedes} to supersede")
            e["supersedes"] = args.supersedes
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"saved {e['id']} ({e['type']}): {e['title']}")

    elif args.cmd == "search":
        pool = [e for e in active(entries) if not args.type or e["type"] == args.type]
        hits = score(pool, args.query)[: args.limit]
        if not hits:
            print("no matches"); return
        for sc, e in hits:
            print(fmt_index(e, sc))
        print(f"-- {len(hits)} shown. Use `get <id> --summary` then `get <id>` only for what matters.")

    elif args.cmd == "get":
        e = next((x for x in entries if x["id"].startswith(args.id)), None)
        if not e:
            sys.exit(f"no entry {args.id}")
        if args.summary:
            print(f"{fmt_index(e)}\n  {e['summary']}\n  tags: {', '.join(e['tags']) or '-'} · files: {', '.join(e['files']) or '-'}")
        else:
            print(json.dumps(e, indent=2, ensure_ascii=False))

    elif args.cmd == "list":
        pool = [e for e in active(entries) if not args.type or e["type"] == args.type]
        for e in sorted(pool, key=lambda x: -x.get("ts", 0))[: args.limit]:
            print(fmt_index(e))
        if not pool:
            print("empty")

    elif args.cmd == "compact":
        keep = active(entries)
        seen: dict[tuple, dict] = {}
        for e in sorted(keep, key=lambda x: x.get("ts", 0)):
            seen[(e["type"], e["title"].lower(), e.get("body", "").strip().lower())] = e  # latest wins
        result = sorted(seen.values(), key=lambda x: x.get("ts", 0))
        for e in result:
            e.pop("supersedes", None)
        save_all(path, result)
        print(f"compacted {len(entries)} → {len(result)} entries")


if __name__ == "__main__":
    import signal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles/CI
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # quiet when piped to head
    main()
