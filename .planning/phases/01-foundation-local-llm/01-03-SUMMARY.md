---
phase: 01-foundation-local-llm
plan: 03
subsystem: infra
tags: [python, strip, cloud-llm-removal, openrouter, anthropic, openai, playwright, smoke-test, fork-03]

# Dependency graph
requires:
  - phase: 01-foundation-local-llm-02
    provides: heretek/ Python package after upstream rename; supervisor/__main__.py CLI entrypoint; scripts/smoke_test.py with test_package_rename flipped to real PASS
provides:
  - "Source tree free of cloud LLM env var names (OPENROUTER_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY) and cloud hosts (openrouter.ai / api.openai.com / api.anthropic.com)"
  - "heretek/llm.py — LLMClient class shell preserved with chat()/vision_query()/default_model()/available_models() intact; cloud-specific helpers and headers stripped; ready for Plan 04 Ollama patch on a clean canvas"
  - "Tool registry: 39 tools loaded (down from 41 after deletion of browser/github/review/health/search; tool registry's pkgutil.iter_modules + try/except silently skipped the deleted files — no registry edits required)"
  - "supervisor/state.py — OpenRouter ground-truth cross-check removed; drift fields permanently None; budget tracking still records local accounting numbers"
  - "requirements.txt — playwright + playwright-stealth removed"
  - "scripts/smoke_test.py — test_no_cloud_hosts flipped from SKIP to real recursive grep over heretek/ + supervisor/; currently PASSES"
affects: [phase-01-plan-04, phase-01-plan-05, phase-02-persona, phase-03-guardrails, phase-04-launch]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hard-delete-no-stubs: deleted modules are simply removed from disk; tool registry's dynamic discovery (pkgutil.iter_modules + per-module try/except) silently skips missing files — no registry edits and no transitional stub files"
    - "Silent cloud-env-var strip: cloud env var loaders (OPENROUTER_API_KEY/OPENAI_API_KEY/ANTHROPIC_API_KEY) removed without startup warnings or hard errors — if they remain in someone's environment, they do nothing (per CONTEXT.md decision)"
    - "Surgical preservation: LLMClient class shell + public method signatures kept intact for Plan 04 to patch onto Ollama on a clean canvas, rather than rewriting in one mega-plan"
    - "Smoke-test SKIP-to-real flip continues: Plan 02 flipped test_package_rename, Plan 03 flips test_no_cloud_hosts; test_bilingual_ollama_reply remains SKIP until Plan 05"
    - "Deferred-items.md log: out-of-scope discoveries (vision/screenshot tools as permanent no-ops) recorded for future plans rather than fixed in the current task — preserves a tight strip"

key-files:
  created:
    - ".planning/phases/01-foundation-local-llm/01-03-SUMMARY.md — this file"
    - ".planning/phases/01-foundation-local-llm/deferred-items.md — vision/screenshot no-op tools logged for Plan 04/05 follow-up"
  modified:
    - "heretek/agent.py — _build_review_context method deleted; review_context_builder kwarg dropped from build_llm_messages call; cleanup_browser try-block removed from handle_task's finally"
    - "heretek/llm.py — class LLMClient shell preserved; cloud env reads, fetch_openrouter_pricing, _fetch_generation_cost, HTTP-Referer/X-Title headers, openrouter.ai base URL removed"
    - "heretek/loop.py — _get_pricing() reduced to static-table return; dead globals (_pricing_fetched, _cached_pricing, _pricing_lock) and threading import removed"
    - "heretek/tools/shell.py — _claude_code_edit + helpers (_run_claude_cli, _check_uncommitted_changes, _parse_claude_output) removed; run_shell preserved"
    - "supervisor/state.py — check_openrouter_ground_truth() and both call sites removed; cloud-drift display block in status formatter removed"
    - "requirements.txt — playwright + playwright-stealth removed"
    - "scripts/smoke_test.py — test_no_cloud_hosts flipped from SKIP stub to recursive grep of heretek/ + supervisor/ for cloud LLM regex"
  deleted:
    - "heretek/tools/github.py — upstream multi-file GitHub API tool (Heretek does not push to remote)"
    - "heretek/tools/review.py — upstream multi-model HTTP review orchestrator"
    - "heretek/tools/browser.py — upstream Playwright browser tool"
    - "heretek/review.py — package-root multi-model review/metrics orchestrator"
    - "heretek/tools/health.py — codebase_health tool (depended on deleted heretek/review.py — Rule 3 cleanup)"
    - "heretek/tools/search.py — _web_search depended on OPENAI_API_KEY + OpenAI Responses API (Rule 3 cleanup)"

