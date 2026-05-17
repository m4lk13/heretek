"""supervisor/boot.py — Phase 4 production boot sequence + TG long-poll loop.

Called from supervisor/__main__.py after env validation + data-root
resolution land. Owns the locked boot order from 04-CONTEXT.md:

  1. state.init(drive_root)
  2. git_ops.init(repo_dir, drive_root, remote_url, ...)
  3. TelegramClient(token) + telegram.init(...)
  4. workers.init(...) + spawn_workers(HERETEK_MAX_WORKERS)
  5. consciousness.start()  [daemon thread on OLLAMA_MODEL_LIGHT]
  6. Enter main TG long-poll loop

On SIGINT/SIGTERM: drain workers, stop consciousness, exit 0.

Phase 4 owner gate (LAUNCH-05):
  Layer 1 (primary) — _dispatch_update checks is_owner_message before
    any downstream call; non-owners go to handle_non_owner_message.
  Layer 2 (defense) — handle_slash_command re-checks (added by Plan 04-02).
  Layer 3 (defense) — agent task entry can also re-check (Plan 04-04 may add).
"""
from __future__ import annotations

import datetime
import logging
import os
import queue as queue_mod
import signal
import sys
import threading
import time
import types
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

# In-process flag flipped by signal handlers
_SHUTDOWN_REQUESTED = False
_EVENT_DRAINER_STOP = threading.Event()


def _utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _request_shutdown(signum, frame):
    """SIGINT/SIGTERM handler — sets the flag; main loop checks it."""
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True
    log.info("boot: shutdown requested (signum=%s)", signum)


def run(data_root: Path) -> int:
    """Production boot sequence + TG long-poll loop. Returns exit code."""
    from supervisor import state, git_ops, workers, queue
    from supervisor.state import append_jsonl, load_state, save_state
    from supervisor.telegram import (
        TelegramClient, send_with_budget, handle_slash_command,
        is_owner_message, handle_non_owner_message, init as telegram_init,
    )

    # --- 1. state.init ---
    # MUST be first so subsequent load_state()/append_jsonl() calls hit the
    # right drive_root (Pitfall 3 in 04-RESEARCH).
    state.init(drive_root=data_root)

    # --- 2. git_ops.init ---
    repo_dir = Path(__file__).resolve().parent.parent
    git_ops.init(
        repo_dir=repo_dir,
        drive_root=data_root,
        remote_url=os.environ.get("HERETEK_REMOTE_URL", "") or "",
        branch_dev=os.environ.get("HERETEK_PLAYGROUND_BRANCH", "playground"),
        branch_stable="last-known-good",
    )

    # --- 3. TelegramClient + telegram.init ---
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    # Token presence already validated in __main__._validate_required_env;
    # this is defense-in-depth.
    if not token:
        print("[boot] FATAL: TELEGRAM_BOT_TOKEN missing at boot.run()", file=sys.stderr)
        return 2
    tg = TelegramClient(token)
    telegram_init(
        drive_root=data_root,
        total_budget_limit=0.0,
        budget_report_every=10,
        tg_client=tg,
    )

    # --- 4. workers.init + spawn ---
    max_workers = int(os.environ.get("HERETEK_MAX_WORKERS", "2") or "2")
    workers.init(
        repo_dir=repo_dir,
        drive_root=data_root,
        max_workers=max_workers,
        soft_timeout=int(os.environ.get("HERETEK_SOFT_TIMEOUT_SEC", "600") or "600"),
        hard_timeout=int(os.environ.get("HERETEK_HARD_TIMEOUT_SEC", "1800") or "1800"),
        total_budget_limit=0.0,  # Local Ollama — no $ budget
    )
    workers.spawn_workers(n=max_workers)

    # --- 5. consciousness daemon thread ---
    # Lazy import to keep boot.py free of agent-side import cost
    consciousness = None
    try:
        from heretek.consciousness import BackgroundConsciousness

        # owner_chat_id_fn returns the current owner chat_id from state.json
        def _owner_chat_fn() -> Optional[int]:
            try:
                st = load_state()
                cid = st.get("owner_chat_id")
                return int(cid) if cid else None
            except Exception:
                return None

        consciousness = BackgroundConsciousness(
            drive_root=data_root,
            repo_dir=repo_dir,
            event_queue=workers.get_event_q(),
            owner_chat_id_fn=_owner_chat_fn,
        )
        consciousness.start()
        log.info("boot: consciousness started")
    except Exception as e:
        log.warning("boot: consciousness failed to start: %s", e, exc_info=True)
        consciousness = None

    # --- 6. event drainer thread ---
    # Worker/agent events land on workers.get_event_q() but nothing was
    # consuming them — agent-side `send_message` events sat forever in the
    # queue, so the bot typed but never spoke. Build a ctx bundle and start
    # a daemon that dispatches each event via supervisor.events.dispatch_event.
    ctx = _build_event_ctx(tg, data_root, send_with_budget, consciousness)
    drainer = threading.Thread(
        target=_event_drainer_loop,
        args=(workers.get_event_q(), ctx),
        name="event-drainer",
        daemon=True,
    )
    drainer.start()
    log.info("boot: event drainer started")

    # --- 7. signal handlers ---
    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    # --- 8. polling loop ---
    try:
        _run_polling_loop(tg, data_root)
    except KeyboardInterrupt:
        log.info("boot: KeyboardInterrupt — shutting down")
    finally:
        # Graceful shutdown — stop drainer, drain workers, stop consciousness
        _EVENT_DRAINER_STOP.set()
        try:
            workers.shutdown(timeout=5.0)
        except Exception:
            log.warning("boot: workers.shutdown failed", exc_info=True)
        if consciousness is not None:
            try:
                consciousness.stop()
            except Exception:
                log.warning("boot: consciousness.stop failed", exc_info=True)
        append_jsonl(data_root / "logs" / "supervisor.jsonl", {
            "ts": _utc_iso(), "type": "boot_shutdown_complete",
        })

    return 0


