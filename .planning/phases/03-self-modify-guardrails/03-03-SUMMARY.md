---
phase: 03-self-modify-guardrails
plan: 03
subsystem: infra
tags: [git, evolve, sanction, dry-run, import-test, self-modification, smoke-test, commands]

# Dependency graph
requires:
  - phase: 03-self-modify-guardrails
    plan: 01
    provides: safe_push() chokepoint; _make_test_repo hermetic fixture; SAFE-* SKIP-stub scaffold; .heretek/ gitignored
  - phase: 03-self-modify-guardrails
    plan: 02
    provides: cmd_evolve()/cmd_sanction() stubs; argparse CLI shim with --test-diff/--repo-dir; handle_slash_command() TG dispatch stub
provides:
  - cmd_evolve() fully implemented — writes .heretek/dryruns/<id>.patch + sidecar JSON; zero git calls; single-active-proposal policy
  - cmd_sanction() fully implemented — import-test gate BEFORE tag advance (Risk 2 + Pitfall 8); SHA256 tamper detection; best-effort archive
  - _run_import_test() helper — uses real project root PYTHONPATH; decoupled from hermetic test repos
  - scripts/fixtures/heresy_test.patch — deterministic unified-diff fixture for HERETEK_EVOLVE_TEST_DIFF injection
  - SAFE-02/03/04/06 automated: 3 SKIP-stubs flipped to live PASS
  - Phase 3 phase gate GREEN: 11 pass · 0 fail · 0 skip · 11 total
affects: [Phase 4 launch — full Telegram polling loop wires handle_slash_command()]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import-test-before-tag-advance invariant: _run_import_test() called BEFORE git tag -f -a in cmd_sanction() — Risk 2 + Pitfall 8 mitigation"
    - "SHA256 hand-edit detection: patch content hashed at /evolve time, recomputed at /sanction time; mismatch refuses"
    - "Synthetic dryrun ID: dr-<UTC>-<8hex> format (datetime + secrets.token_hex(4)); not a git SHA — nothing committed yet at /evolve time"
    - "_run_import_test() uses real project root PYTHONPATH (not hermetic repo) — import test always validates real heretek package"
    - "Best-effort archive step: patch+sidecar moved to .heretek/dryruns/archive/ post-sanction; failure logged but does not fail the sanction"

key-files:
  created:
    - scripts/fixtures/heresy_test.patch
  modified:
    - supervisor/commands.py
    - scripts/smoke_test.py

key-decisions:
  - "_run_import_test() is a standalone helper (not a call to supervisor.git_ops.import_test()) — git_ops.import_test() uses REPO_DIR which may point at a hermetic test repo (no heretek package); the helper uses pathlib.Path(__file__).resolve().parent.parent as project root so it always validates the real package"
  - "Import-test gate BEFORE tag advance — the tag must NEVER advance to a broken commit, or /heresy rolls back TO the broken commit (Risk 2). Structural enforcement: _run_import_test() call is at line N, git tag -f -a is at line N+15 in cmd_sanction()"
  - "cmd_evolve() has zero git subprocess calls — the cardinal rule 'no live-tree changes until /sanction' is structurally enforced, not just asserted"
  - "Single-active-proposal policy: cmd_evolve() refuses with EVOLVE_REFUSED if any sidecar with status='pending' exists in .heretek/dryruns/; corrupt sidecars silently skipped"
  - "Fixture patch applies to hermetic test repo BIBLE.md ('# baseline\\n') because _make_test_repo creates exactly that content and playground branch only adds PLAYGROUND.md — BIBLE.md is untouched at '# baseline\\n'"

patterns-established:
  - "Dry-run pipeline pattern: /evolve writes patch+sidecar (no git); /sanction reads, verifies, applies, commits, import-tests, tags — full cycle proven end-to-end via smoke subtests"
  - "HERETEK_EVOLVE_TEST_DIFF injection seam: env var overrides LLM diff generation for testing; Phase 4 LLM-loop path simply omits this env var and generates the diff itself"

requirements-completed:
  - SAFE-02
  - SAFE-03
  - SAFE-04
  - SAFE-06

# Metrics
duration: 5min
completed: 2026-05-16
---

# Phase 3 Plan 03: Self-Modify Guardrails — /evolve dry-run + /sanction with import-test gate Summary

**`/evolve` dry-run pipeline + `/sanction` with import-test-before-tag-advance gate; Phase 3 phase gate GREEN at 11 pass · 0 fail · 0 skip · 11 total**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-16T17:17:16Z
- **Completed:** 2026-05-16T17:22:28Z
- **Tasks:** 4
- **Files modified:** 2 (+ 1 created)

## Accomplishments

