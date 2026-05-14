---
phase: 01-foundation-local-llm
plan: 05
type: execute
wave: 5
depends_on:
  - "04"
files_modified:
  - scripts/smoke_test.py
  - CLAUDE.md
  - .planning/STATE.md  # progress bump; orchestrator handles but we touch the Current state line
autonomous: true
requirements:
  - LLM-06
must_haves:
  truths:
    - "scripts/smoke_test.py test_bilingual_ollama_reply executes a real RU prompt and a real EN prompt against Ollama and PASSES with non-empty responses"
    - "python scripts/smoke_test.py exits 0 with 3 PASS, 0 FAIL, 0 SKIP when Ollama is running and both models are pulled"
    - "python scripts/smoke_test.py exits non-zero with a clear actionable message if either Ollama is down or a model is missing"
    - "CLAUDE.md §3 reflects the correct ~24GB primary model size (not ~20GB) and corrected headroom estimate"
    - "CLAUDE.md §6 'Current state' section accurately reflects 'Phase 1 complete — Ollama wired, bilingual smoke test green'"
  artifacts:
    - path: "scripts/smoke_test.py"
      provides: "Full end-to-end smoke test including bilingual Ollama call + model-pulled precondition"
      contains: "qwen3.6:35b-a3b-q4_K_M"
    - path: "CLAUDE.md"
      provides: "Updated architecture doc reflecting actual model size and Phase 1 completion"
      contains: "24GB"
    - path: "logs/tokens.jsonl"
      provides: "At least two JSONL records (one RU call, one EN call) from running the smoke test"
      contains: ""
  key_links:
    - from: "scripts/smoke_test.py test_bilingual_ollama_reply"
      to: "heretek.llm.LLMClient.chat()"
      via: "direct instantiation + chat() call (bypasses Telegram and supervisor worker queue)"
      pattern: "LLMClient.*chat"
    - from: "scripts/smoke_test.py"
      to: "ollama CLI (precondition check)"
      via: "subprocess.run(['ollama', 'list'])"
      pattern: "ollama.*list"
---

<objective>
Flip the final SKIP-state subtest (`test_bilingual_ollama_reply`) to a real assertion: instantiate the patched `heretek.llm.LLMClient`, call `chat()` with a RU prompt, call `chat()` with an EN prompt, assert both return non-empty responses that contain at least one character of the target script. Add a `check_models_pulled` precondition that fails loud with a `ollama pull ...` instruction if either model is missing. Update CLAUDE.md to correct the 20GB→24GB model size and to mark Phase 1 §6 status as complete.

Purpose: Phase 1 success gates on Roadmap Success Criteria 2 and 3 (`python -m supervisor` boots and Ollama responds; RU and EN both work). This plan delivers the end-to-end verification. CLAUDE.md is the canonical project doc for future-Claude — leaving stale 20GB references would mislead future planning.

Output: A green `python scripts/smoke_test.py` (when Ollama is running with both models pulled). CLAUDE.md reflects the actual model size and the current phase status. Phase 1 is complete.
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
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-04-SUMMARY.md
@/Users/evgeniy/Projects/140526_heretek/CLAUDE.md

<interfaces>
heretek.llm public surface (post-Plan-04):
- `LLMClient(api_key=None, base_url=None)` — defaults to Ollama
- `LLMClient.chat(model, messages, **kwargs)` — issues OpenAI-compat call to Ollama; returns response object with `.choices[0].message.content` and `.usage.{prompt_tokens, completion_tokens}`
- `available_models()` — returns dict with 'main', 'code', 'light' keys
- `_log_tokens(model, prompt_tokens, completion_tokens)` — JSONL appender

