---
phase: 01-foundation-local-llm
plan: 05
subsystem: testing
tags: [python, ollama, smoke-test, llm-client, qwen, bilingual, ipv4, httpx, proxy-bypass, phase-1-close, llm-06]

# Dependency graph
requires:
  - phase: 01-foundation-local-llm-04
    provides: heretek.llm.LLMClient wired to Ollama with chat() returning (msg_dict, usage_dict); module-level available_models() returning {main, code, light}; logs/tokens.jsonl JSONL token logger
  - phase: 01-foundation-local-llm-01
    provides: scripts/smoke_test.py Wave-0 scaffold with three SKIP placeholders and --static-only flag
provides:
  - "scripts/smoke_test.py — full end-to-end smoke test: package rename, no cloud hosts, models-pulled precondition (ollama list), bilingual RU+EN Ollama reply via heretek.llm.LLMClient with char-class assertions (Cyrillic for RU, Latin for EN)"
  - "scripts/smoke_test.py — actionable failure UX: missing-model FAIL prints exact `ollama pull <tag>` lines; ollama-down FAIL prints `ollama serve` remediation; chat() connection-error FAIL probes Ollama liveness and prints `OLLAMA_MODEL=qwen3:4b` low-RAM cheat-code"
  - "heretek/llm.py — LLMClient default base URL forced to IPv4 (http://127.0.0.1:11434/v1) to bypass httpx's broken IPv6→IPv4 fallback when Ollama binds AF_INET only"
  - "heretek/llm.py — LLMClient's httpx transport uses trust_env=False to bypass macOS system-wide HTTP proxies (scutil --proxy) that intercept localhost when the proxy exception list is not honored by Python's urllib.request.getproxies()"
  - "CLAUDE.md — model size corrected 20GB → 24GB across §0/§2/§3/§4/§5; §6 Current state rewritten as Phase-1-complete summary with resume protocol; ~/code/heretek path corrected to in-place project root; Phase 0+1 checklist items marked [x]"
  - "Phase 1 administratively closed: ROADMAP.md Phase 1 [x] with 5/5 Complete; STATE.md completed_phases 0→1, completed_plans 4→5, Current Position pivoted to Phase 2; REQUIREMENTS.md LLM-06 Partial → Complete; traceability shows all 10 Phase-1 reqs Complete"
affects: [phase-02-persona, phase-03-guardrails, phase-04-launch]

# Tech tracking
tech-stack:
  added:
    - "(none — Plan 05 is a verification + correctness plan, no new dependencies)"
  patterns:
    - "Smoke-test precondition pattern: fail-loud-with-remediation. `check_models_pulled` runs FIRST in the full suite, separately from the bilingual subtest, so a missing model never gets misdiagnosed as a code defect. FileNotFoundError → install instruction; TimeoutExpired → `ollama serve` hint; missing tags → exact `ollama pull <tag>` lines."
    - "Best-effort response-shape extraction: `_extract_content()` helper handles three return shapes (tuple-of-(msg_dict, usage_dict) — the Plan-04 canonical shape; OpenAI SDK object; plain dict from .model_dump()) so the smoke test survives small contract drift in LLMClient.chat() without coordinated change."
    - "Char-class assertion for bilingual verification: regex `[Ѐ-ӿ]` (Cyrillic U+0400–U+04FF) for RU, `[A-Za-z]` for EN. Asserts AT LEAST ONE character of the target script — a mixed-script reply (Russian with embedded English tech terms) still PASSes for RU. Matches VALIDATION.md's 'basic char-class heuristic.'"
    - "IPv4 default for localhost backends: any OpenAI-SDK-compatible local backend (Ollama, LM Studio, llamafile) should default to `http://127.0.0.1:port/v1` rather than `localhost:port/v1` because httpx does not fall back AAAA→A on Connection-Refused (unlike curl)."
    - "trust_env=False as a hard isolation knob for localhost-only HTTP clients: when the backend is always local, picking up env-discovered proxies is never correct."

