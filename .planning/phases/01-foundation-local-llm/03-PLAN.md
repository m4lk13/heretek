---
phase: 01-foundation-local-llm
plan: 03
type: execute
wave: 3
depends_on:
  - "02"
files_modified:
  - heretek/tools/github.py  # DELETED
  - heretek/tools/review.py  # DELETED
  - heretek/tools/browser.py  # DELETED
  - heretek/review.py  # DELETED (package-root multi-model orchestrator)
  - heretek/agent.py  # _build_review_context helper removed; browser cleanup branch removed
  - heretek/llm.py  # cloud env var loaders (OPENROUTER_API_KEY/OPENAI_API_KEY/ANTHROPIC_API_KEY) stripped silently
  - requirements.txt  # playwright deps removed; httpx removed if review.py was sole importer
autonomous: true
requirements:
  - FORK-03
must_haves:
  truths:
    - "heretek/tools/github.py, heretek/tools/review.py, heretek/tools/browser.py, and heretek/review.py do not exist on disk"
    - "agent.py contains no reference to _build_review_context or cleanup_browser as call sites or imports"
    - "heretek/ source tree contains no literal strings: 'OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY' (cloud-LLM env var names)"
    - "python -c 'import heretek' still succeeds (no broken imports introduced)"
    - "python -c 'from heretek.tools import registry; r = registry.Registry(); r._load_modules()' (or equivalent registry init) succeeds without raising ImportError for deleted modules"
    - "playwright deps removed from requirements.txt"
  artifacts:
    - path: "heretek/agent.py"
      provides: "Orchestrator without browser/review entanglement"
      contains: "class"
    - path: "heretek/llm.py"
      provides: "LLM client with cloud env var loaders stripped (NOT YET patched for Ollama — that's Plan 04)"
      contains: "OpenAI"
    - path: "requirements.txt"
      provides: "Trimmed deps: no playwright, no httpx (if review.py was sole importer)"
      contains: "openai"
  key_links:
    - from: "heretek/tools/__init__.py or registry.py"
      to: "filesystem (pkgutil.iter_modules)"
      via: "dynamic discovery; missing files simply not loaded"
      pattern: "pkgutil\\.iter_modules"
    - from: "heretek/agent.py handle_task() finally"
      to: "(was browser cleanup; now absent)"
      via: "code block removed"
      pattern: "cleanup_browser"
---

<objective>
Hard-delete the four upstream modules we do not want in Heretek (`tools/github.py`, `tools/review.py`, `tools/browser.py`, package-root `review.py`), remove the lazy-import call sites in `agent.py` that referenced them, and silently strip the cloud-LLM env-var loading code from `llm.py` (OPENROUTER, OPENAI, ANTHROPIC). Also remove playwright/httpx from `requirements.txt` if no other module imports them.

Purpose: The CONTEXT.md decision is "hard delete, no stubs." Leaving these modules in place pollutes the tool registry, keeps dead code that could be re-summoned via prompt injection, and leaves a network attack surface (the OpenRouter HTTP drift-check in budget tracking). Plan 04 patches the LLM client for Ollama; this plan clears the path so Plan 04 only has to touch positive changes, not removals.

Output: Heretek's source tree is free of cloud-LLM, browser, and multi-model-review surface area. The tool registry's dynamic discovery seamlessly skips the deleted files (no registry edits needed — confirmed in research). `import heretek` still works. The smoke test's `test_no_cloud_hosts` subtest is flipped from SKIP to PASS.
</objective>

<execution_context>
@/Users/evgeniy/.claude/get-shit-done/workflows/execute-plan.md
@/Users/evgeniy/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/evgeniy/Projects/140526_heretek/.planning/PROJECT.md
@/Users/evgeniy/Projects/140526_heretek/.planning/ROADMAP.md
@/Users/evgeniy/Projects/140526_heretek/.planning/REQUIREMENTS.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-02-SUMMARY.md

<interfaces>
Files to read fully before editing:
- heretek/agent.py — locate _build_review_context method and the finally block in handle_task that imports cleanup_browser
- heretek/llm.py — locate the os.environ.get calls for OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
- heretek/tools/registry.py — confirm it uses pkgutil.iter_modules and per-module try/except (deleting tool files is safe with no registry edits)
- requirements.txt — current dep list before pruning