CLAUDE.md sections to edit (per research finding 2 and orchestrator notes):
- §0 TL;DR — if it mentions 20GB anywhere, fix to 24GB
- §2 Architecture — model size line: `~20GB on disk` → `~24GB on disk`
- §3 Why Qwen 3.6-35B-A3B specifically — `~12GB for KV cache, OS, browser tool, your other work` → `~8GB for KV cache, OS, your other work` (browser tool deleted)
- §6 Current state — flip from "Pre-Phase 0. Nothing built yet." to a Phase-1-complete summary
- §8 Environment variables — confirm `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M` matches code defaults (it already does — sanity check only)
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Flip test_bilingual_ollama_reply to real Ollama call + add models-pulled precondition</name>
  <files>scripts/smoke_test.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py (current state — test_package_rename PASS, test_no_cloud_hosts PASS, test_bilingual_ollama_reply SKIP)
    - /Users/evgeniy/Projects/140526_heretek/heretek/llm.py (post-Plan-04 — confirm LLMClient signature and chat() method shape)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Smoke test rigor — RU + EN prompts, PASS/FAIL per check, ollama list precondition with loud-fail message)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 5: Smoke Test via handle_chat_direct — reference implementation; §Code Examples — Ollama Chat Completions Request)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-VALIDATION.md (§Manual-Only Verifications — quality is subjective; smoke test only asserts that a reply was received and looks like the target language via basic char-class heuristic)
  </read_first>
  <action>
Two new behaviors in `scripts/smoke_test.py`:

**(A) Add `check_models_pulled` as a precondition that runs FIRST in the full suite (not in --static-only).** If either model is missing, print a clear instruction and the function returns "fail". Use subprocess to invoke `ollama list`.

**(B) Replace the body of `test_bilingual_ollama_reply` with a real end-to-end call** through `heretek.llm.LLMClient`. Send a RU prompt and an EN prompt. Assert each response is non-empty and contains at least one character of the target script (Cyrillic for RU, Latin for EN). This matches VALIDATION.md's "basic char-class heuristic."