key-decisions:
  - "Hard-delete, no stubs (CONTEXT.md): four target modules removed from disk via git rm; tool registry's pkgutil.iter_modules + try/except discovery pattern silently skips missing files, so no registry edits or transitional stubs were needed"
  - "Plan 03 expanded scope to cover heretek/tools/health.py and heretek/tools/search.py [Rule 3 - Blocking]: both depended on now-deleted code (heretek.review for health; OPENAI_API_KEY for search). Leaving them in place would cause runtime crashes or smoke-test failures. Deletion was the cleanest cut — pattern matches the four explicit targets"
  - "Plan 03 expanded scope to strip supervisor/state.py and heretek/tools/shell.py [Rule 3 - Blocking, smoke-test prereq]: Plan author explicitly authorized this expansion in Task 4 acceptance criteria — 'If the test FAILs because some file under heretek/ or supervisor/ still mentions an OpenRouter URL or env var: that's a leak from Plan 03 Task 3. Fix the source file (or update the strip task) before flipping the test. Do NOT loosen the regex.'"
  - "LLMClient class shell preserved with chat()/vision_query()/default_model()/available_models() public methods intact: the chat() body still calls the OpenAI client (which is OpenAI-compatible at the wire level, including Ollama's /v1 endpoint). Plan 04 patches only the __init__ defaults (Ollama base_url + literal 'ollama' api_key) without rewriting the method bodies"
  - "OUROBOROS_MODEL* env vars (carry-over from upstream) left untouched: Plan 02 SUMMARY decision — these are owned by Plan 04, which renames them to OLLAMA_*. Plan 03 only strips the three cloud API key names; lowercase 'OUROBOROS' env vars do not match the smoke-test regex"
  - "Vision/screenshot tools (heretek/tools/vision.py, parts of heretek/tools/core.py) intentionally left in place [out-of-scope]: they read ctx.browser_state.last_screenshot_b64 which can never be populated now that browser.py is gone, but they return graceful 'No screenshot stored' warnings rather than crashing — logged in deferred-items.md for Plan 04/05 follow-up"

patterns-established:
  - "Pattern: Hard-delete with dynamic-discovery safety net — when the tool registry uses pkgutil.iter_modules + per-module try/except, deleting a tool module is a single 'git rm' operation with no further edits required. The registry simply discovers fewer modules at next instantiation. Confirmed empirically: tool count went from 43 to 39 across this plan with zero registry code changes."
  - "Pattern: Surgical surface preservation — when stripping a module that another plan will rewrite, preserve class shell + public method signatures rather than nuking the file. Plan 04 patches LLMClient.__init__ to point at Ollama; the rest of LLMClient.chat() body (effort plumbing, cached_tokens extraction, etc.) is reused verbatim because it's wire-compatible with both OpenRouter and Ollama's OpenAI-compatible endpoint."
  - "Pattern: deferred-items.md log — discoveries that are out-of-scope for the current plan but worth fixing later are recorded in a phase-scoped log file rather than addressed in the moment. Keeps the strip tight and gives the next plan a checklist."

requirements-completed: [FORK-03]

# Metrics
duration: 9 min
completed: 2026-05-15
---

# Phase 1 Plan 3: Strip Cloud LLM Surface Area Summary

**Hard-deleted six upstream modules (github/review×2/browser/health/search) and silently stripped cloud LLM env-var loaders, OpenRouter pricing API, Anthropic CLI delegation, and OpenRouter drift cross-check across heretek/llm.py, heretek/loop.py, heretek/tools/shell.py, and supervisor/state.py — preserving LLMClient class shell for Plan 04's Ollama patch.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-15T12:45:47Z
- **Completed:** 2026-05-15T12:54:54Z
- **Tasks:** 4
- **Files modified:** 7 modified + 6 deleted + 2 created = 15 files touched

