---
phase: 01-foundation-local-llm
plan: 04
subsystem: infra
tags: [python, ollama, llm-client, openai-sdk, qwen, token-logger, jsonl, budget-neuter, env-vars, context-cap, fork-04, llm-01, llm-02, llm-03, llm-04, llm-05]

# Dependency graph
requires:
  - phase: 01-foundation-local-llm-02
    provides: heretek/ Python package (post-rename); supervisor/__main__.py CLI entrypoint
  - phase: 01-foundation-local-llm-03
    provides: stripped LLMClient class shell with chat()/vision_query()/default_model()/available_models() bodies intact and ready for an Ollama swap on a clean canvas; supervisor/state.py with the OpenRouter ground-truth cross-check already removed
provides:
  - "heretek/llm.py — LLMClient defaults route to http://localhost:11434/v1 with api_key='ollama'; OpenAI Python SDK is wire-compatible with Ollama's /v1/chat/completions endpoint so chat()/vision_query() bodies are preserved"
  - "Module-level _log_tokens() that appends one JSONL record {ts, model, prompt_tokens, completion_tokens, total} to logs/tokens.jsonl after every chat() call (best-effort: I/O failures swallowed)"
  - "Module-level available_models() returning {main, code, light} dict with defaults qwen3.6:35b-a3b-q4_K_M and qwen3:4b (code aliases to main — Heretek runs everything on Qwen)"
  - "OLLAMA_MODEL / OLLAMA_MODEL_LIGHT env vars as the source of truth for model tag names; OLLAMA_BASE_URL / OLLAMA_API_KEY overridable transport knobs"
  - "heretek/consciousness.py — BackgroundConsciousness._model reads OLLAMA_MODEL_LIGHT (default qwen3:4b); HERETEK_BG_BUDGET_PCT (default 0) replaces OUROBOROS_BG_BUDGET_PCT"
  - "heretek/context.py — HERETEK_MAX_CONTEXT_TOKENS (default 32000) caps assembled message tokens via apply_message_token_soft_cap (was hardcoded 200000); tool-history compaction helper reads OLLAMA_MODEL_LIGHT"
  - "supervisor/state.py — budget_remaining() returns float('inf'); budget_pct() returns 0.0; set_budget_limit() is a no-op; update_budget_from_usage() preserves token accumulators (spent_calls / spent_tokens_prompt / completion / cached) and never accumulates spent_usd, never makes HTTP calls; public shape preserved so workers.assign_tasks() keeps working unchanged"
affects: [phase-01-plan-05, phase-02-persona, phase-03-guardrails, phase-04-launch]

# Tech tracking
tech-stack:
  added:
    - "Ollama (HTTP only — Python client is the existing openai SDK pointed at http://localhost:11434/v1 with api_key='ollama')"
  patterns:
    - "Best-effort logging contract: token logger swallows OSError and any other exception inside chat()'s call-site try/except; the LLM call path must never break on disk I/O — JSONL logging is observability, not the spine"
    - "OpenAI SDK + Ollama wire-compatibility: keep upstream OpenAI-shaped LLMClient code intact; only the constructor's base_url/api_key defaults change. No new dependencies needed."
    - "Public-shape preservation for the budget API: optional st parameter on budget_remaining(st=None) / budget_pct(st=None) lets both the plan's verification snippet (`budget_remaining()`) and the existing caller (`workers.assign_tasks() → budget_remaining(load_state())`) keep working without coordinated changes"
    - "Env-var rename via search-and-replace at the read site, not introducing parallel mechanisms: rename OUROBOROS_MODEL_LIGHT → OLLAMA_MODEL_LIGHT in place rather than adding a second function with a different name and a fallback chain"
    - "Context cap via env-var-with-default helper: _max_context_tokens() reads HERETEK_MAX_CONTEXT_TOKENS, falls back to 32000 on missing/invalid, called from the single existing call site in apply_message_token_soft_cap — no new abstraction layer"

