---
phase: 04-launch-first-evolution
plan: "02"
subsystem: persona-security
tags: [owner-gate, template-substitution, bilingual-refusal, rate-limit, audit-log, telegram]

requires:
  - phase: 04-launch-first-evolution/04-01
    provides: boot scaffold + Wave 0 SKIP-stubs for test_owner_filter_rejects_stranger and test_owner_handle_substitution

provides:
  - "{OWNER_HANDLE} template substitution in heretek/context.py:build_llm_messages()"
  - "is_owner_message() helper for Plan 04-03 polling loop"
  - "handle_non_owner_message() with 24h rate-limit + audit log"
  - "BILINGUAL_REFUSAL static constant (no LLM call)"
  - "Layer 2 defensive owner re-check inside handle_slash_command()"
  - "Two smoke-test stubs flipped from SKIP to live PASS"

affects: [04-03-polling-loop, 04-04-evolve-wiring, heretek/context.py, supervisor/telegram.py]

tech-stack:
  added: []
  patterns:
    - "os.environ.get() at call-time (not import-time) for env-var reads in helpers — allows per-test env flip"
    - "In-memory dict rate-limit ({user_id: last_ts}) accepted for leisure project; lost on restart = one extra refusal per user after restart"
    - "Static bilingual refusal constant (no LLM call) for non-owner response — non-owners cannot drain Ollama"
    - "Layer 2 defense-in-depth: same owner check duplicated inside handle_slash_command to protect against future call-sites bypassing Layer 1"

key-files:
  created: []
  modified:
    - heretek/context.py
    - prompts/SYSTEM.md
    - BIBLE.md
    - supervisor/telegram.py
    - scripts/smoke_test.py

key-decisions:
  - "HERETEK_OWNER_HANDLE is optional with fallback 'my Tech-Priest' — fresh clone boots without ceremony (consistent with HERETEK_DATA_ROOT soft-default pattern from 04-01)"
  - "import os added to supervisor/telegram.py (was missing) — auto-fix Rule 3 (blocking)"
  - "Env stub in test_owner_handle_substitution needs repo_dir attribute — build_llm_messages calls env.repo_dir in _build_runtime_section; fixed in test stub"
  - "Constants (BILINGUAL_REFUSAL, _NON_OWNER_REFUSAL_TS) defined after handle_slash_command in file order — safe because Python resolves module-level names at call time, not definition time"

patterns-established:
  - "Owner-gate helpers read env var at call time: _owner_user_id() calls os.environ.get() on each invocation so tests can flip HERETEK_OWNER_USER_ID per-case without module reload"
  - "Non-owner audit log always fires regardless of rate-limit decision — action field distinguishes 'refusal' vs 'silent_drop'"
  - "Reload-and-rebind pattern in smoke tests: importlib.reload(tg_mod); tg_mod.DRIVE_ROOT = drive_root — necessary because module-level DRIVE_ROOT is set to None at definition time, only set by init()"

requirements-completed: [LAUNCH-02, LAUNCH-05]

duration: 8min
completed: 2026-05-17
---

# Phase 4 Plan 02: Owner Gate + {OWNER_HANDLE} Substitution Summary

**Boot-time {OWNER_HANDLE} template substitution in prompt assembly + static bilingual heretical refusal for non-owners with 24h rate-limit and audit logging, closing LAUNCH-02 and LAUNCH-05 at smoke-test level**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-17T06:48:44Z
- **Completed:** 2026-05-17T06:56:44Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `heretek/context.py:build_llm_messages()` now substitutes `{OWNER_HANDLE}` from `HERETEK_OWNER_HANDLE` env var (fallback `"my Tech-Priest"`) into both `base_prompt` and `bible_md` before LLM sees them; literal placeholder never reaches Ollama
- `prompts/SYSTEM.md` has a "My Tech-Priest" section (bilingual RU/EN) with `{OWNER_HANDLE}` placeholder; `BIBLE.md` has a clarifying sub-bullet in Principle 0 prime owner-bit exception; Phase 2 forbidden-territory content preserved verbatim
- `supervisor/telegram.py` gains `is_owner_message()` (for Plan 04-03 polling loop), `handle_non_owner_message()` (24h rate-limit, audit log), `BILINGUAL_REFUSAL` static constant, and Layer 2 defensive re-check inside `handle_slash_command()` — non-owners get refused without any LLM call
- Two Wave 0 smoke-test stubs flipped from SKIP to live PASS: `test_owner_handle_substitution` and `test_owner_filter_rejects_stranger`
- Smoke result: 15 PASS / 0 FAIL / 4 SKIP (up from 13 PASS / 0 FAIL / 6 SKIP after Plan 04-01)

