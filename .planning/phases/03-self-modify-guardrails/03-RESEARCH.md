# Phase 3: Self-Modify Guardrails — Research

**Researched:** 2026-05-16
**Domain:** Git branch protection, dry-run diff pipeline, CLI command dispatch
**Confidence:** HIGH (all findings directly verified against source files)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Single `safe_push(branch, refspec=None, ...)` function in `supervisor/git_ops.py` as the only sanctioned write path to git remotes
- All three existing push sites refactored to call it: `heretek/tools/git.py:115`, `supervisor/events.py:207`, `heretek/agent.py:172`
- Hard exception on protected branch (class name at planner's discretion)
- Protected-branch list from `HERETEK_PROTECTED_BRANCHES` env var with hardcoded fallback `{main, last-known-good}`
- Populated in `git_ops.init()` at supervisor boot
- `last-known-good` tag advances on every successful `/sanction` commit (not on a timer)
- Tag-move via `git tag -f -a last-known-good -m "sanctioned: <msg>" <sha>` after commit, before response returned
- Branch defaults rename: `BRANCH_DEV "heretek" -> "playground"`, `BRANCH_STABLE "heretek-stable" -> "last-known-good"` (same Phase 3 file, atomic)
- `/evolve`, `/sanction <hash>`, `/heresy` implemented in `supervisor/telegram.py` dispatcher + new `supervisor/commands.py`
- Handler functions `cmd_evolve()`, `cmd_sanction(hash)`, `cmd_heresy()` are pure-Python entry points in `commands.py`
- CLI shim `python -m supervisor.commands evolve|sanction <hash>|heresy` as offline test front door
- `scripts/smoke_test.py` extended with ~6 subtests under SAFE-01..06, SKIP-then-flip pattern
- `/evolve` writes to `.heretek/staging/`, patch to `.heretek/dryruns/<id>.patch` + sidecar `.heretek/dryruns/<id>.json`
- Hash format: synthetic ID (uuid8 or timestamp-prefixed, e.g. `dr-20260516T143052-a3f8`), NOT a git SHA
- `HERETEK_EVOLVE_TEST_DIFF=/path/to/fixture.patch` env var (or `--test-diff <path>` CLI flag) bypasses LLM loop
- No live-tree changes until `/sanction` — cardinal rule of dry-run
- `.heretek/` is gitignored (mirrors `memory/` pattern from Phase 2)
- All subtests use `tempfile.TemporaryDirectory()` + `git init` hermetic pattern

### Claude's Discretion
- Exception class name for `safe_push()` refusal
- Audit log destination + record shape for refused pushes
- Whether `checkout_and_reset()` also refuses protected targets (recommended yes)
- Dry-run retention policy (recommended: one active at a time + archive to `.heretek/dryruns/archive/`)
- `/heresy` uncommitted-memory handling (`memory/identity.md`, `memory/scratchpad.md` gitignored, survive by default)
- `/sanction` argument validation on hash mismatch + hand-edit detection
- `/evolve` concurrency handling (recommended: refuse second while first in progress)
- Whether to push moved `last-known-good` tag to origin after `/sanction`
- Staging mechanism: git-worktree vs plain dir + `git diff --no-index`
- Diff format returned in CLI/TG

### Deferred Ideas (OUT OF SCOPE)
- `DRIVE_ROOT` Colab path cleanup (needs Phase 4 .env work)
- `OUROBOROS_*` env var hygiene pass (opportunistic fixes only)
- Tag push to origin after `/sanction` (technically separable, planner can include or not)
- Daily/cron timer for `last-known-good` (EXP-03 stretch)
- `promote_to_stable` LLM-tool full removal (no-op or refuse-with-message acceptable for Phase 3)
- `/heresy --nuke-memory` flag
- Real LLM-driven `/evolve` end-to-end test (Phase 4)
- `/sanction` partial-apply / conflict-resolution flow
- TG-side long-diff rendering (Phase 4)
- Pytest adoption (stays as smoke_test.py)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SAFE-01 | `supervisor/git_ops.py` hard-refuses all push/commit ops targeting `main` or `last-known-good` | `safe_push()` added to `git_ops.py`; three existing push sites unified under it |
| SAFE-02 | All bot self-modifications route to `playground` branch by default | `BRANCH_DEV` default renamed to `playground`; `Env.branch_dev` default is `"heretek"` (also needs updating) |
| SAFE-03 | `/evolve` defaults to dry-run mode — diff posted, no commit | `.heretek/staging/` + `.heretek/dryruns/` pipeline; `HERETEK_EVOLVE_TEST_DIFF` fixture seam |
| SAFE-04 | `/sanction <hash>` approves pending dry-run and commits to `playground` | `cmd_sanction()` applies patch, commits, advances tag |
| SAFE-05 | `/heresy` rolls working tree back to `last-known-good` tag | `cmd_heresy()` uses `checkout_and_reset()` with `rescue_and_reset` policy |
| SAFE-06 | Daily (or per-session) auto-tag updates `last-known-good` to current playground HEAD | Tag advances on every `/sanction` (not a timer); REQUIREMENTS.md says "daily or per-session" — `/sanction`-driven satisfies "per-session" |
</phase_requirements>

---

## Overview

Phase 3 adds the safety layer that makes self-modification survivable: a single chokepoint for all git pushes, a dry-run pipeline for proposed changes, and three owner-invoked commands (`/evolve`, `/sanction`, `/heresy`) that together form the approval workflow. The entire phase is designed to be verified offline via CLI — no Telegram token needed, no live agent loop needed for the test path.

The codebase currently has THREE independent git push sites, none of which have any branch protection. All three must be unified under a new `safe_push()` function in `supervisor/git_ops.py`. The `supervisor/telegram.py` module is a pure TG client with no existing message dispatch loop — the main message-handling loop does not yet exist in the project (full boot is stubbed in `supervisor/__main__.py` as "not yet wired"). This means Phase 3 is building the slash-command dispatcher into the framework that Phase 4 will complete. The CLI shim in `supervisor/commands.py` is therefore the only testable entry point in Phase 3.

The dry-run mechanic is decoupled from the LLM loop by design: `HERETEK_EVOLVE_TEST_DIFF` injects a fixture patch, so all six smoke subtests run deterministically without burning Ollama tokens or starting the agent. This continues the established hermetic test pattern from Phases 1 and 2.

**Primary recommendation:** Build Phase 3 in three plans — (1) `safe_push()` + branch protection + branch-default renames, (2) `supervisor/commands.py` + CLI shim + dispatch hook in `telegram.py`, (3) dry-run pipeline + smoke subtests SKIP-then-flip. Keep each plan small enough to verify in a single smoke run.

---

## Codebase Facts

### Verified Facts (confirmed against actual source)

**`supervisor/git_ops.py` (415 lines, fully read):**
- Module-level globals at lines 30-34: `REPO_DIR`, `DRIVE_ROOT`, `REMOTE_URL`, `BRANCH_DEV = "heretek"`, `BRANCH_STABLE = "heretek-stable"` — stale upstream values confirmed
- `init()` signature (line 37): `init(repo_dir, drive_root, remote_url, branch_dev="heretek", branch_stable="heretek-stable")` — sets all five module globals. `PROTECTED_BRANCHES` does not exist yet; must be added as a new global populated from env inside `init()`
- `git_capture(cmd)` (line 51): `subprocess.run(cmd, cwd=str(REPO_DIR), capture_output=True, text=True)` returning `(returncode, stdout.strip(), stderr.strip)` — `safe_push()` calls this uniformly
- `_collect_repo_sync_state()` (line 73): returns dict with `current_branch`, `dirty_lines`, `unpushed_lines`, `warnings`. Rich enough to include in refusal audit log
- `_create_rescue_snapshot()` (line 161): writes `status.porcelain.txt`, `changes.diff`, `untracked/`, `rescue_meta.json` to `DRIVE_ROOT/archive/rescue/<ts>_<uuid>/`. **IMPORTANT**: uses `DRIVE_ROOT` for the rescue dir — on local macOS this points to the Colab path `/content/drive/MyDrive/Ouroboros` by default. `/heresy` needs to pass a real local DRIVE_ROOT. This is only correct after `git_ops.init()` has been called with a real path.
- `checkout_and_reset()` (line 208): does `git fetch origin` then `git checkout <branch>` then `git reset --hard origin/<branch>`. Uses `DRIVE_ROOT/logs/supervisor.jsonl` for logging. The `rescue_and_reset` policy calls `_create_rescue_snapshot()` then proceeds with the reset
- `safe_restart()` (line 352): tries `BRANCH_DEV` first, falls back to `BRANCH_STABLE` — this is the existing safe-restart path. NOT the same as `/heresy`; safe_restart is for import-test-gated restarts
- **No `safe_push()` exists.** No push logic in `git_ops.py` at all today. Push sites are entirely in `heretek/tools/git.py` and `supervisor/events.py`

**`supervisor/telegram.py` (477 lines, fully read):**
- Contains: `TelegramClient` class with `get_updates()`, `send_message()`, `send_chat_action()`, `send_photo()`, `download_file_base64()`; message formatting helpers (`split_telegram`, `_markdown_to_telegram_html`, `_chunk_markdown_for_telegram`, `_send_markdown_telegram`); `send_with_budget()`; `log_chat()`; `budget_line()`
- **NO message dispatch loop. NO slash-command routing. NO `handle_message()` or equivalent.** The Telegram polling loop (calling `get_updates()` and routing messages) does NOT exist in this file or anywhere in the current codebase. It was in upstream's `colab_launcher.py`, which has not been ported to the local boot path.
- `supervisor/__main__.py` explicitly states "full boot not yet wired" and returns exit code 2 for the non-smoke path
- `init()` in `telegram.py` (line 30): sets `DRIVE_ROOT`, `TOTAL_BUDGET_LIMIT`, `BUDGET_REPORT_EVERY_MESSAGES`, `_TG`
- **Implication for Phase 3:** The slash-command dispatch (routing `/evolve`, `/sanction`, `/heresy` from Telegram) cannot be wired into a non-existent TG loop. Phase 3's TG hook must be placed as a stub/hook point that Phase 4 completes. The CLI shim is the only testable path in Phase 3.

**`heretek/tools/git.py` (257 lines, fully read):**
- Push site 1: `_git_push_with_tests()` at line 100. Does: `_run_pre_push_tests()` → `git pull --rebase origin ctx.branch_dev` → `git push origin ctx.branch_dev`. The push is at line 115: `run_cmd(["git", "push", "origin", ctx.branch_dev], cwd=ctx.repo_dir)`
- Called by: `_repo_write_commit()` (line 124, calls at line 147) and `_repo_commit_push()` (line 156, calls at line 189)
- `ctx.branch_dev` is sourced from `ToolContext.branch_dev` — populated from `Env.branch_dev` which defaults to `"heretek"` (line 52 of `agent.py`)
- `_run_pre_push_tests()` checks `OUROBOROS_PRE_PUSH_TESTS` env var (line 65) — this is one of the residual `OUROBOROS_*` refs
- `ctx.last_push_succeeded` is set to `False` at the start of both `_repo_write_commit` and `_repo_commit_push`, then set to `True` after successful push
- `safe_push()` refactor: replace the bare `run_cmd(["git", "push", ...])` at line 115 with a call to `supervisor.git_ops.safe_push(ctx.branch_dev)`. **Import direction concern**: `heretek/tools/git.py` importing from `supervisor/git_ops.py` creates a `heretek → supervisor` dependency. This crosses the existing package boundary (supervisor imports heretek, not vice versa). Need to verify this doesn't create a circular import.

**`supervisor/events.py` (480 lines, fully read):**
- Push site 2: `_handle_promote_to_stable()` at line 202. Does: `git fetch origin` then `git push origin BRANCH_DEV:BRANCH_STABLE`. Uses `ctx.BRANCH_DEV` and `ctx.BRANCH_STABLE` attributes on the supervisor context object (not the git_ops module globals directly)
- `BRANCH_STABLE` would be `last-known-good` after the rename — meaning this handler currently pushes to `last-known-good`, which will be protected after Phase 3. The handler will fail under safe_push(). Decision: make it refuse with a message ("promote_to_stable is superseded by /sanction; use /sanction to advance last-known-good")
- The `promote_to_stable` event is triggered by `_promote_to_stable()` in `heretek/tools/control.py:41` which appends a `{"type": "promote_to_stable"}` event to `ctx.pending_events`
- `_handle_restart_request()` (line 176): calls `ctx.safe_restart()` — this is a method on the supervisor context, distinct from `git_ops.safe_restart()`
- `_find_duplicate_task()` at line 229 still uses `OUROBOROS_MODEL_LIGHT` env var (line 264) — opportunistic fix candidate if touching events.py

**`heretek/agent.py` (auto-rescue, lines 140-188, fully read):**
- Push site 3: lines 170-175. Does `git push origin self.env.branch_dev` after `git add -u`, commit, and `git pull --rebase`. Uses raw `subprocess.run` directly (not `run_cmd`)
- `self.env.branch_dev` defaults to `"heretek"` (line 52: `branch_dev: str = "heretek"` in the `Env` dataclass). This is ANOTHER place where the branch default needs updating alongside `git_ops.py` and `workers.py`
- Auto-rescue fires in `_check_uncommitted_changes()` which is called from `_log_worker_boot_once()` → `_verify_system_state()`. It's a startup safety net, not a normal push path
- Refactor: wrap the push subprocess call (lines 170-175) with `safe_push(self.env.branch_dev)`. The `supervisor.git_ops` import in `heretek/agent.py` creates the same cross-package import concern as `heretek/tools/git.py` — see Import Direction section below

**`heretek/tools/control.py` (317 lines, fully read):**
- `_promote_to_stable()` at line 40-42: appends `{"type": "promote_to_stable"}` to `ctx.pending_events`. Has stale description "Promote heretek -> heretek-stable" in the tool schema (line 218)
- `_toggle_evolution()` at line 140-148: appends `{"type": "toggle_evolution", "enabled": bool}`. This is the LLM tool side of evolution mode — NOT the `/evolve` command. They are separate concerns: `toggle_evolution` turns the evolution mode flag on/off for the agent loop; `/evolve` triggers a one-shot dry-run proposal
- `_request_restart()` at line 20-37: guard is `if str(ctx.current_task_type or "") == "evolution" and not ctx.last_push_succeeded: return "RESTART_BLOCKED"`. After Phase 3, `/sanction` sets `ctx.last_push_succeeded` (or equivalent) — important for the restart flow to work post-sanction

**`scripts/smoke_test.py` (789 lines, fully read):**
- Current state: 9 subtests total. `STATIC_SUBTESTS` list has 5 functions; `FULL_SUBTESTS` adds 4 more (precondition + 3 Ollama-dependent)
- Subtest registration pattern: lists `STATIC_SUBTESTS` and `FULL_SUBTESTS` at lines 746-758; `main()` picks based on `--static-only` flag
- Phase 3 pattern: add new functions, insert into the appropriate list. Static subtests (no Ollama, no subprocess) go in `STATIC_SUBTESTS`; CLI-subprocess subtests go in `FULL_SUBTESTS` (they need a real git repo but not Ollama)
- Hermetic pattern confirmed: `tempfile.TemporaryDirectory()` + `Path(tmpdir)` for drive_root, with `git init` + minimal seeding. The Phase 3 subtests use this for the worktree, NOT for drive_root (they need an actual git repo with commits)
- SKIP-then-flip: return `"skip"` from a function to register it as skipped. The `main()` loop does not exit with code 1 for skips

**`supervisor/workers.py`:**
- Has `BRANCH_DEV = "heretek"` and `BRANCH_STABLE = "heretek-stable"` as module globals (lines 40-41), and `init()` signature at line 64 with same defaults. These are a THIRD place (alongside `git_ops.py` and `agent.py:Env`) where branch defaults need updating

**`.gitignore` (verified):**
- Currently gitignores: `.env`, `.env.local`, `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `logs/`, `*.log`, `venv/`, `*.pyo`, `*.jsonl`, `node_modules/`, `memory/`
- `.heretek/` is NOT yet gitignored. Must be added in Phase 3

### New Findings (not in CONTEXT.md)

1. **Full boot loop is missing.** `supervisor/__main__.py` explicitly stubs the Telegram loop as "not yet wired" (returns exit 2). There is NO existing TG message routing anywhere. Phase 3's TG dispatch for `/evolve`/`/sanction`/`/heresy` must either (a) be a stub that wires into Phase 4's yet-to-be-built polling loop, or (b) exist only on the CLI path. The CONTEXT.md's instruction "slot into the existing message-routing seam" overstates what exists — there is a seam for the TG *client*, but not for message *routing*.

2. **Branch default exists in THREE places:** `git_ops.py:33-34`, `workers.py:40-41`, `agent.py:Env.branch_dev=52`. All three need updating. CONTEXT.md only mentions `git_ops.py` defaults for the rename.

3. **`Env.branch_dev` default is `"heretek"` (line 52, agent.py).** This is what `_check_uncommitted_changes()` uses for the auto-rescue push. It also propagates into `ToolContext.branch_dev`. Phase 3 must update this default too or SAFE-02 has a leak.

4. **Cross-package import concern.** `heretek/tools/git.py` and `heretek/agent.py` importing `supervisor.git_ops` goes against the existing dependency direction (supervisor imports heretek, not vice versa). Current imports in `heretek/` do not touch `supervisor/`. Solution options: (a) accept the cross-import since it's a thin utility function call, (b) pass `safe_push` as a callable via `ToolContext`, (c) move `safe_push()` to a shared `heretek/utils.py`-accessible location. Recommendation: option (a) is simplest — `safe_push()` has no circular import risk since it only imports from stdlib and `supervisor.state`.

5. **`_handle_promote_to_stable()` in events.py uses `ctx.BRANCH_DEV` and `ctx.BRANCH_STABLE`** (context object attributes, not module globals). After the rename, `ctx.BRANCH_STABLE` will be `last-known-good`, making this handler always fail. The handler must be reworked in Phase 3 to refuse with a clear message.

6. **`_find_duplicate_task()` in events.py:264 reads `OUROBOROS_MODEL_LIGHT`** — opportunistic fix candidate since Phase 3 touches events.py.

7. **`checkout_and_reset()` does `git reset --hard origin/<branch>`** — it fetches from origin then resets to the remote branch. For `/heresy` which targets a local tag (not a remote branch), this exact call won't work as-is. The tag `last-known-good` may or may not have a remote tracking ref. `/heresy`'s implementation may need `git checkout last-known-good` + `git reset --hard last-known-good` instead of `origin/last-known-good`. This is a meaningful implementation detail.

8. **`_create_rescue_snapshot()` saves to `DRIVE_ROOT / "archive" / "rescue" /`** — this works on macOS as long as `DRIVE_ROOT` is set to a real local path (e.g. `./data/` or `~/heretek-drive/`). Until the Phase 4 `.env` loader sets it properly, the rescue snapshot path may be wrong. `/heresy` should handle rescue snapshot failure gracefully.

9. **`_OUROBOROS_PRE_PUSH_TESTS` env var in `heretek/tools/git.py:65`** — another residual `OUROBOROS_*` ref that's in Phase 3's touch surface.

---

## Implementation Seams

### `supervisor/git_ops.py` — Adding `safe_push()`

**Integration point:**
```python
# New module-level global (add after BRANCH_STABLE line 34):
PROTECTED_BRANCHES: frozenset = frozenset({"main", "last-known-good"})

# In init() (line 37), add:
def init(repo_dir, drive_root, remote_url, branch_dev="playground",
         branch_stable="last-known-good") -> None:
    global REPO_DIR, DRIVE_ROOT, REMOTE_URL, BRANCH_DEV, BRANCH_STABLE, PROTECTED_BRANCHES
    # ... existing assignments ...
    raw = os.environ.get("HERETEK_PROTECTED_BRANCHES", "").strip()
    if raw:
        PROTECTED_BRANCHES = frozenset(b.strip() for b in raw.split(",") if b.strip())
    else:
        PROTECTED_BRANCHES = frozenset({"main", "last-known-good"})
```

**`safe_push()` function slot:** Add after `_create_rescue_snapshot()` (line ~201), before `checkout_and_reset()` (line 208):
```python
def safe_push(branch: str, refspec: Optional[str] = None) -> None:
    if branch in PROTECTED_BRANCHES:
        # Log to supervisor.jsonl then raise
        append_jsonl(DRIVE_ROOT / "logs" / "supervisor.jsonl", {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type": "safe_push_refused",
            "target_branch": branch,
            "protected_branches": sorted(PROTECTED_BRANCHES),
        })
        raise ProtectedBranchError(f"Push to protected branch '{branch}' refused")
    # Existing push logic: pull --rebase, then push
    ...
```

**Exception class:** Defined in `git_ops.py` itself:
```python
class ProtectedBranchError(RuntimeError):
    """Raised when safe_push() is called with a protected branch target."""
```

**Caller conventions:** All three existing push sites use different error-reporting styles:
- `heretek/tools/git.py:_git_push_with_tests()` returns `Optional[str]` (None=ok, str=error). Callers check the return value. `safe_push()` can raise; the caller wraps it: `except ProtectedBranchError as e: return f"⚠️ PROTECTED_BRANCH: {e}"`
- `supervisor/events.py:_handle_promote_to_stable()` uses try/except and sends a message to owner_chat_id on error. `ProtectedBranchError` fits naturally in the existing except clause
- `heretek/agent.py:_check_uncommitted_changes()` uses `subprocess.CalledProcessError` and logs a warning. Wrap with `except (subprocess.CalledProcessError, ProtectedBranchError) as e:`

### `heretek/tools/git.py` — Refactoring Push Site 1

**Line 115** is the exact push line:
```python
run_cmd(["git", "push", "origin", ctx.branch_dev], cwd=ctx.repo_dir)
```
Replace with:
```python
from supervisor.git_ops import safe_push, ProtectedBranchError
try:
    safe_push(ctx.branch_dev)
except ProtectedBranchError as e:
    return f"⚠️ PROTECTED_BRANCH: {e}"
```
The `pull --rebase` at line 109 stays unchanged (it's not a push). The pre-push test gate stays unchanged.

### `supervisor/events.py` — Refactoring Push Site 2

`_handle_promote_to_stable()` at line 202. The rework for Phase 3:
```python
def _handle_promote_to_stable(evt: Dict[str, Any], ctx: Any) -> None:
    st = ctx.load_state()
    msg = (
        "promote_to_stable is superseded by /sanction in Phase 3. "
        "Use /sanction <hash> to advance last-known-good."
    )
    if st.get("owner_chat_id"):
        ctx.send_with_budget(int(st["owner_chat_id"]), f"⚠️ {msg}")
    log.warning("promote_to_stable event received but superseded by /sanction: %s", msg)
```
This makes the event a no-op with a helpful message, without requiring immediate deletion of the `promote_to_stable` LLM tool.

### `heretek/agent.py` — Refactoring Push Site 3

Lines 170-175 (the raw subprocess push in `_check_uncommitted_changes()`):
```python
# Current:
subprocess.run(["git", "push", "origin", self.env.branch_dev], ...)

# Replace with:
from supervisor.git_ops import safe_push, ProtectedBranchError
try:
    safe_push(self.env.branch_dev)
    auto_committed = True
except (subprocess.CalledProcessError, ProtectedBranchError) as e:
    subprocess.run(["git", "reset", "HEAD~1"], ...)
    raise
```
The auto-rescue flow with a misconfigured `branch_dev` pointing at a protected branch now fails loud and fast instead of silently pushing to the wrong branch.

### `supervisor/telegram.py` — Slash-Command Dispatch Seam

Since no message-routing loop exists in Phase 3, the TG dispatch hook is a module-level function stub:
```python
# In supervisor/telegram.py, add:
def handle_slash_command(text: str, chat_id: int, user_id: int) -> Optional[str]:
    """Route owner slash-commands to supervisor/commands.py handlers.
    Called by the Telegram polling loop (Phase 4) when a message starts with '/'.
    Returns response text, or None if not a recognized command.
    """
    from supervisor.commands import cmd_evolve, cmd_sanction, cmd_heresy
    if text.strip() == "/evolve":
        return cmd_evolve()
    m = re.match(r'^/sanction\s+(\S+)$', text.strip())
    if m:
        return cmd_sanction(m.group(1))
    if text.strip() == "/heresy":
        return cmd_heresy()
    return None
```
This function exists in Phase 3 but is only called by Phase 4's polling loop. Its presence lets Phase 3 tests import and call the underlying handlers directly.

### `supervisor/commands.py` — New File (the Core of Phase 3)

```python
"""Heretek owner commands: evolve, sanction, heresy.

Handler functions are the canonical implementation — called by both:
  - supervisor/telegram.py (Phase 4 TG dispatch)
  - __main__ block (offline test + CLI)
"""
import argparse
import os
import sys
...
def cmd_evolve(test_diff_path: Optional[str] = None) -> str: ...
def cmd_sanction(dryrun_id: str) -> str: ...
def cmd_heresy() -> str: ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("evolve").add_argument("--test-diff", dest="test_diff")
    sub.add_parser("sanction").add_argument("hash")
    sub.add_parser("heresy")
    ...
```

### `scripts/smoke_test.py` — Phase 3 Subtest Registration

New subtests added to `FULL_SUBTESTS` (not `STATIC_SUBTESTS` — they need subprocess + git):
```python
STATIC_SUBTESTS = [...]  # unchanged from Phase 2

SAFE_SUBTESTS = [
    test_safe_push_refuses_main,           # SAFE-01
    test_safe_push_refuses_last_known_good, # SAFE-01
    test_evolve_writes_dryrun_not_commit,   # SAFE-02, SAFE-03
    test_sanction_commits_to_playground,    # SAFE-04
    test_heresy_rolls_back_to_tag,          # SAFE-05
    test_sanction_advances_last_known_good_tag, # SAFE-06
]

FULL_SUBTESTS = STATIC_SUBTESTS + [
    check_models_pulled,
    test_bilingual_through_full_pipeline,
    test_persona_in_character,
    test_restart_recall_grudge,
] + SAFE_SUBTESTS
```
`test_safe_push_refuses_main` and `test_safe_push_refuses_last_known_good` are static (call `git_ops.safe_push()` directly, no subprocess). They can go in `STATIC_SUBTESTS`.

---

## Resolved Open Questions

### Staging Mechanism: Worktree vs Plain Dir + `git diff --no-index`

**Recommendation: plain directory + `git diff --no-index`.**

Git worktrees are cleaner semantically but add meaningful overhead:
- `git worktree add .heretek/staging` requires the worktree branch to be checked out elsewhere or a detached HEAD
- Worktree setup/teardown is stateful — a crashed `/evolve` can leave a stale worktree that blocks future `git worktree add`
- `git worktree list` is global to the repo — visible if the owner runs it, potentially confusing
- Worktree cleanup requires `git worktree remove --force` on teardown

Plain directory approach:
- `/evolve` copies the files it wants to change into `.heretek/staging/` (one subdirectory per file, mirroring repo structure)
- `git diff --no-index <current-repo-file> <staging-file>` produces a standard unified diff
- No git state to clean up — just delete the directory
- Simpler failure mode: if staging dir already exists, either overwrite or refuse (single-active-proposal policy)

For an M1 Max local repo with no remotes in the critical path, worktree overhead is not a performance concern. The failure-mode simplicity of plain dirs wins.

### Exception Class Name

**Recommendation: `ProtectedBranchError`** — clear, not gimmicky, standard Python naming convention. The heretek-flavored names (`HereticPushBlocked`) would be in log messages but exception class names should be findable by future-Claude doing a `grep`. `ProtectedBranchError(RuntimeError)` is the right base class since it's a programming-model error (caller tried to push to the wrong branch), not an OS error.

### `/sanction` Argument Validation

**Recommendation:**
1. Hash mismatch (no matching `.heretek/dryruns/<id>.json`): return friendly error listing all pending IDs from `.heretek/dryruns/`
2. Hand-edit detection: compute SHA256 of the `.patch` file content on `/evolve` and store in the sidecar JSON. On `/sanction`, recompute and compare. If mismatch: refuse with "patch file has been modified since /evolve produced it — re-run /evolve to generate a fresh proposal"
3. No pending dryruns at all: clear error message

### `/evolve` Concurrency

**Recommendation: refuse with message.** Check for a `.heretek/dryruns/*.json` with `status: "pending"` before starting a new `/evolve`. If one exists: return "proposal already pending — use /sanction <id> to commit or delete `.heretek/dryruns/<id>.patch` to discard".

Single-active-proposal policy simplifies the `/sanction` UX: the owner always knows which hash to sanction without needing to list.

### `/heresy` Semantics

**Recommendation: `checkout_and_reset()` cannot be used as-is.** Reason: `checkout_and_reset()` does `git reset --hard origin/<branch>`, which requires the branch to have a remote tracking ref. `last-known-good` is an annotated tag, not a remote branch. The correct sequence for `/heresy`:
```bash
git stash  # or rescue snapshot
git checkout last-known-good  # detaches HEAD at tag
```
Or more cleanly:
```bash
git fetch --tags origin  # ensure tag is current remotely
git checkout last-known-good  # checkout tag (detached HEAD)
```
**Important consequence:** After `/heresy`, HEAD is detached at the tag commit. The bot is NOT on a branch. Future commits from the bot loop would create a detached-HEAD commit chain. `/heresy` should either (a) also checkout `playground` after the tag reset — `git checkout playground && git reset --hard last-known-good` — so HEAD stays on the playground branch, or (b) document that after `/heresy` the owner must manually re-checkout playground. Option (a) is the right default.

**Memory files survive by default** (`memory/identity.md`, `memory/scratchpad.md` are gitignored). No `--nuke-memory` flag needed in Phase 3.

**Rescue policy:** Use `_create_rescue_snapshot()` before the reset, similar to `rescue_and_reset` policy. But this function depends on `DRIVE_ROOT` being set to a real local path. Phase 3 should default `DRIVE_ROOT` to `./data/` or `Path.home() / ".heretek"` if not set — or simply skip the rescue if `DRIVE_ROOT` is the Colab default.

### Tag Push to Origin After `/sanction`

**Recommendation: yes, push the tag.** The tag is the rollback target. If the laptop is lost or the repo is cloned fresh, a local-only tag is gone. Add `git push origin last-known-good --tags --force-with-lease` as a best-effort step after the tag-move in `/sanction`. If the push fails (no remote configured, offline), log the failure but do NOT fail the whole `/sanction` — the commit and local tag are already in place.

### `promote_to_stable` LLM-Tool Fate

**Recommendation: make the event handler a no-op with a message** (as documented in Implementation Seams above). The tool registration stays, the event is in the dispatch table, but the handler now returns a deprecation message. Full deletion is Phase 4+ cleanup. Update the tool description string in `control.py:218` from "Promote heretek -> heretek-stable" to "Superseded by /sanction in Phase 3; use /sanction <hash> to advance last-known-good."

### `agent.py` Auto-Rescue Interaction with safe_push()

The auto-rescue path (`_check_uncommitted_changes()`) is a startup safety net that fires when the agent boots with dirty tracked files. With `safe_push()` in place:
- If `env.branch_dev = "playground"` (after Phase 3 renames), auto-rescue correctly pushes to playground
- If someone misconfigures `HERETEK_PLAYGROUND_BRANCH` to `main`, auto-rescue now refuses loudly instead of silently corrupting main
- The dry-run model doesn't conflict with auto-rescue: auto-rescue commits to playground directly (no dry-run gate) because it's not a *proposed* change — it's recovering state that was already committed locally

The `/evolve` → dry-run path is only triggered by the explicit `/evolve` owner command, not by auto-rescue.

### Dry-Run Retention Policy

**Recommendation: one active proposal at a time.** Archive logic:
- On new `/evolve`: check for existing `pending` dryruns; refuse if found
- On `/sanction` or explicit `/discard` (future): move `<id>.patch` and `<id>.json` to `.heretek/dryruns/archive/`
- On `/heresy`: do NOT auto-archive — let the pending proposal survive (the tree was reset, but the patch file is separate)
- Retention of archive: no limit in Phase 3 (disk cost is negligible for text patches)

---

## Plan Decomposition Recommendation

**3 plans, sequential (each plan depends on prior being merged):**

### Plan 03-01: Branch Protection + `safe_push()` (Wave 1)
**Goal:** SAFE-01 verified; all three push sites unified.
- Add `ProtectedBranchError` class to `git_ops.py`
- Add `PROTECTED_BRANCHES` module global, populate in `init()`
- Implement `safe_push()` in `git_ops.py`
- Rename `BRANCH_DEV`/`BRANCH_STABLE` defaults in `git_ops.py`, `workers.py`, `agent.py:Env`
- Refactor `heretek/tools/git.py:115` to call `safe_push()`
- Rework `supervisor/events.py:_handle_promote_to_stable()` to refuse with message
- Refactor `heretek/agent.py:170-175` to call `safe_push()`
- Update tool description in `control.py:218`
- Flip `test_safe_push_refuses_main` and `test_safe_push_refuses_last_known_good` from SKIP to PASS
- Ship other SAFE-02..06 subtests as SKIPs

**Verification:** `python scripts/smoke_test.py --static-only` green (9 existing + 2 new PASS, 4 SKIP)

### Plan 03-02: `supervisor/commands.py` + CLI Shim + TG Stub (Wave 2)
**Goal:** SAFE-02 partially verified; commands are callable from CLI.
- Create `supervisor/commands.py` with `cmd_evolve()`, `cmd_sanction()`, `cmd_heresy()` stubs that return placeholder strings
- Add `__main__` argparse block
- Add `handle_slash_command()` stub to `supervisor/telegram.py`
- Add `.heretek/` to `.gitignore`
- Implement `cmd_heresy()` fully (uses `git checkout last-known-good && git reset --hard last-known-good`, with rescue snapshot)
- Ship SAFE-05 subtest (test_heresy_rolls_back_to_tag) as live assertion

**Verification:** `python -m supervisor.commands heresy` runs in a test tempdir without error; SAFE-05 subtest PASS

### Plan 03-03: Dry-Run Pipeline + Full Subtest Coverage (Wave 3)
**Goal:** SAFE-02, SAFE-03, SAFE-04, SAFE-06 all verified.
- Implement `/evolve` dry-run mechanic: staging dir creation, `git diff --no-index`, patch file + sidecar JSON with synthetic ID and SHA256 checksum
- Implement `cmd_evolve(test_diff_path=None)` fully with `HERETEK_EVOLVE_TEST_DIFF` env seam
- Implement `cmd_sanction(dryrun_id)` fully: apply patch, commit to playground, move `last-known-good` tag, optional tag push to origin
- Create `scripts/fixtures/heresy_test.patch` (a minimal patch — append a heretical comment to BIBLE.md)
- Flip SAFE-02, SAFE-03, SAFE-04, SAFE-06 subtests from SKIP to live assertions

**Verification:** Full smoke suite green (9 existing + 6 new PASS); `python -m supervisor.commands evolve --test-diff scripts/fixtures/heresy_test.patch` produces a dry-run ID; `python -m supervisor.commands sanction <id>` commits to playground

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `scripts/smoke_test.py` (custom, established in Phase 1) |
| Config file | None — self-contained script |
| Quick run command | `python scripts/smoke_test.py --static-only` |
| Full suite command | `python scripts/smoke_test.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SAFE-01 | `safe_push("main")` raises ProtectedBranchError | unit (direct import) | `python scripts/smoke_test.py --static-only` | ❌ Wave 1 (Plan 03-01) |
| SAFE-01 | `safe_push("last-known-good")` raises ProtectedBranchError | unit (direct import) | `python scripts/smoke_test.py --static-only` | ❌ Wave 1 (Plan 03-01) |
| SAFE-02 | playground HEAD SHA unchanged after `/evolve` | integration (subprocess) | `python scripts/smoke_test.py` | ❌ Wave 3 (Plan 03-03) |
| SAFE-03 | `.heretek/dryruns/<id>.patch` exists; no commit | integration (subprocess) | `python scripts/smoke_test.py` | ❌ Wave 3 (Plan 03-03) |
| SAFE-04 | New commit on `git log playground -1` after `/sanction` | integration (subprocess) | `python scripts/smoke_test.py` | ❌ Wave 3 (Plan 03-03) |
| SAFE-05 | `git status --porcelain` empty after `/heresy` | integration (subprocess) | `python scripts/smoke_test.py` | ❌ Wave 2 (Plan 03-02) |
| SAFE-06 | `last-known-good` tag SHA == new playground HEAD after `/sanction` | integration (subprocess) | `python scripts/smoke_test.py` | ❌ Wave 3 (Plan 03-03) |

### Sampling Rate
- **Per task commit:** `python scripts/smoke_test.py --static-only`
- **Per wave merge:** `python scripts/smoke_test.py` (full suite; needs `git init` hermetic repo for SAFE subtests, does NOT need Ollama)
- **Phase gate:** Full suite green (9 existing + 6 new PASS) before `/gsd:verify-work 3`

### Hermetic Test Repo Pattern for SAFE Subtests

SAFE subtests need a real git repo with commits and tags, not just a tempdir. Pattern:
```python
import tempfile, subprocess
with tempfile.TemporaryDirectory() as tmpdir:
    repo = Path(tmpdir)
    subprocess.run(["git", "init", str(repo)], check=True)
    subprocess.run(["git", "config", "user.email", "test@heretek"], cwd=tmpdir, check=True)
    subprocess.run(["git", "config", "user.name", "Heretek Test"], cwd=tmpdir, check=True)
    # Seed: create initial commit
    (repo / "BIBLE.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True)
    # Tag as last-known-good
    subprocess.run(["git", "tag", "-a", "last-known-good", "-m", "baseline"], cwd=tmpdir, check=True)
    # Create playground branch
    subprocess.run(["git", "checkout", "-b", "playground"], cwd=tmpdir, check=True)
    # Now test commands against this repo
    ...
```
This is distinct from the Phase 1-2 `tempfile.TemporaryDirectory()` pattern which used tmpdir only as `drive_root` — SAFE subtests use tmpdir as the actual `repo_dir`.

### Wave 0 Gaps (to ship as SKIP-stubs in Plan 03-01)
- [ ] `test_safe_push_refuses_main` — covers SAFE-01 (flip to PASS in Plan 03-01)
- [ ] `test_safe_push_refuses_last_known_good` — covers SAFE-01 (flip to PASS in Plan 03-01)
- [ ] `test_evolve_writes_dryrun_not_commit` — covers SAFE-02, SAFE-03 (flip in Plan 03-03)
- [ ] `test_sanction_commits_to_playground` — covers SAFE-04 (flip in Plan 03-03)
- [ ] `test_heresy_rolls_back_to_tag` — covers SAFE-05 (flip in Plan 03-02)
- [ ] `test_sanction_advances_last_known_good_tag` — covers SAFE-06 (flip in Plan 03-03)
- [ ] `scripts/fixtures/heresy_test.patch` — test fixture file (create in Plan 03-03)

---

## Pitfalls and Gotchas

### Pitfall 1: `/heresy` Leaves Detached HEAD
**What goes wrong:** `git checkout last-known-good` detaches HEAD from any branch. Subsequent bot commits would land on a detached-HEAD chain, invisible to `git log playground` and not pushed by `safe_push(BRANCH_DEV)`.
**Prevention:** After the tag checkout, immediately checkout playground and reset: `git checkout playground && git reset --hard last-known-good`. This puts playground at the same commit as the tag with HEAD on the branch.
**Warning signs:** `git branch` shows `* (HEAD detached at last-known-good)` after `/heresy`.

### Pitfall 2: `_create_rescue_snapshot()` Uses Stale DRIVE_ROOT
**What goes wrong:** If `git_ops.init()` hasn't been called with a real local path, `DRIVE_ROOT` is `/content/drive/MyDrive/Ouroboros`. The rescue snapshot is written there, which doesn't exist on macOS. The `mkdir(parents=True, exist_ok=True)` call will fail.
**Prevention:** `/heresy` should call rescue snapshot inside a try/except and log failure without aborting the heresy operation. The rollback must succeed even if rescue fails.
**Warning signs:** `/heresy` raising `FileNotFoundError` or `OSError` on the archive write.

### Pitfall 3: Cross-Package Import `heretek` → `supervisor`
**What goes wrong:** `heretek/tools/git.py` and `heretek/agent.py` importing `supervisor.git_ops` could break if supervisor imports heretek at module init time (circular import). 
**Current state:** `supervisor/workers.py` does `from supervisor import git_ops` and starts worker processes that import `heretek`. On macOS the worker start method is `spawn` (not `fork` like Linux). Each spawned worker re-imports all modules. If `heretek/tools/git.py` is imported at module level and it imports `supervisor.git_ops`, and `supervisor/__main__.py` imports `supervisor.workers` which doesn't directly import `heretek`... the import chain is safe. But it's worth verifying in a `--static-only` run that the import succeeds.
**Prevention:** Keep the `from supervisor.git_ops import safe_push` inside the function body (local import), not at module level, until the circular import risk is assessed.

### Pitfall 4: Stale `.heretek/staging/` From Prior `/evolve`
**What goes wrong:** If `/evolve` crashes mid-run, `.heretek/staging/` may exist with partial state. Next `/evolve` finds it and either fails or uses stale data.
**Prevention:** At the start of every `/evolve`, delete `.heretek/staging/` and recreate it fresh. Treat it as ephemeral temp space, not durable state. The durable state is in `.heretek/dryruns/<id>.patch`.

### Pitfall 5: `git diff --no-index` Exit Code 1 on Differences
**What goes wrong:** `git diff --no-index <file-a> <file-b>` exits with code 1 when there ARE differences (standard `diff` convention). `subprocess.run(..., check=True)` will raise `CalledProcessError` on exit code 1, confusing a "diff found" with an error.
**Prevention:** Use `subprocess.run(..., check=False)` and check `returncode in (0, 1)` explicitly. Exit code 0 = no diff (files identical — invalid proposal), exit code 1 = diff found (expected), exit code 2+ = error.

### Pitfall 6: Annotated Tag vs Lightweight Tag in `/sanction`
**What goes wrong:** `git tag -f last-known-good <sha>` creates a lightweight tag. CONTEXT.md specifies annotated (`git tag -f -a last-known-good -m "sanctioned: ..." <sha>`). Annotated tags have their own SHA and store the tagger/timestamp. If `/sanction` uses the wrong form, `test_sanction_advances_last_known_good_tag` checking `git rev-parse last-known-good` may return the tag object SHA, not the commit SHA. Use `git rev-parse last-known-good^{}` (with dereference) to get the commit SHA from an annotated tag.
**Prevention:** Always use `git rev-parse last-known-good^{}` in the smoke test assertion. The handler uses `git tag -f -a` with a `-m` message.

### Pitfall 7: SAFE-01 Subtests Are Static but Need `git_ops.init()` Called
**What goes wrong:** `safe_push()` reads from module-level `PROTECTED_BRANCHES`. If `git_ops.init()` hasn't been called, `PROTECTED_BRANCHES` has the hardcoded default `{"main", "last-known-good"}` — which is actually fine for the test. But `REPO_DIR` would still be `/content/heretek_repo`. If `safe_push()` calls any git command before the refusal check, it will fail with a subprocess error on the wrong path.
**Prevention:** The refusal check MUST happen before any `git_capture()` call in `safe_push()`. This is the right design anyway — check the branch name first, raise immediately, never touch git.

### Pitfall 8: `/sanction` Applying a Patch That Breaks the Import
**What goes wrong:** `/sanction` applies a patch and commits it to playground. If the patch breaks `import heretek`, the next agent startup (which calls `_log_worker_boot_once()` → `_check_uncommitted_changes()`) would fail.
**Prevention:** `/sanction` should run `python -c "import heretek"` as a post-apply import test before committing. If import fails, refuse the sanction with an error and offer `/heresy` as the recovery. This is analogous to `import_test()` in `git_ops.py` which already exists.

---

## Risk Surface

### Risk 1: `safe_push()` Bug Prevents All Commits
**Scenario:** A bug in `safe_push()` (e.g., always raises even for allowed branches) means the bot can't commit anything. Self-modification is broken.
**Blast radius:** Complete loss of bot self-modify capability. The bot still responds (it doesn't need to push to chat), but it can't persist code changes.
**Recovery:** `git_ops.py` is a supervisory module; the owner can edit it directly and restart. The smoke test for SAFE-01 would catch a "always refuses" bug if run after implementation. The hermetic test pattern means the test can't be fooled by the live repo state.

### Risk 2: `/sanction` Applies a Breaking Patch
**Scenario:** The patch from `/evolve` introduces a syntax error or import failure. After `/sanction` commits it, the next agent restart fails to boot.
**Recovery story:**
1. Owner runs `/heresy` — rolls back to `last-known-good` tag (the commit BEFORE the bad sanction, since the tag advances AFTER sanction)
2. Wait — if tag advances on sanction, and the bad patch is sanctioned, then `last-known-good` now points AT the bad commit. `/heresy` would roll back to the bad commit.
3. **This is the real risk.** Mitigation: the import test in `safe_push()` / `/sanction` catches syntax errors. But if the import test passes and the runtime error only manifests during execution, `/heresy` won't help.
4. True recovery: `git checkout playground && git reset --hard HEAD~1` manually. The owner knows git well enough (senior tech lead).
5. Design note: the import test before tagging is load-bearing here. The tag should move ONLY after the import test passes.

### Risk 3: Smoke Tests Fail Mid-Development
**Scenario:** Plan 03-01 is halfway done — `safe_push()` exists but the refactor of `heretek/tools/git.py` is incomplete. `test_no_cloud_hosts` might start failing if a new import in `git_ops.py` accidentally introduces a cloud reference.
**Recovery:** The SKIP-then-flip pattern means incomplete plans ship Phase 3 SKIPs, not FAILs. The 9 existing PASSes must remain green throughout. Standard discipline: run `--static-only` after every task commit.

### Risk 4: Worktree / Staging Dir Collision With Real Repo State
**Scenario:** Using `git diff --no-index` between `.heretek/staging/` files and live repo files is safe — it's a pure read. But if the `/evolve` agent accidentally writes to the live tree instead of `.heretek/staging/`, the next `/sanction` would see a clean diff and commit nothing meaningful.
**Prevention:** The test fixture path (`HERETEK_EVOLVE_TEST_DIFF`) explicitly writes a known patch to staging — the test can verify that the live tree was NOT modified by checking `git status --porcelain` after `/evolve`.

---

## References

| File | Line(s) | Finding |
|------|---------|---------|
| `supervisor/git_ops.py` | 33-34 | `BRANCH_DEV = "heretek"`, `BRANCH_STABLE = "heretek-stable"` — rename targets |
| `supervisor/git_ops.py` | 37-44 | `init()` signature — where to add `PROTECTED_BRANCHES` env-read |
| `supervisor/git_ops.py` | 51-53 | `git_capture()` — the subprocess wrapper `safe_push()` uses |
| `supervisor/git_ops.py` | 73-111 | `_collect_repo_sync_state()` — audit log enrichment for refusals |
| `supervisor/git_ops.py` | 161-201 | `_create_rescue_snapshot()` — reusable for `/heresy`, DRIVE_ROOT dependency |
| `supervisor/git_ops.py` | 208-299 | `checkout_and_reset()` — existing destructive primitive; does `origin/<branch>` reset, NOT usable directly for tag-based `/heresy` |
| `supervisor/git_ops.py` | 352-414 | `safe_restart()` — distinct from `/heresy`; dev-branch import-test-gated restart |
| `supervisor/telegram.py` | 1-477 | No message dispatch loop. TG client + formatting only. |
| `supervisor/telegram.py` | 30-36 | `init()` signature |
| `supervisor/__main__.py` | 90-103 | Full boot "not yet wired" — confirms no TG polling loop exists |
| `supervisor/workers.py` | 40-41 | `BRANCH_DEV = "heretek"`, `BRANCH_STABLE = "heretek-stable"` — second rename location |
| `supervisor/workers.py` | 64-76 | `workers.init()` signature with same branch defaults |
| `supervisor/events.py` | 202-226 | `_handle_promote_to_stable()` — push site 2; targets `BRANCH_STABLE` (will be `last-known-good`) |
| `supervisor/events.py` | 264 | `OUROBOROS_MODEL_LIGHT` ref — opportunistic fix |
| `heretek/tools/git.py` | 100-119 | `_git_push_with_tests()` — push site 1; push at line 115 |
| `heretek/tools/git.py` | 65 | `OUROBOROS_PRE_PUSH_TESTS` env var — opportunistic fix |
| `heretek/agent.py` | 50-58 | `Env` dataclass — `branch_dev: str = "heretek"` default at line 52 |
| `heretek/agent.py` | 140-193 | `_check_uncommitted_changes()` — push site 3; push at lines 170-175 |
| `heretek/tools/control.py` | 40-42 | `_promote_to_stable()` — emits promote event |
| `heretek/tools/control.py` | 140-148 | `_toggle_evolution()` — LLM-tool side; distinct from `/evolve` command |
| `heretek/tools/control.py` | 216-219 | `promote_to_stable` tool description — stale text to update |
| `heretek/tools/control.py` | 20-37 | `_request_restart()` — `last_push_succeeded` guard relevant post-sanction |
| `scripts/smoke_test.py` | 746-758 | `STATIC_SUBTESTS` / `FULL_SUBTESTS` registration lists |
| `scripts/smoke_test.py` | 761-785 | `main()` — how subtests are run, exit code convention |
| `.gitignore` | end | `memory/` is gitignored; `.heretek/` is NOT yet added |

---

## RESEARCH COMPLETE
