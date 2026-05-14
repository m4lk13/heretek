# Phase 1: Foundation + Local LLM - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Fork Ouroboros v6.2.0 to `heretek`, rename the Python package, strip out the modules that don't survive the cut, wire the LLM client at local Ollama, and smoke-test that a stripped supervisor boots and replies bilingually (RU + EN) without any cloud calls. No persona work (Phase 2), no self-mod guardrails (Phase 3), no Telegram wiring (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Repo & fork workflow
- Fork lives at the current project root: `/Users/evgeniy/Projects/140526_heretek/`. The fork's contents overlay this directory (which already holds CLAUDE.md and `.planning/`). CLAUDE.md's reference to `~/code/heretek` is superseded — update it during planning.
- Forked via `gh repo fork razzant/ouroboros --fork-name heretek --remote --clone`, renaming on GitHub to `heretek` in one step.
- Branches created immediately after clone, before any stripping work:
  - `playground` — all dev work happens here from this point forward
  - `last-known-good` — tagged at upstream HEAD on `main` at clone time (rollback target, refreshed in later phases)
- Upstream remote kept: `upstream` → `razzant/ouroboros`. Lets future-Claude cherry-pick upstream improvements (e.g. circuit-breaker fixes) without entangling git history.

### Stripping strategy
- **Hard delete** the unwanted modules — no stubs, no neutered placeholders:
  - `tools/github.py`
  - `tools/review.py` (the multi-model review tool)
  - `tools/browser.py` (Playwright)
  - Any multi-model review orchestration in `review.py` (the orchestrator file) — also hard-deleted