Insert this code into `scripts/smoke_test.py` (replace `test_bilingual_ollama_reply`'s body; add `check_models_pulled` as a new function; update `STATIC_SUBTESTS` and `FULL_SUBTESTS` to include the precondition):

```python
import os as _os
import subprocess as _subprocess
import re as _re

OLLAMA_PRIMARY = _os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
OLLAMA_LIGHT = _os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
_CYRILLIC_RE = _re.compile(r"[Ѐ-ӿ]")
_LATIN_RE = _re.compile(r"[A-Za-z]")


def check_models_pulled() -> str:
    """Precondition for the bilingual test: both Ollama models must be pulled."""
    try:
        result = _subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        print(f"{FAIL} check_models_pulled: 'ollama' CLI not found in PATH. Install with: brew install ollama")
        return "fail"
    except _subprocess.TimeoutExpired:
        print(f"{FAIL} check_models_pulled: 'ollama list' timed out. Is the Ollama server running? Try: ollama serve")
        return "fail"

    output = result.stdout
    missing = []
    for tag in (OLLAMA_PRIMARY, OLLAMA_LIGHT):
        if tag not in output:
            missing.append(tag)
    if missing:
        print(f"{FAIL} check_models_pulled: missing models: {missing}")
        print("  Run before retrying:")
        for tag in missing:
            print(f"    ollama pull {tag}")
        return "fail"
    print(f"{PASS} check_models_pulled: both Ollama models present in `ollama list`")
    return "pass"


def test_bilingual_ollama_reply() -> str:
    """LLM-06 verification: RU prompt -> RU reply, EN prompt -> EN reply via Ollama."""
    try:
        from heretek.llm import LLMClient
    except ImportError as e:
        print(f"{FAIL} test_bilingual_ollama_reply: cannot import heretek.llm.LLMClient: {e}")
        return "fail"

    client = LLMClient()

    prompts = [
        ("RU", "ответь по-русски одним коротким предложением, без перевода", _CYRILLIC_RE),
        ("EN", "respond in one short English sentence, no translation", _LATIN_RE),
    ]

    all_pass = True
    for lang, prompt, script_re in prompts:
        try:
            response = client.chat(
                model=OLLAMA_PRIMARY,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            print(f"{FAIL} test_bilingual_ollama_reply [{lang}]: chat() raised: {type(e).__name__}: {e}")
            all_pass = False
            continue

        # The chat() return shape may be a dict, an OpenAI response object, or a tuple.
        # Try common access patterns:
        content = None
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, KeyError):
            try:
                content = response["choices"][0]["message"]["content"]
            except (TypeError, IndexError, KeyError):
                # Upstream may wrap response in (text, usage) tuple
                if isinstance(response, tuple) and response:
                    content = response[0]

        if not content:
            print(f"{FAIL} test_bilingual_ollama_reply [{lang}]: empty response")
            all_pass = False
            continue

        if not script_re.search(content):
            preview = content[:120].replace("\n", " ")
            print(f"{FAIL} test_bilingual_ollama_reply [{lang}]: reply lacks {lang} script chars: {preview!r}")
            all_pass = False
            continue

        preview = content[:120].replace("\n", " ")
        print(f"{PASS} test_bilingual_ollama_reply [{lang}]: got {len(content)} chars: {preview!r}")

    return "pass" if all_pass else "fail"


# Replace at the bottom of the file:
STATIC_SUBTESTS = [test_package_rename, test_no_cloud_hosts]
FULL_SUBTESTS = STATIC_SUBTESTS + [check_models_pulled, test_bilingual_ollama_reply]
```

CRITICAL: The exact response-access pattern depends on what `LLMClient.chat()` returns (see Plan 04's implementation). The triple-fallback (`.choices[0]...`, `["choices"][0]...`, tuple) covers the three most common upstream shapes. If the actual return value is different (e.g., a custom dataclass), update accordingly during execution. The smoke test framework otherwise is correct.

The `re.compile` patterns:
- Cyrillic: `[Ѐ-ӿ]` — Russian alphabet block
- Latin: `[A-Za-z]` — basic Latin letters

Note: a Russian reply that includes English words (e.g., a tech term) still PASSes because the test asserts "at least one Cyrillic char" — not "100% Cyrillic." This matches VALIDATION.md's "basic char-class heuristic."

Step-by-step:
```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Edit scripts/smoke_test.py via Edit tool

# Step 2: Sanity-check --static-only still passes (precondition + bilingual are full-suite only)
python scripts/smoke_test.py --static-only
# Expected: 2 PASS, 0 FAIL, 0 SKIP; exit 0

# Step 3: Run the full suite (requires Ollama + both models)
# If Ollama is running with models pulled, expect 4 PASS (rename, no-cloud, models-pulled, bilingual)
# If Ollama is not running or models missing, expect a loud FAIL with clear remediation message
python scripts/smoke_test.py
# Capture the exit code:
echo "Full suite exit: $?"

# Step 4: Commit
git add scripts/smoke_test.py
git commit -m "test(phase-1): flip test_bilingual_ollama_reply to real Ollama call + add models-pulled precondition"
```

If step 3 fails because Ollama is not running on the host: that is a USER-SETUP gap, not a code defect. The smoke test must print the actionable message; the executor records this in the SUMMARY.md but DOES NOT block the commit. Phase 1's gate is "smoke test is correct" not "smoke test passes right now on this host." If Ollama is down, the smoke test will fail and the executor should leave a note in the summary: "Ollama not running at execution time; static checks green; full suite to be retried by user with Ollama up."

If step 3 fails because the chat() response shape doesn't match any of the three fallback patterns: read the actual return shape from `heretek/llm.py` and update the access pattern. This is iteration-allowed within the task.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && grep -q "def check_models_pulled" scripts/smoke_test.py && grep -q "def test_bilingual_ollama_reply" scripts/smoke_test.py && grep -q "qwen3.6:35b-a3b-q4_K_M" scripts/smoke_test.py && grep -q "u0400-\\\\u04FF" scripts/smoke_test.py && python scripts/smoke_test.py --static-only 2>&1 | grep -q "Summary: 2 pass · 0 fail · 0 skip" && python scripts/smoke_test.py --static-only; test $? -eq 0</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "def check_models_pulled" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `grep -q "def test_bilingual_ollama_reply" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `grep -q "qwen3.6:35b-a3b-q4_K_M" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `grep -q "qwen3:4b" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `grep -q "Cyrillic\\|u0400" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0 (Cyrillic char-class regex present)
    - `grep -q "ollama pull" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0 (remediation message present)
    - `grep -q "ответь по-русски" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0 (RU prompt literal present)
    - `grep -q "from heretek.llm import LLMClient" /Users/evgeniy/Projects/140526_heretek/scripts/smoke_test.py` exits 0
    - `python scripts/smoke_test.py --static-only` exits 0 with `Summary: 2 pass · 0 fail · 0 skip · 2 total`
    - `python scripts/smoke_test.py --help 2>&1 | grep -q "static-only"` exits 0 (the --static-only flag is still wired)
    - `! grep -q "not yet implemented" scripts/smoke_test.py` (all SKIP placeholder text removed)
    - `! grep "return \"skip\"" scripts/smoke_test.py` (no functions return skip anymore)
    - `git log --oneline -1` contains substring `test_bilingual_ollama_reply`
    - Full-suite run (`python scripts/smoke_test.py`) either: (a) exits 0 with 4 PASS lines AND `logs/tokens.jsonl` has 2+ new records, OR (b) exits non-zero with a stdout message containing either `ollama pull qwen` (missing models) or `Ollama` (server-down) — both are acceptable based on host state. Record which in the SUMMARY.
  </acceptance_criteria>
  <done>Smoke test fully implements end-to-end Ollama verification; --static-only still green for fast feedback; full suite either passes (host ready) or fails with actionable remediation (host not ready); no SKIPs remain.</done>
</task>

<task type="auto">
  <name>Task 2: Update CLAUDE.md for 24GB correction and Phase 1 status</name>
  <files>CLAUDE.md</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/CLAUDE.md (FULL read — locate every reference to 20GB, ~12GB headroom, ~/code/heretek, and §6 Current state)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pitfall 6: 24GB model leaves only ~8GB headroom; §Standard Stack Models — 24GB confirmed)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Decisions — CLAUDE.md reference to ~/code/heretek is superseded; update during planning)
  </read_first>
  <action>