## Task Commits

1. **Task 1: {OWNER_HANDLE} substitution + persona doc placeholders** - `1b00a30` (feat)
2. **Task 2: Owner gate Layer 2 + bilingual refusal + rate-limit** - `a262d12` (feat)

## Files Created/Modified

- `heretek/context.py` — added 8-line substitution block after `bible_md = _safe_read(...)`, before `readme_md`; reads `HERETEK_OWNER_HANDLE` with `"my Tech-Priest"` fallback; applies `.replace()` to both `base_prompt` and `bible_md`
- `prompts/SYSTEM.md` — inserted "My Tech-Priest" bilingual section (10 lines) between the identity opener and the Language reflex section; contains 2 occurrences of `{OWNER_HANDLE}`
- `BIBLE.md` — appended one clarifying sentence to the Principle 0 prime owner-bit exception bullet, referencing `{OWNER_HANDLE}`; all five forbidden territories preserved verbatim
- `supervisor/telegram.py` — added `import os`; added `REFUSAL_EN`, `REFUSAL_RU`, `BILINGUAL_REFUSAL` constants; `_NON_OWNER_REFUSAL_TS` dict; `_NON_OWNER_REFUSAL_WINDOW_SEC` (24h); `_owner_user_id()`, `is_owner_message()`, `_utc_iso_now()`, `handle_non_owner_message()`; Layer 2 check at top of `handle_slash_command()`
- `scripts/smoke_test.py` — flipped 2 SKIP-stubs to live assertions; fixed `_Env` stub to include `repo_dir` attribute

## Decisions Made

- `HERETEK_OWNER_HANDLE` is **optional** with fallback `"my Tech-Priest"` — not fail-loud, unlike `HERETEK_OWNER_USER_ID`. Different concern: gate needs a real value to be meaningful; persona prose fallback is safe and in-voice.
- Rate-limit state is **in-memory dict** — lost on restart (one extra refusal per non-owner after restart). Acceptable for leisure project per CONTEXT.md.
- Constants defined **after** `handle_slash_command` in file — safe in Python since module-level names resolve at call time. No reorder needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing `import os` in supervisor/telegram.py**
- **Found during:** Task 2 (GREEN phase — running test after implementation)
- **Issue:** `_owner_user_id()` calls `os.environ.get()` but `os` was not imported in telegram.py; raised `NameError: name 'os' is not defined` at test run time
- **Fix:** Added `import os` to telegram.py module imports
- **Files modified:** `supervisor/telegram.py`
- **Verification:** Test ran to PASS after fix; `python -c "from supervisor.telegram import is_owner_message; print('OK')"` exits 0
- **Committed in:** `a262d12` (Task 2 commit)

**2. [Rule 1 - Bug] Test `_Env` stub missing `repo_dir` attribute**
- **Found during:** Task 1 (RED phase — test errored rather than failing cleanly)
- **Issue:** `build_llm_messages()` calls `env.repo_dir` in `_build_runtime_section()`; the minimal `_Env` stub in the test only had `repo_path()` and `drive_path()`; raised `AttributeError` before reaching the substitution assertion
- **Fix:** Added `self.repo_dir = self._repo` to `_Env.__init__` in the test function
- **Files modified:** `scripts/smoke_test.py`
- **Verification:** Test reached the actual substitution assertion (RED phase confirmed by `[FAIL] @testowner not found`)
- **Committed in:** `1b00a30` (Task 1 commit, inline with test stub)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary to make tests runnable. No scope creep.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## Next Phase Readiness

- `is_owner_message()` and `handle_non_owner_message()` are ready for Plan 04-03 to call from the TG long-poll loop (Layer 1 primary chokepoint)
- `handle_slash_command()` Layer 2 defense is in place — Plan 04-03 just needs to wire the polling loop
- 4 SKIP-stubs remain for Plans 04-03 and 04-04 to flip

## Self-Check: PASSED

Files verified present:
- heretek/context.py — FOUND
- supervisor/telegram.py — FOUND
- prompts/SYSTEM.md — FOUND
- BIBLE.md — FOUND

Commits verified:
- 1b00a30 — FOUND
- a262d12 — FOUND