key-files:
  created:
    - ".planning/phases/01-foundation-local-llm/01-05-SUMMARY.md — this file"
  modified:
    - "scripts/smoke_test.py — replaced test_bilingual_ollama_reply SKIP placeholder with a real end-to-end RU+EN call via heretek.llm.LLMClient; added check_models_pulled precondition; added _extract_content helper for response-shape resilience; added Ollama-liveness probe in failure path with OLLAMA_MODEL=qwen3:4b cheat-code suggestion; removed all SKIP-returning paths"
    - "heretek/llm.py — default base URL `localhost` → `127.0.0.1` (IPv4 force); _get_client passes `http_client=httpx.Client(trust_env=False)` to OpenAI(); both fixes inline-documented"
    - "CLAUDE.md — top-of-file Status: 'Planning phase — v0.0.0' → 'Phase 1 complete (Foundation + Local LLM) — v0.1.0'; §0–§5 20GB→24GB and ~12GB→~8GB headroom; §5 ~/code/heretek path removed and overlaid-in-place marker added; §5 Phase 0 + Phase 1 checklist items marked [x]; §6 Current state fully rewritten as Phase-1-complete resume protocol; Phase 0 smoke-test command line annotated with `scripts/smoke_test.py` reference"
    - ".planning/ROADMAP.md — Phase 1 list item flipped [ ]→[x]; Plan 05 row flipped [ ]→[x]; progress table Phase 1 row updated to '5/5 | Complete | 2026-05-15'"
    - ".planning/STATE.md — frontmatter completed_phases 0→1, completed_plans 4→5; Current Position pivoted to Phase 2 with 25% progress bar; Performance Metrics: Plan 05 row added (15min, 3 tasks, 4 files); Decisions: 5 new entries (IPv4 default, trust_env proxy bypass, light-model OOM workaround, CLAUDE.md 24GB correction, smoke-test design); Blockers: replaced 'qwen3.6 not pulled' with '32GB host OOM' operational concern, replaced 'residual OUROBOROS_* in tool-loop' with 'did not surface in direct-chat path; Phase 2 to clear'; Session Continuity: stopped_at flipped to Phase-1-complete, recommended next is git push -u origin playground"
    - ".planning/REQUIREMENTS.md — LLM-06 checkbox [ ]→[x] with inline note on light-model verification path; traceability table LLM-06 Partial → Complete; footer date 2026-05-14 → 2026-05-15"

key-decisions:
  - "Defaulted LLMClient base URL to 127.0.0.1 (not localhost). Forced IPv4 to bypass httpx's broken IPv6→IPv4 fallback on Connection-Refused. Curl tolerates this; httpx does not. Users can override via OLLAMA_BASE_URL."
  - "Passed http_client=httpx.Client(trust_env=False) to the OpenAI() constructor in LLMClient._get_client. Bypasses macOS system-wide HTTP proxies (scutil --proxy) that Python's urllib.request.getproxies() picks up but does not honor the exception list for. Safe for all Heretek calls because OLLAMA_BASE_URL is always local by design."
  - "Smoke test uses OLLAMA_PRIMARY (= os.environ.get('OLLAMA_MODEL', 'qwen3.6:35b-a3b-q4_K_M')) for the bilingual call, NOT the light model. Light-model use is the documented escape hatch (`OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py`), not the default. Smoke-test default exercises the production wire."
  - "Connection-error path now actively probes Ollama liveness via subprocess curl and emits a remediation hint that names the specific failure mode (OOM during 24GB model load) and the specific cheat-code (OLLAMA_MODEL=qwen3:4b). Makes the smoke test self-documenting for new operators."
  - "CLAUDE.md §3 headroom revised down from ~12GB to ~8GB. The original estimate did not account for system memory pressure on macOS Tahoe; verified empirically that 24GB model + 32GB host = OOM under realistic conditions."

patterns-established:
  - "Fail-loud preconditions before behavioral subtests: a missing dependency must be diagnosed with a remediation command, never silently turn into a chat() exception buried in a stack trace."
  - "Liveness probing in failure paths: when a downstream service can crash mid-operation (Ollama OOM during model load), the failure handler should re-check liveness and emit a hint that distinguishes 'service crashed' from 'service rejected the request'."
  - "Robustness fixes are runtime-correctness, not test-only fixes: when the smoke test exposes a localhost-routing bug, fix the runtime client (heretek/llm.py), not the test. The actual bot would hit the same failures."

