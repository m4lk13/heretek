---
phase: 01-foundation-local-llm
verified: 2026-05-15T13:42:00Z
status: passed
score: 12/12 must-haves verified
re_verification:
  previous_status: none
  note: "Initial verification — no prior VERIFICATION.md existed."
---

# Phase 1: Foundation + Local LLM — Verification Report

**Phase Goal:** Strip the upstream Ouroboros cloud-LLM surface, rename the package to `heretek/`, swap the LLM client to local Ollama (qwen3.6:35b-a3b-q4_K_M + qwen3:4b), neuter budget tracking, and ship a Wave 0 smoke test harness whose subtests progressively flip from SKIP to PASS as the phase progresses.
**Outcome:** `python scripts/smoke_test.py` proves `import heretek` works, no cloud LLM hosts/keys remain, and the local Ollama server returns bilingual (RU+EN) replies through the patched `heretek.llm.LLMClient`.
**Verified:** 2026-05-15
**Status:** passed
**Re-verification:** No — initial verification.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `playground` branch is checked out and `last-known-good` tag dereferences to upstream v6.2.0 commit | ✓ VERIFIED | `git branch --show-current` → `playground`; `git rev-parse last-known-good^{commit}` and `git rev-parse v6.2.0^{commit}` both → `8344285bfb51c2cbb19df20c5dc85aaa4d0d3340` |
| 2 | Both git remotes configured: `origin` → user fork, `upstream` → razzant/ouroboros | ✓ VERIFIED | `git remote -v` shows `origin git@github.com:m4lk13/heretek.git` and `upstream https://github.com/razzant/ouroboros.git` |
| 3 | `ouroboros/` package fully renamed to `heretek/` — no remaining `ouroboros` imports in source | ✓ VERIFIED | `ls /Users/evgeniy/Projects/140526_heretek/ouroboros` → not found; `grep -rn "import ouroboros\|from ouroboros"` over `heretek/` + `supervisor/` returns zero matches; only intentional references are in `scripts/smoke_test.py` asserting the import fails |
| 4 | `supervisor/__main__.py` exists with at least `--help` working | ✓ VERIFIED | `python -m supervisor --help` exits 0 and prints usage including `--smoke`; `python -m supervisor --smoke` reports `smoke OK: supervisor.{state,workers} import cleanly` |
| 5 | `heretek/tools/{github,review,browser}.py` and root `heretek/review.py` are deleted | ✓ VERIFIED | All four `ls` calls return `No such file or directory`; `heretek/tools/` contents listed (no github/review/browser members) |
| 6 | No cloud LLM hosts (`openrouter.ai`, `api.openai.com`, `api.anthropic.com`) or env keys (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) inside `heretek/` or `supervisor/` | ✓ VERIFIED | `grep -rn "openrouter.ai\|api.openai.com\|api.anthropic.com"` → no matches; `grep -rn "OPENROUTER_API_KEY\|OPENAI_API_KEY\|ANTHROPIC_API_KEY"` → no matches; `test_no_cloud_hosts` smoke subtest PASS |
| 7 | `heretek/llm.py` routes to `http://localhost:11434/v1` with `api_key="ollama"` (env-overridable) | ✓ VERIFIED | `heretek/llm.py:98` reads `OLLAMA_API_KEY` with default `"ollama"`; `heretek/llm.py:105-107` reads `OLLAMA_BASE_URL` with default `http://127.0.0.1:11434/v1` (127.0.0.1 used instead of `localhost` to force IPv4 — documented at lines 99-104) |
| 8 | `OLLAMA_MODEL`, `OLLAMA_MODEL_LIGHT`, `HERETEK_MAX_CONTEXT_TOKENS` env vars recognized with sensible defaults | ✓ VERIFIED | `heretek/llm.py:242` defaults `OLLAMA_MODEL` → `qwen3.6:35b-a3b-q4_K_M`; `heretek/llm.py:268` defaults `OLLAMA_MODEL_LIGHT` → `qwen3:4b`; `heretek/context.py:44` defaults `HERETEK_MAX_CONTEXT_TOKENS` → `32000` (line 40 documents the cap rationale); `heretek/consciousness.py:87` honours `OLLAMA_MODEL_LIGHT` |
| 9 | `supervisor/state.py` budget neutered (no live HTTP, no cost calculation, counters preserved) | ✓ VERIFIED | `update_budget_from_usage` at `supervisor/state.py:276-310` accumulates `spent_calls`, `spent_tokens_{prompt,completion,cached}` but explicitly does NOT touch `spent_usd` (line 306-307 comment); `budget_remaining` returns `float("inf")`; `budget_pct` returns `0.0`; `set_budget_limit` is a no-op; `grep -n "httpx\|requests.get\|requests.post\|urllib\|urlopen"` over state.py returns no matches |
| 10 | JSONL token logger writes `{ts, model, prompt_tokens, completion_tokens, total}` to `logs/tokens.jsonl` | ✓ VERIFIED | `heretek/llm.py:38-61` implements `_log_tokens()` with exact schema; live log at `logs/tokens.jsonl` (11 lines) shows records like `{"ts": "2026-05-15T13:40:35.731132Z", "model": "qwen3:4b", "prompt_tokens": 19, "completion_tokens": 250, "total": 269}` |
| 11 | `python scripts/smoke_test.py --static-only` exits 0 with at least 2 PASS subtests (`test_package_rename`, `test_no_cloud_hosts`) | ✓ VERIFIED | Run output: `[PASS] test_package_rename`, `[PASS] test_no_cloud_hosts`, `Summary: 2 pass · 0 fail · 0 skip · 2 total`, EXIT_CODE=0 |
| 12 | With Ollama running and `qwen3:4b` pulled, full suite exits 0 with `test_bilingual_ollama_reply [RU]` and `[EN]` both PASS | ✓ VERIFIED | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` produced `[PASS] test_bilingual_ollama_reply [RU]: got 8 chars: 'Я понял.'` and `[PASS] test_bilingual_ollama_reply [EN]: got 18 chars: "I'm ready to help."`; `Summary: 4 pass · 0 fail · 0 skip · 4 total`, EXIT_CODE=0 |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `heretek/` (package) | Renamed from `ouroboros/`; importable | ✓ VERIFIED | Directory exists with `__init__.py`, `agent.py`, `apply_patch.py`, `consciousness.py`, `context.py`, `llm.py`, `loop.py`, `memory.py`, `owner_inject.py`, `tools/`, `utils.py`. `import heretek` succeeds (proven by smoke test). |
| `heretek/llm.py` | Routes to Ollama `localhost:11434/v1`; primary + light models from env | ✓ VERIFIED | LLMClient at lines 83-148; defaults to `http://127.0.0.1:11434/v1`; `OLLAMA_MODEL`/`OLLAMA_MODEL_LIGHT` env reads at lines 242/268; JSONL logger at lines 35-61 |
| `heretek/context.py` | Reads `HERETEK_MAX_CONTEXT_TOKENS` with 32000 default | ✓ VERIFIED | Line 44 reads env var with default 32000; cap rationale documented (32GB host OOM prevention) |
| `supervisor/__main__.py` | Local CLI entry point with `--help` and `--smoke` | ✓ VERIFIED | File exists; `python -m supervisor --help` exits 0; `--smoke` mode imports `supervisor.{state, workers}` cleanly and reports Ollama configuration |
| `supervisor/state.py` | Budget API preserved but neutered (no HTTP, no cost) | ✓ VERIFIED | Plan-04 neuter visible at lines 234-310 with explicit comments; counters preserved, `spent_usd` intentionally not accumulated |
| `scripts/smoke_test.py` | Executable, `--static-only` flag, 4 subtests, real assertions (not SKIP) | ✓ VERIFIED | File present (304 lines), executable bit set, argparse-driven, all 4 subtests flipped from SKIP to real checks (Plans 02/03/05) |
| `heretek/tools/github.py` | Should NOT exist | ✓ DELETED | `ls` returns "No such file or directory" |
| `heretek/tools/review.py` | Should NOT exist | ✓ DELETED | `ls` returns "No such file or directory" |
| `heretek/tools/browser.py` | Should NOT exist | ✓ DELETED | `ls` returns "No such file or directory" |
| `heretek/review.py` (root) | Should NOT exist | ✓ DELETED | `ls` returns "No such file or directory" |
| `.gitignore` | Contains `.env`, `logs/`, `.venv/`, `__pycache__/`, `*.jsonl` | ✓ VERIFIED | All five literal entries present (verified via `grep -E`) |
| `logs/tokens.jsonl` | Live JSONL token log with required schema | ✓ VERIFIED | File exists with 11 records; schema matches `{ts, model, prompt_tokens, completion_tokens, total}` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| git HEAD | branch `playground` | `git checkout playground` | ✓ WIRED | `git branch --show-current` → `playground` |
| tag `last-known-good` | upstream v6.2.0 commit | annotated tag | ✓ WIRED | Tag dereferences via `^{commit}` to `8344285bfb51c2cbb19df20c5dc85aaa4d0d3340` (matches `v6.2.0`) |
| `origin` remote | `<user>/heretek` GitHub repo | git remote | ✓ WIRED | `git@github.com:m4lk13/heretek.git` |
| `upstream` remote | `razzant/ouroboros` GitHub repo | git remote | ✓ WIRED | `https://github.com/razzant/ouroboros.git` |
| `heretek.llm.LLMClient` | Ollama `http://127.0.0.1:11434/v1` | `OpenAI(base_url=…)` with `OLLAMA_BASE_URL` override | ✓ WIRED | End-to-end bilingual call PASSes; proxy-bypass and IPv4-pin documented inline |
| `scripts/smoke_test.py::test_bilingual_ollama_reply` | `heretek.llm.LLMClient.chat()` | direct import + call | ✓ WIRED | RU + EN prompts return RU + EN replies on live qwen3:4b |
| `LLMClient.chat()` | `logs/tokens.jsonl` | `_log_tokens()` post-call | ✓ WIRED | 11 records appended; latest from this verification's smoke run (model=qwen3:4b, prompt=19, completion=250, total=269) |
| `supervisor.__main__` | `OLLAMA_MODEL` / `OLLAMA_MODEL_LIGHT` env | os.environ.get | ✓ WIRED | `--smoke` output reports `heretek primary=qwen3.6:35b-a3b-q4_K_M light=qwen3:4b base=http://localhost:11434/v1` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status in REQUIREMENTS.md | Evidence |
|-------------|-------------|-------------|---------------------------|----------|
| FORK-01 | 01-PLAN | Fork v6.2.0, clone, create `playground` + `last-known-good` branches | ✓ Complete | Truth #1, #2; merge commit + tag verified by git rev-parse |
| FORK-02 | 02-PLAN | Rename `ouroboros/` → `heretek/`; update pyproject/imports | ✓ Complete | Truth #3; `test_package_rename` PASS |
| FORK-03 | 03-PLAN | Remove `tools/{github,review,browser}.py` | ✓ Complete | Truth #5; all four files absent |
| FORK-04 | 04-PLAN | Neuter budget; token counter only | ✓ Complete | Truth #9, #10; state.py neuter + tokens.jsonl logger live |
| LLM-01 | 04-PLAN | Patch `heretek/llm.py` → Ollama `localhost:11434/v1`, api_key `"ollama"` | ✓ Complete | Truth #7; LLMClient routes to 127.0.0.1:11434/v1 |
| LLM-02 | 04-PLAN | Primary model `qwen3.6:35b-a3b-q4_K_M` via `OLLAMA_MODEL` | ✓ Complete | Truth #8; default at llm.py:242 |
| LLM-03 | 04-PLAN | Secondary model `qwen3:4b` via `OLLAMA_MODEL_LIGHT` | ✓ Complete | Truth #8; default at llm.py:268 and consciousness.py:87 |
| LLM-04 | 04-PLAN | Cap context to 32K via `HERETEK_MAX_CONTEXT_TOKENS` | ✓ Complete | Truth #8; context.py:44 defaults to 32000 |
| LLM-05 | 03-PLAN + 04-PLAN | No cloud fallback chain | ✓ Complete | Truth #6; `test_no_cloud_hosts` PASS |
| LLM-06 | 05-PLAN | Smoke test bilingual RU+EN via Ollama | ✓ Complete | Truth #12; `test_bilingual_ollama_reply [RU]` + `[EN]` both PASS |