Research-confirmed lazy-import call sites (from 01-RESEARCH.md §Pitfall 3):
- heretek/agent.py, inside _build_review_context(): `from heretek.review import collect_sections, ...`
- heretek/agent.py, inside handle_task() finally: `from heretek.tools.browser import cleanup_browser`

Tool registry pattern (from 01-RESEARCH.md §Code Examples — Tool Registry Auto-Discovery):
The registry uses pkgutil.iter_modules + importlib + try/except. Deleted tool files are silently skipped at discovery time — no registry edits needed.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Hard-delete the four target modules</name>
  <files>
    heretek/tools/github.py (DELETE),
    heretek/tools/review.py (DELETE),
    heretek/tools/browser.py (DELETE),
    heretek/review.py (DELETE)
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Stripping strategy — hard delete, no stubs)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Code Examples — Tool Registry Auto-Discovery confirms no registry edits needed)
    - /Users/evgeniy/Projects/140526_heretek/heretek/tools/registry.py (confirm pkgutil.iter_modules + try/except pattern present)
    - `ls -la /Users/evgeniy/Projects/140526_heretek/heretek/tools/` (confirm the three target files exist before deletion)
    - `ls -la /Users/evgeniy/Projects/140526_heretek/heretek/review.py` (confirm package-root review.py exists; it is distinct from `heretek/tools/review.py`)
  </read_first>
  <action>
Tool registry uses dynamic filesystem scanning (`pkgutil.iter_modules` + per-module try/except) — confirmed via research. Deleting files is safe; no registry edits required. No `__init__.py` updates required either (tools are not statically imported in `__init__.py`).

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Confirm all four files exist before deletion
test -f heretek/tools/github.py || { echo "FAIL: heretek/tools/github.py missing"; exit 1; }
test -f heretek/tools/review.py || { echo "FAIL: heretek/tools/review.py missing"; exit 1; }
test -f heretek/tools/browser.py || { echo "FAIL: heretek/tools/browser.py missing"; exit 1; }
test -f heretek/review.py       || { echo "FAIL: heretek/review.py missing"; exit 1; }

# Delete via git rm (preserves git history of deletion)
git rm heretek/tools/github.py
git rm heretek/tools/review.py
git rm heretek/tools/browser.py
git rm heretek/review.py

# Confirm registry pattern is intact (no static imports of deleted modules)
# These should print nothing (no matches):
grep -rn "from heretek.tools.github" heretek/ supervisor/ scripts/ 2>/dev/null || true
grep -rn "from heretek.tools.browser" heretek/ supervisor/ scripts/ 2>/dev/null || true
grep -rn "from heretek.review" heretek/ supervisor/ scripts/ 2>/dev/null || true
# If any matches surface, Task 2 handles them — proceed to commit this delete first.

# Sanity: import heretek still works (no broken module-level imports yet — the lazy ones in agent.py are addressed in Task 2 and won't break import)
python -c "import heretek; import heretek.tools; print('OK')"

# Commit
git commit -m "refactor(phase-1): hard-delete github, review (multi-model), browser tools"
```

If `import heretek` fails after deletion: a static module-level import of one of the deleted modules exists somewhere. Run `rg "from heretek\\.(tools\\.github|tools\\.review|tools\\.browser|review)" heretek/ supervisor/` to find it. If found, that file needs the import (and any uses) removed in this same task, then re-test, then commit.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && test ! -f heretek/tools/github.py && test ! -f heretek/tools/review.py && test ! -f heretek/tools/browser.py && test ! -f heretek/review.py && python -c "import heretek; import heretek.tools" && git log --oneline -1 | grep -q "hard-delete"</automated>
  </verify>
  <acceptance_criteria>
    - `test ! -f /Users/evgeniy/Projects/140526_heretek/heretek/tools/github.py` exits 0
    - `test ! -f /Users/evgeniy/Projects/140526_heretek/heretek/tools/review.py` exits 0
    - `test ! -f /Users/evgeniy/Projects/140526_heretek/heretek/tools/browser.py` exits 0
    - `test ! -f /Users/evgeniy/Projects/140526_heretek/heretek/review.py` exits 0
    - `python -c "import heretek"` exits 0
    - `python -c "import heretek.tools"` exits 0
    - `git log --oneline -1` contains substring `hard-delete`
    - `git diff HEAD~1 HEAD --stat | grep -c "^ heretek.*\\.py "` is at least 4 (or `git show --stat HEAD | grep -c "deleted file"` is 4)
    - `! rg -q "^from heretek\\.tools\\.(github|browser|review) " heretek/ supervisor/` (no remaining static imports of deleted modules)
    - `! rg -q "^from heretek\\.review " heretek/ supervisor/` (no remaining static import of package-root review)
  </acceptance_criteria>
  <done>Four target modules deleted from disk and from git's tracked tree; tool registry continues to load successfully via dynamic discovery (deleted files silently skipped); no module-level imports broken.</done>
</task>

<task type="auto">
  <name>Task 2: Remove lazy-import call sites in agent.py</name>
  <files>heretek/agent.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/heretek/agent.py (READ FULLY — find _build_review_context method definition and the cleanup_browser call site inside handle_task)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pitfall 3: agent.py lazy import call sites survive the delete — exact substrings to grep)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Stripping strategy — "All imports and call sites updated/removed in the same commit chain")
  </read_first>
  <action>
The research finding (Pitfall 3) is precise: two lazy in-function imports must be cleaned up.

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Locate the two dangerous substrings
grep -n "_build_review_context" heretek/agent.py
grep -n "from heretek.review" heretek/agent.py
grep -n "cleanup_browser" heretek/agent.py
grep -n "from heretek.tools.browser" heretek/agent.py
```

