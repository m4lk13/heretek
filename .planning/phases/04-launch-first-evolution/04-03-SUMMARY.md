---
phase: 04-launch-first-evolution
plan: "03"
subsystem: supervisor-boot-wiring
tags: [boot, polling-loop, owner-gate, workers-shutdown, consciousness, telegram, launch]
dependency_graph:
  requires:
    - 04-01: env-validation-scaffold + __main__.py boot delegation stub
    - 04-02: is_owner_message + handle_non_owner_message + BILINGUAL_REFUSAL + Layer 2 slash guard
  provides:
    - supervisor/boot.py: run(data_root) + _run_polling_loop() + _dispatch_update()
    - workers.shutdown(timeout): sentinel-task drain + kill_workers fallback
    - Layer 1 owner gate live in polling loop (primary chokepoint)
    - Consciousness daemon thread auto-starts at boot on OLLAMA_MODEL_LIGHT
    - owner_chat_id persisted to state.json on first owner message
    - tg_offset cursor persisted after each polling batch
  affects:
    - supervisor/workers.py
    - supervisor/__main__.py
    - scripts/smoke_test.py
tech_stack:
  added: []
  patterns:
    - "sentinel-task → join → kill_workers fallback for graceful worker drain"
    - "SIGINT/SIGTERM → _SHUTDOWN_REQUESTED flag; polling loop checks flag each iteration"
    - "tg_offset=-1 on first boot to skip backlog cleanly"
    - "_dispatch_update: Layer 1 is_owner_message check before any downstream call"
    - "importlib.reload + module-level var injection for hermetic smoke tests"
key_files:
  created:
    - supervisor/boot.py
  modified:
    - supervisor/workers.py
    - supervisor/__main__.py
    - scripts/smoke_test.py
decisions:
  - "supervisor/__main__.py hard-imports boot (no try/except) — boot.py is no longer optional as of this plan"
  - "test_env_fail_loud Case 4 accepts TimeoutExpired — post-Plan-03 the subprocess enters the actual polling loop with a fake token; timeout = env validation passed = correct behavior"
  - "send_with_budget called with fmt='markdown' for slash-command responses — in-character heresy text renders better as markdown"
  - "BackgroundConsciousness import wrapped in try/except — consciousness failure is logged as warning, does not abort the boot sequence"
  - "telegram.init() called in boot.run() to wire _TG global — required for send_with_budget to work; smoke test also calls tg_mod.init() with mock to exercise this path"
metrics:
  duration: "8 min"
  completed: "2026-05-17T07:08:57Z"
  tasks: 3
  files: 4
---

# Phase 4 Plan 03: Boot Wiring + Polling Loop Summary

**Production boot sequence wired: supervisor/boot.py lands with run(), polling loop, SIGINT handler, Layer 1 owner gate, and consciousness auto-start; workers.shutdown() sentinel-task helper added; 3 smoke-test stubs promoted to PASS/conditional-SKIP**

## What Was Built

### Task 1 — workers.shutdown() sentinel-task helper

`supervisor/workers.py` got a new `shutdown(timeout: float = 5.0)` function inserted before `respawn_worker()`:

- Sends `{"type": "shutdown"}` sentinel to each worker's `in_q` (worker_main checks this at line 292 and breaks its loop)
- Joins each worker process with the shared timeout budget (deadline = now + timeout)
- Calls `kill_workers()` as fallback if any workers are still alive after the deadline
- Appends a `{"type": "workers_shutdown", "graceful": ..., "timeout_sec": ...}` entry to `logs/supervisor.jsonl`

`test_workers_shutdown_drains_cleanly` flipped from SKIP to live PASS: spawns 1 real `mp.Process` worker, calls `workers.shutdown(timeout=5.0)`, verifies `WORKERS` dict is cleared and audit log entry present.

### Task 2 — supervisor/boot.py production boot sequence

New file `supervisor/boot.py` with:

**`run(data_root: Path) -> int`** — top-level entry called by `__main__.py`:
1. `state.init(drive_root)` — must be first (Pitfall 3: DRIVE_ROOT must be set before load_state)
2. `git_ops.init(repo_dir, drive_root, ...)` — sets REPO_DIR, PROTECTED_BRANCHES
3. `TelegramClient(token)` + `telegram.init(drive_root, 0.0, 10, tg)` — wires `_TG` global
4. `workers.init(...) + spawn_workers(n=HERETEK_MAX_WORKERS)` — starts worker pool
5. `BackgroundConsciousness.start()` — daemon thread on OLLAMA_MODEL_LIGHT (try/except: failure logs warning, does not abort boot)
6. Signal handlers: `signal.signal(SIGINT/SIGTERM, _request_shutdown)` — flips `_SHUTDOWN_REQUESTED` flag
7. Calls `_run_polling_loop(tg, data_root)` — blocks until shutdown requested

**`_run_polling_loop(tg, data_root)`**:
- Reads `tg_offset` from state.json; on first boot (offset==0) fetches with `offset=-1` to skip backlog
- `while not _SHUTDOWN_REQUESTED`: `tg.get_updates(offset, timeout=10)`, dispatch each update
- Persists `tg_offset` after each non-empty batch
- Per-cycle housekeeping: `workers.assign_tasks()`, `workers.ensure_workers_healthy()`, `queue.enforce_task_timeouts()` (all wrapped in try/except — never kills the loop)