**All 10 phase requirement IDs are marked Complete in REQUIREMENTS.md AND substantiated by verifiable evidence in the codebase.** No orphaned requirements detected — the phase's traceability table maps exactly to FORK-01..04 + LLM-01..06.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `heretek/consciousness.py` | 229 | `"provider": "openrouter"` literal string tag in `llm_usage` event payload | ℹ️ Info | Cosmetic — this is an event-classifier string for log aggregation, not a runtime routing decision. The actual LLM call uses `LLMClient` which routes to Ollama. Does NOT contradict must-have #6 (which targets hostnames + key names, not provider tags). |
| `heretek/context.py` | 211-212 | `state_data.get("openrouter_total_usd", 0)` budget-drift warning string | ℹ️ Info | Dead-code path — reads a key from state.json that is no longer written (FORK-04 neutered all `spent_usd` writes). The drift check defaults to 0 and never fires. Safe to remove in a future cleanup but does not block goal achievement. |
| `heretek/loop.py` | 27-34 | Hardcoded `_PRICING` table referencing `anthropic/claude-*`, `openai/o3` | ℹ️ Info | Legacy pricing dictionary. With budget neutered, the cost-multiplication paths return 0 even if these tags were used. No call site currently feeds these model names through the local Ollama client. |
| `heretek/utils.py` | 266-269 | Key-redaction regexes for `sk-ant-…`, `sk-or-…`, `sk-…` | ℹ️ Info | These are DEFENSIVE redaction patterns (used by `redact_secrets`), not key references. They protect log output from accidentally leaking any pre-existing cloud keys in environment. Correct behavior — keep. |
| `heretek/tools/vision.py` | 23 | `_DEFAULT_VLM_MODEL = "anthropic/claude-sonnet-4.6"` | ⚠️ Warning | Vision tool still references a cloud VLM model tag. Vision is out-of-scope for Phase 1 (LLM-01..06) and the tool is not wired into a runtime path that would fire a request — but this string is a future-tech-debt landmine when Phase 2/3 begins exercising tools. Suggest tracking in `deferred-items.md`. |