Three edits to `CLAUDE.md`. Use the Edit tool with exact before/after strings.

**(A) Fix model size: 20GB → 24GB everywhere**

Locate every instance of `~20GB` (and `20GB` standalone) referring to the primary model and replace with `~24GB`. Search:
```bash
grep -n "20GB\|~20" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md
```

Edits to make (verify each exists; if upstream changed slightly, adapt):
- §0 TL;DR — any 20GB mention → 24GB
- §2 Architecture diagram comment: `~20GB on disk, 3B active params/token` → `~24GB on disk, 3B active params/token`
- §3 "Why Qwen 3.6-35B-A3B specifically": `Q4_K_M fits in 20GB. Leaves ~12GB for KV cache, OS, browser tool, your other work.` → `Q4_K_M fits in 24GB. Leaves ~8GB for KV cache, OS, and your other work. (Browser tool removed in Phase 1; tighter than originally estimated.)`
- §4 Risk register, the "Disk fills" row: `20GB primary + 2.5GB background` → `24GB primary + 2.5GB background`; `Need ~30GB free` → `Need ~32GB free`

**(B) Fix the host path: `~/code/heretek` → in-place at the project root**

Search:
```bash
grep -n "~/code/heretek" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md
```

Replace each occurrence. In §5 Phase 0 the line reads something like:
```
- [ ] `git clone` the fork locally to `~/code/heretek`
```

Replace with:
```
- [x] Fork is overlaid in-place at `/Users/evgeniy/Projects/140526_heretek/` (existing planning directory was preserved; see .planning/phases/01-foundation-local-llm/01-01-SUMMARY.md)
```

(Note: This is in §5 which is the planning checklist. Mark complete items with `- [x]` where Phase 1 has shipped them.)

**(C) Update §6 Current state to reflect Phase 1 completion**

The current §6 reads:
```
## 6. Current state

**Status: Pre-Phase 0. Nothing built yet.**
```

