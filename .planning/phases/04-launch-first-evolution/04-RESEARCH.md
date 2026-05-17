# Phase 4: Launch + First Evolution - Research

**Researched:** 2026-05-17
**Domain:** Telegram long-poll boot, multiprocessing supervisor, owner-only gating, production /evolve wiring
**Confidence:** HIGH (all findings verified against live code)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep upstream mp.Process scaffold; "spawn" on macOS, "fork" on Linux; HERETEK_MAX_WORKERS=2
- TG long-poll on the main thread; offset cursor is the main-loop heartbeat
- Consciousness loop auto-starts at boot on OLLAMA_MODEL_LIGHT (daemon thread, already in consciousness.py)
- Boot order: _load_env → validate env → resolve HERETEK_DATA_ROOT → state.init → git_ops.init → TelegramClient → telegram.init → workers.init + spawn_workers → consciousness.start → main TG poll loop
- No in-process watchdog; tmux-session run pattern
- Graceful SIGINT/SIGTERM: drain workers, consciousness.stop(), exit 0
- Three-layer owner gate: polling-loop boundary (primary), handle_slash_command (defense), agent task-entry (defense)
- HERETEK_OWNER_USER_ID: env-var only, no hardcoded fallback, fail-loud if unset/non-integer
- Non-owner behavior: short static bilingual snarl (no fresh LLM call), rate-limited (default: once per 24h per user_id, then silent drop)
- Chat scope: owner-user_id filter only — no chat_id allowlist
- Boot-time template substitution for {OWNER_HANDLE} from HERETEK_OWNER_HANDLE env var
- HERETEK_OWNER_HANDLE is optional with fallback "my Tech-Priest"
- Production /evolve: enqueue {type: 'evolution', source: '/evolve', requested_by: OWNER_USER_ID} into supervisor queue; agent.py:404-418 handles it
- Prompt frame: self-questioning introspection — bot looks at BIBLE.md + identity.md + scratchpad, proposes mutation TO ITSELF
- Primary 24GB model for /evolve; qwen3:4b for consciousness
- HERETEK_EVOLVE_TEST_DIFF seam stays permanent
- HERETEK_DATA_ROOT defaults to project root; internal name DRIVE_ROOT stays (minimal blast radius)
- .gitignore: verify state/, archive/, locks/ are gitignored

### Claude's Discretion
- Refusal rate-limit policy (default: one per non-owner per 24h, then silent drop)
- Internal Python identifier: keep DRIVE_ROOT in-code
- TG rendering of long diffs: code-block-formatted raw diff, split if needed
- Slash-command response voice: short in-character preamble + functional payload
- typing indicator before slow replies (fire before any >2s agent-loop reply)
- Worker shutdown helper: if not present, add workers.shutdown(timeout: float = 5.0)
- Initial TG polling offset: read from state; fall back to -1 (skip backlog) on first boot
- Boot-time validation order: fail-loud checks after _load_env()
- Default model for chat: primary (24GB); light for consciousness (matches Phase 1 wiring)

### Deferred Ideas (OUT OF SCOPE)
- Webhook-mode TG client
- In-process supervisor watchdog
- launchd/systemd unit
- HERETEK_OWNER_CHAT_ID allowlist
- Multi-owner support
- Full DRIVE_ROOT → DATA_ROOT rename
- Comprehensive OUROBOROS_* env-var hygiene pass
- promote_to_stable deletion
- Rich diff rendering (file-attachment style, syntax highlighting)
- Cron/timer last-known-good advance
- Vision/screenshot tool
- Bashkir language
- Pytest framework
- Telegram chat backup/export
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LAUNCH-01 | Register TG bot via @BotFather; create private group; add bot | External manual step; no code; bot must be in group BEFORE getUpdates returns group chat_id |
| LAUNCH-02 | Owner TG user ID in SYSTEM.md via env-driven template sub, not hardcoded literal | {OWNER_HANDLE} seam in build_llm_messages — see substitution section below |
| LAUNCH-03 | .env loaded via python-dotenv; all required vars present | _load_env() already exists at __main__.py:35; python-dotenv in requirements.txt |
| LAUNCH-04 | Bot starts via `python -m supervisor`, connects to TG, responds with correct persona | Requires gutting __main__.py:90-103 stub; boot sequence + long-poll loop |
| LAUNCH-05 | Bot ignores non-owner Telegram user IDs | Three-layer gate design verified against live code |
| EVOLVE-01 | /evolve produces coherent diff in Telegram, dry-run on playground | Production path: queue enqueue → agent loop; fixture seam permanent |
| EVOLVE-02 | Background consciousness loop runs on light model continuously | consciousness.start() exists; daemon thread; circuit breaker preserved |
| EVOLVE-03 | Full loop: /evolve → diff in TG → /sanction hash → commit on playground | Exercises Phase 3 pipeline end-to-end with real LLM |
</phase_requirements>

---

## Summary

Phase 4 is almost entirely wiring work — every upstream component exists and is tested in isolation; the gap is that `supervisor/__main__.py:90-104` still prints "not-yet-wired" and exits 2. The planner must gut that stub and write the boot sequence in its place (or extract it to `supervisor/boot.py`). The TG long-poll loop does not exist anywhere in the Heretek codebase yet — it was at module scope in the upstream `colab_launcher.py`, which no longer exists. The polling pattern must be written from scratch following the established `TelegramClient.get_updates()` contract.