requirements-completed:
  - LLM-06

# Metrics
duration: 20min
completed: 2026-05-15
---

# Phase 01 Plan 05: Phase-1 close-out + bilingual smoke flip Summary

**Phase 1 (Foundation + Local LLM) administratively closed. Smoke test `test_bilingual_ollama_reply` flipped from SKIP to a real end-to-end RU+EN call via `heretek.llm.LLMClient` against Ollama, with a `check_models_pulled` precondition and an actionable failure path. Two `heretek/llm.py` robustness fixes landed during deviations: IPv4 default base URL (httpx IPv6 fallback bug) and `trust_env=False` httpx transport (macOS system-proxy bypass). CLAUDE.md model size corrected 20GB→24GB, host path updated, §6 marked Phase-1-complete. All 10 Phase-1 requirements (FORK-01..04, LLM-01..06) traceable to commits on `playground`.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-05-15T13:13:02Z
- **Completed:** 2026-05-15T13:33:44Z
- **Tasks:** 3
- **Files modified:** 5 source/doc files (scripts/smoke_test.py, heretek/llm.py, CLAUDE.md, .planning/ROADMAP.md, .planning/STATE.md, .planning/REQUIREMENTS.md)

## Accomplishments

- **LLM-06 fully delivered:** `test_bilingual_ollama_reply` now does a real RU prompt + real EN prompt through `heretek.llm.LLMClient`, asserts each reply is non-empty and contains at least one Cyrillic / Latin character respectively. Verified GREEN with `OLLAMA_MODEL=qwen3:4b` (Russian: "Помогу вам на русском языке." / English: clean English sentence). With default 24GB primary model the test fails-with-actionable-hint (Ollama OOMs on this 32GB host under memory pressure).
- **Precondition gate added:** `check_models_pulled` runs FIRST in the full suite (NOT in `--static-only`, which stays a 3s no-Ollama fast-feedback gate). Distinguishes three failure modes: no ollama CLI, ollama serve down, models not pulled. Each prints its exact remediation command.
- **Two LLMClient robustness fixes (deviation Rule 1 — bugs):**
  - IPv4 forced default base URL: `localhost:11434` → `127.0.0.1:11434`. httpx does not retry AF_INET when AF_INET6 returns ECONNREFUSED, surfacing as `APIConnectionError: Connection error` even with Ollama healthy on IPv4.
  - `trust_env=False` httpx transport: macOS users with a system-wide HTTP proxy (scutil --proxy showing HTTPProxy 127.0.0.1:1082 etc.) would have all localhost traffic intercepted because Python's `urllib.request.getproxies()` does not honor the macOS proxy exception list.
- **CLAUDE.md corrected:** all 20GB references → 24GB; headroom 12GB → 8GB with explanation; `~/code/heretek` path → in-place project root marker; §5 Phase 0+1 checklists marked [x]; §6 Current state rewritten as Phase-1-complete summary with resume protocol; top-of-file Status: v0.0.0 → v0.1.0.
- **Phase 1 closed:** ROADMAP.md Phase 1 [x] (5/5 Complete 2026-05-15); STATE.md completed_phases 0→1, Current Position pivots to Phase 2; REQUIREMENTS.md LLM-06 Complete; all 10 Phase-1 requirements traceable.

## Task Commits

Each task was committed atomically:

1. **Deviation fix (pre-Task-1):** `fix(01-05): isolate LLMClient from host proxy + IPv6 quirks` — `275cac5` (fix)
2. **Task 1:** `test(01-05): flip test_bilingual_ollama_reply to real Ollama call + add models-pulled precondition` — `9538762` (test)
3. **Task 2:** `docs(01-05): fix model size 20GB->24GB, update path, mark Phase 1 complete` — `dbfc941` (docs)
4. **Task 3:** `docs(01-05): mark Phase 1 complete in ROADMAP/STATE/REQUIREMENTS` — `9c1249a` (docs)

**Plan metadata commit:** [appended after this file + STATE/ROADMAP/REQS are staged together]

