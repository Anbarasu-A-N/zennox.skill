# 04 — Context, Memory, Model Routing & Cost

Three levers cut tokens and money without cutting quality: **read less** (graph), **remember
more** (memory), **pay less per token** (routing). Plus output discipline.

## Contents
1. Codebase graph (read the map, not the territory)
2. Project memory (three-layer recall)
3. Model routing and fallback
4. Token budget rules
5. Cost estimation for apps that call LLMs
6. Reporting gain

---

## 1. Codebase graph

`scripts/project_graph.py <repo>` parses import statements for JS/TS, Python, Go, Rust,
Dart, Kotlin and Swift, then writes `.zennox/graph.json` and `.zennox/GRAPH_REPORT.md`.

The report contains:
- **God nodes** — most-imported files. Usually shared utilities or core types. Read these
  first when orienting.
- **Hubs** — files that import the most. Often entry points or over-coupled modules.
- **Clusters** — files grouped by top-level directory with intra/inter edge counts; high
  inter-cluster coupling suggests a missing boundary.
- **Cycles** — import cycles (bugs waiting to happen in bundlers and test runners).
- **Orphans** — files nothing imports (dead code candidates, or entry points).
- **Layer violations** — `core`/`shared`/`domain` files importing platform modules
  (`react-native`, `electron`, `@tauri-apps`, `window`, `fs` …).

How to use it:
1. On first touch of a repo: build the graph, read the report (≈ 1–2k tokens instead of
   reading dozens of files).
2. Before answering "where is X / how does Y work": check the report and `graph.json`
   neighbours of the likely file, then open only those files.
3. Re-run after big changes; unchanged files are cached by SHA-256 so it's fast.

The script is regex-based and deliberately small. For deep semantic graphs (call graphs, docs,
PDFs, images in one graph) the user can install a dedicated tool such as graphify; this skill
doesn't require it.

## 2. Project memory

`scripts/memory.py` stores observations in `.zennox/memory.jsonl` (append-only, git-friendly,
human-readable). Each entry: id, timestamp, type, title, one-line summary, body, tags, files.

Types: `decision`, `bug`, `pattern`, `debt`, `preference`, `note`.

Three-layer retrieval keeps recall cheap:
1. `search "<query>"` → returns an **index**: id, type, title, score (≈ 15 tokens each).
2. `get <id> --summary` → the one-line summary + tags + files.
3. `get <id>` → full body. Only for the 1–3 entries that actually matter.

When to write:
- End of each lifecycle phase: decisions made, with the *why*.
- After fixing a non-obvious bug: symptom → root cause → fix → test name.
- User states a preference ("we use pnpm", "no Tailwind"): `--type preference`.
- Any deliberate shortcut: `--type debt`.

When to read: at session start (`list --limit 10` for recent context), and before any decision
that might already have been made. `compact` merges duplicate titles and drops superseded
entries (marked with `--supersedes <id>`).

Never store secrets, tokens, personal data or credentials in memory.

## 3. Model routing and fallback

Applies in two places: (a) how *you* split agentic work if the host supports sub-agents or
model selection, and (b) how the *app being built* calls LLMs.

Route by task, cheapest capable tier first:

| Task | Tier |
|---|---|
| Classification, extraction, formatting, short summaries, lint-style checks | Small / fast tier |
| Routine coding, refactors, test writing, most chat features | Mid tier |
| Architecture, hard debugging, security reasoning, long multi-step plans | Frontier tier |

Gateway pattern for apps (the idea behind routers like OmniRoute, LiteLLM, OpenRouter):
- One internal endpoint (OpenAI- or Anthropic-compatible) that the app calls; providers and
  models are configuration, not code.
- **Fallback chains:** ordered list per task; on rate limit, timeout or 5xx, try the next.
- **Resilience layers:** provider-level circuit breaker, per-key cooldown after 429s,
  per-model lockout after repeated failures.
- **Budgets:** per-user and per-feature token caps, enforced server-side.
- **Caching:** exact-match response cache for deterministic prompts; provider prompt caching
  for long, stable system prompts and documents (check the provider's docs for how and what it
  costs — for Claude see docs.claude.com).
- **Batch** non-interactive jobs (nightly summarisation, backfills) via the provider's batch
  API where offered; usually cheaper than synchronous calls.
- Keys live server-side only. Never ship provider keys in a web, mobile or desktop bundle.

Do not use or recommend routers' features for evading regional restrictions, provider terms
of service, or rate limits that are meant to apply to you.

## 4. Token budget rules

Input:
- Send excerpts with line numbers, not whole files. Send the graph report, not the tree.
- Summarise long tool outputs before reasoning over them (keep errors verbatim).
- Load references from this skill only when the mode needs them (see SKILL.md §1).
- Put stable instructions first and variable content last so prompt caches hit.

Output:
- Diffs or targeted edits instead of reprinting whole files.
- No restating the question, no recap of what you just did beyond one line.
- Code comments only where intent isn't obvious.
- Ask one question instead of writing three speculative versions.

## 5. Cost estimation for apps that call LLMs

Give the user a back-of-envelope table before they ship an AI feature:

```
monthly_cost ≈ users × sessions/user/month × calls/session
               × (input_tokens × input_price + output_tokens × output_price)
```

Show it at 1×, 10× and 100× users, with current prices looked up (don't quote prices from
memory), and with caching/routing savings as a separate column so the user sees what each
optimisation is worth.

## 6. Reporting gain

For `/zennox gain`, report only what you measured or can reasonably estimate, labelled as such:
files read vs. files in repo, memory hits that avoided re-investigation, dependencies avoided,
lines removed in trim passes, model-tier downgrades applied.