Expected matches (from research):
- `_build_review_context` defined as a method and called from somewhere (likely from `handle_task` or a review-routing branch).
- `from heretek.review import collect_sections, ...` lives inside `_build_review_context`'s body.
- `cleanup_browser` is called inside `handle_task`'s `finally:` block; the call is wrapped in try/except.
- `from heretek.tools.browser import cleanup_browser` lives inside that try block.

Step 2: Edit `heretek/agent.py`:

(a) **Remove the entire `_build_review_context` method.** Find its `def _build_review_context(self...)` line and delete from that line through the end of the method body (next `def` at the same indentation level, or end of class). Also delete every call site to `self._build_review_context(...)` — those are likely in a review-routing branch of `handle_task`.

If `handle_task` has a branch like:
```python
if task.type == "review":
    ctx = self._build_review_context(task)
    # ... review-specific logic
    return ...
```
Delete the entire `if task.type == "review":` branch (or whatever the condition is — read first to confirm). After deletion, the bot will simply not handle review-type tasks; since the multi-model review tool is gone, no review-type tasks will ever be submitted anyway.

(b) **Remove the `cleanup_browser` call and import.** Inside `handle_task`'s `finally:` block, locate the try/except that imports and calls `cleanup_browser`. Delete the entire try block (and any surrounding conditional that exists solely to call it). The `finally:` block should remain, but without the browser-cleanup body.

Step 3: Verify the file still parses and imports cleanly:
```bash
python -c "import heretek.agent; print('OK')"
```

Step 4: Re-grep to confirm cleanup:
```bash
grep -n "_build_review_context" heretek/agent.py    # must print nothing
grep -n "cleanup_browser" heretek/agent.py           # must print nothing
grep -n "from heretek.review" heretek/agent.py       # must print nothing
grep -n "from heretek.tools.browser" heretek/agent.py # must print nothing
```

Step 5: Commit:
```bash
git add heretek/agent.py
git commit -m "refactor(phase-1): remove _build_review_context and cleanup_browser call sites from agent.py"
```

CRITICAL: Do NOT use a blunt `sed -i '/_build_review_context/d'` — that would delete random lines containing the string but not entire method blocks. Use the Edit tool with concrete before/after blocks read from the current file.

