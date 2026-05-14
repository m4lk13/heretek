---
phase: 01-foundation-local-llm
plan: 02
type: execute
wave: 2
depends_on:
  - "01"
files_modified:
  - ouroboros/  # entire tree renamed to heretek/
  - heretek/  # destination (post-rename)
  - supervisor/__main__.py
  - pyproject.toml
  - setup.py
  - setup.cfg
  - requirements.txt
  - colab_launcher.py
  - scripts/smoke_test.py  # flip test_package_rename SKIP to real
autonomous: true
requirements:
  - FORK-02
  - LLM-06  # entry point (python -m supervisor) is half of LLM-06's gate
must_haves:
  truths:
    - "python -c 'import heretek' succeeds from the project root"
    - "python -c 'import ouroboros' fails with ModuleNotFoundError"
    - "python -m supervisor --help (or equivalent) launches without ImportError"
    - "No file under heretek/, supervisor/, or tools/ contains the literal string 'ouroboros' in its Python source (case-sensitive)"
    - "scripts/smoke_test.py test_package_rename returns PASS"
  artifacts:
    - path: "heretek/"
      provides: "Renamed Python package (was ouroboros/)"
      contains: "__init__.py"
    - path: "heretek/llm.py"
      provides: "LLM client (still upstream code; patched in Plan 04)"
      contains: "OPENROUTER_API_KEY"
    - path: "supervisor/__main__.py"
      provides: "Local CLI entry point for python -m supervisor"
      min_lines: 10
    - path: "pyproject.toml"
      provides: "Package name updated to 'heretek'"
      contains: "heretek"
  key_links:
    - from: "heretek/tools/*.py"
      to: "heretek.tools.registry"
      via: "from heretek.tools.registry import ToolContext, ToolEntry"
      pattern: "from heretek\\.tools\\.registry import"
    - from: "supervisor/__main__.py"
      to: "supervisor.workers (or supervisor's existing entry function)"
      via: "import supervisor.workers; supervisor.workers.run() or equivalent"
      pattern: "from supervisor"
---

<objective>
Rename the upstream `ouroboros/` Python package to `heretek/`, replace every `ouroboros` reference in source/config files with `heretek`, and author `supervisor/__main__.py` so `python -m supervisor` becomes the local boot command (replacing upstream's Colab-specific `colab_launcher.py`).

Purpose: Every downstream task imports `heretek.something`. Without the rename, the strip plan (Plan 03) and the LLM swap plan (Plan 04) cannot touch the right files. The supervisor entry point is also load-bearing — Phase 1 Success Criterion 2 requires `python -m supervisor` to work.

Output: A renamed package where `import heretek` succeeds, `import ouroboros` fails, all intra-package imports resolve, and `python -m supervisor` boots without ImportError. The smoke test's `test_package_rename` subtest is flipped from SKIP to PASS.
</objective>

<execution_context>
@/Users/evgeniy/.claude/get-shit-done/workflows/execute-plan.md
@/Users/evgeniy/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/evgeniy/Projects/140526_heretek/.planning/PROJECT.md
@/Users/evgeniy/Projects/140526_heretek/.planning/ROADMAP.md
@/Users/evgeniy/Projects/140526_heretek/.planning/STATE.md
@/Users/evgeniy/Projects/140526_heretek/.planning/REQUIREMENTS.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-01-SUMMARY.md

<interfaces>
Key upstream files this plan touches (post-fork in Plan 01). Executor should read these files directly to confirm signatures before editing.

Upstream package root files:
- ouroboros/__init__.py
- ouroboros/agent.py
- ouroboros/consciousness.py
- ouroboros/context.py
- ouroboros/llm.py
- ouroboros/loop.py
- ouroboros/memory.py
- ouroboros/review.py  (will be deleted in Plan 03 — but the import sweep here must not break)
- ouroboros/tools/__init__.py
- ouroboros/tools/registry.py  (defines ToolContext, ToolEntry, _load_modules using pkgutil)
- ouroboros/tools/*.py  (each imports: `from ouroboros.tools.registry import ToolContext, ToolEntry`)

Supervisor:
- supervisor/__init__.py
- supervisor/state.py
- supervisor/workers.py  (exposes handle_chat_direct(chat_id, text, image_data=None))
- supervisor/telegram.py, queue.py, events.py, git_ops.py

Upstream entry point (Colab-only, will be replaced):
- colab_launcher.py  (Google Colab bootstrap — sets env, calls supervisor's start function)

Note: supervisor/__main__.py does NOT exist at v6.2.0 (research finding 5). This plan creates it.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rename ouroboros/ to heretek/ and sweep all references</name>
  <files>
    ouroboros/ (renamed to heretek/),
    pyproject.toml,
    setup.py,
    setup.cfg,
    requirements.txt,
    colab_launcher.py,
    supervisor/*.py,
    heretek/**/*.py
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pitfall 2: pkgutil.iter_modules uses physical path; §Open Questions 3; §Code Examples — Package Rename Sweep Commands)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Stripping strategy — all imports updated in same commit chain; no dangling references)
    - Output of: `cd /Users/evgeniy/Projects/140526_heretek && rg -l "ouroboros" --type-add 'cfg:*.cfg' --type-add 'toml:*.toml' -t py -t toml -t cfg -t txt`
    - Output of: `cat /Users/evgeniy/Projects/140526_heretek/pyproject.toml` (current package metadata)
  </read_first>
  <action>