Replace with:
```
## 6. Current state

**Status: Phase 1 complete — Foundation + Local LLM shipped.**

Last updated: 2026-05-14

What landed in Phase 1:
- Fork of razzant/ouroboros@v6.2.0 overlaid at project root; `playground` branch and `last-known-good` tag in place
- Package renamed `ouroboros/` → `heretek/`; `python -m supervisor` is the local boot command
- Hard-deleted: `tools/github.py`, `tools/review.py`, `tools/browser.py`, package-root `review.py`
- Stripped: cloud LLM env-var loaders (OPENROUTER/OPENAI/ANTHROPIC), OpenRouter HTTP drift-check in budget tracker, playwright deps
- Wired: Ollama at `http://localhost:11434/v1` with api_key=`ollama`; primary `qwen3.6:35b-a3b-q4_K_M` via `OLLAMA_MODEL`; light `qwen3:4b` via `OLLAMA_MODEL_LIGHT`; context cap `HERETEK_MAX_CONTEXT_TOKENS=32000`
- Budget tracker public shape preserved; cost zeroed; per-call token log at `logs/tokens.jsonl` (JSONL with `{ts, model, prompt_tokens, completion_tokens, total}`)
- Smoke test `scripts/smoke_test.py` covers: package rename, no cloud hosts, models pulled, bilingual RU+EN Ollama reply

What's next: Phase 2 (Persona + Identity) — author `CODEX_HERETICUS.md` and `SYSTEM.md`, prove the bot has a chaos-heretic voice and persistent memory across restarts.

When resuming:
1. Check this section first.
2. `git log --oneline -20` on `playground` for recent commits.
3. `ollama list` should show both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b`.
4. `python scripts/smoke_test.py` (or `--static-only` for fast feedback) is the phase gate.
```

Step-by-step:
```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Identify all 20GB mentions
grep -n "20GB" CLAUDE.md
grep -n "~/code/heretek" CLAUDE.md
grep -n "^## 6" CLAUDE.md

# Step 2: Apply edits via Edit tool (one Edit per logical change)

# Step 3: Verify
grep -q "24GB" CLAUDE.md && echo "OK 24GB present"
! grep -q "Pre-Phase 0" CLAUDE.md && echo "OK Phase 0 marker gone"
grep -q "Phase 1 complete" CLAUDE.md && echo "OK Phase 1 marker present"
! grep -q "~/code/heretek" CLAUDE.md && echo "OK home-dir path gone"

# Step 4: Commit
git add CLAUDE.md
git commit -m "docs(phase-1): fix model size 20GB->24GB, update path, mark Phase 1 complete"
```

Acceptance: no remaining `20GB` references that describe the primary model (CLAUDE.md may still contain unrelated mentions of 20GB in historical context — those are fine; only PRIMARY-MODEL references must be 24GB).
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && grep -q "24GB" CLAUDE.md && grep -q "Phase 1 complete" CLAUDE.md && ! grep -q "Pre-Phase 0" CLAUDE.md && ! grep -q "~/code/heretek" CLAUDE.md && grep -q "qwen3.6:35b-a3b-q4_K_M" CLAUDE.md && grep -q "OLLAMA_MODEL" CLAUDE.md</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "24GB" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits 0
    - `grep -q "Phase 1 complete" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits 0
    - `grep -q "Pre-Phase 0" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits non-zero (status updated)
    - `grep -q "~/code/heretek" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits non-zero (host path corrected)
    - `grep -q "qwen3.6:35b-a3b-q4_K_M" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits 0 (model tag unchanged)
    - `grep -q "OLLAMA_MODEL" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md` exits 0 (env var unchanged)
    - `grep -q "20GB" /Users/evgeniy/Projects/140526_heretek/CLAUDE.md`: if non-zero exit (no matches), accept. If matches exist, manually confirm they are NOT about the primary model (e.g., historical reference, anomaly note) — verify by inspecting each match.
    - The §6 block contains the substrings: `Foundation + Local LLM shipped`, `playground`, `last-known-good`, `OLLAMA_MODEL_LIGHT`, `HERETEK_MAX_CONTEXT_TOKENS`, `scripts/smoke_test.py`
    - `git log --oneline -1` contains substring `model size` or `24GB`
  </acceptance_criteria>
  <done>CLAUDE.md reflects accurate 24GB model size, removes obsolete ~/code/heretek path, marks Phase 1 complete in §6 with a useful resume summary for future-Claude.</done>
</task>

