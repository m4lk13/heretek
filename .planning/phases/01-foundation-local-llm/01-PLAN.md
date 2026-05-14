---
phase: 01-foundation-local-llm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .git/config
  - .gitignore
  - scripts/smoke_test.py
autonomous: true
requirements:
  - FORK-01
user_setup:
  - service: github
    why: "Forking upstream razzant/ouroboros to <owner>/heretek requires authenticated GitHub CLI session"
    env_vars: []
    dashboard_config:
      - task: "Authenticate gh CLI"
        location: "Local terminal: gh auth status; if not logged in, gh auth login --web"
must_haves:
  truths:
    - "The project root contains the upstream Ouroboros v6.2.0 source tree (heretek/, supervisor/, tools/, etc.) alongside the existing .planning/ and CLAUDE.md"
    - "Local branch playground is checked out and contains the upstream source"
    - "Local tag last-known-good points at the upstream v6.2.0 HEAD commit"
    - "git remote -v shows origin → <user>/heretek and upstream → razzant/ouroboros"
    - "scripts/smoke_test.py exists with three named subtests that exit SKIP (2) and a --static-only flag"
  artifacts:
    - path: "supervisor/state.py"
      provides: "Inherited upstream supervisor scaffold present at project root"
      contains: "def update_budget_from_usage"
    - path: "ouroboros/llm.py"
      provides: "Inherited upstream LLM client (to be patched in Plan 04 after rename in Plan 02)"
      contains: "OPENROUTER_API_KEY"
    - path: "scripts/smoke_test.py"
      provides: "Wave 0 smoke test scaffold with SKIP stubs and --static-only flag"
      contains: "test_package_rename"
    - path: ".gitignore"
      provides: ".env, logs/, __pycache__/, .venv/ excluded"
      contains: ".env"
  key_links:
    - from: "git HEAD"
      to: "branch playground"
      via: "git checkout playground"
      pattern: "On branch playground"
    - from: "tag last-known-good"
      to: "upstream/main HEAD at fork time"
      via: "git tag last-known-good <sha>"
      pattern: "last-known-good"
---

<objective>
Establish the Git foundation for Heretek: fork razzant/ouroboros v6.2.0 to <owner>/heretek on GitHub, overlay the upstream source tree onto the existing `/Users/evgeniy/Projects/140526_heretek/` directory (which already contains `.planning/` and `CLAUDE.md` and is already a git repo at branch `master`), create `playground` and `last-known-good` branches, configure `origin` and `upstream` remotes, and ship a Wave 0 smoke test scaffold so downstream plans have a verification harness.

Purpose: This phase has nothing to strip or patch until the upstream code is locally available and on the right branch. Everything downstream depends on `playground` being checked out with Ouroboros code merged in.

Output: A git repo at `/Users/evgeniy/Projects/140526_heretek/` whose `playground` branch contains the merged contents of upstream `razzant/ouroboros@v6.2.0` plus the pre-existing `.planning/` and `CLAUDE.md`, with `last-known-good` tagged at upstream HEAD, both remotes configured, and `scripts/smoke_test.py` shipped as a SKIP-returning scaffold.
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
@/Users/evgeniy/Projects/140526_heretek/CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fork upstream and overlay source into existing repo</name>
  <files>
    .git/config
    (all upstream files merged in)
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Repo & fork workflow — locked decisions on directory overlay)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pitfall 1: gh repo fork --clone directory collision; §Open Questions 2)
    - Run `git remote -v` first — confirm no remotes set
    - Run `git status` first — confirm branch is `master` and working tree is clean
  </read_first>
  <action>
The existing directory `/Users/evgeniy/Projects/140526_heretek/` is already a git repo with branch `master`, no remotes, and contains `.planning/`, `.claude/`, `.gitignore`, `CLAUDE.md`. We must NOT `gh repo fork --clone` (would create a subdirectory). Sequence:

```bash
# Step 1: Confirm authenticated and clean state (defensive)
gh auth status                                              # must succeed
git -C /Users/evgeniy/Projects/140526_heretek status        # working tree clean expected
git -C /Users/evgeniy/Projects/140526_heretek remote -v     # must be empty

# Step 2: Fork on GitHub WITHOUT cloning
gh repo fork razzant/ouroboros --fork-name heretek --clone=false --remote=false
# Resolve <owner> from gh:
GH_USER=$(gh api user --jq .login)
echo "GH_USER=$GH_USER"

# Step 3: Wire remotes in the existing repo
cd /Users/evgeniy/Projects/140526_heretek
git remote add origin   "https://github.com/${GH_USER}/heretek.git"
git remote add upstream "https://github.com/razzant/ouroboros.git"
git remote -v   # must show origin + upstream

# Step 4: Fetch upstream's v6.2.0 tag and resolve its commit SHA
git fetch upstream --tags
UPSTREAM_SHA=$(git rev-parse v6.2.0^{commit})
echo "UPSTREAM_SHA=$UPSTREAM_SHA"

# Step 5: Merge upstream v6.2.0 content into the existing master branch as an unrelated history merge
git merge --allow-unrelated-histories -m "merge(upstream): bring in razzant/ouroboros@v6.2.0" "$UPSTREAM_SHA"
# This may produce conflicts ONLY if upstream contains a file we already have. Current local tracked files: .gitignore, CLAUDE.md, .planning/**. Upstream does NOT contain any of these, so no conflicts expected.
# If a .gitignore conflict appears: keep BOTH — concat upstream .gitignore at end of local .gitignore. Resolve, `git add .gitignore`, `git commit -m "merge(upstream): combine .gitignore"`.

# Step 6: Create playground branch from the merged HEAD
git checkout -b playground

# Step 7: Tag last-known-good at the upstream v6.2.0 commit (NOT at the merge commit)
git tag -a last-known-good "$UPSTREAM_SHA" -m "Heretek rollback target: upstream razzant/ouroboros@v6.2.0 at fork time"

# Step 8: Confirm result
git branch --list playground master
git tag --list last-known-good
git log --oneline -3
git rev-parse last-known-good   # must equal $UPSTREAM_SHA
```

If `gh auth status` fails: the executor must stop and report — this is a user-setup gap requiring `gh auth login --web`.

If the merge produces unexpected conflicts beyond `.gitignore`: abort via `git merge --abort` and stop. Report the conflict list; do NOT force-merge.

Do NOT push to origin yet — push is deferred to Plan 05 final wrap-up (we want stripped/renamed code to be the first push, not raw upstream).
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek &amp;&amp; git rev-parse --abbrev-ref HEAD | grep -qx playground &amp;&amp; git rev-parse last-known-good &amp;&amp; git remote -v | grep -q "origin.*heretek" &amp;&amp; git remote -v | grep -q "upstream.*ouroboros" &amp;&amp; test -d supervisor &amp;&amp; test -d ouroboros &amp;&amp; test -d tools &amp;&amp; test -f ouroboros/llm.py</automated>
  </verify>
  <acceptance_criteria>
    - `git -C /Users/evgeniy/Projects/140526_heretek rev-parse --abbrev-ref HEAD` outputs exactly `playground`
    - `git -C /Users/evgeniy/Projects/140526_heretek rev-parse last-known-good` outputs a 40-char SHA (the upstream v6.2.0 commit)
    - `git -C /Users/evgeniy/Projects/140526_heretek rev-parse last-known-good` equals `git -C /Users/evgeniy/Projects/140526_heretek rev-parse v6.2.0^{commit}`
    - `git -C /Users/evgeniy/Projects/140526_heretek remote -v` contains BOTH `origin` pointing to `github.com/<user>/heretek` AND `upstream` pointing to `github.com/razzant/ouroboros`
    - `test -d /Users/evgeniy/Projects/140526_heretek/supervisor` is true
    - `test -d /Users/evgeniy/Projects/140526_heretek/ouroboros` is true (not yet renamed to heretek — that's Plan 02)
    - `test -d /Users/evgeniy/Projects/140526_heretek/tools` OR `test -d /Users/evgeniy/Projects/140526_heretek/ouroboros/tools` is true
    - `test -f /Users/evgeniy/Projects/140526_heretek/.planning/STATE.md` still true (existing planning files preserved)
    - `test -f /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` still true (existing CLAUDE.md preserved)
    - `git log --oneline -5` shows the merge commit at HEAD with message containing `merge(upstream)`
  </acceptance_criteria>
  <done>The project root is a unified working tree containing upstream Ouroboros source plus the pre-existing .planning/ and CLAUDE.md, with playground checked out, last-known-good tagged at upstream HEAD, and both remotes configured. No code stripped or renamed yet — that's Plans 02/03.</done>
</task>

<task type="auto">
  <name>Task 2: Update .gitignore for Heretek runtime artifacts</name>
  <files>.gitignore</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.gitignore (current state before changes)
    - /Users/evgeniy/Projects/140526_heretek/CLAUDE.md (§8 Environment variables — .env handling)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (Token logger design — logs/tokens.jsonl pattern)
  </read_first>
  <action>
After the upstream merge, the repo's `.gitignore` is the concatenation of the pre-existing local one and whatever upstream provides. Ensure it contains the following entries (append any missing — do not duplicate existing ones):

```
# Heretek runtime
.env
.env.local
.venv/
venv/
__pycache__/
*.pyc
*.pyo
logs/
*.jsonl
.DS_Store
node_modules/
```

Implementation: read current `.gitignore`, for each line in the block above that is NOT already a literal line in the file, append it under a `# Heretek runtime` header. If `# Heretek runtime` header already exists, only append missing entries beneath it.

Then:
```bash
git add .gitignore
git commit -m "chore(phase-1): extend .gitignore for Heretek runtime (.env, logs, venv)"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek &amp;&amp; grep -qx ".env" .gitignore &amp;&amp; grep -qx "logs/" .gitignore &amp;&amp; grep -qx "__pycache__/" .gitignore &amp;&amp; grep -qx ".venv/" .gitignore &amp;&amp; git log --oneline -1 | grep -q "extend .gitignore"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -qx ".env" .gitignore` exits 0
    - `grep -qx "logs/" .gitignore` exits 0
    - `grep -qx "__pycache__/" .gitignore` exits 0
    - `grep -qx ".venv/" .gitignore` exits 0
    - `grep -qx "*.jsonl" .gitignore` exits 0
    - `git log --oneline -1` contains the substring `extend .gitignore`
    - No duplicate lines (each entry appears exactly once): `awk 'NF' .gitignore | sort | uniq -d | wc -l` outputs `0`
  </acceptance_criteria>
  <done>.gitignore protects local secrets, logs, virtualenvs, and Python bytecode from being committed. Committed on playground.</done>
</task>

<task type="auto">
  <name>Task 3: Ship Wave 0 smoke test scaffold with SKIP stubs</name>
  <files>scripts/smoke_test.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md (§Wave 0 Requirements — exact subtest names and SKIP semantics)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 5: Smoke Test via handle_chat_direct — reference skeleton)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Smoke test rigor — PASS/FAIL per check, runnable script not pytest)
  </read_first>
  <action>