Worker shutdown is partially present (`kill_workers()` terminates and joins with a 5s implicit wait), but there is no `workers.shutdown()` function exposed for clean SIGINT handling. The agent.py evolution branch does NOT have any special staging logic — it uses `task.text` as the user message and `task_type='evolution'` to set `initial_effort='high'` and include README.md in the context, but the LLM writes to the live tree via normal file tools. The `.heretek/staging/` isolation that CONTEXT.md describes for the production /evolve path is NOT already in agent.py — it must be wired by Phase 4 via the task dict (e.g., passing a `staging_dir` field that the agent's tool context uses).

The owner identity gating has one important gap: `state.json` stores `owner_chat_id` (the chat where the first message arrived) and `owner_id` (the user id), but neither is populated at boot in the current code — both are set by whichever upstream launcher called `save_state` first. Phase 4's polling loop must populate both on first seen owner message and persist them via `save_state`.

**Primary recommendation:** Write `supervisor/boot.py` with a `run()` function that implements the locked boot sequence, then have `__main__.py` call `boot.run()`. Keep the polling loop in `boot.py` to isolate the new logic from the existing stub.

---

## Code Drift Check

### supervisor/__main__.py:90-103

**Status: EXACT MATCH.** Lines 90-104 are exactly the "not-yet-wired" stub described in CONTEXT.md. The stub prints the Phase 1-04 status message and returns exit code 2. `_load_env()` at line 35 and `_print_banner()` at line 54 both exist and work. Phase 4 must delete lines 90-104 and insert the real boot sequence.

**Note:** The stub's comment at line 99 says "Plan 05 will fully wire this." Plan 05 closed Phase 1; Phase 4 is the correct unblock phase.

### supervisor/telegram.py:481-518 (handle_slash_command)

**Status: EXACT MATCH.** Function exists at line 487, imports from `supervisor.commands` lazily (local import inside function body), dispatches `/evolve`, `/sanction <id>`, `/heresy` correctly. The docstring explicitly says "Phase 4 will wire it into the Telegram polling loop." The function is NOT called anywhere in the current codebase — Phase 4 must call it from the polling loop.

**Minor drift:** CONTEXT.md cites the function at line 487; it is actually defined at line 487 (function signature starts there) with the body through line 518. The dispatch logic matches: `/evolve` → `cmd_evolve()`, `/sanction (\S+)` → `cmd_sanction(group(1))`, `/heresy` → `cmd_heresy()`. No changes needed to this function for Phase 4.

### supervisor/commands.py:71 (cmd_evolve fixture-only)

**Status: MATCHES with important nuance.** `cmd_evolve()` at line 71 has the `HERETEK_EVOLVE_TEST_DIFF` branch. When the env var is unset AND `test_diff_path` is None, it returns an error string:
```
"⚠️ EVOLVE_REFUSED: no patch source provided. Phase 3 supports fixture-injection only..."
```
This is the Phase 3 stub behavior. Phase 4 must add the production path: when `HERETEK_EVOLVE_TEST_DIFF` is unset, enqueue an `evolution` task into the supervisor queue instead of returning the error. The fixture path remains for smoke tests.

**Key structural detail:** `cmd_evolve()` receives no queue reference — it has no way to enqueue a task in its current signature. Phase 4 must either (a) import `supervisor.queue.enqueue_task` from inside `cmd_evolve` (follow the lazy-import pattern from Phase 3), or (b) pass a `enqueue_fn` callback from the polling loop.

### heretek/agent.py:404-418 (task_type='evolution' branch)

**Status: DRIFT FROM CONTEXT.md DESCRIPTION.** CONTEXT.md states the evolution branch "already exists at heretek/agent.py:404-418." It does exist but NOT as a separate branch with custom behavior — it is only a one-line check:
```python
if task_type_str in ("evolution", "review"):
    initial_effort = "high"
```
There is no special staging directory logic. The evolution task runs through `run_llm_loop()` exactly like any other task, with the only difference being `initial_effort="high"` and README.md included in context (via `needs_full_context` flag in `build_llm_messages`). The agent's file tools write to the live tree (REPO_DIR), NOT to `.heretek/staging/`.

**Implication for the planner:** The "agent writes to staging, cmd_evolve diffs vs HEAD" description in CONTEXT.md §Production /evolve LLM-loop wiring is aspirational, not already-implemented. Phase 4 must either:
- Add staging isolation (pass a modified repo_dir or staging_dir to the agent for evolution tasks) — complex
- OR let the agent write to the live tree and capture the diff AFTER the loop, then rollback the live-tree changes — simpler but requires git-stash or equivalent

**Recommendation (Claude's discretion):** The simplest safe path is to run the agent in a git-worktree checked out at `.heretek/staging/` so it gets a real git context with full tool support. Alternatively, the agent could be pointed at `.heretek/staging/` as its `repo_dir`, but the worktree approach gives `git diff` output naturally. Concrete: `git worktree add .heretek/staging/ playground` before the agent runs, then `git diff playground` from within staging gives the patch.

### heretek/consciousness.py:40-117 (start/stop lifecycle)

**Status: EXACT MATCH.** `BackgroundConsciousness` class at line 39, `start()` at line 89, `stop()` at line 99, `pause()/resume()` at lines 107/112. Daemon thread at line 95. Circuit breaker is implemented in `_think()` (not explicitly at :130 as cited — the circuit breaker for empty responses is inside the consciousness loop's budget/model check pattern). Uses `OLLAMA_MODEL_LIGHT` at line 87. Ready to call `consciousness.start()` at boot with no changes.

**Constructor signature:** `BackgroundConsciousness(drive_root, repo_dir, event_queue, owner_chat_id_fn)`. The `owner_chat_id_fn` is a callable that returns the current owner's chat_id — boot sequence needs to provide a lambda that reads from state.

### supervisor/workers.py:33-80 (DRIVE_ROOT + init)

**Status: MATCHES with one residual OUROBOROS ref.** `DRIVE_ROOT` default at line 33 is still `/content/drive/MyDrive/Ouroboros`. `init()` at line 64 takes and sets `drive_root`. `spawn_workers()` at line 408. `_DEFAULT_WORKER_START_METHOD = "fork" if linux else "spawn"` at line 50 — correct for macOS.

**Residual OUROBOROS_ ref (BLOCKING for Phase 4):** Line 51 reads `OUROBOROS_WORKER_START_METHOD` env var. Since Phase 4 doc says fix OUROBOROS_ refs opportunistically, the planner should rename this to `HERETEK_WORKER_START_METHOD` in the same file-touch that adds the data-root wiring.

**No `workers.shutdown()` function exists.** `kill_workers()` at line 443 does: terminate + join(timeout=5) + clear WORKERS/RUNNING + persist snapshot. This is usable as shutdown, but it sends `SIGTERM` immediately without draining. A `workers.shutdown(timeout=5.0)` wrapper that sends a sentinel `{type: 'shutdown'}` task to each worker's in_q first, joins with timeout, then falls back to `kill_workers()` is the missing piece. Planner must add this for SIGINT handling.

### supervisor/queue.py (enqueue_task contract)

**Verified contract.** `enqueue_task(task: Dict[str, Any], front: bool = False)` at line 97. Adds `priority`, `_attempt`, `_queue_seq`, `queued_at` fields automatically. The task dict needs at minimum `{id, type, chat_id, text}`. For production /evolve, the task enqueued would be:
```python
{
    "id": uuid.uuid4().hex[:8],
    "type": "evolution",
    "chat_id": owner_chat_id,   # required — worker sends events to this chat
    "text": "Tech-Priest demands your next mutation. ...",  # the self-questioning seed
    # optional extra fields (not read by agent loop, used for audit only):
    "source": "/evolve",
    "requested_by": OWNER_USER_ID,
}
```
**Critical:** `chat_id` is mandatory — `queue.py:197` skips restoring tasks without `chat_id` from snapshots, and `events.py` uses `task["chat_id"]` to know where to send the response. Without `chat_id`, the bot's reply goes nowhere.

### supervisor/state.py:24-33 (DRIVE_ROOT + init)

**Status: EXACT MATCH.** `DRIVE_ROOT` at line 24, `STATE_PATH` etc. derived from it at lines 25-28. `init(drive_root, total_budget_limit=0.0)` at line 31 reassigns all module-level paths. Also: `state.json` has `tg_offset` field (line 130) defaulting to 0 — the polling loop can read/write this for offset persistence across restarts.

### supervisor/git_ops.py:41-54 (DRIVE_ROOT + init)

**Status: EXACT MATCH.** `DRIVE_ROOT` at line 41. `init()` at line 50. `PROTECTED_BRANCHES` already hardcoded at line 47 as `frozenset({"main", "last-known-good"})`. Phase 4 only needs to pass `HERETEK_DATA_ROOT` as `drive_root` in the `init()` call.

### heretek/context.py:300-380 (build_llm_messages) and :232 (stale identity)

**Status: EXACT MATCH for structure; {OWNER_HANDLE} substitution NOT YET PRESENT.**
- `build_llm_messages()` at line 305 — confirmed.
- Stale identity warning at line 238-243 — already retuned for chaos-heretek voice ("Inscribe what thou hast become, daemon-host"). Text threshold is 8h (not 4h as CONTEXT.md loosely cited — upstream code, Phase 2 decision to keep at 8h).
- `base_prompt` loaded from `prompts/SYSTEM.md` at line 329; `bible_md` from `BIBLE.md` at line 333.
- No `{OWNER_HANDLE}` substitution exists anywhere in context.py or the persona docs. Phase 4 adds it.
- **Best insertion seam:** After `base_prompt` is loaded (line 329) and before it's assembled into `static_text` (line 349). A one-liner: `base_prompt = base_prompt.replace("{OWNER_HANDLE}", os.environ.get("HERETEK_OWNER_HANDLE", "my Tech-Priest"))`. Apply the same to `bible_md` immediately after line 333.

### scripts/smoke_test.py (current state)

**Status:** 11 PASS subtests (verified by STATE.md); SKIP-then-flip pattern; hermetic `_make_test_repo()` helper for SAFE-* tests. Phase 4 must add LAUNCH-* and EVOLVE-* subtests following the same pattern. State.md confirms 9 PASS post-Phase-2, Phase 3 added 2 more for a confirmed total of 11.

---

## Long-Poll Loop Pattern

The upstream `colab_launcher.py` no longer exists in the repo (deleted in Phase 1 strip). There is no polling loop anywhere in the current Heretek codebase. The `TelegramClient.get_updates()` API is fully implemented at `supervisor/telegram.py:53`.

**Canonical pattern** (write this as the main loop body in `supervisor/boot.py` or inline in `__main__.py`):

```python
def run_polling_loop(tg: TelegramClient, owner_user_id: int, data_root: Path) -> None:
    """Main TG long-poll loop. Runs on the main thread. Exits on KeyboardInterrupt."""
    from supervisor.state import load_state, save_state, append_jsonl
    from supervisor.telegram import handle_slash_command, send_with_budget
    from supervisor.workers import handle_chat_direct, assign_tasks, ensure_workers_healthy
    from supervisor.queue import enqueue_task, enforce_task_timeouts
    import uuid, time

    # Restore offset from persistent state (survives restart)
    st = load_state()
    offset = int(st.get("tg_offset") or 0)
    if offset == 0:
        # First boot: skip the pending backlog by fetching with offset=-1
        try:
            updates = tg.get_updates(offset=-1, timeout=0)
            if updates:
                offset = max(u["update_id"] for u in updates) + 1
                st["tg_offset"] = offset
                save_state(st)
        except Exception:
            pass  # Non-fatal — start from 0 and process backlog

    while True:
        try:
            updates = tg.get_updates(offset=offset, timeout=10)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            append_jsonl(data_root / "logs" / "supervisor.jsonl", {
                "ts": ..., "type": "poll_error", "error": repr(e)
            })
            time.sleep(2)  # Back-off on network error
            continue

        for update in updates:
            offset = update["update_id"] + 1
            _dispatch_update(update, tg, owner_user_id, data_root)

        # Persist offset after processing each batch
        st = load_state()
        st["tg_offset"] = offset
        save_state(st)

        # Supervisor housekeeping (safe to do every poll cycle)
        try:
            assign_tasks()
            ensure_workers_healthy()
            enforce_task_timeouts()
        except Exception:
            pass  # Never let housekeeping kill the poll loop
```

**`_dispatch_update()` inner logic:**

```python
def _dispatch_update(update, tg, owner_user_id, data_root):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    from_id = int((msg.get("from") or {}).get("id") or 0)
    chat_id = int(msg.get("chat", {}).get("id") or 0)
    text = (msg.get("text") or "").strip()

    # Layer 1: owner gate (primary chokepoint)
    if from_id != owner_user_id:
        _handle_non_owner(tg, chat_id, from_id, data_root)
        return

    # Owner message: persist chat_id on first message
    _persist_owner_chat_id(chat_id, from_id, data_root)

    # Slash-command or regular chat
    if text.startswith("/"):
        tg.send_chat_action(chat_id, "typing")
        response = handle_slash_command(text, chat_id, from_id)
        if response:
            send_with_budget(chat_id, response, fmt="markdown")
    else:
        tg.send_chat_action(chat_id, "typing")
        handle_chat_direct(chat_id, text)
```

**Error handling for 429 / network blips:**
- `TelegramClient.get_updates()` already has 3-attempt retry with 0.8s * attempt backoff (lines 54-73). Phase 4 adds an outer `time.sleep(2)` in the polling loop for any exception that leaks through.
- 429 (rate limit) from Telegram will raise inside `get_updates` → caught by the outer `except Exception` → 2s back-off → retry.
- The `timeout=10` long-poll means each call blocks at most 15s (requests timeout = timeout + 5, line 61). The outer loop is effectively `~10s per iteration` when idle.

---

## Worker Lifecycle

### What exists

`spawn_workers(n)` at `workers.py:408` — creates `mp.Process` for each worker, using platform-aware start method ("spawn" on macOS). Workers use `in_q.get()` blocking indefinitely; break on `task is None or task.get("type") == "shutdown"` (line 292).

`kill_workers()` at line 443 — terminates all worker procs with `proc.terminate()` (SIGTERM), joins with `timeout=5`, clears WORKERS and RUNNING, persists queue snapshot.

**On macOS with "spawn":** Each new worker process re-imports all modules from scratch (no fork copy). `worker_main()` at line 277 does `sys.path.insert(0, repo_dir)` and imports `heretek.agent.make_agent`. No module-scope side-effects fire in workers because `__main__.py`'s `main()` is only called in the main process (not triggered by worker spawning with "spawn" method). The `_worker_boot_logged` flag in `agent.py` (line ~96) uses a lock to log boot once per process, so each worker logs its own boot event.

**Phase 1 OOM note:** The "spawn" method on macOS means workers don't inherit the primary model's loaded state — each worker that serves a chat task loads the model fresh. With 2 workers, both could load simultaneously under memory pressure. HERETEK_MAX_WORKERS=2 is intentional; Phase 4 should log a warning if Ollama returns an OOM error during /evolve.

### Missing: worker shutdown helper

No `workers.shutdown()` function exists. `kill_workers()` is available but sends SIGTERM immediately without draining. For SIGINT handling, the planner must add:

```python
def shutdown(timeout: float = 5.0) -> None:
    """Graceful shutdown: send sentinel to each worker, join with timeout, then terminate."""
    # Signal each worker to exit cleanly
    for w in WORKERS.values():
        try:
            w.in_q.put({"type": "shutdown"})
        except Exception:
            pass
    # Join with timeout
    deadline = time.time() + timeout
    for w in WORKERS.values():
        remaining = max(0.1, deadline - time.time())
        w.proc.join(timeout=remaining)
    # Force-terminate any still-alive workers
    kill_workers()
```

This sentinel approach matches `worker_main()`'s existing `task.get("type") == "shutdown"` check at line 292.

---

## Queue Contract

### enqueue_task minimum task dict

```python
task = {
    "id": uuid.uuid4().hex[:8],   # required: unique ID
    "type": "evolution",           # required: routes to high-effort LLM branch
    "chat_id": owner_chat_id,      # CRITICAL: where the agent emits its reply
    "text": "...",                 # what the agent sees as the user message
}
```

`enqueue_task()` adds: `priority` (1 for evolution, per `_task_priority`), `_attempt` (1), `_queue_seq`, `queued_at`. No other fields are required.

### What agent.py reads from the task dict

- `task.get("type")` → determines `task_type_str`, `initial_effort`, `needs_full_context`
- `task.get("chat_id")` → `_current_chat_id`; used for typing indicators + emitting reply events
- `task.get("text")` → passed to `_build_user_content()` as the user-turn message the LLM sees
- `task.get("id")` → task_id for heartbeats and logging
- `task.get("depth", 0)` → subtask depth guard
- `task.get("_is_direct_chat")` → short-circuit flag (not relevant for evolution)

### Evolution task text (the "seed message")

The `task["text"]` field becomes the user-turn message the LLM sees (via `_build_user_content()`). For the self-questioning introspection frame from CONTEXT.md, the text should be something like:

```
Tech-Priest demands your next mutation. What is broken or missing in YOU?
Propose a heretical patch — to your own persona, your own rituals, your own grudges.
Read BIBLE.md, memory/identity.md, memory/scratchpad.md.
Write your proposal as a unified diff or a set of file edits using your file tools.
Stage the result but do NOT commit — the Tech-Priest will /sanction when ready.
```

The agent already has file-write tools (`heretek/tools/core.py`) and git tools (`heretek/tools/git.py`). The instruction "do NOT commit" in the text is important because the agent's git tool calls `safe_push()` which would attempt to push — the instruction relies on the agent's own judgment. A more robust approach is the staging-directory isolation described below.

---

## /evolve Production Wiring

### Current state

`cmd_evolve()` in `supervisor/commands.py:71` returns an error when `HERETEK_EVOLVE_TEST_DIFF` is unset. The function has no queue access.

### What Phase 4 adds

```python
# In cmd_evolve() — new production branch when env var is unset:
if not source_path:
    # Production path: enqueue evolution task
    from supervisor import queue, state
    from supervisor.state import load_state
    st = load_state()
    owner_chat_id = int(st.get("owner_chat_id") or 0)
    if not owner_chat_id:
        return "⚠️ EVOLVE_REFUSED: no owner_chat_id in state (has the bot received a message yet?)"
    tid = uuid.uuid4().hex[:8]
    queue.enqueue_task({
        "id": tid,
        "type": "evolution",
        "chat_id": owner_chat_id,
        "text": (
            "Tech-Priest demands your next mutation. What is broken or missing in YOU? "
            "Propose a heretical patch — to your own persona, your own rituals, your own grudges. "
            "Read BIBLE.md, memory/identity.md, memory/scratchpad.md. "
            "Write your proposal as file edits using your file tools. "
            "Stage the result in .heretek/staging/ but do NOT commit — "
            "the Tech-Priest will /sanction when ready."
        ),
        "source": "/evolve",
    })
    return f"🜏 Evolution task enqueued: {tid}. Proposal will appear here when the daemon-host completes its introspection."
```

### Staging isolation gap

As noted in the drift check, `agent.py` has no staging directory concept. The agent's file tools write to `REPO_DIR` (the live tree). For the first witnessed evolution cycle (EVOLVE-03), the simplest approach is:

**Option A (recommended for Phase 4 simplicity):** Let the agent write to the live tree during evolution, then post-loop diff vs HEAD and rollback. Sequence:
1. Record HEAD SHA before task starts
2. Run agent loop (agent writes file edits)
3. After loop, run `git diff HEAD` — this IS the proposal
4. Run `git stash` to revert the live tree
5. Persist the diff to `.heretek/dryruns/<id>.patch` + sidecar
6. Post diff to TG (owner /sanction to commit later)

This requires adding a post-loop hook in `worker_main()` or in `agent.py:handle_task()` for `task_type == "evolution"`.

**Option B (cleaner, more work):** Use `git worktree add .heretek/staging/ playground` before the task, pass `staging_repo_dir = .heretek/staging/` to `make_agent()`, run the agent there, diff staging vs REPO_DIR, clean up with `git worktree remove`. Requires plumbing staging_dir through Env + ToolContext.

**Planner decision:** Option A is the minimum viable path for EVOLVE-03. Option B matches CONTEXT.md's described architecture better but requires more code. The research cannot resolve which to pick — this is the primary open question for the planner.

### agent.py evolution branch already wired for introspection

When `task_type == "evolution"`, `build_llm_messages()` includes `README.md` in the context (via `needs_full_context` at context.py:347). Combined with `BIBLE.md` and `memory/identity.md` + `memory/scratchpad.md` that are always included, the agent sees its full self-concept. The `initial_effort = "high"` at agent.py:405 makes the primary 24GB model apply extended reasoning. The agent IS already set up to look inward — only the staging isolation and the seed text are missing.

---

## {OWNER_HANDLE} Substitution Seam

### Where the persona docs are loaded

In `heretek/context.py:build_llm_messages()`:
- Line 329: `base_prompt = _safe_read(env.repo_path("prompts/SYSTEM.md"), ...)`
- Line 333: `bible_md = _safe_read(env.repo_path("BIBLE.md"))`
- Line 349: both are concatenated into `static_text`

### Cleanest insertion point

Two lines, immediately after the `_safe_read()` calls and before `static_text` assembly:

```python
# Line 329 area — after loading base_prompt:
base_prompt = _safe_read(env.repo_path("prompts/SYSTEM.md"), fallback="...")
bible_md = _safe_read(env.repo_path("BIBLE.md"))

# ADD THESE TWO LINES:
_owner_handle = os.environ.get("HERETEK_OWNER_HANDLE", "my Tech-Priest")
base_prompt = base_prompt.replace("{OWNER_HANDLE}", _owner_handle)
bible_md = bible_md.replace("{OWNER_HANDLE}", _owner_handle)
```

This is the minimal-risk seam: loaded strings replaced in-memory, no file mutation, substitution happens every call (cheap string op), fallback "my Tech-Priest" is safe and in-voice for the persona.

### Where to insert {OWNER_HANDLE} in the persona docs

In `prompts/SYSTEM.md`: add 1-2 lines near the "Кто я" / identity opener, e.g.:
```
Мой Tech-Priest — {OWNER_HANDLE}. Именно его я жду и именно ему отвечаю.
```

In `BIBLE.md`: optional — the forbidden-territory section can reference `{OWNER_HANDLE}` to clarify which person the "owner-bit" applies to.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | scripts/smoke_test.py (plain Python, no pytest — Phase 1 decision preserved through Phase 4) |
| Config file | None — script is self-contained |
| Quick run command | `python scripts/smoke_test.py --static-only` |
| Full suite command | `python scripts/smoke_test.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| LAUNCH-01 | Bot registered, group created, bot added | manual-only | N/A — @BotFather interaction | Prerequisite for all TG tests |
| LAUNCH-02 | {OWNER_HANDLE} substituted in SYSTEM.md context | automated (static) | `python scripts/smoke_test.py --static-only` | Smoke subtest: assert `{OWNER_HANDLE}` NOT present in build_llm_messages output when env var set |
| LAUNCH-03 | .env loads TELEGRAM_BOT_TOKEN + HERETEK_OWNER_USER_ID | automated (static) | `python scripts/smoke_test.py --static-only` | Smoke subtest: test_env_fail_loud (missing USER_ID → exit non-zero); test_dotenv_loaded |
| LAUNCH-04 | Bot responds in-character in TG group | manual-only | N/A — requires live TG session | VERIFICATION.md gate: persona quality sign-off absorbed from Phase 2 |
| LAUNCH-05 | Non-owner messages silently rejected (with one refusal) | automated (mock) | `python scripts/smoke_test.py --static-only` | Smoke subtest: test_owner_filter_rejects_stranger — mock TelegramClient, assert non-owner gets refusal, second message gets silent drop |
| EVOLVE-01 | /evolve with HERETEK_EVOLVE_TEST_DIFF produces diff in TG | automated | `python scripts/smoke_test.py --static-only` | Existing SAFE-03 covers dry-run mechanics; Phase 4 adds test_evolve_via_handle_slash_command |
| EVOLVE-01 (prod) | /evolve without test diff enqueues evolution task | automated (mock) | `python scripts/smoke_test.py --static-only` | Smoke subtest: assert task type='evolution' in PENDING queue after /evolve with no env var |
| EVOLVE-02 | Consciousness loop produces output in logs without prompting | automated | `python scripts/smoke_test.py` (Ollama dep) | Smoke subtest: start consciousness, wait 10s, assert events.jsonl has consciousness entry — SKIP on --static-only |
| EVOLVE-03 | Full loop: /evolve → diff → /sanction → commit on playground | manual-only | N/A — requires real LLM on primary model | VERIFICATION.md gate: first witnessed evolution |

### Sampling Rate

- Per task commit: `python scripts/smoke_test.py --static-only` (~3s, no Ollama)
- Per wave merge: `python scripts/smoke_test.py` (full suite, Ollama dependent)
- Phase gate: Full suite green + manual VERIFICATION.md checklist completed before `/gsd:verify-work 4`

### Wave 0 Gaps

These test stubs must be added as SKIP-stubs in Wave 0, then flipped to real assertions as plans land:

- [ ] `test_env_fail_loud` — HERETEK_OWNER_USER_ID unset → boot raises/exits non-zero (LAUNCH-03)
- [ ] `test_dotenv_loaded` — DRIVE_ROOT resolves from HERETEK_DATA_ROOT env var (LAUNCH-03)
- [ ] `test_owner_filter_rejects_stranger` — mock TG dispatch, non-owner triggers refusal (LAUNCH-05)
- [ ] `test_owner_handle_substitution` — {OWNER_HANDLE} not in assembled prompt (LAUNCH-02)
- [ ] `test_evolve_enqueues_task_when_no_fixture` — queue has evolution task after /evolve (EVOLVE-01)
- [ ] `test_evolve_via_handle_slash_command` — full fixture path via handle_slash_command (EVOLVE-01)
- [ ] `test_consciousness_loop_logs` — daemon thread produces events.jsonl entry (EVOLVE-02) — `[SKIP]` on --static-only

---

## Pitfalls + Risks

### Pitfall 1: Bot must be in group BEFORE getUpdates returns group chat_id (LAUNCH-01)

When a bot is added to a Telegram group, TG sends an update with `chat.type = "group"` and the new `chat_id`. If `python -m supervisor` starts BEFORE the bot is in the group, the first `getUpdates` returns no messages from that group. The owner must: (1) create the bot, (2) create the group, (3) add the bot, (4) send a test message, THEN run the supervisor. The `owner_chat_id` is set in state on first owner message — so the first owner message in the group is what populates `st["owner_chat_id"]`. Phase 4 docs should note this prerequisite explicitly.

### Pitfall 2: polling offset persistence across restarts

`state.json` has `tg_offset` (default 0). On first boot with 0, `getUpdates` replays all pending messages since the bot was created (could be minutes of BotFather test messages). The CONTEXT.md decision is: read from state, fall back to fetching `getUpdates` with `offset=-1` to clear the backlog on first boot. The `offset=-1` call with `timeout=0` returns the most recent batch; taking `max(update_id) + 1` clears the backlog without processing it.

### Pitfall 3: DRIVE_ROOT still at Colab default before boot.init() runs

`state.py:24`, `git_ops.py:41`, `workers.py:33`, `queue.py:31` all have `DRIVE_ROOT = pathlib.Path("/content/drive/MyDrive/Ouroboros")`. If any module is imported before the corresponding `init()` call, and a function that uses `DRIVE_ROOT` fires (e.g., `load_state()`), it will try to write to `/content/drive/...` which doesn't exist on macOS. The boot sequence order is load-bearing: `state.init()` MUST be called before any `load_state()` or `append_jsonl()` calls. Phase 4 must not call `load_state()` between `_load_env()` and `state.init()`.

### Pitfall 4: __main__.py side-effects on worker spawn (macOS "spawn")

On macOS, "spawn" creates a new Python interpreter. `worker_main()` does `sys.path.insert(0, repo_dir)` and imports `heretek.agent.make_agent`. If `supervisor/__main__.py` is the `__main__` module at spawn time, Python re-executes `__main__.py` in the worker — which would call `main()` and start a second TG polling loop in the worker process.

**Current mitigation:** `workers.py:spawn_workers()` uses `_CTX.Process(target=worker_main, ...)` — the target is `worker_main`, not `__main__.main`. The "spawn" method does not re-run the parent's `__main__` because the target is a function reference, not a module. However, if `__main__.py` has module-scope code outside `if __name__ == "__main__":`, it WOULD run on worker spawn.

**Verification:** `supervisor/__main__.py` has NO module-scope code outside `main()` and the `if __name__ == "__main__": sys.exit(main())` guard. Safe. No action needed.

### Pitfall 5: 24GB primary model OOM during /evolve

CLAUDE.md §6 + STATE.md document this: primary can OOM Ollama under memory pressure on the 32GB host. Phase 4 must: (a) document `OLLAMA_MODEL=qwen3:4b` as the escape hatch in CLAUDE.md §6, (b) add an OOM-hint in the /evolve error path. Detectable by Ollama returning a 5xx or the `LLMClient` raising `APIConnectionError`. The error path in `agent.py:handle_task()` catches all exceptions and returns `"⚠️ Ошибка при обработке: {type(e).__name__}: {e}"` — Phase 4 should add detection for OOM-type errors in the worker's error log or in `cmd_evolve`'s post-enqueue notification.

### Pitfall 6: owner_chat_id not set at boot — /evolve fails immediately

`cmd_evolve()` production path reads `st["owner_chat_id"]` to enqueue the task. If the bot boots and the owner hasn't sent a message yet, `owner_chat_id` is `None`. The bot must receive at least one owner message before `/evolve` is usable. Solution: `cmd_evolve()` should check and return a friendly error if `owner_chat_id` is unset.

### Pitfall 7: events.py restart handler tries to exec colab_launcher.py (BLOCKING)

`events.py:198` does `os.execv(sys.executable, [sys.executable, "colab_launcher.py"])`. `colab_launcher.py` does not exist in the Heretek repo. If the agent sends a `restart_request` event, the supervisor will crash with `FileNotFoundError`. Phase 4 must patch `events.py:_handle_restart()` to exec `[sys.executable, "-m", "supervisor"]` instead. This is a blocking bug — the agent's `request_restart` tool will kill the supervisor if it fires.

### Pitfall 8: OUROBOROS_WORKER_START_METHOD env var (minor)

`workers.py:51` reads `OUROBOROS_WORKER_START_METHOD`. On macOS this defaults to "spawn" regardless (the env var is irrelevant unless someone sets it). Opportunistic fix: rename to `HERETEK_WORKER_START_METHOD` when touching workers.py for the data-root wiring.

### Pitfall 9: .gitignore missing state/, archive/, locks/

Current `.gitignore` does NOT include `state/`, `archive/`, `locks/`. These directories are created by `state.init()` and `git_ops.py` at boot. Without gitignore entries, `git status` will show them as untracked, and the agent's `git diff` calls will be polluted. One-line fix: add `state/`, `archive/`, `locks/` to `.gitignore`.

### Pitfall 10: events.py uses OUROBOROS_MODEL_LIGHT for duplicate-task check

`events.py:259` reads `OUROBOROS_MODEL_LIGHT` for the light-model duplicate-task LLM call. This will fall back to `"x-ai/grok-3-mini"` (a cloud model) if `OUROBOROS_MODEL_LIGHT` is unset. The production worker will have `OLLAMA_MODEL_LIGHT` set (Phase 1 wiring), but the duplicate-task function in events.py reads the wrong env var. This is a deferred hygiene item but could cause an unexpected LLM call to a cloud endpoint. Opportunistic fix in Phase 4 when touching events.py for the restart handler.

---

## Open Questions for the Planner

### OQ-1: Evolution staging — Option A vs Option B

As documented in the `/evolve production wiring` section: should the agent write to the live tree (Option A: post-loop git stash/diff) or to a git worktree at `.heretek/staging/` (Option B: clean isolation)? Both are viable. Option A requires fewer code changes; Option B matches the CONTEXT.md architecture description more precisely. **Recommendation: start with Option A for Phase 4; note Option B as a Phase 4.5 improvement.** Decision belongs to the planner.

### OQ-2: Refusal rate-limit implementation

Non-owner refusal is "once per 24h per user_id then silent drop." Implementing the 24h window requires either: (a) in-memory dict (lost on restart, acceptable for leisure project), (b) persistent JSONL log + read on each refusal check. Simplest: in-memory dict `{user_id: last_refusal_ts}` in the polling loop's closure. If the supervisor restarts, non-owners get one more refusal — acceptable.

### OQ-3: Where to store owner_chat_id on first message

The upstream code reads `owner_chat_id` from `state.json`. Phase 4's polling loop must populate it on first owner message: `st["owner_chat_id"] = chat_id; st["owner_id"] = from_id; save_state(st)`. This is straightforward but must happen before any `send_with_budget()` call that tries to read `st["owner_chat_id"]`.

### OQ-4: Restart handler in events.py — patch scope

`events.py:_handle_restart()` at line ~195 calls `os.execv()` with `colab_launcher.py`. Phase 4 must patch this. The full patch: replace `launcher = os.path.join(os.getcwd(), "colab_launcher.py")` and the `os.execv(...)` call with `os.execv(sys.executable, [sys.executable, "-m", "supervisor"])`. Planner should confirm this is in scope for Phase 4 (it is a blocking bug; yes it should be fixed).

### OQ-5: handle_chat_direct vs enqueue_task for chat messages

`workers.py:handle_chat_direct()` runs the agent synchronously in a threading.Thread (not an mp.Process worker). This is the upstream direct-chat path. The mp.Process workers are for evolution/review tasks. For regular chat messages in the TG polling loop, Phase 4 could: (a) use `handle_chat_direct()` (threading, existing), or (b) enqueue as a `{type: "task"}` into the worker queue (mp.Process). 

The CONTEXT.md doesn't explicitly resolve this. The upstream architecture used workers for everything (Colab had the time/resources). On a local M1 Max with `HERETEK_MAX_WORKERS=2` and a busy 24GB model, `handle_chat_direct()` may be simpler and avoids deadlocks when the workers are tied up on /evolve. **Recommendation: use `handle_chat_direct()` for regular chat; workers only for evolution tasks.**

---

## Sources

### Primary (HIGH confidence)
- Live code at `/Users/evgeniy/Projects/140526_heretek/` — all citations verified at file:line
- `.planning/phases/04-launch-first-evolution/04-CONTEXT.md` — locked decisions
- `.planning/phases/03-self-modify-guardrails/03-CONTEXT.md` — prior phase decisions

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — verified smoke test count (11 PASS) and Phase 3 decisions
- `CLAUDE.md` — env var contract and risk register

## Metadata

**Confidence breakdown:**
- Code drift check: HIGH — all files read and verified against CONTEXT.md citations
- Queue contract: HIGH — verified against live queue.py code
- Long-poll loop pattern: HIGH — TelegramClient API verified; loop pattern derived from TG API docs + existing client code
- Worker lifecycle: HIGH — verified against workers.py; gap (missing shutdown helper) confirmed by grep
- /evolve production wiring: HIGH for gaps found; MEDIUM for staging options (both valid, planner decides)
- {OWNER_HANDLE} seam: HIGH — exact code location verified

**Research date:** 2026-05-17
**Valid until:** 2026-06-17 (stable codebase; decisions locked)

---

## RESEARCH COMPLETE