<task type="auto">
  <name>Task 3: Phase 1 final gate — run full smoke + ROADMAP/STATE check-off</name>
  <files>
    .planning/ROADMAP.md,
    .planning/STATE.md
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/.planning/ROADMAP.md (find the Phase 1 checkbox and the Phase Details Phase 1 Success Criteria — confirm we are about to check them off)
    - /Users/evgeniy/Projects/140526_heretek/.planning/STATE.md (find current position, stopped_at, progress numbers)
    - /Users/evgeniy/Projects/140526_heretek/.planning/REQUIREMENTS.md (find FORK-01..04 and LLM-01..06 status rows)
    - Run: `python scripts/smoke_test.py --static-only` and capture output
    - Run: `python scripts/smoke_test.py` and capture output (may fail if Ollama not running; record exit code either way)
  </read_first>
  <action>
This is the final administrative gate of Phase 1. Three updates:

**(A) Run the smoke test one more time and record the result.**

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Static-only must pass
python scripts/smoke_test.py --static-only > /tmp/smoke-static.log 2>&1
STATIC_EXIT=$?
cat /tmp/smoke-static.log
echo "static exit: $STATIC_EXIT"

# Full suite: pass IF Ollama is up, else fail with clear message — either way, record
python scripts/smoke_test.py > /tmp/smoke-full.log 2>&1
FULL_EXIT=$?
cat /tmp/smoke-full.log
echo "full exit: $FULL_EXIT"
```

If `STATIC_EXIT != 0`: STOP. The static gate must be green before Phase 1 can close. Investigate and fix.

If `STATIC_EXIT == 0 && FULL_EXIT == 0`: full Phase 1 success — both gates green.

If `STATIC_EXIT == 0 && FULL_EXIT != 0`: Inspect `/tmp/smoke-full.log`. If the failure is `models not pulled` or `ollama serve not running`: this is a USER-SETUP gap, not a code defect. Phase 1 is gateable as "code complete; user must run `ollama serve` and pull models to fully verify." Record this in the SUMMARY.

**(B) Update ROADMAP.md to check off Phase 1.**

In `.planning/ROADMAP.md`, find the Phases list line:
```
- [ ] **Phase 1: Foundation + Local LLM** - ...
```

Change to:
```
- [x] **Phase 1: Foundation + Local LLM** - ...
```

Also in the Progress table at the bottom, update the Phase 1 row:
```
| 1. Foundation + Local LLM | 5/5 | Completed | 2026-05-14 |
```
(Or whatever today's date is at execution time. Plan count is 5.)

**(C) Update STATE.md current position.**

```yaml
stopped_at: "Phase 1 complete; ready for Phase 2"
last_activity: "<today's date> — Phase 1 shipped (foundation + local LLM)"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 5
  completed_plans: 5
  percent: 25
```

Update the `Current Position` section:
```markdown
## Current Position

Phase: 2 of 4 (Persona + Identity)
Plan: 0 of ? in current phase
Status: Ready to plan (Phase 1 complete)
Last activity: <date> — Phase 1 shipped (foundation + local LLM)

Progress: [██░░░░░░░░] 25%
```

**(D) Update REQUIREMENTS.md traceability rows.**

Find the rows for FORK-01..FORK-04 and LLM-01..LLM-06 and change Status from `Pending` to `Validated` (only if the full smoke suite passed end-to-end with Ollama running) OR `Done` (if static-only passed but Ollama-dependent checks were not exercised at this commit).

Single bash to apply mass status edit (only if both passed):
```bash
cd /Users/evgeniy/Projects/140526_heretek
# Only run if FULL_EXIT == 0:
if [ "$FULL_EXIT" = "0" ]; then
  STATUS_NEW="Validated"
else
  STATUS_NEW="Done (validation pending host setup)"
fi
# Use perl for precise line-targeted replacement
for ID in FORK-01 FORK-02 FORK-03 FORK-04 LLM-01 LLM-02 LLM-03 LLM-04 LLM-05 LLM-06; do
  perl -pi -e "s/\\| ${ID} \\| Phase 1 \\| Pending \\|/| ${ID} | Phase 1 | ${STATUS_NEW} |/" .planning/REQUIREMENTS.md
