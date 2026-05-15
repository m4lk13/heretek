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
