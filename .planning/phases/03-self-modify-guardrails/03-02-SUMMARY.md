---
phase: 03-self-modify-guardrails
plan: 02
subsystem: infra
tags: [git, heresy, rollback, commands, telegram, smoke-test, argparse, self-modification]

# Dependency graph
requires:
  - phase: 03-self-modify-guardrails
    plan: 01
    provides: safe_push() chokepoint; _make_test_repo hermetic fixture; SAFE-* SKIP-stub scaffold; .heretek/ gitignored
provides:
  - cmd_heresy() fully implemented in supervisor/commands.py — git checkout playground + git reset --hard last-known-good^{commit}
  - cmd_evolve() / cmd_sanction() stubs in supervisor/commands.py (Plan 03-03 fills them)
  - Argparse CLI shim: python -m supervisor.commands {evolve|sanction <id>|heresy} [--repo-dir <path>]
  - handle_slash_command(text, chat_id, user_id) -> Optional[str] in supervisor/telegram.py (Phase 4 polling loop will call it)
  - SAFE-05 automated: test_heresy_rolls_back_to_tag live PASS via subprocess hermetic test
  - Static smoke gate: 8 pass / 0 fail / 3 skip / 11 total
affects: [03-03-PLAN, Phase 4 launch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-front-door pattern: same handler function callable via argparse CLI + future TG dispatch"
    - "Per-subcommand --repo-dir flag: placed on each subparser (not parent) so <subcommand> --repo-dir <path> works"
    - "Lazy import of supervisor.commands inside handle_slash_command body (avoids bootstrap-order coupling)"
    - "Best-effort rescue snapshot: try/except wraps _create_rescue_snapshot; rollback proceeds even on failure"
    - "Pitfall 1 mitigation: git checkout <branch> before git reset --hard (no detached HEAD)"
    - "Pitfall 6 mitigation: last-known-good^{commit} dereference mandatory for annotated tags in rev-parse"

key-files:
  created:
    - supervisor/commands.py
  modified:
    - supervisor/telegram.py
    - scripts/smoke_test.py

key-decisions:
  - "--repo-dir flag placed on each subcommand parser, not the parent parser — argparse does not pass parent flags to subcommands when they appear AFTER the subcommand token; smoke test calls 'heresy --repo-dir <path>' so the flag must live on p_heresy"
  - "cmd_heresy() uses _collect_repo_sync_state() before calling _create_rescue_snapshot() — the actual git_ops signature is (branch, reason, repo_state: Dict) not a simple (reason=) keyword call"
  - "handle_slash_command() uses a lazy local import of supervisor.commands to avoid circular-import risk at telegram.py module-load time"
  - "DRIVE_ROOT Colab-default check ('/content/drive' prefix) skips rescue snapshot on macOS — Pitfall 2 mitigation; rollback always proceeds"

patterns-established:
  - "Dual-front-door: CLI shim + TG dispatcher share the same handler function — Plan 03-03 follows this for cmd_evolve/cmd_sanction"

requirements-completed:
  - SAFE-05

# Metrics
duration: 3min
completed: 2026-05-16
---

# Phase 3 Plan 02: Self-Modify Guardrails — /heresy Rollback Command Summary

**`/heresy` rollback via `cmd_heresy()` + argparse CLI shim + TG dispatch stub + SAFE-05 automated (8 pass / 0 fail / 3 skip)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-16T17:09:39Z
- **Completed:** 2026-05-16T17:13:37Z
- **Tasks:** 3
- **Files modified:** 2 (+ 1 created)

## Accomplishments

- `supervisor/commands.py` created with `cmd_heresy()` fully implemented (git checkout playground + git reset --hard last-known-good^{commit}), plus `cmd_evolve()` and `cmd_sanction()` stubs returning NOT_IMPLEMENTED messages
- Argparse CLI shim wired at the bottom of `commands.py`: `python -m supervisor.commands heresy --repo-dir <path>` is the hermetic test seam; `evolve` and `sanction` subcommands are also wired (stubs)
- `handle_slash_command(text, chat_id, user_id) -> Optional[str]` added to `supervisor/telegram.py` with lazy import of `supervisor.commands` — Phase 4 polling loop has a concrete callable to hook in
- `test_heresy_rolls_back_to_tag` flipped from SKIP to live PASS via subprocess hermetic integration test; asserts clean tree + HEAD == last-known-good^{commit} + HEAD on playground branch (Pitfalls 1 and 6 both checked)

## Task Commits

1. **Task 1: Create supervisor/commands.py** — `b691db3` (feat)
2. **Task 2: Add handle_slash_command() to supervisor/telegram.py** — `54d6d67` (feat)
3. **Task 3: Flip test_heresy_rolls_back_to_tag + fix argparse --repo-dir** — `bf405f5` (feat)

## Files Created/Modified

- `supervisor/commands.py` — New module: cmd_heresy() (full), cmd_evolve() / cmd_sanction() (stubs), argparse CLI shim with per-subcommand --repo-dir
- `supervisor/telegram.py` — Added handle_slash_command() at end of file; lazy import of supervisor.commands inside function body
- `scripts/smoke_test.py` — test_heresy_rolls_back_to_tag replaced from SKIP-stub to live subprocess integration test

## Decisions Made

- `--repo-dir` flag placed on each subcommand parser (not the parent) because argparse does not propagate parent-level flags that appear AFTER the subcommand token. The smoke test calls `python -m supervisor.commands heresy --repo-dir <path>` — the flag MUST be on `p_heresy`.
- `_create_rescue_snapshot()` in `supervisor/git_ops.py` takes `(branch, reason, repo_state: Dict)`, not a keyword-only `reason=` call as the plan's inline pseudocode suggested. `cmd_heresy()` calls `_collect_repo_sync_state()` first, then passes the result. Rescue is still best-effort inside try/except.
- `handle_slash_command()` uses a lazy local import (`from supervisor.commands import ...` inside the function body) to decouple telegram.py's module-load order from the new commands.py module.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] argparse `--repo-dir` placement: moved from parent parser to each subparser**
- **Found during:** Task 3 (test_heresy_rolls_back_to_tag live integration)
- **Issue:** Parent-level `--repo-dir` not propagated to subcommand namespace when the flag appears AFTER the subcommand token in argv. `python -m supervisor.commands heresy --repo-dir <path>` raised `unrecognized arguments: --repo-dir ...` (argparse exit 2).
- **Fix:** Removed parent-level `--repo-dir`; added `--repo-dir` to each of the three subparsers (evolve, sanction, heresy) individually.
- **Files modified:** `supervisor/commands.py`
- **Verification:** `python scripts/smoke_test.py --static-only` exits 0 with `8 pass · 0 fail · 3 skip · 11 total`
- **Committed in:** `bf405f5` (Task 3 commit)

**2. [Rule 1 - Bug] _create_rescue_snapshot() actual signature differs from plan pseudocode**
- **Found during:** Task 1 (reading supervisor/git_ops.py)
- **Issue:** Plan inline code called `_create_rescue_snapshot(reason="heresy_rollback")` (keyword-only). Actual signature is `_create_rescue_snapshot(branch: str, reason: str, repo_state: Dict[str, Any])` — requires a branch name and a pre-collected repo state dict.
- **Fix:** `cmd_heresy()` calls `git_ops._collect_repo_sync_state()` first, then passes `(branch=branch_name, reason="heresy_rollback", repo_state=repo_state)`.
- **Files modified:** `supervisor/commands.py`
- **Verification:** Module imports cleanly; cmd_heresy() runs on hermetic repo; rescue snapshot call is inside try/except (failure does not abort rollback)
- **Committed in:** `b691db3` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs: one argparse placement, one API signature mismatch)
**Impact on plan:** Both fixes necessary for correctness. No scope creep. The dual-front-door pattern and pitfall mitigations are all intact as designed.

