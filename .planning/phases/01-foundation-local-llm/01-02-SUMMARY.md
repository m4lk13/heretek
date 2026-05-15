---
phase: 01-foundation-local-llm
plan: 02
subsystem: infra
tags: [python, package-rename, supervisor, dotenv, smoke-test, argparse, cli, fork-02]

# Dependency graph
requires:
  - phase: 01-foundation-local-llm-01
    provides: forked razzant/ouroboros@v6.2.0 source overlaid at project root; playground branch active; scripts/smoke_test.py scaffold with three SKIP subtests
provides:
  - heretek/ — renamed Python package (was ouroboros/); 32 files renamed, intra-package imports rewired
  - supervisor/__main__.py — local CLI entry point with --help, --smoke, and stubbed full-boot path (Plans 03/04/05 will wire the real main loop)
  - requirements.txt: python-dotenv>=1.0.0 added
  - pyproject.toml: package name updated (ouroboros → heretek)
  - scripts/smoke_test.py: test_package_rename flipped from SKIP to real PASS check (FORK-02 covered)
  - sys.path hardening in scripts/smoke_test.py so `python scripts/smoke_test.py` works regardless of cwd
affects: [phase-01-plan-03, phase-01-plan-04, phase-01-plan-05, phase-02-persona, phase-03-guardrails, phase-04-launch]

# Tech tracking
tech-stack:
  added:
    - "python-dotenv>=1.0.0 (.env loader for local boot)"
  patterns:
    - "git mv + perl bulk sweep — single-commit package rename with git rename detection preserved across 32 files"
    - "Scoped rename: source/config files (.py/.toml/.cfg/.txt) rewritten; .planning/*.md and CLAUDE.md historical references to upstream razzant/ouroboros preserved (case-sensitive lowercase-only replacement)"
    - "Stub-then-wire entry point: supervisor/__main__.py ships with --help + --smoke working immediately; full boot path returns exit 2 with a status message pointing at Plans 03/04/05"
    - "Smoke test sys.path bootstrap: scripts/ subdirectory prepends project root to sys.path so 'python scripts/smoke_test.py' has the same module resolution as 'python -c'"

key-files:
  created:
    - "supervisor/__main__.py — argparse CLI, .env loader, --smoke mode that imports supervisor.{state,workers} cleanly"
    - ".planning/phases/01-foundation-local-llm/01-02-SUMMARY.md — this file"
  modified:
    - "heretek/* — entire package renamed from ouroboros/ (32 files via git mv); intra-package imports updated to from heretek.tools.registry"
    - "pyproject.toml — project name: ouroboros → heretek"
    - "requirements.txt — appended python-dotenv>=1.0.0"
    - "supervisor/{state,workers,events,git_ops}.py — internal heretek.* imports updated by perl sweep"
    - "scripts/smoke_test.py — test_package_rename now imports heretek (PASS) and asserts import ouroboros raises ModuleNotFoundError; sys.path hardened"
    - "tests/test_{message_routing,smoke,vision}.py — internal imports updated by perl sweep"
    - "colab_launcher.py, colab_bootstrap_shim.py — internal heretek.* imports updated (these files will be deleted/replaced in later plans, but their imports are correct now)"

key-decisions:
  - "Bulk rename via git mv + perl -pi -e: preserves git rename detection (30 of 32 files showed >80% similarity) and lands as a single atomic commit; no half-renamed tree at any HEAD"
  - "Lowercase-only sweep: replaced 'ouroboros' but not 'Ouroboros'/'OUROBOROS' — case variants (e.g., OUROBOROS_MODEL env var, Ouroboros class name) are intentionally left for Plan 04's LLM swap which renames env vars to OLLAMA_*"
  - "Stub the full boot path in __main__.py: upstream v6.2.0 has no supervisor.run()/start()/main() — boot is all at module scope in colab_launcher.py and gated on cloud-LLM secrets. Wiring a real local boot now would require duplicating logic that Plans 03/04 will strip. Instead, --help + --smoke work immediately; full boot returns exit 2 with a clear status message"
  - "Add project root to sys.path in scripts/smoke_test.py: needed once test_package_rename stopped returning SKIP, because Python sets sys.path[0] to the script's directory (scripts/), not cwd. This was a latent bug in Plan 01's scaffold that surfaced as soon as a real import was attempted"