Execute the rename as a single commit so the tree is never in a half-renamed state. Use git's rename detection (git mv) and a bulk perl sweep.

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Generate the definitive hit list BEFORE the rename
rg -l "ouroboros" --type-add 'toml:*.toml' --type-add 'cfg:*.cfg' -t py -t toml -t cfg -t txt > /tmp/heretek-rename-hits.txt
echo "Files containing 'ouroboros':"
cat /tmp/heretek-rename-hits.txt

# Step 2: Rename the directory
git mv ouroboros heretek

# Step 3: Bulk replace 'ouroboros' to 'heretek' in all source/config files
# macOS-safe (perl -pi -e works identically on macOS and Linux):
xargs -I{} perl -pi -e 's/ouroboros/heretek/g' {} < /tmp/heretek-rename-hits.txt

# Step 4: Re-grep — must be zero hits in source/config (matches inside .planning/ and CLAUDE.md are fine and must be preserved)
REMAINING=$(rg -l "ouroboros" --type-add 'toml:*.toml' --type-add 'cfg:*.cfg' -t py -t toml -t cfg -t txt 2>/dev/null || true)
if [ -n "$REMAINING" ]; then
  echo "FAIL: ouroboros still in: $REMAINING"
  exit 1
fi

# Step 5: Clear stale bytecode
find . -path ./.git -prune -o -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -path ./.git -prune -o -type f -name "*.pyc" -delete 2>/dev/null || true

# Step 6: Sanity check the imports resolve. Use a venv if one is available; otherwise system Python.
# Note: colab_launcher.py may have undeclared deps (google.colab, etc) — DO NOT exec it.
# Just verify package import works at module level.
python -c "import heretek; print('OK:', heretek.__name__)"
python -c "import heretek.tools; print('OK:', heretek.tools.__name__)"
python -c "import heretek.tools.registry; print('OK:', heretek.tools.registry.__name__)"
# This MUST succeed:
python -c "import ouroboros" 2>&1 | grep -q "ModuleNotFoundError" && echo "OK: ouroboros gone"