If `python -c "import heretek.agent"` fails after editing: the edit broke indentation or left orphaned lines. Re-read the file and fix before committing.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && ! grep -q "_build_review_context" heretek/agent.py && ! grep -q "cleanup_browser" heretek/agent.py && ! grep -q "from heretek.review" heretek/agent.py && ! grep -q "from heretek.tools.browser" heretek/agent.py && python -c "import heretek.agent" && git log --oneline -1 | grep -q "remove _build_review_context"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "_build_review_context" /Users/evgeniy/Projects/140526_heretek/heretek/agent.py` exits non-zero (no matches)
    - `grep -n "cleanup_browser" /Users/evgeniy/Projects/140526_heretek/heretek/agent.py` exits non-zero (no matches)
    - `grep -n "from heretek.review" /Users/evgeniy/Projects/140526_heretek/heretek/agent.py` exits non-zero
    - `grep -n "from heretek.tools.browser" /Users/evgeniy/Projects/140526_heretek/heretek/agent.py` exits non-zero
    - `python -c "import heretek.agent"` exits 0
    - `python -c "from heretek.agent import *"` exits 0 (no module-level eval errors)
    - `git log --oneline -1` contains substring `remove _build_review_context`
    - The file still contains `def handle_task` (this method is the orchestrator entry; we removed call sites inside it, not the method itself): `grep -q "def handle_task" heretek/agent.py` exits 0
  </acceptance_criteria>
  <done>Lazy-import call sites for the deleted review and browser modules are gone from agent.py; the file imports cleanly; orchestrator's `handle_task` method survives with the review-branch and browser-cleanup logic excised.</done>
</task>

<task type="auto">
  <name>Task 3: Strip cloud-LLM env var loaders from llm.py and prune requirements.txt</name>
  <files>
    heretek/llm.py,
    requirements.txt
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/heretek/llm.py (READ FULLY — find every os.environ.get for OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, and the HTTP-Referer / X-Title custom headers)
    - /Users/evgeniy/Projects/140526_heretek/requirements.txt (READ — confirm what's currently listed)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Stripping strategy — legacy cloud env-var loading: strip loading code entirely, no startup warnings, silent ignore)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 1: Ollama LLM Client Patch — the patched __init__ keeps base_url and api_key parameterized; Pitfall 4: OpenRouter HTTP in update_budget_from_usage)
    - `rg -n "httpx" /Users/evgeniy/Projects/140526_heretek/heretek/ /Users/evgeniy/Projects/140526_heretek/supervisor/ 2>/dev/null` — confirm whether anything besides the now-deleted review.py imports httpx
  </read_first>
  <action>
This task does NOT yet patch llm.py to point at Ollama (that's Plan 04). It ONLY strips the cloud-env-var loading code so a `grep -q "OPENROUTER_API_KEY" heretek/llm.py` returns nothing. Plan 04 will then write the new Ollama init code on a clean canvas.

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Locate all cloud-env-var references in heretek/llm.py
grep -n "OPENROUTER_API_KEY\|OPENAI_API_KEY\|ANTHROPIC_API_KEY" heretek/llm.py
grep -n "HTTP-Referer\|X-Title\|openrouter.ai" heretek/llm.py
```

Step 2: Edit `heretek/llm.py`:

(a) **Remove every `os.environ.get("OPENROUTER_API_KEY", ...)` line.** Replace the assignment with nothing if the variable is no longer used, or with a placeholder that Plan 04 will overwrite. Example transformation:

Before:
```python
def __init__(self, api_key=None, base_url="https://openrouter.ai/api/v1"):
    self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    self._base_url = base_url
```

After (in this task — Plan 04 will fully rewrite to Ollama-shaped defaults):
```python
def __init__(self, api_key=None, base_url=None):
    # Cloud LLM env vars intentionally not read - Heretek is local-only.
    # Plan 04 will populate the Ollama defaults here.
    self._api_key = api_key or ""
    self._base_url = base_url or ""
```

(b) **Remove OPENAI_API_KEY and ANTHROPIC_API_KEY reads** wherever they appear (likely in a fallback chain or `available_models()` function).

(c) **Remove the custom OpenRouter headers** (`HTTP-Referer`, `X-Title`) from the OpenAI client construction. They were OpenRouter-specific and meaningless for Ollama.

(d) **DO NOT touch:** the `LLMClient` class definition itself, the `chat()` method body, `available_models()`'s function signature, or anything else. Plan 04 owns those. This task is a surgical strip.

(e) **DO NOT add warnings.** The CONTEXT.md decision is explicit: "If those vars are still in someone's environment, they do nothing — silent ignore. No startup warnings, no hard errors."

Step 3: Verify imports still work:
```bash
python -c "import heretek.llm; print('OK')"
# Expected: prints OK (the module imports fine even if LLMClient.__init__ now has empty defaults)
```