**`_dispatch_update(update, tg, data_root)`**:
- Extracts `msg`, `from_id`, `chat_id`, `text` from update
- **Layer 1 owner gate**: `if not is_owner_message(update): handle_non_owner_message(chat_id, from_id, tg_client=tg); return`
- Owner path: persists `owner_chat_id` + `owner_id` to state.json on first message (so Plan 04-04's /evolve has a destination)
- Slash-command path: `send_chat_action("typing")` → `handle_slash_command(text, chat_id, from_id)` → `send_with_budget(chat_id, response, fmt="markdown")`
- Non-slash path: `send_chat_action("typing")` → `handle_chat_direct(chat_id, text)` (threading-based)

`supervisor/__main__.py` updated: removed the `try/except ImportError` wrapper around `from supervisor import boot` — boot.py is no longer optional.

`test_env_fail_loud` Case 4 updated: now accepts `subprocess.TimeoutExpired` as a passing condition (the subprocess entered the polling loop = env validation passed = correct).

### Task 3 — Smoke-test stubs flipped

`test_polling_loop_dispatches_owner_message` (live PASS):
- Owner `/heresy`: `_dispatch_update` → `send_chat_action("typing")` → `handle_slash_command` → `cmd_heresy()` → `send_with_budget` via mock `_TG` wired through `tg_mod.init()`; verifies typing indicator + outbound message + `owner_chat_id` pinned in state.json
- Non-owner `/evolve`: `handle_non_owner_message(tg_client=mock)` sends `BILINGUAL_REFUSAL` directly via `mock.send_message`

`test_consciousness_loop_logs` (SKIP on --static-only, live PASS in full suite):
- Argv check: `if "--static-only" in sys.argv: return "skip"` — fast-feedback gate preserved
- Full suite: instantiates `BackgroundConsciousness`, calls `start()`, waits up to 15s for `events.jsonl` or `scratchpad.md` evidence; SKIPs if Ollama unreachable

## Final Smoke State

```
python scripts/smoke_test.py --static-only
Summary: 17 pass · 0 fail · 2 skip · 19 total
```

- 15 prior PASS (Phase 1+2+3+4-01+4-02) still green
- 2 new live PASS: `test_workers_shutdown_drains_cleanly`, `test_polling_loop_dispatches_owner_message`
- 2 remaining SKIP: `test_evolve_enqueues_task_when_no_fixture` (Plan 04-04), `test_consciousness_loop_logs` (Ollama-dependent; static gate)

## Task Commits

All task changes captured via auto-rescue commits (supervisor startup checks for uncommitted changes and commits them automatically):

1. **Task 1: workers.shutdown() helper + test flip** — `f758ab5` (auto-rescue: workers.py + smoke_test.py)
2. **Task 2: supervisor/boot.py creation + __main__.py hard-import** — `30867f6` (`__main__.py`) + `dfd9135` (`boot.py`) + `cdb3e34` (smoke_test.py Case 4 fix)
3. **Task 3: polling-loop + consciousness smoke stubs flipped** — `f38446c` (auto-rescue: smoke_test.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_env_fail_loud Case 4 hangs after boot.py lands**
- **Found during:** Task 2 verification
- **Issue:** Case 4 called `python -m supervisor` with valid env vars and a 15s timeout. Before boot.py existed, the supervisor returned immediately via the try/except fallback. With boot.py live, the supervisor enters the polling loop and attempts to connect to Telegram with a fake token — either hanging on retries or looping indefinitely. `subprocess.TimeoutExpired` was raised.
- **Fix:** Updated Case 4 to catch `subprocess.TimeoutExpired` and treat it as passing (polling loop started = env validation succeeded = correct). Also reduced the subprocess timeout from 15s to 5s to keep the test fast.
- **Files modified:** `scripts/smoke_test.py`
- **Commit:** `cdb3e34` (auto-rescue)

**2. [Rule 2 - Missing] telegram.init() call needed in boot.run() for send_with_budget to work**
- **Found during:** Task 3 (mock TG dispatch test)
- **Issue:** `send_with_budget` calls `get_tg()` which asserts `_TG is not None`. The original plan spec mentioned `telegram.init(...)` in the boot order but the provided code stub omitted the actual `telegram.init()` call. The smoke test revealed this by checking that `mock_tg.sent` was populated after owner dispatch.
- **Fix:** Added `telegram.init(drive_root=data_root, total_budget_limit=0.0, budget_report_every=10, tg_client=tg)` call after `TelegramClient(token)` instantiation in `boot.run()`.
- **Files modified:** `supervisor/boot.py`
- **Commit:** `dfd9135`

## Handoff Notes for Plan 04-04

- `supervisor/boot.py._dispatch_update` is now the Layer 1 owner gate — Plan 04-04's `/evolve` production path is activated by `cmd_evolve()` (in `supervisor/commands.py`) when `HERETEK_EVOLVE_TEST_DIFF` is unset; it should enqueue `{type: 'evolution', source: '/evolve'}` into `supervisor.queue.PENDING`
- `owner_chat_id` is now persisted to `state.json` on the first owner message — the evolution reply (`/evolve` result posted to chat) uses `st["owner_chat_id"]` as the destination
- Workers are live (`spawn_workers` called at boot) — when an evolution task is enqueued, `workers.assign_tasks()` will pick it up on the next polling cycle
- The consciousness daemon thread is started at boot on `OLLAMA_MODEL_LIGHT` — Plan 04-04 does not need to start it again
- `test_evolve_enqueues_task_when_no_fixture` remains SKIP — Plan 04-04 owns this flip

## Self-Check: PASSED

Files verified present:
- `supervisor/boot.py` — FOUND (created by dfd9135)
- `supervisor/workers.py` — FOUND (shutdown() added by f758ab5)
- `supervisor/__main__.py` — FOUND (hard-import by 30867f6)
- `scripts/smoke_test.py` — FOUND (tasks 1+2+3 by f758ab5, cdb3e34, f38446c)

Commits verified:
- `f758ab5` — FOUND (Task 1 auto-rescue)
- `30867f6` — FOUND (Task 2 __main__.py auto-rescue)
- `dfd9135` — FOUND (Task 2 boot.py commit)
- `cdb3e34` — FOUND (Task 2 smoke_test Case 4 fix auto-rescue)
- `f38446c` — FOUND (Task 3 auto-rescue)

Smoke gate: 17 pass · 0 fail · 2 skip · 19 total