## Smoke test output

### `python scripts/smoke_test.py --static-only` (post-Plan-05)

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/

Summary: 2 pass · 0 fail · 0 skip · 2 total
exit=0
```

### `python scripts/smoke_test.py` (full suite, default `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M`, 32GB host)

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/
[PASS] check_models_pulled: both Ollama models present in `ollama list`
[FAIL] test_bilingual_ollama_reply [RU]: chat() raised: APIConnectionError: Connection error.
  Hint: Ollama is not responding on 127.0.0.1:11434 (probe=000). The server may have OOM-crashed while loading qwen3.6:35b-a3b-q4_K_M. Retry with: `ollama serve &` then `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (use light model on low-RAM hosts).
[FAIL] test_bilingual_ollama_reply [EN]: chat() raised: APIConnectionError: Connection error.
  Hint: Ollama is not responding on 127.0.0.1:11434 (probe=000). The server may have OOM-crashed while loading qwen3.6:35b-a3b-q4_K_M. Retry with: `ollama serve &` then `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (use light model on low-RAM hosts).

Summary: 3 pass · 1 fail · 0 skip · 4 total
exit=1
```

Per Plan 05 acceptance criteria: "exits non-zero with a stdout message containing... `Ollama` (server-down) — both are acceptable based on host state." This is path (b). Exit code 1 confirms the failure is signaled.

### `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (full suite, light-model override — the documented low-RAM verification path)

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/
[PASS] check_models_pulled: both Ollama models present in `ollama list`
[PASS] test_bilingual_ollama_reply [RU]: got 28 chars: 'Помогу вам на русском языке.'
[PASS] test_bilingual_ollama_reply [EN]: got 85 chars: 'I understand your request for a one-sentence response in English with no translation.'

Summary: 4 pass · 0 fail · 0 skip · 4 total
exit=0
```

Per Plan 05 acceptance criteria: "exits 0 with 4 PASS lines AND `logs/tokens.jsonl` has 2+ new records." This is path (a) — bilingual Ollama wire verified end-to-end. `logs/tokens.jsonl` shows the two new records appended after the RU+EN calls.

## Ollama state at execution time

- `ollama list` showed both `qwen3.6:35b-a3b-q4_K_M` (23GB, pulled during this plan's execution) and `qwen3:4b` (2.5GB, pulled before Plan 05 started).
- `ollama serve` was running on `127.0.0.1:11434`; `/api/tags` returned 200.
- The 24GB primary model OOMed Ollama mid-load on this 32GB host. This is a known operational constraint per CLAUDE.md §4 Risk register ("Ollama OOM kills macOS" — in practice it just kills the Ollama subprocess). Smoke test now self-documents this case via the failure-path hint.
- `logs/tokens.jsonl` accumulated 4 new records during Plan 05 execution (qwen3:4b RU prompt, qwen3:4b EN prompt, two earlier direct-invocation test calls).

## CLAUDE.md §6 after rewrite (paste)

```markdown
## 6. Current state

**Status: Phase 1 complete — Foundation + Local LLM shipped.**

Last updated: 2026-05-15

What landed in Phase 1:
- Fork of `razzant/ouroboros@v6.2.0` overlaid in-place at the project root; `playground` branch live, `last-known-good` annotated tag at the upstream v6.2.0 commit
- Package renamed `ouroboros/` → `heretek/`; `python -m supervisor` is the local boot entry point
- Hard-deleted: `tools/github.py`, `tools/review.py`, `tools/browser.py`, `tools/health.py`, `tools/search.py`, package-root `review.py`
- Stripped: cloud LLM env-var loaders (OPENROUTER/OPENAI/ANTHROPIC), OpenRouter HTTP drift-check in the budget tracker, Playwright dep
- Wired: Ollama at `http://127.0.0.1:11434/v1` with `api_key="ollama"`; primary `qwen3.6:35b-a3b-q4_K_M` via `OLLAMA_MODEL`; light `qwen3:4b` via `OLLAMA_MODEL_LIGHT`; context cap `HERETEK_MAX_CONTEXT_TOKENS=32000`
- Robustness: `LLMClient` forces IPv4 (httpx does not fall back from IPv6 ::1 to 127.0.0.1 cleanly) and uses `trust_env=False` on its httpx client (bypasses macOS system-wide HTTP proxies that intercept localhost)
- Budget tracker public shape preserved; cost zeroed; per-call token log at `logs/tokens.jsonl` (JSONL with `{ts, model, prompt_tokens, completion_tokens, total}`)
- Smoke test `scripts/smoke_test.py` covers: package rename, no cloud hosts, models-pulled precondition, bilingual RU+EN Ollama reply (RU asserts Cyrillic in reply, EN asserts Latin)