## Accomplishments

- Four target modules deleted (heretek/tools/github.py, heretek/tools/review.py, heretek/tools/browser.py, heretek/review.py) — plus two Rule 3 cleanups (heretek/tools/health.py, heretek/tools/search.py)
- agent.py freed of `_build_review_context` and `cleanup_browser` lazy-import call sites; orchestrator's `handle_task` finally block now cleanly drains the message queue without browser cleanup attempts
- heretek/llm.py reduced from 294 lines to 184 lines while preserving the LLMClient class shell (chat/vision_query/default_model/available_models still exported with intact signatures)
- supervisor/state.py freed of cloud HTTP cross-checks; budget tracking still records local accounting numbers
- requirements.txt trimmed of playwright + playwright-stealth (browser tool deleted); httpx was already absent
- scripts/smoke_test.py: test_no_cloud_hosts now does a recursive regex grep over heretek/ + supervisor/ and PASSES on the current tree

## Task Commits

Each task was committed atomically; Task 3 spanned 2 commits because a `git add` pathspec failure on an already-staged delete split the commit:

1. **Task 1: Hard-delete four target modules** — `77894e8` (refactor)
2. **Task 2: Remove lazy-import call sites in agent.py + Rule 3 delete of tools/health.py** — `4ba61a0` (refactor)
3. **Task 3a: Strip cloud LLM call sites (search.py delete carrier)** — `4eb7d28` (refactor)
4. **Task 3b: Strip cloud LLM call sites across llm/loop/shell/state** — `f61b1ce` (refactor)
5. **Task 4: Flip test_no_cloud_hosts SKIP to real check** — `63e816b` (test)

**Plan metadata commit:** will be created after this SUMMARY + STATE.md + ROADMAP.md updates.

## Files Created/Modified

### Created

- `.planning/phases/01-foundation-local-llm/01-03-SUMMARY.md` — this file
- `.planning/phases/01-foundation-local-llm/deferred-items.md` — vision/screenshot tools logged as permanent no-ops; Plan 04/05 to revisit

### Modified

- `heretek/agent.py` — see Removed Code Blocks below
- `heretek/llm.py` — see Removed Code Blocks below
- `heretek/loop.py` — `_get_pricing()` reduced to a one-line static-table return; dead globals + `threading` import removed
- `heretek/tools/shell.py` — `_claude_code_edit` and its helpers (`_run_claude_cli`, `_check_uncommitted_changes`, `_parse_claude_output`) removed; `run_shell` preserved
- `supervisor/state.py` — `check_openrouter_ground_truth()` and both call sites removed; cloud-drift display block in formatter removed
- `requirements.txt` — playwright + playwright-stealth removed
- `scripts/smoke_test.py` — `test_no_cloud_hosts` flipped from SKIP stub to real recursive grep

### Deleted

- `heretek/tools/github.py` (target — upstream GitHub API tool)
- `heretek/tools/review.py` (target — multi-model HTTP review orchestrator)
- `heretek/tools/browser.py` (target — Playwright browser tool)
- `heretek/review.py` (target — package-root multi-model review/metrics orchestrator)
- `heretek/tools/health.py` (Rule 3 — depended on deleted heretek/review.py)
- `heretek/tools/search.py` (Rule 3 — depended on OPENAI_API_KEY + OpenAI Responses API)

## Removed Code Blocks

### heretek/agent.py — block 1: `_build_review_context` method (lines 573-607 before)

```python
# =====================================================================
# Review context builder
# =====================================================================

def _build_review_context(self) -> str:
    """Collect code snapshot + complexity metrics for review tasks."""
    try:
        from heretek.review import collect_sections, compute_complexity_metrics, format_metrics
        sections, stats = collect_sections(self.env.repo_dir, self.env.drive_root)
        metrics = compute_complexity_metrics(sections)

        parts = [
            "## Code Review Context\n",
            format_metrics(metrics),
            f"\nFiles: {stats['files']}, chars: {stats['chars']}\n",
            "\nUse repo_read to inspect specific files. "
            "Use run_shell for tests. Key files below:\n",
        ]
        # ... 25 more lines of file-section assembly ...
        return "\n".join(parts)
    except Exception as e:
        return f"## Code Review Context\n\n(Failed to collect: {e})\nUse repo_read and repo_list to inspect code."
```