key-files:
  created:
    - ".planning/phases/01-foundation-local-llm/01-04-SUMMARY.md — this file"
  modified:
    - "heretek/llm.py — LLMClient.__init__ defaults Ollama-shaped; available_models() now module-level returning {main, code, light} dict (instance shim preserved for any caller); default_model() reads OLLAMA_MODEL with Qwen primary default; _log_tokens() module-level + invoked from chat() after each response"
    - "supervisor/state.py — budget tracking neutered: cost zeroed permanently, inf/0.0 sentinels, no HTTP, token accumulators preserved"
    - "heretek/consciousness.py — _model property reads OLLAMA_MODEL_LIGHT (default qwen3:4b); OUROBOROS_BG_BUDGET_PCT → HERETEK_BG_BUDGET_PCT with default 0"
    - "heretek/context.py — _max_context_tokens() helper + wired into apply_message_token_soft_cap call site; OUROBOROS_MODEL_LIGHT in tool-history compaction → OLLAMA_MODEL_LIGHT"
    - ".planning/phases/01-foundation-local-llm/deferred-items.md — logged residual OUROBOROS_* env vars in non-modified files (loop.py, tools/*, supervisor/events.py, supervisor/workers.py) for a future env-var hygiene pass"

key-decisions:
  - "Module-level available_models() returns dict (per plan spec) AND instance LLMClient.available_models() returns List[str] (preserved for any upstream caller). Best of both worlds; zero caller breakage. Module-level is the new canonical entrypoint."
  - "budget_remaining / budget_pct now accept Optional[Dict] = None instead of the upstream required Dict[str, Any]. Lets the plan's no-arg verification snippet pass without breaking workers.assign_tasks()'s budget_remaining(load_state()) call."
  - "OUROBOROS_BG_BUDGET_PCT renamed to HERETEK_BG_BUDGET_PCT inside consciousness.py — same Plan-02 lowercase-sweep artifact class as the model env vars; default changed from '10' to '0' per CLAUDE.md §8 spec ('local inference is free; throttle off by default')."
  - "Soft cap reduced from upstream 200000 (cloud-budget-driven) to 32000 (Heretek M1 Max RAM-driven, per CLAUDE.md §4 Risk register). Override via HERETEK_MAX_CONTEXT_TOKENS env var."
  - "Cost accumulation line in update_budget_from_usage removed entirely (was already a no-op since cost is always 0 on local Ollama, but its presence encouraged the wrong mental model)."
  - "Residual OUROBOROS_* env vars in heretek/loop.py, heretek/tools/*, supervisor/events.py, supervisor/workers.py left in place per scope-boundary rule (plan's files_modified frontmatter scoped to llm/consciousness/context/state) — logged in deferred-items.md."

patterns-established:
  - "Best-effort observability logging pattern: separate try/except inside the LLM call function so logging failures cannot propagate into the LLM call path"
  - "Public-shape-preserving neuter: replace function bodies with sentinel returns while keeping signatures backward-compatible via optional parameters"
  - "Env-var rename at the read site only: avoid introducing parallel mechanisms or fallback chains; just rename in place and update the default value to match the new transport"

requirements-completed:
  - LLM-01
  - LLM-02
  - LLM-03
  - LLM-04
  - LLM-05
  - FORK-04

# Metrics
duration: 7min
completed: 2026-05-15
---

# Phase 01 Plan 04: Ollama swap + budget neuter Summary

**LLMClient now routes to local Ollama (`http://localhost:11434/v1`, api_key=`ollama`) with Qwen 3.6 / Qwen 3 4B model tags, soft-capped at 32K tokens, JSONL token logger writing `logs/tokens.jsonl`, and the supervisor budget tracker neutered to zero cost / no HTTP / preserved token accumulators.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-05-15T13:00:43Z
- **Completed:** 2026-05-15T13:07:18Z
- **Tasks:** 3
- **Files modified:** 4 source files (heretek/llm.py, heretek/consciousness.py, heretek/context.py, supervisor/state.py) + 1 deferred-items doc

## Accomplishments