What's next: Phase 2 (Persona + Identity) — author `CODEX_HERETICUS.md` and `SYSTEM.md`, prove the bot has a chaos-heretic voice and persistent identity across restarts.

When resuming:
1. Check this section first.
2. `git log --oneline -20` on `playground` for recent commits.
3. `ollama list` should show both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b`.
4. `python scripts/smoke_test.py --static-only` is the fast-feedback gate (2 PASS, ~3s, no Ollama dependency).
5. `python scripts/smoke_test.py` is the end-to-end gate. On a 32GB host the 24GB primary model can OOM Ollama — set `OLLAMA_MODEL=qwen3:4b` to use the light model for the wire check.
6. Tail `./logs/tokens.jsonl` for per-call token records.
```

## Files Created/Modified

- `scripts/smoke_test.py` — `test_bilingual_ollama_reply` SKIP→real Ollama call; `check_models_pulled` precondition; `_extract_content` helper; failure-path liveness probe + remediation hint
- `heretek/llm.py` — default base URL IPv4 (127.0.0.1); `trust_env=False` httpx transport
- `CLAUDE.md` — 20GB→24GB; headroom 12GB→8GB; ~/code/heretek→in-place; §5 checklists [x]; §6 rewritten Phase-1-complete; status v0.0.0→v0.1.0
- `.planning/ROADMAP.md` — Phase 1 [x]; Plan 05 [x]; progress table 5/5 Complete 2026-05-15
- `.planning/STATE.md` — frontmatter completed_phases 0→1, completed_plans 4→5; Current Position → Phase 2; Plan 05 metrics + decisions + blockers added; session continuity → Phase-1-complete
- `.planning/REQUIREMENTS.md` — LLM-06 [ ]→[x]; traceability LLM-06 Complete; footer date bumped

## Decisions Made

- **Default LLMClient base URL set to 127.0.0.1 (IPv4 explicit), not localhost.** httpx's IPv6→IPv4 fallback on ECONNREFUSED is broken; curl tolerates it but the OpenAI SDK does not. Users can still override via OLLAMA_BASE_URL.
- **httpx `trust_env=False` for the OpenAI client transport.** Bypasses macOS system-wide HTTP proxies that Python's `urllib.request.getproxies()` picks up but does not honor exception lists for. Safe because OLLAMA_BASE_URL is always local by design.
- **Smoke test bilingual subtest uses OLLAMA_MODEL (primary by default), not the light model.** The primary is the production wire; light-model use is the documented escape hatch for low-RAM hosts (`OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py`).
- **Connection-error failure path actively probes Ollama liveness.** The smoke test's chat() exception handler runs `curl http://127.0.0.1:11434/api/tags` as a subprocess; if the probe returns non-200, prints a hint distinguishing "Ollama crashed" from "Ollama rejected the request" with a concrete remediation command.
- **CLAUDE.md §3 headroom revised down from ~12GB to ~8GB.** Original estimate did not account for system memory pressure on macOS Tahoe; empirically verified that 24GB model + 32GB host = OOM under realistic conditions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing `openai` Python SDK in the active interpreter**
- **Found during:** Task 1, first full smoke test run.
- **Issue:** `heretek.llm.LLMClient` imports `from openai import OpenAI`. The active Python (3.9.7) did not have `openai` installed; `requirements.txt` lists `openai>=1.0.0` but no virtual environment was active and no `pip install` had been run during Plans 01–04.
- **Fix:** `pip install --user openai` — version 2.36.0 installed.
- **Files modified:** none (Python user site-packages only)
- **Verification:** `python -c "import openai; print(openai.__version__)"` → `2.36.0`
- **Committed in:** not committed (environment-only, no source change)