def _build_event_ctx(tg: Any, data_root: Path, send_with_budget: Any,
                     consciousness: Any) -> types.SimpleNamespace:
    """Assemble the ctx object that supervisor.events handlers expect."""
    from supervisor import workers as _workers
    from supervisor import queue as _queue
    from supervisor.state import (
        append_jsonl as _append_jsonl,
        load_state as _load_state,
        save_state as _save_state,
        update_budget_from_usage as _update_budget,
    )
    from supervisor.git_ops import safe_restart as _safe_restart

    ctx = types.SimpleNamespace()
    ctx.TG = tg
    ctx.DRIVE_ROOT = data_root
    ctx.send_with_budget = send_with_budget
    ctx.append_jsonl = _append_jsonl
    ctx.load_state = _load_state
    ctx.save_state = _save_state
    ctx.update_budget_from_usage = _update_budget
    ctx.RUNNING = _workers.RUNNING
    ctx.PENDING = _workers.PENDING
    ctx.WORKERS = _workers.WORKERS
    ctx.kill_workers = _workers.kill_workers
    ctx.enqueue_task = _queue.enqueue_task
    ctx.persist_queue_snapshot = _queue.persist_queue_snapshot
    ctx.sort_pending = _queue.sort_pending
    ctx.cancel_task_by_id = _queue.cancel_task_by_id
    ctx.queue_review_task = _queue.queue_review_task
    ctx.safe_restart = _safe_restart
    ctx.consciousness = consciousness
    return ctx


def _event_drainer_loop(event_q: Any, ctx: types.SimpleNamespace) -> None:
    """Daemon loop: pull events off the worker/agent queue and dispatch."""
    from supervisor.events import dispatch_event
    while not _EVENT_DRAINER_STOP.is_set():
        try:
            evt = event_q.get(timeout=0.5)
        except queue_mod.Empty:
            continue
        except (EOFError, OSError):
            # Queue closed during shutdown
            break
        except Exception:
            log.debug("event drainer: get failed", exc_info=True)
            continue
        if evt is None:  # sentinel
            continue
        try:
            dispatch_event(evt, ctx)
        except Exception:
            log.warning("event drainer: dispatch_event raised", exc_info=True)