Create `/Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` (and `scripts/` directory if missing). This is the Wave 0 scaffold — each subtest currently returns SKIP (status 2) and prints a clear "not yet implemented in Plan NN" message. Downstream plans flip subtests from SKIP to a real assertion.

Exact file content:

```python
#!/usr/bin/env python3
"""scripts/smoke_test.py — Phase 1 verification harness.

Wave 0 scaffold: subtests return SKIP (exit 2) until the plan that owns the
requirement flips them to a real check.

Usage:
    python scripts/smoke_test.py                  # full suite (includes Ollama-dependent tests)
    python scripts/smoke_test.py --static-only    # static checks only (no Ollama, ~3s)

Exit codes:
    0  all subtests PASS (or all run subtests PASS with no FAIL)
    1  at least one FAIL
    2  reserved (per-subtest SKIP marker; never the final exit code)
"""
from __future__ import annotations

import argparse
import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

# Each subtest returns one of: "pass", "fail", "skip".


def test_package_rename() -> str:
    """FORK-02 verification: import heretek succeeds; import ouroboros fails.

    Owned by Plan 02 (package rename). Currently SKIP.
    """
    print(f"{SKIP} test_package_rename — not yet implemented (Plan 02 will flip this)")
    return "skip"


def test_no_cloud_hosts() -> str:
    """LLM-01 + LLM-05 verification: no openrouter.ai / api.openai.com /
    api.anthropic.com strings or cloud-LLM key references inside heretek/.

    Owned by Plan 03 (strip) + Plan 04 (LLM swap). Currently SKIP.
    """
    print(f"{SKIP} test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)")
    return "skip"


def test_bilingual_ollama_reply() -> str:
    """LLM-06 verification: RU prompt → RU reply, EN prompt → EN reply
    through heretek.llm against local Ollama. Owned by Plan 05. Currently SKIP.
    """
    print(f"{SKIP} test_bilingual_ollama_reply — not yet implemented (Plan 05 will flip this)")
    return "skip"


STATIC_SUBTESTS = [test_package_rename, test_no_cloud_hosts]
FULL_SUBTESTS = STATIC_SUBTESTS + [test_bilingual_ollama_reply]


def main() -> int:
    parser = argparse.ArgumentParser(description="Heretek Phase 1 smoke test")
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Run only static subtests (no Ollama dependency, ~3s)",
    )
    args = parser.parse_args()

    subtests = STATIC_SUBTESTS if args.static_only else FULL_SUBTESTS

    results: list[tuple[str, str]] = []
    for fn in subtests:
        outcome = fn()
        results.append((fn.__name__, outcome))

    # Summary
    n_pass = sum(1 for _, o in results if o == "pass")
    n_fail = sum(1 for _, o in results if o == "fail")
    n_skip = sum(1 for _, o in results if o == "skip")
    print()
    print(f"Summary: {n_pass} pass · {n_fail} fail · {n_skip} skip · {len(results)} total")

    # Exit 1 if any FAIL; otherwise 0 (SKIP is acceptable until plan ships)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
```