Step 4: Strip playwright and httpx (if applicable) from requirements.txt:
```bash
# Check current state
cat requirements.txt

# Remove playwright and playwright-stealth (tools/browser.py is deleted)
sed -i.bak -e '/^playwright/d' -e '/^playwright-stealth/d' requirements.txt && rm -f requirements.txt.bak

# Check if anything besides deleted tools/review.py imports httpx
HTTPX_USERS=$(rg -l "import httpx\|from httpx" heretek/ supervisor/ scripts/ 2>/dev/null)
if [ -z "$HTTPX_USERS" ]; then
  echo "httpx has no remaining users — removing from requirements.txt"
  sed -i.bak -e '/^httpx/d' requirements.txt && rm -f requirements.txt.bak
else
  echo "httpx still used by: $HTTPX_USERS — leaving in requirements.txt"
fi
```

Step 5: Re-verify nothing depends on the removed deps:
```bash
python -c "import heretek; import heretek.llm; import heretek.tools; print('OK')"
```

Step 6: Commit:
```bash
git add heretek/llm.py requirements.txt
git commit -m "refactor(phase-1): strip cloud LLM env loaders and unused deps (playwright, httpx)"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && ! grep -q "OPENROUTER_API_KEY" heretek/llm.py && ! grep -q "OPENAI_API_KEY" heretek/llm.py && ! grep -q "ANTHROPIC_API_KEY" heretek/llm.py && ! grep -q "HTTP-Referer" heretek/llm.py && ! grep -q "X-Title" heretek/llm.py && ! grep -q "openrouter.ai" heretek/llm.py && python -c "import heretek.llm" && ! grep -q "^playwright" requirements.txt && git log --oneline -1 | grep -q "strip cloud LLM"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "OPENROUTER_API_KEY" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `grep -q "OPENAI_API_KEY" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `grep -q "ANTHROPIC_API_KEY" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `grep -q "HTTP-Referer" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `grep -q "X-Title" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `grep -q "openrouter.ai" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits non-zero
    - `python -c "import heretek.llm"` exits 0
    - `python -c "import heretek; import heretek.agent; import heretek.llm"` exits 0
    - `grep -q "^playwright" /Users/evgeniy/Projects/140526_heretek/requirements.txt` exits non-zero
    - `grep -q "^playwright-stealth" /Users/evgeniy/Projects/140526_heretek/requirements.txt` exits non-zero
    - If httpx had no remaining users: `grep -q "^httpx" requirements.txt` exits non-zero; else: at least one file under heretek/ or supervisor/ matches `rg -l "import httpx\|from httpx"`
    - The class definition is preserved: `grep -q "class LLMClient" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - The chat method is preserved: `grep -q "def chat" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `git log --oneline -1` contains substring `strip cloud LLM`
  </acceptance_criteria>
  <done>Cloud-LLM env var loaders silently gone from llm.py; OpenRouter custom headers removed; playwright (and httpx if unused) removed from requirements.txt; LLMClient class and chat method preserved for Plan 04 to patch. No startup warnings; silent ignore as decided.</done>
</task>

<task type="auto">
  <name>Task 4: Flip test_no_cloud_hosts SKIP to real assertion</name>
  <files>scripts/smoke_test.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py (current state — test_package_rename PASS, test_no_cloud_hosts and test_bilingual_ollama_reply still SKIP)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md (§Per-Task Verification Map — LLM-01 and LLM-05 covered by test_no_cloud_hosts)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 5: Smoke Test via handle_chat_direct — reference grep pattern)
  </read_first>
  <action>
Replace the body of `test_no_cloud_hosts` in `/Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` with the real assertion. The function must scan all `.py` files under `heretek/` and `supervisor/` for cloud-host substrings and cloud-LLM env-var names. Any hit = FAIL.

```python
def test_no_cloud_hosts() -> str:
    """LLM-01 + LLM-05 verification: no cloud-LLM host strings or env var
    names anywhere in the heretek/ or supervisor/ source trees.
    """
    import re
    from pathlib import Path

    pattern = re.compile(
        r"openrouter\.ai|api\.openai\.com|api\.anthropic\.com|"
        r"OPENROUTER_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY"
    )
    hits: list[str] = []
    for root in ("heretek", "supervisor"):
        root_path = Path(root)
        if not root_path.exists():
            continue
        for path in root_path.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"  {path}:{i}: {line.strip()}")

    if hits:
        print(f"{FAIL} test_no_cloud_hosts: cloud LLM references found:")
        for h in hits:
            print(h)
        return "fail"
    print(f"{PASS} test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/")
    return "pass"
```