### heretek/agent.py — block 2: `cleanup_browser` finally-block (lines 446-454 before)

```python
finally:
    self._busy = False
    # Clean up browser if it was used during this task
    try:
        from heretek.tools.browser import cleanup_browser
        cleanup_browser(self.tools._ctx)
    except Exception:
        log.debug("Failed to cleanup browser", exc_info=True)
        pass
    while not self._incoming_messages.empty():
        ...
```

After:

```python
finally:
    self._busy = False
    while not self._incoming_messages.empty():
        ...
```

### heretek/agent.py — block 3: `review_context_builder` kwarg (line 358 before)

```python
messages, cap_info = build_llm_messages(
    env=self.env,
    memory=self.memory,
    task=task,
    review_context_builder=self._build_review_context,
)
```

After:

```python
messages, cap_info = build_llm_messages(
    env=self.env,
    memory=self.memory,
    task=task,
)
```

(`build_llm_messages` still accepts `review_context_builder: Optional[Any] = None` — the default-None path is taken; the review-context branch never fires.)

### heretek/llm.py — fully stripped blocks

Before this plan, `heretek/llm.py` was 294 lines and contained:

1. `fetch_openrouter_pricing()` — module-level, ~65 lines — HTTP GET to `https://openrouter.ai/api/v1/models` to fetch live pricing for `anthropic/`, `openai/`, `google/`, `meta-llama/`, `x-ai/`, `qwen/` prefixed models
2. `LLMClient.__init__` — read `OPENROUTER_API_KEY` env var with empty-string fallback, default `base_url="https://openrouter.ai/api/v1"`
3. `LLMClient._get_client` — set OpenAI client `default_headers={"HTTP-Referer": "https://colab.research.google.com/", "X-Title": "Ouroboros"}`
4. `LLMClient._fetch_generation_cost` — HTTP GET to `{base_url}/generation?id=...` with `Authorization: Bearer {api_key}` to retrieve per-generation cost as fallback
5. `LLMClient.chat` — Anthropic-specific provider pinning (`extra_body["provider"] = {"order": ["Anthropic"], ...}` for `anthropic/`-prefixed models) + cache_control injection on the last tool schema for Anthropic prompt caching + post-call cost fallback via `_fetch_generation_cost`

After this plan, `heretek/llm.py` is 184 lines and contains:

1. `normalize_reasoning_effort`, `reasoning_rank`, `add_usage` — unchanged module-level helpers
2. `LLMClient.__init__(api_key: Optional[str] = None, base_url: Optional[str] = None)` — no env var fallback; defaults to empty strings (Plan 04 will write the Ollama defaults)
3. `LLMClient._get_client` — `OpenAI(base_url, api_key)` with no custom headers
4. `LLMClient.chat` — preserved core logic (model, messages, max_tokens, extra_body with reasoning effort, optional tools/tool_choice) minus the Anthropic-specific branches and cost-fallback; cached_tokens / cache_write_tokens extraction preserved (those are LLM-agnostic OpenAI-compatible response fields)
5. `LLMClient.vision_query` — preserved unchanged except model default is now `""` (Plan 04/05 will plumb the local VLM)
6. `LLMClient.default_model` / `LLMClient.available_models` — preserved; still read `OUROBOROS_MODEL*` env vars (Plan 04 renames to `OLLAMA_*`)

## requirements.txt diff

Before:

```
openai>=1.0.0
requests
playwright
playwright-stealth
python-dotenv>=1.0.0
```

After:

```
openai>=1.0.0
requests
python-dotenv>=1.0.0
```

httpx was never in the file (it was an import inside the deleted `heretek/tools/review.py` only — gone with the file).

## test_no_cloud_hosts: full stdout of `python scripts/smoke_test.py --static-only`

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/