patterns-established:
  - "Pattern: SKIP-to-real flip — each plan that owns a smoke-test subtest replaces the SKIP stub with a real assertion in a single commit. Established in 01-01 (scaffold), executed in 01-02 (test_package_rename)"
  - "Pattern: scoped grep filters for source/config — 'rg -t py -t toml -t cfg -t txt' excludes .md docs from sweeps so .planning/ history stays intact"

requirements-completed: [FORK-02]  # LLM-06 is partial: Plan 02 delivered the `python -m supervisor` entry point (half of LLM-06's gate per PLAN.md frontmatter comment); the bilingual reply test is gated on Plan 05. Tracked as "Partial" in REQUIREMENTS.md.

# Metrics
duration: 5min
completed: 2026-05-15
---

# Phase 01 Plan 02: heretek/ Rename + supervisor/__main__.py + FORK-02 Smoke Flip Summary

**Renamed the upstream ouroboros/ Python package to heretek/ across 32 source files via git mv + perl sweep, shipped supervisor/__main__.py as the local CLI entry point (--help + --smoke working, full boot deferred to Plans 03/04/05), and flipped test_package_rename from SKIP to a real PASS check that asserts `import heretek` succeeds and `import ouroboros` raises ModuleNotFoundError.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-15T12:33:23Z
- **Completed:** 2026-05-15T12:39:19Z
- **Tasks:** 3 (rename sweep; __main__.py; smoke-test flip)
- **Files modified:** 43 (32 renames + 11 modified/created)

## Accomplishments

- **heretek/ package renamed and importable.** `python -c "import heretek"` succeeds; `python -c "import ouroboros"` fails with `ModuleNotFoundError`. Rename done as a single atomic commit (f17dc99) — 32 files moved via `git mv ouroboros heretek`, then 39 source/config files swept by `perl -pi -e 's/ouroboros/heretek/g'`. Git rename detection preserved for all moves.
- **Planning docs and CLAUDE.md preserved as historical context.** `.planning/*.md` and `CLAUDE.md` retain their references to the upstream `razzant/ouroboros` repo (correct: the fork lineage is documented context). The rg type filter (`-t py -t toml -t cfg -t txt`) excludes `.md` files from the sweep.
- **`supervisor/__main__.py` shipped with working --help and --smoke.** `python -m supervisor --help` prints the Heretek banner and argparse usage (exit 0). `python -m supervisor --smoke` imports `supervisor.{state, workers}` cleanly without starting the Telegram loop (exit 0). The default `python -m supervisor` prints a clear "not yet wired" status pointing at Plans 03/04/05 (exit 2).
- **`python-dotenv>=1.0.0` added to requirements.txt.** Loaded by `_load_env()` in `__main__.py` from the project-root `.env` (if present); otherwise falls back to shell environment.
- **`test_package_rename` flipped SKIP → PASS.** `python scripts/smoke_test.py --static-only` now reports `Summary: 1 pass · 0 fail · 1 skip · 2 total` (exit 0). The remaining SKIP (`test_no_cloud_hosts`) is owned by Plans 03/04.
- **scripts/smoke_test.py sys.path hardening.** Prepends the project root to `sys.path` at module top so `python scripts/smoke_test.py` (which sets `sys.path[0]` to `scripts/`) can still resolve `import heretek`. This was a latent Plan-01 scaffold bug that only surfaced once the SKIP stub became a real import attempt.

## Task Commits

Each task was committed atomically on the `playground` branch:

