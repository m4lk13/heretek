---
phase: 04-launch-first-evolution
plan: "01"
subsystem: supervisor-boot
tags: [boot, env-validation, smoke-test, gitignore, launch]
dependency_graph:
  requires: [03-self-modify-guardrails]
  provides: [env-validation-scaffold, smoke-harness-wave0, dotenv-exemplar, events-restart-fix]
  affects: [supervisor/__main__.py, supervisor/events.py, scripts/smoke_test.py, .gitignore, .env.example]
tech_stack:
  added: []
  patterns: [subprocess-smoke-testing, fail-loud-env-validation, skip-then-flip-smoke]
key_files:
  created: [.env.example]
  modified: [supervisor/__main__.py, supervisor/events.py, scripts/smoke_test.py, .gitignore]
decisions:
  - "HERETEK_DATA_ROOT soft-default to project root with boot log line (NOT fail-loud); fresh clone boots without ceremony"
  - "test_env_fail_loud uses 4-case subprocess exercise so real CLI entry point is exercised (not just function call)"
  - "events.py module docstring updated to remove colab_launcher.py attribution (grep must return no match)"
  - "8 Phase 4 SKIP-stubs added to STATIC_SUBTESTS; test_consciousness_loop_logs stays SKIP on --static-only even after live-flip (Ollama dependency)"
metrics:
  duration: "5 minutes"
  completed: "2026-05-17"
  tasks: 3
  files: 5
---

# Phase 4 Plan 01: Boot Scaffold + Wave 0 Smoke Harness Summary

Boot scaffold for the Heretek supervisor with fail-loud env validation, colab_launcher.py restart blocker fix, and 8 Wave 0 SKIP-stubs covering all LAUNCH-*/EVOLVE-* requirements.

## What Was Built

### Task 1 — Boot scaffold, events.py restart fix, .gitignore

**supervisor/__main__.py** replaced the "not-yet-wired" stub (lines 90-103) with:
- `_validate_required_env()`: fail-loud on missing `TELEGRAM_BOT_TOKEN` (exits 2) or missing/non-integer `HERETEK_OWNER_USER_ID` (exits 2)
- `_resolve_data_root()`: resolves `HERETEK_DATA_ROOT` with project-root soft-default + boot log line; creates `logs/`, `state/`, `archive/`, `locks/`, `memory/` subdirs
- `_print_banner()` extended with `owner_id` + `owner_handle` confirmation lines
- Boot delegates to `supervisor.boot.run()` (Plan 04-03 lands the body); exits 0 cleanly if boot not yet wired

**supervisor/events.py** `_handle_restart()` patched:
- Removed `launcher = os.path.join(os.getcwd(), "colab_launcher.py")` line (deleted file)
- Replaced `os.execv(sys.executable, [sys.executable, launcher])` with `os.execv(sys.executable, [sys.executable, '-m', 'supervisor'])`
- Module docstring attribution to colab_launcher.py removed (grep-clean)

**.gitignore** got `state/`, `archive/`, `locks/` entries grouped under a "Heretek runtime state directories" comment.

### Task 2 — Wave 0 smoke harness + .env.example

**scripts/smoke_test.py** additions:
- `_make_mock_tg_client()` helper: duck-typed TG client recording `.sent`/`.actions`/`.photos`; `get_updates()` returns seeded updates once then `[]` forever; used by Plans 04-02/04-03/04-04 for hermetic polling-loop tests
- 8 SKIP-stub subtests registered in `STATIC_SUBTESTS`:
  1. `test_env_fail_loud` — LAUNCH-03, owned Plan 04-01 (flipped in Task 3)
  2. `test_dotenv_loaded` — LAUNCH-03, owned Plan 04-01 (flipped in Task 3)
  3. `test_owner_filter_rejects_stranger` — LAUNCH-05, owned Plan 04-02
  4. `test_owner_handle_substitution` — LAUNCH-02, owned Plan 04-02
  5. `test_polling_loop_dispatches_owner_message` — LAUNCH-04, owned Plan 04-03
  6. `test_workers_shutdown_drains_cleanly` — LAUNCH-04, owned Plan 04-03
  7. `test_evolve_enqueues_task_when_no_fixture` — EVOLVE-01, owned Plan 04-04
  8. `test_consciousness_loop_logs` — EVOLVE-02, owned Plan 04-03 (SKIP on --static-only even after live-flip)

**.env.example** created with all Phase 4 required + optional env-var keys; committed (not gitignored).

### Task 3 — Flip test_env_fail_loud + test_dotenv_loaded to live PASS

`test_env_fail_loud`: 4-case subprocess exercise:
- Case 1: `HERETEK_OWNER_USER_ID` unset → non-zero exit + `"HERETEK_OWNER_USER_ID required"` in stderr
- Case 2: `HERETEK_OWNER_USER_ID=notanint` → non-zero exit + `"must be an integer"` in stderr
- Case 3: `TELEGRAM_BOT_TOKEN` unset → non-zero exit + `"TELEGRAM_BOT_TOKEN required"` in stderr
- Case 4: Both set + `HERETEK_DATA_ROOT` tempdir → exits 0 or 1 (boot module not yet wired is acceptable)