# Step 7: Commit
git add -A
git commit -m "refactor(phase-1): rename ouroboros package to heretek"
```

CRITICAL constraints for the rename sweep:
- The grep MUST exclude `.planning/` and `CLAUDE.md` from the rename — those documents reference the original upstream repo (razzant/ouroboros) by NAME and that is correct historical context. The `rg -t py -t toml -t cfg -t txt` filter handles this because `.planning/*.md` is type `md`, not in the filter set. If the executor accidentally widens the type filter, planning docs will be corrupted.
- If `python -c "import heretek"` fails: the rename is incomplete. Look for remaining `ouroboros` strings in dotfiles or files with unusual extensions. Add to the sweep and retry. Do NOT commit until imports resolve.
- If a file inside `heretek/` literally contains the word "ouroboros" as a string in user-facing copy (e.g., a tool description "Ouroboros's introspection tool") — the perl sweep already replaces it with "heretek". That is correct: the bot's identity is changing.
- If `requirements.txt` lists a package literally named `ouroboros` (extremely unlikely): leave that line alone — it would be an external dep, not our package. Manually inspect after the sweep and restore if so.
- If `pyproject.toml` declares `name = "ouroboros"` it must become `name = "heretek"` (the perl sweep handles this).
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && test -d heretek && test ! -d ouroboros && python -c "import heretek; import heretek.tools; import heretek.tools.registry" && python -c "import ouroboros" 2>&1 | grep -q ModuleNotFoundError && ! rg -q "ouroboros" --type-add 'toml:*.toml' --type-add 'cfg:*.cfg' -t py -t toml -t cfg -t txt && grep -q "ouroboros" CLAUDE.md && grep -q "ouroboros" .planning/PROJECT.md</automated>
  </verify>
  <acceptance_criteria>
    - `test -d /Users/evgeniy/Projects/140526_heretek/heretek` exits 0
    - `test ! -d /Users/evgeniy/Projects/140526_heretek/ouroboros` exits 0 (old directory gone)
    - `python -c "import heretek"` exits 0
    - `python -c "import heretek.tools"` exits 0
    - `python -c "import heretek.tools.registry"` exits 0
    - `python -c "import ouroboros"` exits non-zero with stderr containing `ModuleNotFoundError`
    - `rg -q "ouroboros" --type-add 'toml:*.toml' --type-add 'cfg:*.cfg' -t py -t toml -t cfg -t txt` exits non-zero (no hits in source/config files)
    - `grep -q "ouroboros" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits 0 (historical references preserved)
    - `grep -q "ouroboros" /Users/evgeniy/Projects/140526_heretek/.planning/PROJECT.md` exits 0 (planning references preserved)
    - `git log --oneline -1` contains substring `rename ouroboros package to heretek`
    - `git diff HEAD~1 HEAD --stat` shows rename detection (`{ouroboros => heretek}/...` lines)
  </acceptance_criteria>
  <done>Package successfully renamed; all intra-package imports resolve to `heretek.*`; old package name removed from source/config but preserved in planning docs and CLAUDE.md as historical references.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Author supervisor/__main__.py for local CLI entry point</name>
  <files>supervisor/__main__.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/colab_launcher.py (READ FULLY — this is the upstream boot sequence we are replacing; we want to keep what is local-friendly and drop what is Colab/Drive/OpenRouter-specific)
    - /Users/evgeniy/Projects/140526_heretek/supervisor/__init__.py (READ — may already export a `main()`, `start()`, or `run()` function; if so, __main__.py just delegates to it)
    - /Users/evgeniy/Projects/140526_heretek/supervisor/workers.py (READ — workers.run() or similar may be the actual boot loop)
    - /Users/evgeniy/Projects/140526_heretek/supervisor/state.py (READ — to understand any state init the entry point must trigger)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§State of the Art — colab_launcher is deprecated; §Open Questions 1 — supervisor/__main__.py likely does not exist at v6.2.0)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Smoke test rigor — `python -m supervisor` is the boot command)
  </read_first>
  <action>
Create `/Users/evgeniy/Projects/140526_heretek/supervisor/__main__.py` so that `python -m supervisor` boots the local Heretek runtime. Logic:

1. First read `colab_launcher.py` and `supervisor/__init__.py` and `supervisor/workers.py` to identify the existing boot entry point. Typical patterns:
   - `colab_launcher.py` calls something like `from supervisor.workers import run_supervisor; run_supervisor()` or `import supervisor; supervisor.start()`.
   - The actual function name is upstream-dependent. Identify it by reading.

2. Replicate that boot sequence in `__main__.py`, stripping:
   - Any `google.colab` imports
   - Any Google Drive mounting
   - Any OpenRouter API-key fetching from Colab secrets
   - Any cloud-LLM env setup

3. Add `python-dotenv` loading at the top so `.env` is read before any module that needs env vars imports.

Template (adapt to actual upstream function name discovered in step 1):

```python
#!/usr/bin/env python3
"""supervisor/__main__.py - Local CLI entry point for Heretek.

Replaces upstream's colab_launcher.py (Google Colab bootstrap). For local
macOS use: loads .env, then dispatches to the supervisor's actual boot
function. Run via:

    python -m supervisor              # boot in normal mode
    python -m supervisor --help       # print usage

Note: The supervisor boot function name is whatever upstream exports. As of
v6.2.0 it's typically supervisor.workers.run_supervisor() OR
supervisor.start() — confirm by reading colab_launcher.py before editing.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_env() -> None:
    """Load .env file if python-dotenv is available; otherwise rely on shell env."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "[supervisor] python-dotenv not installed; skipping .env load. "
            "Run: pip install python-dotenv",
            file=sys.stderr,
        )
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[supervisor] loaded {env_path}")
    else:
        print(f"[supervisor] no .env at {env_path}; using shell environment only")


def _print_banner() -> None:
    primary = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
    light = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    print(f"[supervisor] starting heretek; primary={primary} light={light} base={base}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m supervisor",
        description="Heretek supervisor - local boot entry point",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the smoke test handler instead of the full Telegram loop",
    )
    args = parser.parse_args(argv)

    _load_env()
    _print_banner()

    if args.smoke:
        # Used by scripts/smoke_test.py in Plan 05 - imports handle_chat_direct
        # without spinning up Telegram polling.
        from supervisor import workers  # noqa: F401  side-effect: registers handlers
        print("[supervisor] smoke mode: handlers loaded, exiting without starting Telegram loop")
        return 0

    # Boot the actual supervisor. The exact function name is upstream-dependent;
    # the executor must discover it. Common candidates (try in order, first match wins):
    #   from supervisor.workers import run_supervisor; run_supervisor()
    #   from supervisor import start; start()
    #   from supervisor.workers import main as workers_main; workers_main()
    # Replace this block with the actual call after reading the upstream code.
    try:
        from supervisor.workers import run_supervisor as _entry  # PLACEHOLDER
    except ImportError:
        try:
            from supervisor import start as _entry  # PLACEHOLDER
        except ImportError:
            print(
                "[supervisor] FATAL: could not locate boot entry. "
                "Read colab_launcher.py and wire the correct call.",
                file=sys.stderr,
            )
            return 2

    _entry()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

IMPORTANT: The executor must read `colab_launcher.py` and find the actual boot function name. The PLACEHOLDER imports above are guesses. Replace them with the real name discovered by reading. If colab_launcher.py uses something like `supervisor.workers.run_supervisor`, the import in __main__.py must match exactly.

Add `python-dotenv` to requirements.txt if not already present:
```bash
cd /Users/evgeniy/Projects/140526_heretek
grep -q "python-dotenv" requirements.txt 2>/dev/null || echo "python-dotenv>=1.0.0" >> requirements.txt
```

Then commit:
```bash
git add supervisor/__main__.py requirements.txt
git commit -m "feat(phase-1): add supervisor/__main__.py local CLI entry point"
```

Note: This task does NOT need to actually BOOT the Telegram loop end-to-end. The acceptance criteria only require `python -m supervisor --help` to exit 0 (proves the module is importable and argparse runs). Full boot is exercised in Plan 05 smoke test.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && test -f supervisor/__main__.py && python -m supervisor --help 2>&1 | grep -q "Heretek supervisor" && grep -q "python-dotenv" requirements.txt && python -c "import supervisor.__main__"</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/evgeniy/Projects/140526_heretek/supervisor/__main__.py` exits 0
    - `python -m supervisor --help` exits 0 and stdout contains the string `Heretek supervisor`
    - `python -m supervisor --help` stdout contains the string `--smoke`
    - `grep -q "python-dotenv" /Users/evgeniy/Projects/140526_heretek/requirements.txt` exits 0
    - `python -c "import supervisor.__main__"` exits 0 (module imports without error at parse time)
    - `grep -q "def main" /Users/evgeniy/Projects/140526_heretek/supervisor/__main__.py` exits 0
    - `grep -q "load_dotenv" /Users/evgeniy/Projects/140526_heretek/supervisor/__main__.py` exits 0
    - The file is NOT a verbatim copy of `colab_launcher.py` — verify by: `! diff -q supervisor/__main__.py colab_launcher.py 2>/dev/null`
    - The file contains NO references to `google.colab`, `drive`, or `OPENROUTER`: `! grep -qE "google\\.colab|/content/drive|OPENROUTER" supervisor/__main__.py`
    - `git log --oneline -1` contains substring `__main__.py`
  </acceptance_criteria>
  <done>Module-level entry point exists; `python -m supervisor --help` runs and prints usage; .env loading wired; dotenv added to requirements; placeholder imports either real or clearly flagged for Plan 03/04 follow-up. Telegram-loop boot is intentionally not tested here — that gates on Plan 04's LLM swap.</done>
</task>

<task type="auto">
  <name>Task 3: Flip test_package_rename SKIP to real assertion</name>
  <files>scripts/smoke_test.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py (current SKIP-returning stub from Plan 01)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md (§Wave 0 Requirements — test_package_rename owns FORK-02)
  </read_first>
  <action>
Edit `/Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py`. Replace the body of `test_package_rename` with the real assertion:

```python
def test_package_rename() -> str:
    """FORK-02 verification: import heretek succeeds; import ouroboros fails."""
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    try:
        import heretek  # noqa: F401
    except ImportError as e:
        print(f"{FAIL} test_package_rename: `import heretek` raised: {e}")
        return "fail"
    try:
        import ouroboros  # noqa: F401
    except ImportError:
        print(f"{PASS} test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected")
        return "pass"
    print(f"{FAIL} test_package_rename: `import ouroboros` still succeeds — rename incomplete")
    return "fail"
```

(The PASS/FAIL constants are defined at module scope in the scaffold from Plan 01; keep them there. The local re-definition inside the function is just for clarity in the snippet above — the executor may remove the local lines if module-scope constants are already in scope, which they are. Cleanly: just `print(f"{PASS} ...")` and `print(f"{FAIL} ...")`.)

Then run the static-only smoke test to confirm:
```bash
cd /Users/evgeniy/Projects/140526_heretek
python scripts/smoke_test.py --static-only
# Expected: test_package_rename PASS; test_no_cloud_hosts SKIP; exit 0
```

Commit:
```bash
git add scripts/smoke_test.py
git commit -m "test(phase-1): flip test_package_rename SKIP to real check (FORK-02)"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && python scripts/smoke_test.py --static-only 2>&1 | grep -q "\[PASS\] test_package_rename" && python scripts/smoke_test.py --static-only 2>&1 | grep -q "\[SKIP\] test_no_cloud_hosts" && python scripts/smoke_test.py --static-only; test $? -eq 0</automated>
  </verify>
  <acceptance_criteria>
    - `python scripts/smoke_test.py --static-only` stdout contains the literal line `[PASS] test_package_rename: import heretek OK; import ouroboros raises ModuleNotFoundError as expected`
    - `python scripts/smoke_test.py --static-only` stdout contains `[SKIP] test_no_cloud_hosts` (still SKIP — Plan 03/04 flips it)
    - `python scripts/smoke_test.py --static-only` exits 0
    - `python scripts/smoke_test.py --static-only` stdout summary line is `Summary: 1 pass · 0 fail · 1 skip · 2 total`
    - `grep -q "return \"skip\"" scripts/smoke_test.py | wc -l` — the file still has skip returns for the other two tests
    - `! grep -A2 "def test_package_rename" scripts/smoke_test.py | grep -q "not yet implemented"` (the SKIP placeholder text is gone from test_package_rename's body)
    - `git log --oneline -1` contains substring `flip test_package_rename`
  </acceptance_criteria>
  <done>test_package_rename is now a real PASS-or-FAIL check; the smoke test scaffold is on track to flip remaining SKIPs in Plans 03/04/05.</done>
</task>

</tasks>

<verification>
After all tasks:
1. `python -c "import heretek"` exits 0
2. `python -c "import ouroboros"` fails with ModuleNotFoundError
3. `python -m supervisor --help` exits 0 and prints `Heretek supervisor` usage
4. `python scripts/smoke_test.py --static-only` exits 0 with `test_package_rename PASS` and `test_no_cloud_hosts SKIP`
5. No `ouroboros` string remains in `.py`/`.toml`/`.cfg`/`.txt` files under the project root (except .planning/, CLAUDE.md preserved)
6. Three commits land on playground: rename, __main__, smoke-test-flip
</verification>

<success_criteria>
- FORK-02 fully implemented: heretek package importable, ouroboros removed
- supervisor/__main__.py exists and is importable; --help works
- python-dotenv added to requirements.txt
- Smoke test test_package_rename: SKIP to PASS
- All commits on playground
</success_criteria>

<output>
After completion, create `/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-02-SUMMARY.md` documenting:
- The exact list of files modified by the rename sweep (`git diff HEAD~3 HEAD --stat`)
- The actual boot function name discovered in `colab_launcher.py` and wired into `__main__.py`
- Confirmation that `python -m supervisor --help` works
- Any unexpected `ouroboros` strings encountered (e.g., in user-facing copy) and how they were handled
- The output of `python scripts/smoke_test.py --static-only` (full stdout)
</output>