1. **Task 1: rename ouroboros package to heretek** — `f17dc99` (refactor) — `git mv ouroboros heretek` + perl sweep across 39 .py/.toml/.cfg/.txt files; 32-file rename detected by git; cleared `__pycache__` and `*.pyc` bytecode; verified `import heretek` succeeds and `import ouroboros` fails.
2. **Task 2: supervisor/__main__.py local CLI entry point** — `9ffb6fb` (feat) — argparse with --smoke flag, .env loader via python-dotenv, banner showing OLLAMA_* env vars, stubbed full-boot path returning exit 2; added `python-dotenv>=1.0.0` to requirements.txt.
3. **Task 3: flip test_package_rename SKIP to real check (FORK-02)** — `ef973a2` (test) — replaced SKIP stub with real `try: import heretek` / `try: import ouroboros except ImportError → PASS`; prepended project root to `sys.path` at module top to fix script-relative resolution.

**Plan metadata commit:** pending — will land SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md updates.

## Boot Function Discovery

The plan asked the executor to identify the "actual upstream boot function name" in `colab_launcher.py` and wire it into `__main__.py`.

**Finding:** No such function exists at v6.2.0. `colab_launcher.py` does not export a `run()`, `start()`, or `main()` — the entire 725-line boot sequence runs at module scope and is gated on:
- `OPENROUTER_API_KEY` (required via `get_secret(..., required=True)`)
- `google.colab.userdata` (Colab secrets API)
- `google.colab.drive.mount("/content/drive")` (Drive volume mounting)
- HTTP calls to OpenRouter for budget reconciliation
- `MAX_WORKERS`, `MODEL_MAIN`, etc. read from `OUROBOROS_*` env vars
- A blocking `while True:` main loop also at module scope

None of these work on a local macOS host with no Colab, no Drive, no OpenRouter key, and no upstream env-var naming.

**Decision:** Stub the full-boot path in `__main__.py` with an informative `print()` + `return 2`. Plans 03 (strip cloud modules), 04 (Ollama swap + `OLLAMA_*` env vars), and 05 (wire the local main loop in `__main__.py`) will progressively fill it in. `--help` and `--smoke` work today and gate Plan 02 acceptance.

## Files Created/Modified (Categorized)

**Created:**
- `supervisor/__main__.py` — 108-line CLI entry point (argparse + dotenv + smoke mode + stubbed full-boot)
- `.planning/phases/01-foundation-local-llm/01-02-SUMMARY.md` — this file

**Renamed (32 files, via git mv ouroboros heretek):**
- `heretek/{__init__.py, agent.py, apply_patch.py, consciousness.py, context.py, llm.py, loop.py, memory.py, owner_inject.py, review.py, utils.py}`
- `heretek/tools/{__init__.py, browser.py, compact_context.py, control.py, core.py, dashboard.py, evolution_stats.py, git.py, github.py, health.py, knowledge.py, registry.py, review.py, search.py, self_portrait.py, shell.py, tool_discovery.py, vision.py, webapp_push.py}`

**Modified (content updated by perl sweep):**
- `pyproject.toml` (project name)
- `requirements.txt` (python-dotenv added)
- `supervisor/{state.py, workers.py, events.py, git_ops.py}` (intra-package imports)
- `tests/{test_message_routing.py, test_smoke.py, test_vision.py}` (imports)
- `colab_launcher.py, colab_bootstrap_shim.py` (intra-package imports; full files will be deleted/replaced in Plans 03–05 but their imports are now consistent)
- `scripts/smoke_test.py` (subtest body rewrite + sys.path hardening)

**Total diff:** 43 files changed, 313 insertions(+), 182 deletions(-)

## Smoke Test Verification (current)

`python scripts/smoke_test.py --static-only` exits **0** and prints:

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[SKIP] test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)

Summary: 1 pass · 0 fail · 1 skip · 2 total
```

`python scripts/smoke_test.py` (full mode) exits **0** and prints:

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[SKIP] test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)
[SKIP] test_bilingual_ollama_reply — not yet implemented (Plan 05 will flip this)

Summary: 1 pass · 0 fail · 2 skip · 3 total
```

`python -m supervisor --help` exits **0** and prints:

```
usage: python -m supervisor [-h] [--smoke]

Heretek supervisor — local boot entry point (replaces colab_launcher.py)

optional arguments:
  -h, --help  show this help message and exit
  --smoke     Smoke mode: import supervisor modules without starting the
              Telegram loop. Used by scripts/smoke_test.py after Plan 04 wires
              Ollama.
```

`python -m supervisor --smoke` exits **0** and prints:

```
[supervisor] no .env at /Users/evgeniy/Projects/140526_heretek/.env; using shell environment only
[supervisor] heretek primary=qwen3.6:35b-a3b-q4_K_M light=qwen3:4b base=http://localhost:11434/v1
[supervisor] smoke OK: supervisor.{state,workers} import cleanly
```

## Decisions Made

- **Single-commit rename via git mv + perl sweep.** The plan's instruction was explicit; followed verbatim. 32-file git mv with rename detection preserved at 82–100% similarity per file (per `git diff HEAD~1 HEAD --stat`). The atomic commit means no intermediate HEAD has a half-renamed tree.
- **Stub the full boot in __main__.py, not wire it.** Per the plan's `<done>` note: "placeholder imports either real or clearly flagged for Plan 03/04 follow-up. Telegram-loop boot is intentionally not tested here". Upstream v6.2.0 has no boot function; wiring one would require duplicating colab_launcher.py logic that Plan 03 strips. Stubbed with an exit-2 status message instead.
- **sys.path hardening in scripts/smoke_test.py.** Necessary because Python sets `sys.path[0]` to the script's directory when invoked as `python scripts/smoke_test.py`. The previous Plan 01 scaffold never hit this because all subtests returned SKIP without actually importing anything. Documented as Rule 3 deviation below.
- **Replaced docstring "import ouroboros" reference twice.** Task 1 perl sweep accidentally rewrote the SKIP-stub's docstring (`"import heretek succeeds; import ouroboros fails"` became `"import heretek succeeds; import heretek fails"`), garbling the comment. Task 3 rewrote the whole function body with a fresh, correct docstring — so the intermediate garbled state lived only on disk between Task 1 commit and Task 3 commit, never in any production code path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added project root to sys.path in scripts/smoke_test.py**
- **Found during:** Task 3 (flip test_package_rename SKIP to real)
- **Issue:** After replacing the SKIP stub with a real `import heretek`, `python scripts/smoke_test.py --static-only` failed with `ModuleNotFoundError: No module named 'heretek'`. Root cause: when Python is invoked as `python scripts/smoke_test.py`, it sets `sys.path[0]` to the script's parent directory (`scripts/`), not the cwd — so `heretek/` at the project root is invisible to imports. This was a latent bug in Plan 01's scaffold that only surfaced once a subtest stopped returning SKIP and actually attempted an import.
- **Fix:** Prepended `_PROJECT_ROOT = Path(__file__).resolve().parent.parent` to `sys.path` at module top (before any `import heretek` attempts). Now the harness behaves identically whether invoked as `python scripts/smoke_test.py` or `python -m scripts.smoke_test` or from any cwd.
- **Files modified:** `scripts/smoke_test.py` (8 new lines at module top)
- **Verification:** `python scripts/smoke_test.py --static-only` exits 0 and prints the expected PASS line. Also tested from `/tmp` via absolute path — passes.
- **Committed in:** `ef973a2` (Task 3 commit; sys.path hardening landed alongside the smoke-test flip since both were needed to make the test work)

**2. [Note - not a deviation] `scripts/smoke_test.py` retains literal "ouroboros" string after Task 3**
- **Found during:** Final verification step 5 of the plan ("No `ouroboros` string remains in `.py`/`.toml`/`.cfg`/`.txt` files under the project root")
- **Status:** This is **required** by the smoke test itself — `test_package_rename` deliberately calls `import ouroboros` to assert it raises `ModuleNotFoundError`. The test would not work if it could not reference the old name.
- **Scope check:** The plan's must_haves criterion #4 is scoped to `heretek/`, `supervisor/`, and `tools/` — none of which contain `ouroboros` (confirmed by `rg -l "ouroboros" heretek/ supervisor/` returning empty). `scripts/` is not in that scope. Task 1's acceptance criterion (broader: no ouroboros in source/config) held at Task 1 commit time; the reintroduction in Task 3 is the intended behavior of an inverse-import-asserting test.
- **No action taken** — documented here for traceability.

