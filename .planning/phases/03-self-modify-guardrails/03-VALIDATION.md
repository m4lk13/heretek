---
phase: 3
slug: self-modify-guardrails
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `scripts/smoke_test.py` runnable Python script (NOT pytest) — established Phase 1 pattern |
| **Config file** | none — subtests register inline in `scripts/smoke_test.py` |
| **Quick run command** | `python scripts/smoke_test.py --static-only` |
| **Full suite command** | `python scripts/smoke_test.py` |
| **Estimated runtime** | ~3 seconds (static-only) / ~30-60 seconds (full, with fixture-injection /evolve) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/smoke_test.py --static-only` (the 2-PASS fast-feedback gate inherited from Phase 1)
- **After every plan wave:** Run `python scripts/smoke_test.py` (full suite — includes the new SAFE-01..06 subtests + the existing Phase 1+2 subtests)
- **Before `/gsd:verify-work`:** Full suite must be green (12+ PASS / 0 FAIL / 0 SKIP)
- **Max feedback latency:** ~60 seconds (full suite); ~3 seconds (static-only)

---

## Per-Task Verification Map

> Populated by gsd-planner from RESEARCH.md §"Validation Architecture" mapping. Each new subtest maps 1:1 to a SAFE-* requirement.
>
> **Note on commands:** `scripts/smoke_test.py` does NOT support a `--subtest <name>` flag (only `--static-only` exists, verified in RESEARCH.md). Per-subtest invocation is done either via direct function call (`python -c "from scripts import smoke_test; smoke_test.<fn>()"`) or by running the full suite which prints each subtest's PASS/SKIP/FAIL line. The fast-feedback gate is `--static-only` (≈3s); the full gate is the bare command (≈30-60s). Each task's own `<verify><automated>` block runs the targeted assertion inline; the per-task row below is the suite-level confirmation command.

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-XX-XX | XX | X | SAFE-01 | unit | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-01 | unit | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-02 | integration | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-03 | integration | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-04 | integration | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-05 | integration | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |
| 03-XX-XX | XX | X | SAFE-06 | integration | `python scripts/smoke_test.py --static-only && python scripts/smoke_test.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Task IDs populated by planner. Plan/Wave columns populated by planner based on decomposition.*

*To inspect a single subtest's output during development (not a suite command):*
`python -c "import sys; sys.path.insert(0,'.'); from scripts import smoke_test; print(smoke_test.test_heresy_rolls_back_to_tag())"`

---

## Wave 0 Requirements

Phase 3 Wave 0 ships the smoke-test scaffolding as SKIP-stubs, mirroring the Phase 1+2 pattern. Each stub flips to a real assertion as features land in later waves/plans.

- [ ] `scripts/smoke_test.py` — add 6 new SKIP-stub subtests: `test_safe_push_refuses_main`, `test_safe_push_refuses_last_known_good`, `test_evolve_writes_dryrun_not_commit`, `test_sanction_commits_to_playground`, `test_heresy_rolls_back_to_tag`, `test_sanction_advances_last_known_good_tag`
- [ ] `scripts/smoke_test.py` — add hermetic temp-repo fixture helper (`make_test_repo()` returning a `tempfile.TemporaryDirectory()` + `git init` + minimal seeded commits + annotated `last-known-good` tag) — reuses Phase 2 Plan 02-02 pattern
- [ ] `scripts/smoke_test.py` — add `HERETEK_EVOLVE_TEST_DIFF` fixture-injection precondition check (env var path validation, fail-with-hint if patch invalid)
- [ ] `.gitignore` — append `.heretek/` so dryrun patches and staging dirs never accidentally commit
- [ ] No new framework install — `smoke_test.py` is the existing surface; pytest stays deferred (per Phase 1 deferred-items.md and 03-CONTEXT.md `<deferred>`)

---

## Manual-Only Verifications

Phase 3 success criteria are explicitly **all CLI/git-verifiable** (ROADMAP §Phase 3: "all verifiable without touching Telegram"). The CLI shim on `python -m supervisor.commands` is the load-bearing test surface. No persona-quality / aesthetic sign-off needed for this phase (unlike Phase 2's manual primary-model vibe check).

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|

*All phase behaviors have automated verification via `scripts/smoke_test.py` subtests + CLI subprocess invocation through `python -m supervisor.commands`.*

**Optional follow-up (NOT a Phase 3 gate, deferred to Phase 4 launch):**
- Real LLM-driven `/evolve` end-to-end on the 24GB primary model — verified during Phase 4's `/evolve → diff → /sanction → commit` cycle (EVOLVE-03). Phase 3 only exercises the dry-run plumbing via `HERETEK_EVOLVE_TEST_DIFF` fixture injection.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (6 SKIP-stubs + `.heretek/` gitignore + fixture helper)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s (full suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