- **LLM-01 + LLM-02:** `heretek/llm.py` `LLMClient.__init__` defaults to `http://localhost:11434/v1` with `api_key="ollama"`; `OLLAMA_BASE_URL` and `OLLAMA_API_KEY` env vars override transport. Module-level `available_models()` returns `{main: 'qwen3.6:35b-a3b-q4_K_M', code: 'qwen3.6:35b-a3b-q4_K_M', light: 'qwen3:4b'}` from `OLLAMA_MODEL` / `OLLAMA_MODEL_LIGHT` env vars.
- **LLM-03:** `heretek/consciousness.py` `BackgroundConsciousness._model` reads `OLLAMA_MODEL_LIGHT` (default `qwen3:4b`) — was the Plan-02 leftover `OUROBOROS_MODEL_LIGHT` with OpenRouter `qwen/qwen3.5-plus-02-15`. This is what keeps the 20GB primary from staying hot for the background ramble loop.
- **LLM-04:** `heretek/context.py` reads `HERETEK_MAX_CONTEXT_TOKENS` (default 32000) and caps `apply_message_token_soft_cap` accordingly — was hardcoded `200000`. Reduction is M1 Max RAM-driven, not cloud-budget-driven (per CLAUDE.md §4 Risk register).
- **LLM-05:** Static grep confirms no `openrouter.ai` / `api.openai.com` / `api.anthropic.com` references anywhere in `heretek/` or `supervisor/`. `test_no_cloud_hosts` still PASSES.
- **FORK-04 (budget neuter):** `supervisor/state.py` `update_budget_from_usage` accumulates token counters but never `spent_usd`; `budget_remaining()` returns `float('inf')`; `budget_pct()` returns `0.0`; no `requests.*` HTTP method calls anywhere in the module. Public shape preserved — `workers.assign_tasks()`'s `budget_remaining(load_state())` keeps working unchanged.
- **FORK-04 (token logger):** Module-level `_log_tokens(model, prompt_tokens, completion_tokens)` in `heretek/llm.py` appends one JSONL record to `logs/tokens.jsonl` after every `chat()` call. Best-effort: any I/O exception is swallowed so the LLM call path never breaks on disk errors. `logs/` is gitignored (no commit pollution).

## Task Commits

Each task was committed atomically:

1. **Task 1: Patch heretek/llm.py for Ollama + JSONL token logger** — `1257728` (feat)
2. **Task 2: Neuter supervisor/state.py budget; preserve public shape** — `ce51145` (refactor)
3. **Task 3: Wire OLLAMA_MODEL_LIGHT in consciousness, HERETEK_MAX_CONTEXT_TOKENS in context** — `341c4c4` (feat)

**Plan metadata commit:** [to be added when this file + STATE.md + ROADMAP.md are committed]

## Files Created/Modified

- `heretek/llm.py` — Ollama defaults; `_log_tokens` JSONL logger; module-level `available_models()` dict; `default_model()` reads `OLLAMA_MODEL`
- `heretek/consciousness.py` — `OLLAMA_MODEL_LIGHT` (default `qwen3:4b`); `HERETEK_BG_BUDGET_PCT` (default 0)
- `heretek/context.py` — `HERETEK_MAX_CONTEXT_TOKENS` (default 32000); compaction helper reads `OLLAMA_MODEL_LIGHT`
- `supervisor/state.py` — `budget_remaining/_pct` zero-cost sentinels; `update_budget_from_usage` token-only; no HTTP
- `.planning/phases/01-foundation-local-llm/deferred-items.md` — residual `OUROBOROS_*` env vars in out-of-scope files logged for follow-up

## Before / After Diffs

### LLMClient.__init__ (heretek/llm.py)

**Before (Plan 03 strip — empty defaults, will not call out):**
```python
def __init__(
    self,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    # No cloud env var fallback. Plan 04 will populate Ollama defaults.
    self._api_key = api_key or ""
    self._base_url = base_url or ""
    self._client = None
```

**After (Plan 04 — Ollama-routed):**
```python
def __init__(
    self,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    # Ollama defaults. Ollama ignores the api_key but the OpenAI SDK
    # requires a non-empty string — the literal "ollama" is conventional.
    self._api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama")
    self._base_url = base_url or os.environ.get(
        "OLLAMA_BASE_URL", "http://localhost:11434/v1"
    )
    self._client = None
```

### update_budget_from_usage (supervisor/state.py)

**Stripped (the dead-code cost-accumulation block):**
```python
cost = usage.get("cost") if isinstance(usage, dict) else None
if cost is None:
    cost = 0.0
st["spent_usd"] = _to_float(st.get("spent_usd") or 0.0) + _to_float(cost)
```

Note: the upstream `% 50` OpenRouter HTTP drift-check block was already gone (stripped in Plan 03 — see `.planning/phases/01-foundation-local-llm/01-03-SUMMARY.md` `key-files.modified` for `supervisor/state.py`). Plan 04 only removed the **dead-code cost-accumulation line** that remained pointing at a now-permanently-zero cost. The HTTP drift block was not in this file when Plan 04 began.

### consciousness.py model env var

**Before:**
```python
return os.environ.get("OUROBOROS_MODEL_LIGHT", "") or "qwen/qwen3.5-plus-02-15"
```

**After:**
```python
return os.environ.get("OLLAMA_MODEL_LIGHT", "") or "qwen3:4b"
```

### consciousness.py BG budget pct env var

**Before:**
```python
self._bg_budget_pct: float = float(
    os.environ.get("OUROBOROS_BG_BUDGET_PCT", "10")
)
```

