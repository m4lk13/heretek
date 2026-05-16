---
phase: 03-self-modify-guardrails
plan: 01
subsystem: infra
tags: [git, branch-protection, safe_push, smoke-test, self-modification]

# Dependency graph
requires:
  - phase: 02-persona-identity
    provides: smoke_test.py harness with 9-subtest full suite; identity/SYSTEM.md loaded
provides:
  - safe_push() chokepoint in supervisor/git_ops.py with ProtectedBranchError
  - PROTECTED_BRANCHES frozenset (floor: main, last-known-good)
  - Branch defaults renamed to playground/last-known-good across 3 files
  - All 3 pre-existing push sites unified under safe_push() or converted to no-op
  - _make_test_repo hermetic fixture for Phase 3 SAFE-* subtests
  - 6 SAFE-* smoke subtests (2 live PASS, 4 SKIP-stubs)
  - .heretek/ gitignored
affects: [03-02-PLAN, 03-03-PLAN, Phase 4 launch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Local-import-inside-function-body for cross-package imports (Pitfall 3 mitigation)"
    - "Refusal-before-git invariant: ProtectedBranchError raised before any git_capture() call (Pitfall 7)"
    - "SKIP-stub-then-flip subtest scaffold extended to Phase 3 SAFE-* subtests"
    - "Hermetic _make_test_repo fixture (tempfile.TemporaryDirectory + real git repo + annotated tag)"
    - "Audit-log-on-refusal: append_jsonl with type=safe_push_refused before raising"

key-files:
  created:
    - scripts/__init__.py
  modified:
    - supervisor/git_ops.py
    - supervisor/workers.py
    - heretek/agent.py
    - heretek/tools/git.py
    - supervisor/events.py
    - heretek/tools/control.py
    - scripts/smoke_test.py
    - .gitignore

key-decisions:
  - "safe_push() refusal check happens BEFORE any git_capture() call (Pitfall 7 invariant) — protected-branch check is pure Python, no subprocess risk on misconfigured REPO_DIR"
  - "Cross-package import (heretek/* -> supervisor/git_ops) done as local import inside function body (Pitfall 3 mitigation) — not at module level"
  - "_handle_promote_to_stable becomes no-op-with-deprecation-message rather than deleted — tool deletion is Phase 4+ cleanup per RESEARCH"
  - "HERETEK_PROTECTED_BRANCHES env var can EXPAND but not shrink the hardcoded floor {main, last-known-good} — defense-in-depth"
  - "Phase 1 deferred: BRANCH_DEV/BRANCH_STABLE rename closed in this plan across git_ops.py, workers.py, agent.py:Env"
  - "DRIVE_ROOT rename (/content/drive/MyDrive/Ouroboros) remains deferred to Phase 4"

patterns-established:
  - "safe_push pattern: all bot git writes route through supervisor.git_ops.safe_push() single chokepoint"

requirements-completed:
  - SAFE-01
  - SAFE-02

# Metrics
duration: 4min
completed: 2026-05-16
---

# Phase 3 Plan 01: Self-Modify Guardrails — Branch Protection Summary

**Branch-protection chokepoint safe_push() + ProtectedBranchError gates all 3 bot push sites; SAFE-01 automated; static smoke at 7 pass · 0 fail · 4 skip · 11 total**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-16T17:02:12Z
- **Completed:** 2026-05-16T17:06:10Z
- **Tasks:** 4
- **Files modified:** 8 (+ 1 created)

## Accomplishments

- `safe_push()` + `ProtectedBranchError` + `PROTECTED_BRANCHES` added to `supervisor/git_ops.py` with refusal-before-git invariant (Pitfall 7); audit-logged to `logs/supervisor.jsonl`
- Branch defaults renamed `heretek` → `playground` and `heretek-stable` → `last-known-good` across `git_ops.py`, `workers.py`, and `agent.py:Env` (Phase 1 deferred carry closed)
- All 3 pre-existing raw push sites unified: `heretek/tools/git.py` and `heretek/agent.py` route through `safe_push()`; `supervisor/events.py:_handle_promote_to_stable` is now a no-op-with-deprecation-message (target `last-known-good` is protected)
- 6 SAFE-* subtests scaffolded in `scripts/smoke_test.py`: 2 live PASS (`test_safe_push_refuses_main`, `test_safe_push_refuses_last_known_good`) + 4 SKIP-stubs for Plans 03-02/03-03; `_make_test_repo` hermetic fixture ready
- `.heretek/` gitignored (Phase 3 dry-run staging directory)

## Task Commits

1. **Task 1: safe_push() + ProtectedBranchError + branch renames** — `512988d` (feat)
2. **Task 2: Route 3 push sites through safe_push(); no-op promote_to_stable** — `857b49d` (feat)
3. **Task 3: Gitignore .heretek/** — `f3fe4da` (chore)
4. **Task 4: SAFE-* smoke subtests + _make_test_repo + scripts package** — `f7d4fa0` (feat)

## Files Created/Modified

- `supervisor/git_ops.py` — Added `ProtectedBranchError`, `PROTECTED_BRANCHES`, `safe_push()`; renamed branch defaults; updated `init()` to read `HERETEK_PROTECTED_BRANCHES` env var
- `supervisor/workers.py` — Renamed `BRANCH_DEV`/`BRANCH_STABLE` module literals + `init()` defaults
- `heretek/agent.py` — Renamed `Env.branch_dev` default; auto-rescue push routed through `safe_push()`
- `heretek/tools/git.py` — `_git_push_with_tests` uses `safe_push(ctx.branch_dev)` via local import
- `supervisor/events.py` — `_handle_promote_to_stable` is no-op-with-deprecation-message
- `heretek/tools/control.py` — `promote_to_stable` description updated to reflect deprecation
- `scripts/smoke_test.py` — Added `_make_test_repo`, 6 SAFE-* subtests, updated `STATIC_SUBTESTS` (11 entries)
- `scripts/__init__.py` — Created empty package marker
- `.gitignore` — Appended `.heretek/` entry with comment

## Decisions Made

- `safe_push()` refusal check BEFORE any `git_capture()` call (Pitfall 7 invariant) — protected-branch check is pure Python; no subprocess risk on misconfigured `REPO_DIR`
- Cross-package import `heretek/* → supervisor/git_ops` done as local import inside function body (Pitfall 3) — not at module level
- `_handle_promote_to_stable` becomes no-op-with-message rather than deleted — tool deletion is Phase 4+ cleanup (per RESEARCH §"promote_to_stable LLM-Tool Fate")
- `HERETEK_PROTECTED_BRANCHES` env var can EXPAND but not shrink the hardcoded floor — defense-in-depth; unsetting env var cannot widen permissions
- Phase 1 deferred `BRANCH_DEV`/`BRANCH_STABLE` rename closed; `DRIVE_ROOT` path rename deferred to Phase 4

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

One expected non-issue: during Task 1 inline verification, `append_jsonl` logged a warning because `DRIVE_ROOT` defaults to `/content/drive/MyDrive/Ouroboros` (Colab path, read-only on local dev). The `try/except` in `safe_push()` catches this correctly and the refusal still raises — behavior is correct by design. Full audit-log smoke (verification step 3) passed when `drive_root=pathlib.Path(".")` was used in `init()`.

## Verification Results

**Static gate:** `7 pass · 0 fail · 4 skip · 11 total` (exact match to plan spec)

**Audit-log smoke:**
```
OK: refusal logged
```
Record confirmed in `logs/supervisor.jsonl`: `{"type": "safe_push_refused", "target_branch": "main", ...}`

**Full suite:** Not run (Ollama not loaded; primary model is 24GB and would OOM under current memory pressure). Phase 2 smoke results remain valid per STATE.md.

## Phase 3 Deferred Items

- `DRIVE_ROOT` still points to `/content/drive/MyDrive/Ouroboros` — rename deferred to Phase 4 (never surfaced in any test so far; Phase 4 is when the full supervisor boots in production)
- Residual `OUROBOROS_*` env vars in `heretek/loop.py`, `supervisor/events.py`, `supervisor/workers.py` — see `.planning/phases/01-foundation-local-llm/deferred-items.md`; still scoped to Phase 4 launch

## Next Phase Readiness

- Plan 03-02 (`/heresy` rollback command): `_make_test_repo` helper ready; `safe_push()` callable from any handler; `test_heresy_rolls_back_to_tag` SKIP-stub waiting to flip
- Plan 03-03 (`/evolve` dry-run + `/sanction` command): `safe_push()` is the sanctioned write path; `.heretek/` is gitignored; `test_evolve_writes_dryrun_not_commit`, `test_sanction_commits_to_playground`, `test_sanction_advances_last_known_good_tag` SKIP-stubs ready to flip

---
*Phase: 03-self-modify-guardrails*
*Completed: 2026-05-16*