No 🛑 Blocker anti-patterns. No stubs hiding behind the goal. The two cloud-vendor residues that COULD have been blockers (LLM client routing, state.py HTTP cross-check) are both fully addressed; the residues listed above are cosmetic strings in unused/legacy paths.

### Human Verification Required

None for Phase 1 goal achievement — every must-have was verifiable programmatically:
- Code presence/absence via `ls`/`grep`
- Behavior via `python scripts/smoke_test.py` (both static-only and full)
- Bilingual response quality via the smoke test's character-class heuristic (Cyrillic-block-presence for RU, Latin-presence for EN)

For Phase 2 (Persona), the bilingual response *quality* (idiomatic Russian, in-character heresy register) WILL need human review — but that is out of scope for Phase 1's smoke-test bar, which only certifies "script class present in reply."

### Gaps Summary

No gaps. Phase 1 goal is fully achieved:

1. The fork is established — `playground` branch is the working surface, `last-known-good` tag is bolted to upstream v6.2.0 commit `8344285`, both remotes configured.
2. Package rename complete — `import heretek` works, `import ouroboros` fails as a load-bearing assertion in the smoke test.
3. Cloud LLM surface fully stripped — three deleted tool modules, zero cloud hostnames, zero cloud env keys.
4. Local Ollama wired — `LLMClient` routes to `127.0.0.1:11434/v1`, `OLLAMA_MODEL` + `OLLAMA_MODEL_LIGHT` + `HERETEK_MAX_CONTEXT_TOKENS` recognized with sensible defaults, supervisor `--smoke` confirms clean import.
5. Budget neutered — `update_budget_from_usage` preserves token counters but never touches `spent_usd`, no HTTP in state.py.
6. Token logger live — `logs/tokens.jsonl` is currently 11 records deep with the exact `{ts, model, prompt_tokens, completion_tokens, total}` schema.
7. Smoke test exits 0 in both modes — static-only with 2 PASS, full with 4 PASS including live RU+EN replies from `qwen3:4b`.

Phase 1 closes cleanly. Phase 2 (Persona) is unblocked and may begin.

---

*Verified: 2026-05-15T13:42:00Z*
*Verifier: Claude (gsd-verifier)*