**After:**
```python
self._bg_budget_pct: float = float(
    os.environ.get("HERETEK_BG_BUDGET_PCT", "0")
)
```

### context.py soft-cap

**Before:**
```python
# --- Soft-cap token trimming ---
messages, cap_info = apply_message_token_soft_cap(messages, 200000)
```

**After:**
```python
# --- Soft-cap token trimming ---
# Plan 04: cap from HERETEK_MAX_CONTEXT_TOKENS (default 32000).
messages, cap_info = apply_message_token_soft_cap(messages, _max_context_tokens())
```

Plus the new module-level helper:
```python
_DEFAULT_MAX_CONTEXT_TOKENS = 32000

def _max_context_tokens() -> int:
    raw = os.environ.get("HERETEK_MAX_CONTEXT_TOKENS", str(_DEFAULT_MAX_CONTEXT_TOKENS))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_CONTEXT_TOKENS
```

## Sample logs/tokens.jsonl record

From the post-commit verification invocation of `_log_tokens('t', 1, 2)`:
```jsonl
{"ts": "2026-05-15T13:06:18.936021Z", "model": "t", "prompt_tokens": 1, "completion_tokens": 2, "total": 3}
```
Schema confirmed: `ts` (ISO-8601 UTC with `Z` suffix), `model` (string), `prompt_tokens` / `completion_tokens` (ints), `total = prompt + completion`.

## Smoke test (--static-only) post-Plan-04

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/