Make the script executable:
```bash
mkdir -p /Users/evgeniy/Projects/140526_heretek/scripts
# Write the file via the Write tool, not heredoc
chmod +x /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py
```

Then commit:
```bash
cd /Users/evgeniy/Projects/140526_heretek
git add scripts/smoke_test.py
git commit -m "test(phase-1): Wave 0 smoke test scaffold with SKIP stubs"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek &amp;&amp; test -x scripts/smoke_test.py &amp;&amp; python scripts/smoke_test.py --static-only 2>&amp;1 | grep -q "test_package_rename" &amp;&amp; python scripts/smoke_test.py --static-only 2>&amp;1 | grep -q "test_no_cloud_hosts" &amp;&amp; python scripts/smoke_test.py --static-only 2>&amp;1 | grep -q "Summary: 0 pass · 0 fail · 2 skip" &amp;&amp; python scripts/smoke_test.py --static-only; test $? -eq 0</automated>
  </verify>
  <acceptance_criteria>
    - `test -f /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `test -x /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0 (executable bit set)
    - `python scripts/smoke_test.py --static-only` exits with status 0 (SKIP is acceptable, no FAILs)
    - `python scripts/smoke_test.py --static-only` stdout contains the literal string `test_package_rename`
    - `python scripts/smoke_test.py --static-only` stdout contains the literal string `test_no_cloud_hosts`
    - `python scripts/smoke_test.py --static-only` stdout contains `Summary: 0 pass · 0 fail · 2 skip · 2 total`
    - `python scripts/smoke_test.py` (no flag) stdout contains all three subtest names and `Summary: 0 pass · 0 fail · 3 skip · 3 total`
    - `grep -q "def test_package_rename" scripts/smoke_test.py` exits 0
    - `grep -q "def test_no_cloud_hosts" scripts/smoke_test.py` exits 0
    - `grep -q "def test_bilingual_ollama_reply" scripts/smoke_test.py` exits 0
    - `grep -q "argparse" scripts/smoke_test.py` exits 0 (--static-only flag implemented via argparse)
    - `git log --oneline -1` contains substring `Wave 0 smoke test scaffold`
  </acceptance_criteria>
  <done>scripts/smoke_test.py exists with three SKIP-returning subtests, supports --static-only flag, is executable, and is committed on playground. Downstream plans can now flip individual subtests as features ship.</done>
</task>

</tasks>

<verification>
After all tasks:
1. `git rev-parse --abbrev-ref HEAD` outputs `playground`
2. `git rev-parse last-known-good` outputs the upstream v6.2.0 commit SHA
3. `git remote -v` shows both `origin` (heretek fork) and `upstream` (razzant/ouroboros)
4. Upstream source tree present: `ouroboros/`, `supervisor/`, `tools/` (or `ouroboros/tools/`) directories exist
5. Pre-existing `.planning/` and `CLAUDE.md` preserved
6. `.gitignore` covers .env, logs/, .venv/, __pycache__/
7. `python scripts/smoke_test.py --static-only` exits 0 with 2 SKIP results
</verification>

<success_criteria>
- playground branch checked out, last-known-good tag placed
- origin + upstream remotes configured
- Upstream Ouroboros v6.2.0 source overlaid into project root without losing .planning/ or CLAUDE.md
- Wave 0 smoke test scaffold ships with SKIP semantics and --static-only flag
- All three commits land on playground (merge, .gitignore, scripts/smoke_test.py)
</success_criteria>

<output>
After completion, create `/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-01-SUMMARY.md` documenting:
- The resolved GitHub username and the origin URL
- The exact upstream v6.2.0 commit SHA tagged as last-known-good
- Any merge conflicts encountered (expected: none, or .gitignore only)
- The result of `ls -la /Users/evgeniy/Projects/140526_heretek/` showing both pre-existing files and merged-in upstream files
- Confirmation that `python scripts/smoke_test.py --static-only` exits 0
</output>