**2. [Rule 1 - Bug] LLMClient picks up macOS system-wide HTTP proxy and routes localhost traffic through it**
- **Found during:** Task 1, first end-to-end chat() call attempt against Ollama.
- **Issue:** This host has a macOS system proxy configured via `scutil --proxy` (HTTPProxy 127.0.0.1:1082, HTTPSProxy 127.0.0.1:1082) with `localhost` in the exception list. Python's `urllib.request.getproxies()` returns `{'http': 'http://127.0.0.1:1082', 'https': 'http://127.0.0.1:1082'}` and does NOT honor the exception list — so httpx (with default `trust_env=True`) routes localhost:11434 requests through the proxy. The proxy returns "Server disconnected without sending a response." for upstream localhost traffic, which the OpenAI SDK surfaces as `APIConnectionError: Connection error.`
- **Fix:** Pass `http_client=httpx.Client(trust_env=False)` to the OpenAI() constructor in `LLMClient._get_client()`. Inline-commented with rationale.
- **Files modified:** `heretek/llm.py` (line ~108–119)
- **Verification:** `python -c "from heretek.llm import LLMClient; c=LLMClient(); msg, _ = c.chat(model='qwen3:4b', messages=[{'role':'user','content':'hi'}], max_tokens=16); print(msg.get('content'))"` succeeds.
- **Committed in:** `275cac5` (combined with deviation #3 — same edit hunk)
- **Why a runtime fix, not a test-only fix:** This bug affects the actual bot. The smoke test merely exposes it.

**3. [Rule 1 - Bug] LLMClient's httpx transport does not fall back IPv6→IPv4 on connect-refused**
- **Found during:** Task 1, after deviation #2 was fixed.
- **Issue:** Ollama binds AF_INET (127.0.0.1) only, not AF_INET6 (::1). httpx resolves `localhost` to both AAAA (::1) and A (127.0.0.1), tries AF_INET6 first, gets `[Errno 61] Connection refused`, and does NOT retry AF_INET. curl tolerates this (always retries), so the bug only surfaces in Python httpx code paths.
- **Fix:** Default base URL changed from `http://localhost:11434/v1` to `http://127.0.0.1:11434/v1`. Inline-commented with rationale. Users can override via `OLLAMA_BASE_URL`.
- **Files modified:** `heretek/llm.py` (line ~99–106)
- **Verification:** Same as deviation #2 — chat() succeeds end-to-end after both fixes.
- **Committed in:** `275cac5` (combined with deviation #2 — same edit hunk)
- **Why a runtime fix, not a test-only fix:** Same as deviation #2.

**4. [Rule 2 - Missing Critical] Failure-path UX upgrade in `test_bilingual_ollama_reply`**
- **Found during:** Task 1, after observing the 24GB model OOM-crashing Ollama on this 32GB host.
- **Issue:** Plan's original action body left chat() failures with only `f"{FAIL} ... chat() raised: {type(e).__name__}: {e}"`. On a real OOM crash that prints `APIConnectionError: Connection error.` — no actionable signal. Acceptance criterion (b) explicitly requires the failure message to contain "Ollama" so the operator can disambiguate "server crashed" from "rate limited" or "model rejected my payload."
- **Fix:** Added a subprocess-curl liveness probe in the failure handler. If the probe returns non-200, the test prints: "Ollama is not responding on 127.0.0.1:11434 (probe={code}). The server may have OOM-crashed while loading {model}. Retry with: ollama serve & then OLLAMA_MODEL={light} python scripts/smoke_test.py (use light model on low-RAM hosts)." Includes both the "Ollama" substring AND the concrete remediation.
- **Files modified:** `scripts/smoke_test.py` (failure path in the chat() except block)
- **Verification:** Full-suite run with default 24GB primary now prints the Ollama-down hint with `OLLAMA_MODEL=qwen3:4b` cheat-code, satisfying acceptance criterion (b).
- **Committed in:** `9538762` (folded into the Task 1 commit)

### Logged as deferred

None — Plan 05 was small enough in scope that nothing slipped out.

---

**Total deviations:** 4 auto-fixed (1 Rule 3 Blocking — missing openai SDK install; 2 Rule 1 Bug — IPv4 default + proxy bypass in heretek/llm.py; 1 Rule 2 Missing Critical — actionable failure UX in smoke test).
**Impact on plan:** Two of the four deviations (proxy bypass, IPv4 default) are net-positive runtime corrections that the production bot would have needed anyway. The smoke test surfaced them earlier than Phase 4 (Telegram launch) would have. The openai-install deviation is environment-only; the failure-path UX upgrade made the smoke test self-documenting. No scope creep — every deviation was inside the spirit of Plan 05's stated success criteria.

## Issues Encountered

- **Ollama OOM on 32GB host when loading 24GB primary model.** Not a code issue — operational constraint per CLAUDE.md §4 Risk register. Resolution: smoke test self-documents the workaround (`OLLAMA_MODEL=qwen3:4b`); CLAUDE.md §3 headroom estimate corrected (12GB → 8GB); STATE.md blockers updated to reflect the new operational reality.
- **First full smoke test run reported exit=0 due to a tee-pipeline mistake**, masking what was actually exit=1. Resolved by running the smoke test without `tee` to capture the real exit code. Mentioned only to note that the smoke test exit-code path is correct; the operator-side capture was the issue.

## User Setup Required

None - no external service configuration required for Phase 1. Phase 4 (launch) will introduce Telegram bot token + owner user ID.

## Authentication Gates

None encountered during Plan 05 execution.

## Next Phase Readiness

- **Phase 1 closed.** All 10 v1 requirements (FORK-01..04, LLM-01..06) Complete and traceable.
- **Phase 2 unblocked.** Ready for `/gsd:plan-phase 2` (Persona + Identity).
- **Recommended next user actions:**
  1. `git push -u origin playground` — publish stripped/renamed Heretek to GitHub fork (first public visibility carries stripped/renamed code, not raw upstream Ouroboros; per Phase-01-01 decision).
  2. `/gsd:plan-phase 2` — author CODEX_HERETICUS.md + SYSTEM.md plans for the chaos-heretic persona.
  3. Optional: `du -sh ~/.ollama/models/` to confirm ~30GB disk consumed by Qwen weights.
- **Open concerns carried into Phase 2:**
  - 32GB host RAM constraint on the 24GB primary model — Phase 4 may need an early `OLLAMA_MODEL` decision (use light model for some operations? hybrid? always primary?).
  - Residual `OUROBOROS_*` env vars in non-Plan-modified files (deferred-items.md). Phase 2's persona work will exercise the full prompt-assembly path and may need to clear these before they cause silent mis-routes.

## Self-Check: PASSED

Verified before writing this section:

- Created files exist:
  - `[ -f .planning/phases/01-foundation-local-llm/01-05-SUMMARY.md ]` — this file (about to be written)
- Modified files exist:
  - `scripts/smoke_test.py` — confirmed via grep of `def check_models_pulled` and `def test_bilingual_ollama_reply`
  - `heretek/llm.py` — confirmed via grep of `127.0.0.1` and `trust_env=False`
  - `CLAUDE.md` — confirmed via grep of `24GB` and `Phase 1 complete`
  - `.planning/ROADMAP.md` — confirmed via grep of `[x] **Phase 1: Foundation + Local LLM**`
  - `.planning/STATE.md` — confirmed via grep of `completed_phases: 1` and `completed_plans: 5`
  - `.planning/REQUIREMENTS.md` — confirmed via grep of `| LLM-06 | Phase 1 | Complete |`
- Commits exist on `playground`:
  - `275cac5` — fix(01-05) LLMClient proxy + IPv6 isolation
  - `9538762` — test(01-05) bilingual smoke flip + precondition
  - `dbfc941` — docs(01-05) CLAUDE.md 24GB + Phase 1 complete
  - `9c1249a` — docs(01-05) ROADMAP/STATE/REQUIREMENTS Phase 1 close

---
*Phase: 01-foundation-local-llm*
*Completed: 2026-05-15*