---

**Total deviations:** 1 auto-fixed (1 blocking). Plus 1 documented non-deviation (`scripts/smoke_test.py` intentionally references `ouroboros` to assert it fails to import).
**Impact on plan:** sys.path fix was necessary for the plan's own acceptance criteria to pass (`Summary: 1 pass · 0 fail · 1 skip · 2 total`). No scope creep; no architectural change.

## Issues Encountered

- **`pyproject.toml` declares `requires-python = ">=3.10"` but local Python is 3.9.7.** Did not block this plan because `git mv`, `perl`, and `python -c "import heretek"` all worked under 3.9.7 (the package source is plain Python, no 3.10+ syntax encountered yet). This will need attention before Plan 04's Ollama smoke test if any imported module uses 3.10+ syntax. Logging here for next-plan awareness; not fixed in this plan (would be scope creep).
- **GitNexus index hook prints "stale index" warnings after every commit.** Informational per `known_quirks` in the spawn prompt; ignored.

## User Setup Required

None — Plan 02 made no external service changes. (`python-dotenv` added to `requirements.txt` will need `pip install -r requirements.txt` before Plan 04's Ollama smoke test, but that's tooling install, not configuration.)

## Next Phase Readiness

**Plan 03 (strip cloud-LLM modules, GitHub tools, multi-model review)** is unblocked:

- `heretek/` package importable; `heretek.tools.*` registry functional
- `supervisor/__main__.py` exists with `--smoke` mode that imports `supervisor.{state, workers}` — Plan 03 can use this to verify the strip didn't break any remaining imports
- The Plan-03 target files (`heretek/tools/github.py`, `heretek/tools/review.py`, `heretek/tools/browser.py`, `heretek/review.py`) all exist with the renamed import roots and can be hard-deleted
- Smoke test scaffold ready: `test_no_cloud_hosts` is still SKIP; Plan 03 flips it after stripping cloud-key references and Plan 04 follows up with `openrouter.ai` / `api.openai.com` / `api.anthropic.com` host removal

**No blockers** for Plan 03. The Python-version mismatch (3.9.7 vs ≥3.10) is logged above but does not affect Plan 03's grep-and-delete work.

## Self-Check: PASSED

- FOUND: /Users/evgeniy/Projects/140526_heretek/heretek/__init__.py (renamed from ouroboros/)
- FOUND: /Users/evgeniy/Projects/140526_heretek/heretek/tools/registry.py (renamed)
- FOUND: /Users/evgeniy/Projects/140526_heretek/supervisor/__main__.py (created)
- FOUND: /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py (modified — test_package_rename flipped)
- FOUND: /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-02-SUMMARY.md (this file)
- FOUND commit: f17dc99 (refactor: rename ouroboros to heretek)
- FOUND commit: 9ffb6fb (feat: add supervisor/__main__.py)
- FOUND commit: ef973a2 (test: flip test_package_rename SKIP to real)
- VERIFIED: `python -c "import heretek"` exits 0
- VERIFIED: `python -c "import ouroboros"` exits 1 with ModuleNotFoundError
- VERIFIED: `python -m supervisor --help` exits 0 with "Heretek supervisor" banner
- VERIFIED: `python scripts/smoke_test.py --static-only` exits 0 with `Summary: 1 pass · 0 fail · 1 skip · 2 total`
- VERIFIED: `rg -l "ouroboros" heretek/ supervisor/` returns empty (must-haves criterion #4 scope)
- VERIFIED: CLAUDE.md and .planning/PROJECT.md still contain "ouroboros" (historical references preserved)

---
*Phase: 01-foundation-local-llm*
*Plan: 02*
*Completed: 2026-05-15*