`test_dotenv_loaded`: reads `.env.example`, asserts all 8 required keys present (`TELEGRAM_BOT_TOKEN=`, `HERETEK_OWNER_USER_ID=`, `HERETEK_OWNER_HANDLE=`, `HERETEK_DATA_ROOT=`, `OLLAMA_MODEL=`, `OLLAMA_MODEL_LIGHT=`, `HERETEK_MAX_CONTEXT_TOKENS=`, `HERETEK_PROTECTED_BRANCHES=`).

**LAUNCH-03 fully satisfied at smoke-test level.**

## Final Smoke State

```
python scripts/smoke_test.py --static-only
Summary: 13 pass · 0 fail · 6 skip · 19 total
```

- 11 prior PASS (Phase 1+2+3) still green
- 2 new live PASS: `test_env_fail_loud`, `test_dotenv_loaded`
- 6 remaining SKIP: `test_owner_filter_rejects_stranger`, `test_owner_handle_substitution`, `test_polling_loop_dispatches_owner_message`, `test_workers_shutdown_drains_cleanly`, `test_evolve_enqueues_task_when_no_fixture`, `test_consciousness_loop_logs`

## Deviations from Plan

**1. [Rule 1 - Bug] events.py module docstring contained colab_launcher.py attribution**
- Found during: Task 1
- Issue: Plan acceptance criteria requires `grep -q 'colab_launcher.py' supervisor/events.py` to return NO MATCH, but the module docstring (line 5) said "Extracted from colab_launcher.py main loop"
- Fix: Updated docstring to "Originally extracted from the upstream cloud launcher; heretek boots via `python -m supervisor`"
- Files modified: supervisor/events.py
- Commit: 68c570f

**2. [Rule 1 - Bug] exec call used double-quotes for '-m' literal, failing the grep assertion**
- Found during: Task 1 verification
- Issue: Plan acceptance criteria `grep -q "'-m', 'supervisor'"` requires single-quoted string literals; initial write used double quotes `"-m", "supervisor"`
- Fix: Changed to single-quoted `'-m', 'supervisor'` in the `os.execv()` call
- Files modified: supervisor/events.py
- Commit: 68c570f

## Handoff Notes for Downstream Plans

**Plan 04-02** flips:
- `test_owner_filter_rejects_stranger` (LAUNCH-05): implement non-owner gate in polling loop + bilingual heretical refusal constant; mock TG dispatch
- `test_owner_handle_substitution` (LAUNCH-02): add `{OWNER_HANDLE}` template substitution in `heretek/context.py:build_llm_messages()` after loading `base_prompt` and `bible_md`; insert `{OWNER_HANDLE}` reference in `prompts/SYSTEM.md`

**Plan 04-03** flips:
- `test_polling_loop_dispatches_owner_message` (LAUNCH-04): wire `supervisor/boot.py` with `run()` function and the TG long-poll loop; call from `__main__.py` (the import path is already wired — boot.py just needs to exist)
- `test_workers_shutdown_drains_cleanly` (LAUNCH-04): add `workers.shutdown(timeout=5.0)` function (sentinel-task approach documented in RESEARCH.md)
- `test_consciousness_loop_logs` (EVOLVE-02): boot consciousness on light model and assert `logs/events.jsonl` entry

**Plan 04-04** flips:
- `test_evolve_enqueues_task_when_no_fixture` (EVOLVE-01): wire production `/evolve` path in `supervisor/commands.py:cmd_evolve()` to enqueue `{type: 'evolution'}` task when `HERETEK_EVOLVE_TEST_DIFF` is unset

**Boot order for Plan 04-03:** The `__main__.py` already attempts `from supervisor import boot` and calls `boot.run(data_root=data_root)`. Plan 04-03 only needs to create `supervisor/boot.py` with the full boot sequence (state.init → git_ops.init → TelegramClient → telegram.init → workers.init → spawn_workers → consciousness.start → polling loop). The `data_root` arg is already threaded through.

## Self-Check: PASSED

Files created/modified exist:
- supervisor/__main__.py — contains `_validate_required_env` and `_resolve_data_root`
- supervisor/events.py — no `colab_launcher.py` reference; has `'-m', 'supervisor'`
- .gitignore — has `state/`, `archive/`, `locks/` entries
- scripts/smoke_test.py — has `_make_mock_tg_client` and all 8 Phase 4 stub functions
- .env.example — exists with all required keys

Commits exist:
- 68c570f: feat(04-01): boot scaffold, events.py restart fix, .gitignore runtime dirs
- 29f624a: feat(04-01): Wave 0 smoke-test scaffold + .env.example exemplar
- 64b9b09: test(04-01): flip test_env_fail_loud + test_dotenv_loaded to live PASS