Then run static-only smoke test to confirm:
```bash
cd /Users/evgeniy/Projects/140526_heretek
python scripts/smoke_test.py --static-only
# Expected:
#   [PASS] test_package_rename: ...
#   [PASS] test_no_cloud_hosts: no cloud LLM references...
#   Summary: 2 pass · 0 fail · 0 skip · 2 total
# Exit 0
```

If the test FAILs because some file under heretek/ or supervisor/ still mentions an OpenRouter URL or env var: that's a leak from Plan 03 Task 3. Fix the source file (or update the strip task) before flipping the test. Do NOT loosen the regex.

Commit:
```bash
git add scripts/smoke_test.py
git commit -m "test(phase-1): flip test_no_cloud_hosts SKIP to real check (LLM-01, LLM-05, partial)"
```

Note: This test is "partial" coverage of LLM-01/LLM-05 — it asserts the static surface is clean. Plan 04 fully implements the LLM swap and adds the runtime assertion to test_bilingual_ollama_reply. The static check here is exactly the "no cloud calls" verification per CONTEXT.md §Smoke test rigor.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && python scripts/smoke_test.py --static-only 2>&1 | grep -q "\[PASS\] test_no_cloud_hosts" && python scripts/smoke_test.py --static-only 2>&1 | grep -q "Summary: 2 pass" && python scripts/smoke_test.py --static-only; test $? -eq 0</automated>
  </verify>
  <acceptance_criteria>
    - `python scripts/smoke_test.py --static-only` stdout contains the literal string `[PASS] test_no_cloud_hosts`
    - `python scripts/smoke_test.py --static-only` stdout contains `Summary: 2 pass · 0 fail · 0 skip · 2 total` (test_bilingual_ollama_reply not run under --static-only)
    - `python scripts/smoke_test.py --static-only` exits 0
    - `python scripts/smoke_test.py` (no flag) stdout contains 2 PASS + 1 SKIP (bilingual still pending Plan 05)
    - `grep -q "openrouter\\\\.ai" scripts/smoke_test.py` exits 0 (the regex is in the test code itself, which is acceptable since the regex is bracketed in `re.compile(r"...")`)
    - Side check: the test code's own regex literal is excluded from being a self-match — confirm by running the test on a tree containing the test itself; expected PASS. (The implementation only scans `heretek/` and `supervisor/`, not `scripts/`, so the test's own regex is not in scope.)
    - `! grep -q "return \"skip\"" scripts/smoke_test.py | head -1` — verify by inspecting that test_no_cloud_hosts no longer returns "skip"
    - `git log --oneline -1` contains substring `flip test_no_cloud_hosts`
  </acceptance_criteria>
  <done>test_no_cloud_hosts now does a real recursive grep of heretek/ and supervisor/ for cloud-LLM strings; passes on the current tree post-strip; only test_bilingual_ollama_reply remains in SKIP state (owned by Plan 05).</done>
</task>

</tasks>

<verification>
After all tasks:
1. Four target modules gone: `test ! -f heretek/tools/github.py && test ! -f heretek/tools/review.py && test ! -f heretek/tools/browser.py && test ! -f heretek/review.py`
2. agent.py free of `_build_review_context` and `cleanup_browser`
3. llm.py free of OPENROUTER_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY / HTTP-Referer / X-Title / openrouter.ai
4. requirements.txt free of playwright, playwright-stealth, and (conditionally) httpx
5. `python -c "import heretek; import heretek.agent; import heretek.llm; import heretek.tools"` exits 0
6. `python scripts/smoke_test.py --static-only` exits 0 with 2 PASS, 0 FAIL, 0 SKIP
</verification>

<success_criteria>
- FORK-03 fully implemented: github/review/browser tools + multi-model orchestrator deleted
- Lazy-import dead code in agent.py removed (research-confirmed call sites)
- Cloud-LLM env var loaders stripped silently from llm.py (no warnings, no errors)
- requirements.txt trimmed
- test_no_cloud_hosts flipped to real check, currently green
- All four commits on playground
</success_criteria>

<output>
After completion, create `/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-03-SUMMARY.md` documenting:
- The exact contents of agent.py blocks removed (paste before/after diffs)
- The exact contents of llm.py blocks removed
- Final requirements.txt diff
- Confirmation that the test_no_cloud_hosts regex matches no source lines (paste the full stdout of `python scripts/smoke_test.py --static-only`)
- Whether httpx remained in requirements (yes/no, and the reason)
</output>