## Issues Encountered

- Hermetic `_make_test_repo` helper works cleanly on the host's git version (`git init -b main` supported). Annotated tag creates without issue.
- `git fetch --tags origin` on hermetic repos (no remote) logs a warning but `check=False` means it does not abort. Normal flow.
- DRIVE_ROOT defaults to `/content/drive/MyDrive/Ouroboros` (Colab path) on this macOS host — the `startswith("/content/drive")` guard skips the rescue snapshot correctly. This is the same behavior observed in Plan 03-01.

## Pitfall Confirmations

**Pitfall 1 (detached HEAD) mitigated:**
- `cmd_heresy()` calls `git checkout playground` BEFORE `git reset --hard <tag_commit_sha>`
- `test_heresy_rolls_back_to_tag` asserts `git symbolic-ref --short HEAD == 'playground'` after rollback
- Confirmed: HEAD stays on playground branch, not detached

**Pitfall 6 (annotated tag dereference) mitigated:**
- `cmd_heresy()` uses `git rev-parse last-known-good^{commit}` to get the commit SHA
- `git reset --hard` then uses the pre-dereferenced commit SHA (not the tag object SHA)
- `test_heresy_rolls_back_to_tag` asserts `HEAD == git rev-parse last-known-good^{commit}` (same dereference)
- On the real repo: `git rev-parse last-known-good` → `59c3f4fe...` (tag object); `git rev-parse last-known-good^{commit}` → `8344285b...` (commit)

## Static Suite Output

```
Summary: 8 pass · 0 fail · 3 skip · 11 total
```

Breakdown:
- 5 PASS: existing Phase 1+2 static (test_package_rename, test_no_cloud_hosts, test_bible_forbidden_at_top, test_system_md_loaded, test_identity_seed_scaffold)
- 2 PASS: SAFE-01 from Plan 03-01 (test_safe_push_refuses_main, test_safe_push_refuses_last_known_good)
- 1 PASS: SAFE-05 newly flipped (test_heresy_rolls_back_to_tag)
- 3 SKIP: SAFE-02/03/04/06 awaiting Plan 03-03

## Plan 03-03 Readiness

- `cmd_evolve()` and `cmd_sanction()` stubs are in place; Plan 03-03 replaces the stub bodies with the dry-run pipeline + import-test gate + tag advance
- The CLI surface (`python -m supervisor.commands evolve --test-diff <fixture.patch>`, `sanction <id>`) is already wired in argparse — Plan 03-03 only adds the handler body
- `handle_slash_command()` in telegram.py dispatches all three commands — no changes needed there for Plan 03-03
- `test_evolve_writes_dryrun_not_commit`, `test_sanction_commits_to_playground`, `test_sanction_advances_last_known_good_tag` SKIP-stubs are ready to flip

---
*Phase: 03-self-modify-guardrails*
*Completed: 2026-05-16*