Summary: 2 pass · 0 fail · 0 skip · 2 total
```

`test_bilingual_ollama_reply` remains SKIP — Plan 05's gate.

## Ollama connectivity probe

Out-of-band connectivity check (per env_notes — not added to the smoke suite):
```
OK: ollama reachable, /api/tags returned 3656 bytes
```
Ollama is running on the host. Plan 05 will exercise an actual `chat()` call against `qwen3:4b` (smallest model — fastest to verify the wire) to flip `test_bilingual_ollama_reply` from SKIP to PASS.

## Decisions Made

- **Module-level `available_models()` returns dict, instance method preserved.** Plan's pseudo-code shows module-level dict; existing upstream code uses instance method returning List. Did both — module-level is the new canonical entrypoint, instance method delegates to it for any upstream caller.
- **Optional `st` parameter on `budget_remaining` / `budget_pct`.** Lets both the plan's no-arg verification snippet and the existing `workers.assign_tasks()` caller (passing `load_state()`) work without coordinated changes. Keyword default is `None`, parameter is ignored.
- **Reduced upstream context soft-cap from 200000 to 32000.** Driven by M1 Max RAM headroom (CLAUDE.md §4 Risk register), not cloud cost. Override via `HERETEK_MAX_CONTEXT_TOKENS`.
- **Removed the `spent_usd` accumulation line entirely** in `update_budget_from_usage`. Was a no-op (cost always 0 on Ollama) but its presence encouraged the wrong mental model. Token accumulators preserved.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `OUROBOROS_BG_BUDGET_PCT` rename in consciousness.py**
- **Found during:** Task 3, while editing the same file for the `OUROBOROS_MODEL_LIGHT` → `OLLAMA_MODEL_LIGHT` rename.
- **Issue:** Plan 02's lowercase-only-sweep left this env var as `OUROBOROS_BG_BUDGET_PCT`, but CLAUDE.md §8 specifies `HERETEK_BG_BUDGET_PCT`. Same artifact class as the model env vars; the plan's scope covered only `*_MODEL_LIGHT` but the same file has two adjacent Plan-02 leftovers and the second is also inconsistent with the canonical env-var spec.
- **Fix:** Renamed in place, changed default from `'10'` to `'0'` per CLAUDE.md §8 (local inference is free; throttle off by default).
- **Files modified:** `heretek/consciousness.py` (one line)
- **Verification:** `grep -q "HERETEK_BG_BUDGET_PCT" heretek/consciousness.py` passes; `! grep -q "OUROBOROS_BG_BUDGET_PCT" heretek/consciousness.py` passes; module imports clean.
- **Committed in:** `341c4c4` (Task 3 commit)

**2. [Rule 3 - Blocking] `OUROBOROS_MODEL_LIGHT` rename in context.py (compaction helper)**
- **Found during:** Task 3, post-edit grep across modified files.
- **Issue:** Plan's Task 3 scope was "wire `HERETEK_MAX_CONTEXT_TOKENS`" but `context.py:645` also had a Plan-02 leftover `OUROBOROS_MODEL_LIGHT` reference with cloud default `x-ai/grok-3-mini`. Same file, same artifact class — fixing the cap without fixing the env var would leave context.py inconsistent with the OLLAMA_* canon.
- **Fix:** Renamed in place; default changed from `x-ai/grok-3-mini` to `qwen3:4b`.
- **Files modified:** `heretek/context.py` (one line)
- **Verification:** No new failing tests; smoke test --static-only still 2 PASS.
- **Committed in:** `341c4c4` (Task 3 commit)

### Logged as deferred (out of scope per files_modified frontmatter)

Several files outside the plan's `files_modified` list still reference `OUROBOROS_*` env vars (with cloud-era default values). These were intentionally NOT fixed per the scope-boundary rule:

- `heretek/loop.py:611,674` — `OUROBOROS_MAX_ROUNDS`, `OUROBOROS_MODEL_FALLBACK_LIST`
- `heretek/tools/core.py:261` — `OUROBOROS_MODEL_LIGHT` / `OUROBOROS_MODEL` (with default `anthropic/claude-sonnet-4.6`)
- `heretek/tools/vision.py:28,145,184` — `OUROBOROS_MODEL`
- `heretek/tools/self_portrait.py:208`, `heretek/tools/dashboard.py:241` — `OUROBOROS_MODEL` (status strings only)
- `heretek/tools/evolution_stats.py:28` — `OUROBOROS_REPO_DIR`
- `heretek/tools/git.py:65` — `OUROBOROS_PRE_PUSH_TESTS`
- `supervisor/events.py:264` — `OUROBOROS_MODEL_LIGHT` (with default `x-ai/grok-3-mini`)
- `supervisor/workers.py:51` — `OUROBOROS_WORKER_START_METHOD`

Recorded in `.planning/phases/01-foundation-local-llm/deferred-items.md` for a future env-var hygiene plan (suggest Phase 02 or a dedicated Phase-01 cleanup pass).

---

**Total deviations:** 2 auto-fixed (both Rule 3 Blocking — env-var consistency within already-being-edited files)
**Impact on plan:** Both auto-fixes were within the plan's `files_modified` scope and necessary for consistency with the OLLAMA_* / HERETEK_* canon established by this plan. No scope creep — out-of-scope files were logged, not fixed.

## Issues Encountered

- **None.** Plan executed as written; the only friction was the verification-snippet vs upstream-signature mismatch on `budget_remaining/_pct(st)`, resolved by making `st` optional.

## Unexpected references audit

Per the plan's `<output>` clause ("Whether any unexpected references to `OUROBOROS_*` / `HERETEK_MODEL_*` env vars surfaced outside the expected files") — yes, see "Logged as deferred" above. These were already known and tracked from Plan 02's lowercase-only-sweep decision; this Plan 04 audit confirms the inventory.

## Next Plan Readiness

- **Ready for Plan 05** (smoke-test flip): Ollama is reachable on `localhost:11434` (out-of-band probe returned 3656 bytes of `/api/tags`); `LLMClient` wiring is verified statically; `_log_tokens` writes valid JSONL; no cloud-host regex hits; module web imports clean. Plan 05 should be able to flip `test_bilingual_ollama_reply` from SKIP to a real RU/EN round-trip against `qwen3:4b` (the small model — cheaper to verify the wire than pulling `qwen3.6:35b-a3b-q4_K_M`).
- **Open concerns:**
  - Residual `OUROBOROS_*` env vars in non-modified files (see deferred-items.md) — if Plan 05's real Ollama call touches the tool-loop fallback chain (heretek/loop.py:674) or any tool, the cloud-era defaults may surface as actual mis-routes. Recommend a quick pre-Plan-05 sanity sweep of the call path before flipping the smoke test.
  - `qwen3.6:35b-a3b-q4_K_M` model pull (~20GB) still required before any production use — `ollama list` should be confirmed before Phase 4 launch (already in STATE.md blockers).

## Self-Check: PASSED

- Created files exist: `01-04-SUMMARY.md`, `deferred-items.md` (updated with Plan 04 entries)
- Modified files exist: `heretek/llm.py`, `supervisor/state.py`, `heretek/consciousness.py`, `heretek/context.py`
- Commits exist: `1257728` (Task 1 — llm.py + token logger), `ce51145` (Task 2 — budget neuter), `341c4c4` (Task 3 — env-var wiring)

---
*Phase: 01-foundation-local-llm*
*Completed: 2026-05-15*
