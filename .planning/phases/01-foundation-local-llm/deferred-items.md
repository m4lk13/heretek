# Deferred items — Phase 01 foundation-local-llm

Items discovered during plan execution that are out of scope for the current
plan and should be addressed in a later plan/phase.

## From Plan 01-03 (strip)

### Vision/screenshot tools left as no-ops

**Discovered:** Task 3, while auditing the tool registry after browser.py
deletion.

**Affected tools:**
- `heretek/tools/vision.py` — `analyze_screenshot`
- `heretek/tools/core.py` — second `analyze_screenshot` variant in the core module

**Issue:** Both tools read `ctx.browser_state.last_screenshot_b64`. With
`heretek/tools/browser.py` deleted (no `browse_page` / `browser_action` to
populate the screenshot buffer), these tools will now always return their
"No screenshot stored" warning string. They do not crash, do not import
anything deleted, and do not match the smoke-test cloud-host regex — so
deleting them is not required by Plan 03's contract. Left in place to keep
the strip surgical.

**Resolution:** Either delete the two tools in Plan 04/05 (along with the
`BrowserState` dataclass in `heretek/tools/registry.py`), or revisit when the
"react to screenshots" gimmick is reconsidered (CLAUDE.md §9 open question).

### `OUROBOROS_*` env var carry-over

**Discovered:** Plan 02 SUMMARY (already known), Plan 03 grep confirmed.

**Status:** Owned by Plan 04 (per Plan 02 SUMMARY decision). `OUROBOROS_MODEL`,
`OUROBOROS_MODEL_LIGHT`, `OUROBOROS_MODEL_CODE`, `OUROBOROS_WEBSEARCH_MODEL`
(in deleted search.py — gone), `OUROBOROS_CLAUDE_CODE_PERMISSION_MODE`
(in deleted shell.py block — gone), `OUROBOROS_MODEL_FALLBACK_LIST` (in
heretek/loop.py), `OUROBOROS_TOOL_RECURSION_LIMIT` etc. remain. Plan 04
renames them to `OLLAMA_*` as part of the cloud → local swap.

### Python 3.9 vs `requires-python>=3.10`

**Discovered:** Plan 02 SUMMARY.

**Status:** unchanged.  `pyproject.toml` declares 3.10+ but local dev is on
3.9. No new symptoms surfaced during Plan 03; smoke test passes on 3.9.
Resolve when CI is set up (Phase 4 or later).

## From Plan 01-04 (Ollama swap + budget neuter)

### Residual `OUROBOROS_*` env var references in non-llm/consciousness/context files

**Discovered:** Task 3, after final post-task grep across `heretek/` and
`supervisor/`.

**Affected files (env vars Plan 04 did NOT rename — out of plan scope):**
- `heretek/loop.py:611` — `OUROBOROS_MAX_ROUNDS` (max tool-loop rounds knob)
- `heretek/loop.py:674` — `OUROBOROS_MODEL_FALLBACK_LIST` (cloud-era fallback chain; semantically obsolete on Ollama)
- `heretek/tools/core.py:261` — `OUROBOROS_MODEL_LIGHT` / `OUROBOROS_MODEL` (with cloud-era default `anthropic/claude-sonnet-4.6`)
- `heretek/tools/vision.py:28,145,184` — `OUROBOROS_MODEL` (with cloud-era default; vision tools already noted as no-ops above)
- `heretek/tools/self_portrait.py:208` — `OUROBOROS_MODEL` (status string only)
- `heretek/tools/dashboard.py:241` — `OUROBOROS_MODEL` (status string only)
- `heretek/tools/evolution_stats.py:28` — `OUROBOROS_REPO_DIR` (path resolution)
- `heretek/tools/git.py:65` — `OUROBOROS_PRE_PUSH_TESTS` (CI hook knob)
- `supervisor/events.py:264` — `OUROBOROS_MODEL_LIGHT` (with cloud-era `x-ai/grok-3-mini` default)
- `supervisor/workers.py:51` — `OUROBOROS_WORKER_START_METHOD` (multiprocessing start method)

**Issue:** Plan 04's frontmatter `files_modified` listed only `heretek/llm.py`,
`heretek/consciousness.py`, `heretek/context.py`, `supervisor/state.py`,
`requirements.txt`. The above references are in other files and are
out-of-scope per the deviation-rules scope boundary. They do not block the
plan's smoke tests (no cloud-host regex hit; module imports clean) and they
do not break the Ollama wiring (caller code paths in question are either
no-op vision tools, status text, or features not yet exercised).

**Resolution:** Rename to `HERETEK_*` (for project-internal knobs) or
`OLLAMA_*` (for model-name knobs) in a follow-up env-var hygiene plan
(suggest Phase 02 or a dedicated Phase 01-06 cleanup pass). Cloud-era
defaults inside the env-var values (e.g., `anthropic/claude-sonnet-4.6`,
`x-ai/grok-3-mini`) should be updated to Ollama tags in the same pass.

### Background docstring header still says "Ouroboros"

**Discovered:** Task 3, while editing consciousness.py.

**Status:** Module-level docstring `"""Ouroboros — Background Consciousness."""`
preserved on purpose. Per Plan 02 decision (in STATE.md): the rename sweep
was lowercase-only; case-variant Title-case strings like this one were left
in place. Plan 04 did not own the case-variant rename either. Defer to a
later cleanup plan.