- `cmd_evolve()` fully implemented: writes `.heretek/dryruns/<id>.patch` + sidecar JSON with SHA256, enforces single-active-proposal policy, honors `HERETEK_EVOLVE_TEST_DIFF` env var, has zero git subprocess calls (cardinal rule structurally enforced)
- `cmd_sanction()` fully implemented with import-test gate BEFORE tag advance (Risk 2 + Pitfall 8 mitigation): apply → commit → `_run_import_test()` → ONLY THEN `git tag -f -a`; on import failure: `git reset --hard HEAD~1`, tag stays, `/heresy` remains safe
- `scripts/fixtures/heresy_test.patch` created: deterministic unified-diff appending a heresy-themed comment to `BIBLE.md`; applies cleanly via `git apply` to hermetic test repos seeded by `_make_test_repo`
- Three SKIP-stubs flipped to live integration assertions (`test_evolve_writes_dryrun_not_commit`, `test_sanction_commits_to_playground`, `test_sanction_advances_last_known_good_tag`); Phase 3 phase gate confirmed GREEN

## Task Commits

1. **Task 1: Implement cmd_evolve() dry-run pipeline** — `10a299e` (feat)
2. **Task 2: Implement cmd_sanction() with import-test gate** — `6ca5552` (feat)
3. **Task 3: Create scripts/fixtures/heresy_test.patch** — `1a555c7` (feat)
4. **Task 4: Flip 3 SAFE-* SKIP-stubs to live PASS** — `7622b45` (feat)

## Files Created/Modified

- `supervisor/commands.py` — `cmd_evolve()` fully implemented (105 lines added, stub removed); `cmd_sanction()` fully implemented (197 lines added, stub removed); `_run_import_test()` helper added; module docstring updated to reflect FULLY IMPLEMENTED status
- `scripts/fixtures/heresy_test.patch` — Deterministic unified-diff fixture: 6 lines, appends `# heresy detected: warp-bound subroutine inscribed by /evolve` to `BIBLE.md`
- `scripts/smoke_test.py` — Three SKIP-stubs replaced with live subprocess integration tests (~260 lines net added)

## Decisions Made

- `_run_import_test()` is a standalone helper (not delegating to `supervisor.git_ops.import_test()`) because `git_ops.import_test()` uses `REPO_DIR` which may be pointing at a hermetic test repo (which has no `heretek` package). The helper uses `pathlib.Path(__file__).resolve().parent.parent` as the project root, ensuring the real package is always what gets import-tested.
- Import-test gate is structurally BEFORE the tag advance in `cmd_sanction()` — the ordering in code reflects the invariant; there is no conditional path that skips the gate.
- `cmd_evolve()` has zero git subprocess calls — verified by the Task 1 acceptance criterion. The "no live-tree changes until /sanction" rule is enforced by absence, not assertion.
- Single-active-proposal policy: corrupt/unreadable sidecars are silently skipped in the pending-check loop (OSError + JSONDecodeError both caught with `continue`) — a corrupt sidecar cannot permanently block new proposals.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. All Task 1/2/3/4 verification scripts passed first-run. The `_run_import_test()` design (standalone subprocess vs. delegating to `git_ops.import_test()`) was pre-decided in the plan's interface notes, so no discovery was needed.

## Verification Results

**Phase 3 phase gate (Task 4 acceptance):**
```
Summary: 11 pass · 0 fail · 0 skip · 11 total
```

All 6 SAFE-* subtests live PASS:
- SAFE-01: `test_safe_push_refuses_main` + `test_safe_push_refuses_last_known_good` (Plan 03-01)
- SAFE-05: `test_heresy_rolls_back_to_tag` (Plan 03-02)
- SAFE-02+03: `test_evolve_writes_dryrun_not_commit` (this plan)
- SAFE-04: `test_sanction_commits_to_playground` (this plan)
- SAFE-06: `test_sanction_advances_last_known_good_tag` (this plan)

**No state leak:** `git status --porcelain` after full suite run shows only `M scripts/smoke_test.py` (the planned modified file — pre-commit).

## Phase 4 Readiness

- `handle_slash_command()` in `supervisor/telegram.py` already dispatches all three commands — no changes needed for Phase 4
- `cmd_evolve()` + `cmd_sanction()` + `cmd_heresy()` are all dual-front-door (CLI + TG dispatch) — Phase 4 polling loop hooks in via `handle_slash_command()`
- Phase 3 verification surface complete: all SAFE-* requirements automatable via `python scripts/smoke_test.py --static-only` (no Ollama, no Telegram, ~15s)
- Phase 2 persona-quality sign-off still pending (owner must run a one-time human-eval session on the 24GB primary model per VALIDATION.md §Manual-Only)
- `DRIVE_ROOT` still defaults to Colab path — deferred to Phase 4 launch

---
*Phase: 03-self-modify-guardrails*
*Completed: 2026-05-16*