def _run_polling_loop(tg: Any, data_root: Path) -> None:
    """TG long-poll main loop. Runs on the supervisor's main thread."""
    from supervisor import workers, queue
    from supervisor.state import load_state, save_state, append_jsonl

    # Restore offset; on first boot (offset==0) skip backlog via offset=-1
    st = load_state()
    offset = int(st.get("tg_offset") or 0)
    if offset == 0:
        try:
            updates = tg.get_updates(offset=-1, timeout=0)
            if updates:
                offset = max(int(u["update_id"]) for u in updates) + 1
                st["tg_offset"] = offset
                save_state(st)
                append_jsonl(data_root / "logs" / "supervisor.jsonl", {
                    "ts": _utc_iso(), "type": "boot_skipped_backlog",
                    "skipped_to_offset": offset,
                })
        except Exception:
            log.debug("boot: backlog-skip getUpdates failed", exc_info=True)

    append_jsonl(data_root / "logs" / "supervisor.jsonl", {
        "ts": _utc_iso(), "type": "polling_loop_start", "offset": offset,
    })

    while not _SHUTDOWN_REQUESTED:
        try:
            updates = tg.get_updates(offset=offset, timeout=10)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            append_jsonl(data_root / "logs" / "supervisor.jsonl", {
                "ts": _utc_iso(), "type": "poll_error", "error": repr(e),
            })
            time.sleep(2)
            continue

        for update in updates:
            try:
                offset = int(update["update_id"]) + 1
                _dispatch_update(update, tg, data_root)
            except Exception as e:
                append_jsonl(data_root / "logs" / "supervisor.jsonl", {
                    "ts": _utc_iso(), "type": "dispatch_error",
                    "error": repr(e), "update_id": update.get("update_id"),
                })

        # Persist offset after each batch
        if updates:
            try:
                st = load_state()
                st["tg_offset"] = offset
                save_state(st)
            except Exception:
                log.debug("boot: tg_offset persist failed", exc_info=True)

        # Per-cycle housekeeping (never let it kill the loop)
        try:
            workers.assign_tasks()
        except Exception:
            log.debug("boot: assign_tasks failed", exc_info=True)
        try:
            workers.ensure_workers_healthy()
        except Exception:
            log.debug("boot: ensure_workers_healthy failed", exc_info=True)
        try:
            queue.enforce_task_timeouts()
        except Exception:
            log.debug("boot: enforce_task_timeouts failed", exc_info=True)


def _dispatch_update(update: Dict[str, Any], tg: Any, data_root: Path) -> None:
    """Owner-gate + slash-vs-chat routing for a single TG update."""
    from supervisor.state import load_state, save_state, append_jsonl
    from supervisor.telegram import (
        send_with_budget, handle_slash_command,
        is_owner_message, handle_non_owner_message,
    )
    from supervisor.workers import handle_chat_direct

    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    from_id = int((msg.get("from") or {}).get("id") or 0)
    chat_id = int(msg.get("chat", {}).get("id") or 0)
    text = (msg.get("text") or "").strip()

    # --- LAYER 1 OWNER GATE (primary chokepoint) ---
    if not is_owner_message(update):
        handle_non_owner_message(chat_id=chat_id, from_id=from_id, tg_client=tg)
        return

    # Owner — persist chat_id on first message if not yet set
    st = load_state()
    if not st.get("owner_chat_id"):
        st["owner_chat_id"] = chat_id
        st["owner_id"] = from_id
        save_state(st)
        append_jsonl(data_root / "logs" / "supervisor.jsonl", {
            "ts": _utc_iso(), "type": "owner_chat_id_pinned",
            "chat_id": chat_id, "owner_id": from_id,
        })

    if text.startswith("/"):
        try:
            tg.send_chat_action(chat_id, "typing")
        except Exception:
            log.debug("dispatch: typing indicator failed", exc_info=True)
        response = handle_slash_command(text, chat_id, from_id)
        if response:
            send_with_budget(chat_id, response, fmt="markdown")
    else:
        # Owner chat message — threading-based direct path (not worker queue)
        try:
            tg.send_chat_action(chat_id, "typing")
        except Exception:
            log.debug("dispatch: typing indicator failed", exc_info=True)
        handle_chat_direct(chat_id, text)