Summary: 2 pass · 0 fail · 0 skip · 2 total
```

Exit code: 0. Regex was not loosened.

Full-suite output (`python scripts/smoke_test.py` without --static-only):

```
[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected
[PASS] test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/
[SKIP] test_bilingual_ollama_reply — not yet implemented (Plan 05 will flip this)

Summary: 2 pass · 0 fail · 1 skip · 3 total
```

Exit code: 0 (SKIP is acceptable; only FAIL flips exit non-zero).

## httpx status

httpx was **not** in `requirements.txt` to begin with — the only importer was the deleted `heretek/tools/review.py`. Removing the dep was unnecessary because there was no dep to remove. Final tree has zero `import httpx` / `from httpx` matches under `heretek/`, `supervisor/`, and `scripts/`.

## Decisions Made

See key-decisions in frontmatter — six decisions documented.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Deleted heretek/tools/health.py**

- **Found during:** Task 2 (agent.py cleanup)
- **Issue:** `heretek/tools/health.py:_codebase_health` lazily imports `from heretek.review import collect_sections, compute_complexity_metrics`. With `heretek/review.py` deleted in Task 1, the tool would have crashed at first invocation. The plan's `<read_first>` for Task 2 referenced only two lazy-import sites (research Pitfall 3), but a third existed in health.py.
- **Fix:** Deleted `heretek/tools/health.py` outright. The tool was a companion to the deleted review subsystem; with `heretek/review.py` gone there is no minimal-friction stub that would still provide value. Tool registry auto-discovery silently skips it.
- **Files modified:** Deleted `heretek/tools/health.py`
- **Verification:** Tool registry instantiation succeeded; `codebase_health` confirmed absent from `available_tools()`.
- **Committed in:** `4ba61a0` (Task 2 commit)

**2. [Rule 3 - Blocking] Deleted heretek/tools/search.py**

- **Found during:** Task 3 (llm.py strip — broader grep for cloud env var names)
- **Issue:** `heretek/tools/search.py:_web_search` reads `OPENAI_API_KEY` and calls the OpenAI Responses API directly. This was a leak from the plan's truths block ("heretek/ source tree contains no literal strings: 'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'") and would have caused Task 4's smoke test to FAIL.
- **Fix:** Deleted the entire file. No local search replacement is in scope for Phase 1. Registry auto-discovery silently skips it.
- **Files modified:** Deleted `heretek/tools/search.py`
- **Verification:** Smoke test PASSES; `web_search` confirmed absent from `available_tools()`.
- **Committed in:** `4eb7d28` (Task 3a commit)

**3. [Rule 3 - Blocking] Stripped `_claude_code_edit` from heretek/tools/shell.py**

- **Found during:** Task 3 (broader cloud-env-var grep)
- **Issue:** `heretek/tools/shell.py:_claude_code_edit` reads `ANTHROPIC_API_KEY` and delegates code edits to the Anthropic CLI. Same constraint as search.py — would cause smoke-test FAIL.
- **Fix:** Removed `_claude_code_edit` plus its helpers (`_run_claude_cli`, `_check_uncommitted_changes`, `_parse_claude_output`). Kept `run_shell` unchanged. The `claude_code_edit` ToolEntry no longer registered.
- **Files modified:** `heretek/tools/shell.py`
- **Verification:** Smoke test PASSES; `claude_code_edit` confirmed absent from `available_tools()`; `run_shell` still loaded.
- **Committed in:** `f61b1ce` (Task 3b commit)

**4. [Rule 3 - Blocking] Stripped `check_openrouter_ground_truth` from supervisor/state.py**

- **Found during:** Task 3 (broader cloud-host grep)
- **Issue:** `supervisor/state.py:check_openrouter_ground_truth()` reads `OPENROUTER_API_KEY` and HTTP-GETs `https://openrouter.ai/api/v1/auth/key`. Called from two sites (`initialize_session_snapshots` and `update_budget_from_usage`). The plan's `truths` block requires no cloud env vars in heretek/, but the smoke test in Task 4 scans BOTH heretek/ AND supervisor/. The Plan author explicitly authorized this expansion in Task 4 acceptance criteria: "If the test FAILs because some file under heretek/ or supervisor/ still mentions an OpenRouter URL or env var: that's a leak from Plan 03 Task 3."
- **Fix:** Removed `check_openrouter_ground_truth()` and both call sites; drift fields stay None permanently; cloud-drift display block in status formatter removed.
- **Files modified:** `supervisor/state.py`
- **Verification:** Smoke test PASSES; `supervisor.state` imports cleanly.
- **Committed in:** `f61b1ce` (Task 3b commit)

**5. [Rule 3 - Blocking] Stripped fetch_openrouter_pricing call site from heretek/loop.py**

- **Found during:** Task 3 (consequence of deleting `fetch_openrouter_pricing` from llm.py)
- **Issue:** `heretek/loop.py:_get_pricing()` lazily imports `from heretek.llm import fetch_openrouter_pricing` (line 73 before strip). Without the call site cleanup, the try/except would still wrap the missing import and degrade gracefully — but the dead `_pricing_fetched` / `_cached_pricing` / `_pricing_lock` globals and `threading` import would linger as code smell.
- **Fix:** Replaced `_get_pricing()` body with a one-line `return _MODEL_PRICING_STATIC`. Removed the three dead globals and the unused `threading` import.
- **Files modified:** `heretek/loop.py`
- **Verification:** `import heretek.loop` succeeds; `_get_pricing` returns the static table.
- **Committed in:** `f61b1ce` (Task 3b commit)

---

**Total deviations:** 5 auto-fixed (all Rule 3 — Blocking)
**Impact on plan:** All five were prerequisites for Task 4's smoke test to pass without loosening the regex. The Plan author explicitly anticipated and authorized supervisor/state.py and shell.py strips in Task 4's acceptance criteria. health.py and search.py deletions match the same "hard-delete, no stubs" pattern as the four explicit targets. The loop.py cleanup is a follow-on tidying. No scope creep into Plan 04/05 territory (LLMClient class shell preserved; OUROBOROS_* env vars untouched).

## Issues Encountered

- **`git add` pathspec failure split Task 3 into two commits.** When running `git add heretek/tools/search.py` after the file was already deleted (and the deletion already staged via `git rm`), `git add` exited with `fatal: pathspec '...' did not match any files` — and crucially, that error caused the rest of the `git add` argument list to fail too, leaving 5 of 6 files unstaged. The first commit (`4eb7d28`) captured only the search.py deletion that was already staged. The second commit (`f61b1ce`) captured the remaining 5 files. Both commits are clean and reference Task 3 in their commit messages. Future runs: use separate `git add` invocations or stage deleted files via `git rm` only.

## Next Phase Readiness

- **Plan 04 (LLM swap) is unblocked.** LLMClient class shell + chat/vision_query method bodies are preserved on a clean canvas. Plan 04 only has to:
  - Write Ollama defaults into `LLMClient.__init__` (base_url=`http://localhost:11434/v1`, api_key=`"ollama"`)
  - Rename `OUROBOROS_MODEL*` → `OLLAMA_MODEL*` in `default_model()`, `available_models()`, and the call sites in `heretek/context.py`, `heretek/tools/{core,vision,dashboard,self_portrait}.py`, `heretek/consciousness.py`, `heretek/loop.py:703`, and `supervisor/events.py:264`
  - Update `test_bilingual_ollama_reply` from SKIP to a real check
- **Concern (logged in deferred-items.md):** `heretek/tools/vision.py:analyze_screenshot` and parts of `heretek/tools/core.py` still reference `ctx.browser_state.last_screenshot_b64`. They no longer have a screenshot producer (browser.py is gone) and return graceful "No screenshot stored" warnings. Plan 04 or 05 should either delete them along with the `BrowserState` dataclass in `heretek/tools/registry.py`, or revisit the "react to screenshots" gimmick (CLAUDE.md §9 open question).
- **Concern (logged in deferred-items.md, carry-over from Plan 02 SUMMARY):** Python 3.9 is in local use despite `pyproject.toml` `requires-python>=3.10`. Smoke test passes on 3.9; defer until CI is set up.

## Self-Check: PASSED

- All claimed files exist: `01-03-SUMMARY.md`, `deferred-items.md`
- All claimed deletions verified gone: `heretek/tools/{github,review,browser,health,search}.py`, `heretek/review.py`
- All claimed commits exist in git log: `77894e8`, `4ba61a0`, `4eb7d28`, `f61b1ce`, `63e816b`

---

*Phase: 01-foundation-local-llm*
*Completed: 2026-05-15*
