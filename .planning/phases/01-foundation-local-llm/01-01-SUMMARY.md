---
phase: 01-foundation-local-llm
plan: 01
subsystem: infra
tags: [git, github, gh-cli, ouroboros, fork, playground-branch, smoke-test, python, gitignore]

# Dependency graph
requires:
  - phase: planning
    provides: PROJECT.md, ROADMAP.md, REQUIREMENTS.md, and 01-PLAN.md establishing fork-and-overlay strategy
provides:
  - playground branch with upstream razzant/ouroboros@v6.2.0 source overlaid on the existing project root
  - last-known-good annotated tag at upstream v6.2.0 commit (8344285bfb51c2cbb19df20c5dc85aaa4d0d3340) — rollback target
  - origin remote → git@github.com:m4lk13/heretek.git; upstream remote → https://github.com/razzant/ouroboros.git
  - .gitignore extended with Heretek runtime artifacts (venv/, *.pyo, *.jsonl, node_modules/)
  - scripts/smoke_test.py — Wave 0 verification harness with three SKIP-returning subtests and --static-only flag
affects: [phase-01-plan-02, phase-01-plan-03, phase-01-plan-04, phase-01-plan-05, phase-03-guardrails]

# Tech tracking
tech-stack:
  added:
    - "gh CLI (GitHub fork orchestration)"
    - "Python 3.9.7 (smoke test runtime — pyenv shim)"
  patterns:
    - "Fork-and-overlay: gh repo fork without --clone, then git merge --allow-unrelated-histories into the existing .planning/-bearing directory"
    - "SKIP-stub verification harness: each subtest returns 'skip' until the owning plan flips it; exit 0 on SKIP, exit 1 only on FAIL"
    - "Static vs full smoke-test split via --static-only flag (Ollama-dependent subtests only run in full mode)"
    - "Annotated tag last-known-good points at upstream HEAD commit (not the merge commit) so /heresy reverts to clean upstream state"

key-files:
  created:
    - "scripts/smoke_test.py — Wave 0 smoke test scaffold"
    - ".planning/phases/01-foundation-local-llm/01-01-SUMMARY.md — this file"
  modified:
    - ".gitignore — extended with Heretek runtime entries"
    - ".git/config — remotes wired (origin, upstream)"

key-decisions:
  - "Fork-and-overlay over fork-and-clone: gh repo fork --clone=false + git merge --allow-unrelated-histories preserves the pre-existing .planning/ and CLAUDE.md without a temporary subdirectory shuffle"
  - "last-known-good tag points at upstream v6.2.0 commit 8344285b, not at the merge commit — this gives /heresy a clean rollback target free of any local planning artifacts"
  - "Push to origin is deferred to Plan 05 — first push should carry stripped/renamed code, not raw upstream"
  - "Smoke test SKIP semantics: exit code 0 on SKIP keeps CI green while plans are in flight; exit 1 only on FAIL"
  - ".gitignore extension preserves existing entries (e.g., *.log) rather than enforcing the exact plan list verbatim"

patterns-established:
  - "Pattern 1: SKIP-then-flip — Wave 0 ships scaffold subtests that return SKIP; subsequent plans (02/03/04/05) flip individual subtests to PASS/FAIL checks as features land"
  - "Pattern 2: Static-only fast path — smoke test supports --static-only for Ollama-free checks (rename, no-cloud-hosts grep) to enable sub-3-second iteration in plans that don't touch the LLM"

requirements-completed: [FORK-01]

# Metrics
duration: ~10min (resumed; Task 1 completed by prior agent)
completed: 2026-05-15
---

# Phase 01 Plan 01: Fork + Overlay + Wave 0 Smoke Test Scaffold Summary

**Forked razzant/ouroboros v6.2.0 to m4lk13/heretek, overlaid the upstream source onto the existing planning-bearing project root via unrelated-histories merge, tagged the rollback target, and shipped a SKIP-returning smoke test scaffold with --static-only flag.**

## Performance

