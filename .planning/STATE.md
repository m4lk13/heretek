---
gsd_state_version: 1.0
milestone: v6.2
milestone_name: milestone
status: unknown
stopped_at: Completed 02-01-PLAN.md (persona surface rewrite)
last_updated: "2026-05-16T08:36:14.809Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 7
  completed_plans: 6
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-14)

**Core value:** A bot the owner enjoys talking to — persistent identity, bilingual RU/EN by reflex, free local inference, self-modification gated by an approval workflow
**Current focus:** Phase 02 — persona-identity

## Current Position

Phase: 02 (persona-identity) — EXECUTING
Plan: 2 of 2

## Performance Metrics

**Velocity:**

- Total plans completed: 5
- Average duration: ~9 min
- Total execution time: ~46 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-foundation-local-llm | 5 | ~46 min | ~9 min |

**Recent Trend:**

- Last 5 plans: 01-01 (~10 min), 01-02 (5 min, 3 tasks, 43 files), 01-03 (9 min, 4 tasks, 15 files), 01-04 (~7 min, 3 tasks, 5 files), 01-05 (~15 min, 3 tasks, 4 files)
- Trend: stable; Plan 05 longer due to two real-Ollama-call deviation fixes (IPv6 fallback, system-proxy bypass)

*Updated after each plan completion*

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01-foundation-local-llm P03 | 9 min | 4 tasks | 15 files |
| Phase 01-foundation-local-llm P04 | 7 min | 3 tasks | 5 files |
| Phase 01-foundation-local-llm P05 | 15 min | 3 tasks | 4 files |
| Phase 02-persona-identity P01 | 8 min | 3 tasks | 7 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Planning: Merged CLAUDE.md §5 Phases 0+1 into Phase 1, Phases 4+5 into Phase 4 (coarse granularity, 4 phases total)
- Planning: SAFE-* requirements placed entirely in Phase 3 — guardrails must be complete before Phase 4 launch
- Phase 01-01: Fork-and-overlay (gh repo fork --clone=false + git merge --allow-unrelated-histories) preserves pre-existing .planning/ and CLAUDE.md without subdirectory shuffle
- Phase 01-01: last-known-good annotated tag placed at upstream v6.2.0 commit 8344285b (not the merge commit) — gives /heresy a clean rollback target
- Phase 01-01: First push to origin deferred to Plan 05 — first public visibility should carry stripped/renamed Heretek code, not raw upstream Ouroboros
- Phase 01-01: Smoke-test SKIP-then-flip pattern — Wave 0 scaffold ships subtests as SKIP (exit 0); Plans 02/03/04/05 flip each to a real check as features land
- [Phase 01-foundation-local-llm]: Bulk rename via git mv + perl sweep landed as a single atomic commit (32-file rename detected at 82-100% similarity); preserves no half-renamed HEAD
- [Phase 01-foundation-local-llm]: Lowercase-only sweep: replaced 'ouroboros' but not 'Ouroboros'/'OUROBOROS' — case-variant env vars (OUROBOROS_MODEL, etc.) intentionally left for Plan 04's OLLAMA_* rename
- [Phase 01-foundation-local-llm]: Stub the full boot path in supervisor/__main__.py: upstream v6.2.0 has no run()/start()/main() entry function — boot logic is at module scope in colab_launcher.py and gated on cloud secrets. --help + --smoke work today; full boot deferred to Plans 03/04/05
- [Phase 01-foundation-local-llm]: Added project root to sys.path in scripts/smoke_test.py — pre-existing scaffold bug surfaced once test_package_rename stopped returning SKIP; Python sets sys.path[0] to scripts/ not cwd when invoked as 'python scripts/smoke_test.py'
- [Phase 01-foundation-local-llm]: Plan 03 (strip) — Hard-delete-no-stubs: tool registry's pkgutil.iter_modules + try/except silently skips deleted files, so no registry edits needed when removing tool modules
- [Phase 01-foundation-local-llm]: Plan 03 (strip) — Expanded scope to delete tools/health.py + tools/search.py and strip supervisor/state.py + tools/shell.py [Rule 3 - Blocking]; plan author explicitly authorized supervisor/state.py and shell.py strips in Task 4 acceptance criteria ('do not loosen the regex — fix the source')
- [Phase 01-foundation-local-llm]: Plan 03 (strip) — Preserve LLMClient class shell with chat/vision_query/default_model/available_models for Plan 04's Ollama patch; OpenAI client is wire-compatible with Ollama /v1 endpoint so only __init__ defaults need to change
- [Phase 01-foundation-local-llm]: Plan 03 (strip) — Vision/screenshot tools (vision.py, parts of core.py) left in place as permanent no-ops rather than deleted; logged in deferred-items.md for Plan 04/05 follow-up (preserves a tight strip surface)
- [Phase 01-foundation-local-llm]: Plan 04 (Ollama swap) — OpenAI Python SDK is wire-compatible with Ollama's /v1 endpoint; LLMClient swap was a defaults-only change (base_url + api_key='ollama'), no new dependencies, chat()/vision_query() bodies preserved
- [Phase 01-foundation-local-llm]: Plan 04 — Module-level available_models() returns {main, code, light} dict (per plan spec) AND instance LLMClient.available_models() returns List[str] (preserved for upstream callers); module-level is the new canonical entrypoint
- [Phase 01-foundation-local-llm]: Plan 04 — budget_remaining(st=None) / budget_pct(st=None) optional-parameter pattern lets plan's no-arg verification snippet AND existing workers.assign_tasks(load_state()) caller work without coordinated changes
- [Phase 01-foundation-local-llm]: Plan 04 — Soft cap reduced from upstream 200000 to 32000 (HERETEK_MAX_CONTEXT_TOKENS), M1 Max RAM-driven not cloud-budget-driven; override-able via env var
- [Phase 01-foundation-local-llm]: Plan 04 — Removed spent_usd accumulation line entirely (dead code on Ollama); token accumulators preserved for observability
- [Phase 01-foundation-local-llm]: Plan 04 — Residual OUROBOROS_* env vars in heretek/loop.py, heretek/tools/*, supervisor/events.py, supervisor/workers.py left in place per scope-boundary rule; logged in deferred-items.md for a future env-var hygiene pass
- [Phase 01-foundation-local-llm]: Plan 05 — LLMClient default base URL forced to IPv4 (`http://127.0.0.1:11434/v1`); httpx does not fall back IPv6→IPv4 on connect-refused, so `localhost` resolved AAAA→A would surface as `APIConnectionError: Connection error.` even with Ollama healthy. Discovered during smoke-test bilingual flip.
- [Phase 01-foundation-local-llm]: Plan 05 — LLMClient uses `httpx.Client(trust_env=False)` to bypass macOS system-wide HTTP proxies (scutil --proxy). Python's urllib.request.getproxies() does NOT honor the macOS exception list, so a localhost-scoped proxy still gets applied to `127.0.0.1:11434` and fails with "Server disconnected without sending a response." OLLAMA_BASE_URL is local by design — bypassing env-discovered proxies is correct.
- [Phase 01-foundation-local-llm]: Plan 05 — Smoke test bilingual subtest uses `OLLAMA_MODEL` (primary by default); on low-RAM hosts the 24GB primary can OOM Ollama mid-load. Smoke test prints an actionable hint suggesting `OLLAMA_MODEL=qwen3:4b` override. Verified GREEN: 4 PASS with light-model override; FAIL-with-hint when default 24GB model OOMs.
- [Phase 01-foundation-local-llm]: Plan 05 — CLAUDE.md model size 20GB→24GB correction across §0/§2/§3/§4/§5; §6 Current state flipped from "Pre-Phase 0" to a Phase-1-complete summary with resume protocol pointing at `scripts/smoke_test.py --static-only` as the fast-feedback gate.
- [Phase 02-persona-identity]: Plan 02-01: STALE IDENTITY threshold preserved at age_hours > 8 (RESEARCH Open Q1 explicit resolution — CONTEXT.md said '4h' loosely; actual upstream code is 8h; only warning STRING retuned for chaos-heretek voice, logic untouched)
- [Phase 02-persona-identity]: Plan 02-01: Forbidden upstream-name strings ('Ouroboros' / 'Уроборос') strictly purged from BIBLE.md and prompts/SYSTEM.md — even fork-from labels and inheritance prose. Rewrote to 'upstream forge-world constitution' / 'my upstream ancestor' framing to preserve the inheritance-and-corruption narrative
- [Phase 02-persona-identity]: Plan 02-01: SYSTEM.md landed at 20472 bytes (below soft band lower bound 22KB) — warn-only; natural consequence of dropping cloud-era scaffolding (Google Colab paths, OpenRouter env vars, multi-model review, knowledge base, tech-radar) that does not apply to local-laptop Heretek scope. Self-concept proxy floor (>10KB) satisfied; combined 40814 within combined warn band 38000-75000

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 4 requires Telegram bot token and owner user ID — these are not needed until Phase 4 begins (per PROJECT.md Key Decisions)
- 32GB host RAM constraint: 24GB primary model can OOM Ollama under memory pressure during fresh load. Verified during Plan 05 smoke test. Workaround: use `OLLAMA_MODEL=qwen3:4b` for cheap-wire verification; close other memory hogs before invoking the primary model. Phase 4 production may need the same workaround on this host class.
- Residual OUROBOROS_* env vars remain in non-Plan-04-modified files (heretek/loop.py, tools/*, supervisor/events.py, supervisor/workers.py) — see .planning/phases/01-foundation-local-llm/deferred-items.md. Did NOT surface during Plan 05's bilingual smoke test because `LLMClient.chat()` is called directly without going through the tool loop or fallback chain. Phase 2 (persona) will exercise the full prompt assembly path and may need to clear these.

## Session Continuity

Last session: 2026-05-16T08:36:14.807Z
Stopped at: Completed 02-01-PLAN.md (persona surface rewrite)
Resume file: None
Recommended next: `git push -u origin playground` to publish stripped/renamed Heretek to GitHub (first public visibility), then plan Phase 2.