- All imports and call sites updated/removed in the same commit chain (don't leave dangling references).
- **Legacy cloud-LLM env-var loading code (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`):** strip the loading code entirely from `heretek/llm.py` / config. If those vars are still in someone's environment, they do nothing — silent ignore. No startup warnings, no hard errors.
- **Budget tracker (`supervisor/state.py` budget shape):** keep the module file and the public shape of `state.budget`. Swap the cost-calc internals to return `0` for any dollar-shaped value and accumulate prompt/completion token counts. Goal: minimal blast radius on upstream callers; everything that reads `state.budget` keeps working but reports tokens, not dollars.

### Token logger design
- Format: **JSONL** appended to `logs/tokens.jsonl` (in the repo root, mirrors upstream's `logs/state.jsonl` convention).
- Granularity: **per LLM call** — one record per request to Ollama (both primary and background models).
- Record fields (minimal): `{ts, model, prompt_tokens, completion_tokens, total}`. No prompt/completion text capture (avoid bloat, avoid logging chaotic content).
- Status surface: any upstream `/status` or status-line message that previously reported dollar spend now reports **session tokens + lifetime tokens** instead. No `$0.00` jokes — keep it honest about being free.

### Smoke test rigor
- Bar for "Phase 1 done": **end-to-end** — `python -m supervisor` boots, accepts a test-harness/stdin message, calls `heretek/llm.py`, gets a real Ollama reply. Tested in BOTH languages:
  - RU prompt → RU reply (e.g. "ответь по-русски одним предложением")
  - EN prompt → EN reply (e.g. "respond in one sentence")
- Test script location: `scripts/smoke_test.py` — a runnable Python script (not a pytest). Prints PASS/FAIL per check. Lower-ceremony than a test framework for a leisure project; easy to extend in later phases.
- "No cloud calls" verification: **static** — grep `heretek/` for `openrouter.ai`, `api.openai.com`, `api.anthropic.com`, and any leftover cloud-LLM key imports. Assert zero hits. No runtime network sniffing — static check is sufficient given the strip work.
- Model pull check: smoke test runs `ollama list` first; fails loud with a clear "pull `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b` before retrying" message if either model is missing. The `ollama pull` itself is NOT inside the plan — it's a precondition the test enforces (avoids blocking the plan on a 20GB download).

### Claude's Discretion
- Exact Python entry-point shape inside `python -m supervisor` for the smoke harness (stdin reader vs. a `--once` flag vs. a tiny harness module).
- Internal layout of `scripts/smoke_test.py` (single function vs. PASS/FAIL checklist with named subtests).
- Whether `logs/` is created at import time, on first write, or seeded by the fork commit.
- Whether stripping happens as one mega-commit or staged commits (any-staging is fine as long as `main` stays at clean upstream HEAD and all work lands on `playground`).
- Exact JSONL log rotation policy, if any (deferred — `logs/tokens.jsonl` can grow unbounded for v1).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project intent and architecture
- `CLAUDE.md` — Architecture diagram (§2), rationale for fork + Ollama + Qwen 3.6 (§3), risk register (§4), and full phase breakdown (§5). The §6 "Current state" block is the live status anchor; update it as Phase 1 progresses.
- `.planning/PROJECT.md` — Core value, constraints (32GB RAM ceiling, branch policy, network requirements), and Key Decisions table.
- `.planning/REQUIREMENTS.md` — FORK-01..04, LLM-01..06 are the requirements this phase delivers (§v1 Foundation & Fork and Local LLM sections).
- `.planning/ROADMAP.md` §"Phase 1: Foundation + Local LLM" — five Success Criteria that gate this phase.

### Upstream framework (read on disk after clone)
- `heretek/llm.py` (post-rename) — primary patch target for the Ollama swap (LLM-01, LLM-05).
- `heretek/agent.py`, `heretek/loop.py`, `heretek/context.py` — read to understand the orchestrator before changing LLM wiring.
- `supervisor/state.py` — budget shape lives here; surgically swap the cost internals (FORK-04).
- `tools/` directory — locate `github.py`, `review.py`, `browser.py` for hard delete (FORK-03).
- `review.py` (orchestrator at package root, not `tools/review.py`) — delete the multi-model orchestration logic.
- Upstream README/CHANGELOG on `razzant/ouroboros@v6.2.0` — sanity check that what's documented matches what's in the v6.2.0 tag before stripping.

### External
- `https://github.com/razzant/ouroboros` — upstream repo and v6.2.0 tag.
- `https://github.com/ollama/ollama` — Ollama HTTP API spec (OpenAI-compatible at `/v1`).

No external specs/ADRs beyond CLAUDE.md and the .planning/ docs — requirements are fully captured in the planning artifacts above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Current state of the repo
- Pre-clone. The project directory contains only `CLAUDE.md` and `.planning/`. The Ouroboros fork has not been pulled yet. **The first task of Phase 1 is the `gh repo fork` itself.**
- No existing code conventions to inherit yet — all conventions come from upstream Ouroboros v6.2.0 once the clone lands.

### Reusable assets (post-clone, inherited from Ouroboros)
- **Supervisor scaffold** (`supervisor/`): state, telegram, queue, workers, git_ops, events — keep wholesale.
- **Agent scaffold** (`ouroboros/` → `heretek/`): agent, consciousness, context, loop, llm, memory — keep, with `llm.py` as the patch target.
- **Tool plugins** (`tools/`): core file ops, shell (sandboxed), search — keep. github, review, browser — hard delete.
- **Circuit breaker** in `consciousness.py` (3 empty responses → pause) — preserve unchanged; matches Risk-register mitigation.
- **JSONL state logger** (`logs/state.jsonl`) — pattern is the basis for our new `logs/tokens.jsonl`.

### Established patterns (to be confirmed against the clone)
- OpenAI-compatible client expected as the LLM transport (per CLAUDE.md §3 + the existing OpenRouter wiring) — Ollama's `/v1` endpoint slots into this without a transport rewrite.
- Tool auto-discovery in `tools/__init__.py` (or equivalent) — verify behavior when files are deleted; ensure no `import` of removed modules survives.
- Env-var-driven config — pattern continues; just swap which vars are read.

### Integration points
- `heretek/llm.py` → Ollama at `http://localhost:11434/v1`, API key literal `"ollama"`.
- `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M` (primary), `OLLAMA_MODEL_LIGHT=qwen3:4b` (background consciousness).
- `HERETEK_MAX_CONTEXT_TOKENS=32000` — read by context assembly to cap below model's 262K window.
- New `logs/tokens.jsonl` — written by the patched LLM call site after each request completes.
- `scripts/smoke_test.py` — new file; smoke harness for the phase verification.

</code_context>

<specifics>
## Specific Ideas

- "Works on a train" is a live design value (PROJECT.md §Constraints) — the static grep + `ollama list` check both reinforce: this phase must produce a thing that runs with no network beyond `localhost:11434`.
- `last-known-good` is created at clone time pointing at upstream's clean state — its meaning shifts over time (it becomes "most recent working bot" once Phase 3 ships the auto-tag), but at end of Phase 1 it still points at upstream main. Keep that nuance in the plan.
- The bot does not need to be funny in Phase 1. Bilingual reply via Ollama is the bar. The chaos heretic shows up in Phase 2.

</specifics>

<deferred>
## Deferred Ideas

- **Token log rotation** — `logs/tokens.jsonl` grows unbounded in v1. If it ever becomes a problem, rotate by size or by month. Not now.
- **Network-level "no cloud" verification** (lsof / proxy / firewall rule during smoke test). Static grep is sufficient for v1.
- **Self-critique single-model review** as a tool — different from the upstream multi-model review we're deleting. Not requested; not in scope.
- **Pytest framework adoption** — smoke test is a script for now. If Phase 2/3 want a real test suite, revisit.
- **Browser tool reintroduction** for the v2 vision/screenshot experiment (EXP-02). Out of scope; tracked in REQUIREMENTS.md v2.
- **Bashkir language pre-flight** (EXP-01) — Phase 1 only verifies RU + EN.

</deferred>

---

*Phase: 01-foundation-local-llm*
*Context gathered: 2026-05-14*