- **Duration:** ~10 min (Tasks 2 + 3 + SUMMARY; Task 1 completed by prior agent before resume)
- **Started:** 2026-05-15T (resume after prior agent's Task 1 commit f5989f0)
- **Completed:** 2026-05-15
- **Tasks:** 3 (Task 1 by prior agent; Tasks 2 + 3 by resume agent)
- **Files modified:** 3 (.gitignore extended, scripts/smoke_test.py created, this SUMMARY.md created)

## Accomplishments

- GitHub fork live at https://github.com/m4lk13/heretek (resolved GH user: `m4lk13`); origin remote points at `git@github.com:m4lk13/heretek.git`, upstream at `https://github.com/razzant/ouroboros.git`
- Upstream Ouroboros v6.2.0 source tree merged into `/Users/evgeniy/Projects/140526_heretek/` without losing the pre-existing `.planning/` and `CLAUDE.md`
- `playground` branch checked out as the working branch for the entire Phase 1 (and downstream phases until launch)
- `last-known-good` annotated tag placed at upstream v6.2.0 commit `8344285bfb51c2cbb19df20c5dc85aaa4d0d3340` — the canonical rollback target for `/heresy` (Phase 3)
- `.gitignore` extended to cover Heretek runtime artifacts (`venv/`, `*.pyo`, `*.jsonl`, `node_modules/`) under a clearly-labeled `# Heretek runtime` header, preserving pre-existing entries
- `scripts/smoke_test.py` shipped with three SKIP-returning subtests (`test_package_rename`, `test_no_cloud_hosts`, `test_bilingual_ollama_reply`), `--static-only` argparse flag, and exit-0-on-SKIP semantics — Plans 02/03/04/05 can now incrementally flip subtests as features land

## Task Commits

Each task was committed atomically on the `playground` branch:

1. **Task 1: Fork upstream and overlay source into existing repo** — `f5989f0` (merge) — completed by prior agent before resume; merges upstream `razzant/ouroboros@v6.2.0` into existing repo with `--allow-unrelated-histories`. Also includes the `playground` branch creation and `last-known-good` annotated tag.
2. **Task 2: Update .gitignore for Heretek runtime artifacts** — `57f2756` (chore) — appended `venv/`, `*.pyo`, `*.jsonl`, `node_modules/` under `# Heretek runtime` header
3. **Task 3: Ship Wave 0 smoke test scaffold with SKIP stubs** — `1456d6c` (test) — created executable `scripts/smoke_test.py` with three SKIP subtests and `--static-only` flag

**Plan metadata commit:** pending — will be the final commit landing SUMMARY.md + STATE.md + ROADMAP.md updates on `playground`.

## Git State Snapshot

- **Resolved GitHub username:** `m4lk13`
- **origin URL:** `git@github.com:m4lk13/heretek.git` (SSH)
- **upstream URL:** `https://github.com/razzant/ouroboros.git` (HTTPS)
- **Upstream v6.2.0 commit SHA:** `8344285bfb51c2cbb19df20c5dc85aaa4d0d3340`
- **last-known-good resolves to:** `8344285bfb51c2cbb19df20c5dc85aaa4d0d3340` (identical to v6.2.0^{commit})
- **Annotated tag object SHA:** `59c3f4fe6c4d970345b26b169c7a9a6e6c1418e2` (the tag object itself; normal for annotated tags — `git rev-parse last-known-good^{commit}` resolves to the underlying commit)
- **Current HEAD branch:** `playground`
- **Recent log (most recent first):**
  - `1456d6c test(phase-1): Wave 0 smoke test scaffold with SKIP stubs`
  - `57f2756 chore(phase-1): extend .gitignore for Heretek runtime (.env, logs, venv)`
  - `f5989f0 merge(upstream): bring in razzant/ouroboros@v6.2.0`
  - `7bb9c2d chore(state): sync STATE.md and config.json before phase-1 execution`
  - `d22ae4a docs(phase-1): create phase plan (5 plans, 5 waves, 16 tasks)`

## Working Tree Snapshot (`ls -la /Users/evgeniy/Projects/140526_heretek/`)

Pre-existing planning-bearing files preserved alongside merged-in upstream files:

```
drwxr-xr-x   3 evgeniy  staff     96  .claude            [pre-existing]
drwxr-xr-x   3 evgeniy  staff     96  .cursor            [pre-existing]
drwxr-xr-x  14 evgeniy  staff    448  .git               [pre-existing, now with upstream history]
-rw-r--r--   1 evgeniy  staff    117  .gitignore         [pre-existing, extended in Task 2]
drwxr-xr-x   8 evgeniy  staff    256  .planning          [pre-existing — preserved]
-rw-r--r--   1 evgeniy  staff  21138  BIBLE.md           [upstream]
-rw-r--r--   1 evgeniy  staff  17217  CLAUDE.md          [pre-existing — preserved]
-rw-r--r--   1 evgeniy  staff   1073  LICENSE            [upstream]
-rw-r--r--   1 evgeniy  staff    823  Makefile           [upstream]
-rw-r--r--   1 evgeniy  staff  15177  README.md          [upstream]
-rw-r--r--   1 evgeniy  staff      6  VERSION            [upstream]
-rw-r--r--   1 evgeniy  staff   3339  colab_bootstrap_shim.py    [upstream]
-rw-r--r--   1 evgeniy  staff  28981  colab_launcher.py          [upstream]
drwxr-xr-x   3 evgeniy  staff     96  data               [upstream]
drwxr-xr-x   4 evgeniy  staff    128  docs               [upstream]
drwxr-xr-x  14 evgeniy  staff    448  ouroboros          [upstream — to be renamed to heretek/ in Plan 02]
drwxr-xr-x   4 evgeniy  staff    128  prompts            [upstream]
-rw-r--r--   1 evgeniy  staff    402  pyproject.toml     [upstream]
-rw-r--r--   1 evgeniy  staff     54  requirements.txt   [upstream]
drwxr-xr-x   3 evgeniy  staff     96  scripts            [new — Task 3]
drwxr-xr-x   9 evgeniy  staff    288  supervisor         [upstream]
drwxr-xr-x   7 evgeniy  staff    224  tests              [upstream]
```

## Smoke Test Verification

`python scripts/smoke_test.py --static-only` exits with status **0** and prints:

```
[SKIP] test_package_rename — not yet implemented (Plan 02 will flip this)
[SKIP] test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)

Summary: 0 pass · 0 fail · 2 skip · 2 total
```

`python scripts/smoke_test.py` (full mode, no flag) exits with status **0** and prints:

```
[SKIP] test_package_rename — not yet implemented (Plan 02 will flip this)
[SKIP] test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)
[SKIP] test_bilingual_ollama_reply — not yet implemented (Plan 05 will flip this)

Summary: 0 pass · 0 fail · 3 skip · 3 total
```

Both modes confirm the SKIP-on-exit-0 contract; Plans 02/03/04/05 will flip individual subtests to real checks.

## Decisions Made

- **Fork-and-overlay over fork-and-clone**: gh repo fork was invoked with `--clone=false --remote=false`, and the existing repo's master branch absorbed upstream via `git merge --allow-unrelated-histories`. This preserved `.planning/` and `CLAUDE.md` without a temporary subdirectory or rsync dance.
- **last-known-good at upstream commit, not merge commit**: The annotated tag was placed at `v6.2.0^{commit}` (`8344285b…`) rather than the merge commit (`f5989f0`). This gives the future `/heresy` command a clean upstream state to revert to, free of any local planning artifacts that landed in the merge.
- **Origin URL uses SSH**: `git@github.com:m4lk13/heretek.git` rather than HTTPS — matches the owner's existing GitHub SSH key setup and avoids future credential-helper friction.
- **.gitignore extension preserves `*.log`**: The original local `.gitignore` had `*.log`; the plan's required list didn't include it. Plan instructions explicitly said "do not remove existing entries", so `*.log` survives alongside the new `*.jsonl` token-log pattern.
- **Push to origin deferred to Plan 05**: First push should carry stripped/renamed code, not raw upstream — keeps the public fork's first visible commit aligned with the project's actual identity.

## Deviations from Plan

None — plan executed exactly as written.

The objective explicitly flagged that `*.log` (a pre-existing entry not on the plan's required list) should be preserved per the "do not remove existing entries" instruction, and that the upstream merge produced no conflicts in `.gitignore`. Both held: the merge ran cleanly with no conflicts of any kind, and `.gitignore` retained its original five-line block while gaining four new entries under the `# Heretek runtime` header.

## Issues Encountered

- **`grep` resolves to `ugrep` and treats `*` as regex**: When verifying the `.gitignore` entry for `*.jsonl`, the initial verification call failed because the shell environment maps `grep` → `ugrep`, which interprets `*` as a regex quantifier and threw "empty (sub)expression". Resolved by using `grep -Fxq` (fixed-string, whole-line) explicitly. No file changes required; pure verification-step adjustment.

## User Setup Required

None — the prior agent's Task 1 completed the `gh auth login` step (resolved username `m4lk13` confirms authenticated session worked). No new external service config is needed for Plan 01.

## Next Phase Readiness

Plan 02 (`heretek/` rename + `supervisor/__main__.py` + flip `test_package_rename`) is unblocked:

- `playground` branch is the active working branch
- Upstream `ouroboros/` package directory is present at project root, ready to be renamed
- `scripts/smoke_test.py` exists and Plan 02 only needs to flip `test_package_rename` from SKIP to a real `import heretek` / `assert no ouroboros` check
- `last-known-good` tag is in place so Phase 3 can wire `/heresy` against a known target

**No blockers.** Plan 02 can begin immediately.

## Self-Check: PASSED

- FOUND: /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py
- FOUND: /Users/evgeniy/Projects/140526_heretek/.gitignore
- FOUND: /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-01-SUMMARY.md
- FOUND commit: f5989f0 (merge upstream — prior agent)
- FOUND commit: 57f2756 (extend .gitignore)
- FOUND commit: 1456d6c (Wave 0 smoke test scaffold)

---
*Phase: 01-foundation-local-llm*
*Plan: 01*
*Completed: 2026-05-15*