done
grep -A1 "FORK-01\\|LLM-06" .planning/REQUIREMENTS.md
```

Step 4: Commit:
```bash
git add .planning/ROADMAP.md .planning/STATE.md .planning/REQUIREMENTS.md
git commit -m "docs(phase-1): mark Phase 1 complete in ROADMAP/STATE/REQUIREMENTS"
```

CRITICAL: Do NOT push to origin in this task. Pushing is a separate decision the user makes after Phase 1. The executor should print, at task end, the actionable next step:
```
Phase 1 complete on local playground. To push to GitHub fork:
    git push -u origin playground
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && python scripts/smoke_test.py --static-only && grep -q "\[x\] \*\*Phase 1: Foundation + Local LLM\*\*" .planning/ROADMAP.md && grep -q "Phase 1 complete" .planning/STATE.md && ! grep -q "| FORK-01 | Phase 1 | Pending |" .planning/REQUIREMENTS.md && ! grep -q "| LLM-06 | Phase 1 | Pending |" .planning/REQUIREMENTS.md && git log --oneline -1 | grep -q "mark Phase 1 complete"</automated>
  </verify>
  <acceptance_criteria>
    - `python scripts/smoke_test.py --static-only` exits 0
    - `grep -q "\\[x\\] \\*\\*Phase 1: Foundation + Local LLM\\*\\*" /Users/evgeniy/Projects/140526_heretek/.planning/ROADMAP.md` exits 0
    - `grep -q "Phase 1 complete\\|Phase 1 shipped" /Users/evgeniy/Projects/140526_heretek/.planning/STATE.md` exits 0
    - `grep -q "completed_plans: 5" /Users/evgeniy/Projects/140526_heretek/.planning/STATE.md` exits 0
    - `grep -q "completed_phases: 1" /Users/evgeniy/Projects/140526_heretek/.planning/STATE.md` exits 0
    - For each ID in {FORK-01, FORK-02, FORK-03, FORK-04, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06}: `grep -q "| ${ID} | Phase 1 | Pending |" .planning/REQUIREMENTS.md` exits NON-zero (no row is still Pending)
    - Each of those IDs has either `Validated` or `Done (validation pending host setup)` in its traceability row
    - `git log --oneline -1` contains substring `mark Phase 1 complete`
    - The most recent commit on playground is this admin commit (the prior commits in Plan 05 Tasks 1 and 2 are earlier in history)
  </acceptance_criteria>
  <done>Phase 1 is administratively closed: ROADMAP checked off, STATE.md updated to 25% with Phase 2 as next, REQUIREMENTS.md traceability flipped from Pending. Smoke test static gate green; full gate green if Ollama up.</done>
</task>

</tasks>

<verification>
After all tasks:
1. `python scripts/smoke_test.py --static-only` exits 0 with 2 PASS, 0 FAIL, 0 SKIP
2. `python scripts/smoke_test.py` either exits 0 (Ollama up, 4 PASS) or exits non-zero with actionable `ollama pull` / `ollama serve` message
3. CLAUDE.md reflects 24GB, marks Phase 1 complete in §6
4. ROADMAP.md Phase 1 box is `[x]`; progress table updated
5. STATE.md Current Position points at Phase 2; progress 25%
6. REQUIREMENTS.md FORK-01..04 + LLM-01..06 not in Pending state
7. Three commits land on playground (smoke flip, CLAUDE doc fix, admin)
</verification>

<success_criteria>
- LLM-06 fully implemented: bilingual smoke test active and passing (or actionable-failing) end-to-end
- CLAUDE.md correctness restored: 24GB model size, current path, current phase status
- Roadmap and state docs reflect Phase 1 completion
- Phase 1 is shipped: all 10 requirements (FORK-01..04, LLM-01..06) traceable to commits on playground
</success_criteria>

<output>
After completion, create `/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-05-SUMMARY.md` documenting:
- Full stdout of `python scripts/smoke_test.py --static-only` (must show 2 PASS)
- Full stdout of `python scripts/smoke_test.py` (whether 4 PASS or actionable-fail; record either way)
- Whether Ollama was running at execution time and which models were pulled
- The exact §6 block of CLAUDE.md after the rewrite (paste it)
- Confirmation that ROADMAP.md, STATE.md, REQUIREMENTS.md are all updated
- The git log of all 5 plans' commits on playground (`git log --oneline playground..master` should be empty; `git log --oneline -20` should show the full Phase 1 commit chain)
- Recommended next command: `git push -u origin playground` (to be run by the user when ready)
</output>
