---
phase: 01-foundation-local-llm
plan: 04
type: execute
wave: 4
depends_on:
  - "02"
  - "03"
files_modified:
  - heretek/llm.py
  - heretek/consciousness.py
  - heretek/context.py
  - supervisor/state.py
  - requirements.txt
  - logs/  # created on first write (not committed; .gitignored)
autonomous: true
requirements:
  - LLM-01
  - LLM-02
  - LLM-03
  - LLM-04
  - LLM-05
  - FORK-04
must_haves:
  truths:
    - "heretek/llm.py LLMClient defaults route to base_url='http://localhost:11434/v1' and api_key='ollama'"
    - "heretek/llm.py available_models() returns OLLAMA_MODEL (default 'qwen3.6:35b-a3b-q4_K_M') and OLLAMA_MODEL_LIGHT (default 'qwen3:4b')"
    - "heretek/consciousness.py reads OLLAMA_MODEL_LIGHT (not OUROBOROS_MODEL_LIGHT) with default 'qwen3:4b'"
    - "heretek/context.py reads HERETEK_MAX_CONTEXT_TOKENS (default 32000) and caps context assembly accordingly"
    - "After one Ollama call, logs/tokens.jsonl exists and contains a JSONL record with keys {ts, model, prompt_tokens, completion_tokens, total}"
    - "supervisor/state.py update_budget_from_usage() accumulates token counters but never accumulates a non-zero cost and never makes an HTTP call"
    - "supervisor/state.py budget_remaining() returns inf (or equivalent sentinel for unbounded); budget_pct() returns 0.0"
  artifacts:
    - path: "heretek/llm.py"
      provides: "Ollama-routed LLMClient with token logger"
      contains: "localhost:11434"
    - path: "heretek/consciousness.py"
      provides: "Background loop reading OLLAMA_MODEL_LIGHT"
      contains: "OLLAMA_MODEL_LIGHT"
    - path: "heretek/context.py"
      provides: "Context assembly respecting HERETEK_MAX_CONTEXT_TOKENS"
      contains: "HERETEK_MAX_CONTEXT_TOKENS"
    - path: "supervisor/state.py"
      provides: "Budget shape preserved; cost zeroed; OpenRouter HTTP drift-check stripped"
      contains: "spent_tokens_prompt"
    - path: "logs/tokens.jsonl"
      provides: "Per-call token log (created on first write; gitignored)"
      contains: ""  # contents grow at runtime
  key_links:
    - from: "heretek/llm.py chat()"
      to: "Ollama at http://localhost:11434/v1/chat/completions"
      via: "openai.OpenAI client with base_url override and api_key='ollama'"
      pattern: "OpenAI\\(.*base_url.*localhost:11434"
    - from: "heretek/llm.py chat() after response"
      to: "logs/tokens.jsonl"
      via: "_log_tokens(model, prompt_tokens, completion_tokens)"
      pattern: "_log_tokens\\("
    - from: "supervisor/state.py update_budget_from_usage()"
      to: "(was OpenRouter HTTP; now nothing — local-only)"
      via: "function body — no requests.* calls allowed"
      pattern: "requests\\."
---

<objective>
Swap the LLM client to point at local Ollama (`http://localhost:11434/v1`, api_key=`ollama`), configure primary (`qwen3.6:35b-a3b-q4_K_M`) and light (`qwen3:4b`) models via `OLLAMA_MODEL` / `OLLAMA_MODEL_LIGHT` env vars, cap context to 32K via `HERETEK_MAX_CONTEXT_TOKENS`, neuter `supervisor/state.py` budget tracking (preserve shape, zero the cost, strip the OpenRouter HTTP drift-check), and add the JSONL token logger that appends `{ts, model, prompt_tokens, completion_tokens, total}` to `logs/tokens.jsonl` after every Ollama call.

Purpose: This plan delivers LLM-01..05 (Ollama wiring + context cap + local-only fallback) and FORK-04 (budget neuter + token logger). It is the heaviest plan of the phase — it touches the LLM transport, the consciousness loop's model selection, the context assembly's cap parameter, and the budget tracker's internals. It does NOT include the end-to-end smoke test (that's Plan 05) — but it must leave the system in a state where Plan 05's smoke test can pass.

Output: `heretek/llm.py` issues HTTP requests to `localhost:11434/v1` and writes a JSONL token log on every call. `heretek/consciousness.py` reads the light-model env var. `heretek/context.py` caps context. `supervisor/state.py` still has the public budget shape callers expect, but reports tokens, not dollars, and makes zero network calls. `python-dotenv` confirmed in requirements.
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
@/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-03-SUMMARY.md

<interfaces>
Files to read fully before editing:
- heretek/llm.py (post-Plan-03 strip — class LLMClient still present, cloud env-var loaders gone; chat() and available_models() bodies still intact)
- heretek/consciousness.py (search for OUROBOROS_MODEL_LIGHT and BackgroundConsciousness class; reference 01-RESEARCH.md §Code Examples — consciousness.py model env var)
- heretek/context.py (search for any existing context-cap parameter; reference 01-RESEARCH.md §Phase Requirements LLM-04: "context.py accepts the cap parameter; wiring point identified")
- supervisor/state.py (locate: update_budget_from_usage, budget_remaining, budget_pct, STATE_LOCK, _load, _save, _spent_calls counter and the % 50 OpenRouter drift-check block — reference 01-RESEARCH.md §Pattern 3 + §Pitfall 4)

Key Ollama OpenAI-compat contract (from 01-RESEARCH.md §Code Examples):
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
response = client.chat.completions.create(
    model="qwen3.6:35b-a3b-q4_K_M",
    messages=[{"role": "user", "content": "..."}],
    stream=False,
)
# response.usage.prompt_tokens, response.usage.completion_tokens, response.usage.total_tokens
```

Token logger contract (from 01-CONTEXT.md §Token logger design):
- Format: JSONL appended to logs/tokens.jsonl
- Per LLM call (both primary and background models)
- Record: {"ts": "<iso-utc-Z>", "model": "<tag>", "prompt_tokens": <int>, "completion_tokens": <int>, "total": <int>}
- No prompt/completion text capture
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Patch heretek/llm.py for Ollama + add JSONL token logger</name>
  <files>
    heretek/llm.py,
    requirements.txt
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/heretek/llm.py (READ FULLY — current post-strip state: LLMClient with empty api_key/base_url defaults, chat() method intact, available_models() function intact)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 1: Ollama LLM Client Patch; §Pattern 2: Model Env Var Rename; §Pattern 4: JSONL Token Logger; §Code Examples — Ollama Chat Completions Request)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Token logger design — exact JSONL field set; §Stripping strategy — Ollama swap goals)
  </read_first>
  <action>
This is the heart of Plan 04. Three edits to `heretek/llm.py`:

(A) **Update `LLMClient.__init__`** so defaults are Ollama-shaped:

```python
def __init__(self, api_key=None, base_url=None):
    self._api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama")
    self._base_url = base_url or os.environ.get(
        "OLLAMA_BASE_URL", "http://localhost:11434/v1"
    )
    self._client = None  # lazy-init; matches upstream pattern
```

And inside `_get_client()` (or wherever the `OpenAI(...)` constructor is called), strip any leftover OpenRouter custom headers and build a clean client:

```python
def _get_client(self):
    if self._client is None:
        from openai import OpenAI
        self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
    return self._client
```

(B) **Update `available_models()`** to return Ollama tags. From research:

```python
def available_models():
    main = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
    light = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
    # code-specialized model dropped; Qwen handles both
    return {
        "main": main,
        "code": main,   # alias - keep callers happy without a separate model
        "light": light,
    }
```

If the upstream signature returned a tuple or different keys, preserve that shape — change only the VALUES, not the SHAPE. Read the original function first, then surgically replace the env-var reads and defaults.

(C) **Add the JSONL token logger** at module level and call it from `chat()`. Insert near the top of the file (after imports):

```python
import json as _json
import pathlib as _pathlib
import datetime as _datetime

_TOKENS_LOG_PATH = _pathlib.Path("logs/tokens.jsonl")

def _log_tokens(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Append one JSONL record to logs/tokens.jsonl after each LLM call."""
    try:
        _TOKENS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": _datetime.datetime.utcnow().isoformat() + "Z",
            "model": model,
            "prompt_tokens": int(prompt_tokens or 0),
            "completion_tokens": int(completion_tokens or 0),
            "total": int((prompt_tokens or 0) + (completion_tokens or 0)),
        }
        with _TOKENS_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(record) + "\n")
    except OSError:
        # Logging is best-effort; never break the call path
        pass
```

Then inside `chat()` (or wherever the OpenAI response is received), after the response is returned and BEFORE the function returns to the caller, call:

```python
# After response = self._get_client().chat.completions.create(...)
try:
    usage = getattr(response, "usage", None)
    if usage is not None:
        _log_tokens(
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
except Exception:
    pass  # logging must never break the LLM call
```

CRITICAL constraints:
- Do NOT remove `update_budget_from_usage(...)` calls from inside `chat()`. The budget tracker is patched in Task 2 of this plan to make those calls cheap and local-only. Keep the call site.
- Do NOT change the `chat()` signature. Any caller (consciousness loop, agent) expects the same signature.
- The token logger is best-effort: any I/O exception inside `_log_tokens` is swallowed. Never propagate.
- The OpenAI Python SDK package name in requirements.txt is `openai>=1.0.0` — confirm it's still there after Plan 03's prune.

Step-by-step:
```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Read current state to inform the edit
grep -n "class LLMClient\|def __init__\|def _get_client\|def chat\|def available_models\|def update_budget_from_usage" heretek/llm.py

# Step 2: Edit via the Edit tool (NOT sed/awk — these edits are too complex for line-based replacement)

# Step 3: Confirm imports still work
python -c "from heretek.llm import LLMClient, available_models; print(available_models())"
# Expected output (or similar): {'main': 'qwen3.6:35b-a3b-q4_K_M', 'code': 'qwen3.6:35b-a3b-q4_K_M', 'light': 'qwen3:4b'}

# Step 4: Confirm token logger is callable directly
python -c "
from heretek.llm import _log_tokens
import pathlib
_log_tokens('test:model', 10, 20)
p = pathlib.Path('logs/tokens.jsonl')
assert p.exists(), 'tokens.jsonl not created'
last = p.read_text().splitlines()[-1]
print('LOG OK:', last)
import json
record = json.loads(last)
assert record['model'] == 'test:model'
assert record['prompt_tokens'] == 10
assert record['completion_tokens'] == 20
assert record['total'] == 30
assert 'ts' in record
print('SCHEMA OK')
"

# Step 5: Confirm openai is in requirements.txt
grep -q "^openai" requirements.txt || echo "openai>=1.0.0" >> requirements.txt

# Step 6: Commit
git add heretek/llm.py requirements.txt
git commit -m "feat(phase-1): patch heretek/llm.py for Ollama + JSONL token logger"
```

Note: This task does NOT make an actual Ollama HTTP call — that requires Ollama to be running and the model pulled, which is Plan 05's gate. This task only verifies the WIRING is correct via the static token-logger invocation in step 4.
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && grep -q "localhost:11434" heretek/llm.py && grep -q "OLLAMA_MODEL" heretek/llm.py && grep -q "qwen3.6:35b-a3b-q4_K_M" heretek/llm.py && grep -q "qwen3:4b" heretek/llm.py && grep -q "def _log_tokens" heretek/llm.py && grep -q "logs/tokens.jsonl" heretek/llm.py && python -c "from heretek.llm import LLMClient, available_models, _log_tokens; m = available_models(); assert 'qwen' in m['main']" && python -c "from heretek.llm import _log_tokens; import pathlib, json; _log_tokens('smoke:model', 1, 2); r = json.loads(pathlib.Path('logs/tokens.jsonl').read_text().splitlines()[-1]); assert r['model']=='smoke:model' and r['prompt_tokens']==1 and r['completion_tokens']==2 and r['total']==3 and 'ts' in r"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "localhost:11434" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "OLLAMA_BASE_URL" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "OLLAMA_MODEL" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "OLLAMA_MODEL_LIGHT" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "qwen3.6:35b-a3b-q4_K_M" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "qwen3:4b" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "def _log_tokens" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "logs/tokens.jsonl" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `grep -q "api_key=\"ollama\"\\|api_key='ollama'" /Users/evgeniy/Projects/140526_heretek/heretek/llm.py` exits 0
    - `python -c "from heretek.llm import LLMClient, available_models, _log_tokens"` exits 0
    - `python -c "from heretek.llm import available_models; m = available_models(); assert 'qwen' in m['main'].lower()"` exits 0
    - After running `_log_tokens('test:m', 5, 7)`: `test -f /Users/evgeniy/Projects/140526_heretek/logs/tokens.jsonl` exits 0; last line parsed as JSON has fields ts, model, prompt_tokens=5, completion_tokens=7, total=12
    - `grep -q "^openai" /Users/evgeniy/Projects/140526_heretek/requirements.txt` exits 0
    - `git log --oneline -1` contains substring `Ollama` and `token logger`
  </acceptance_criteria>
  <done>LLMClient defaults to Ollama; available_models() returns Qwen tags; _log_tokens writes JSONL records matching the spec; chat() calls the logger after each response; openai SDK in requirements; module imports cleanly.</done>
</task>

<task type="auto">
  <name>Task 2: Neuter supervisor/state.py budget; preserve public shape</name>
  <files>supervisor/state.py</files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/supervisor/state.py (READ FULLY — locate: update_budget_from_usage, budget_remaining, budget_pct, _load, _save, STATE_LOCK, TOTAL_BUDGET_LIMIT global, set_budget_limit function, and the `% 50` OpenRouter HTTP drift-check block)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Stripping strategy — Budget tracker: keep module + public shape of state.budget; swap cost-calc internals; minimal blast radius)
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-RESEARCH.md (§Pattern 3: Budget Neutering surgeon approach; §Pitfall 4: OpenRouter HTTP in update_budget_from_usage)
  </read_first>
  <action>
This task patches `supervisor/state.py` surgically. The goal: keep every public function callable with the same signature; make cost zero; strip the OpenRouter HTTP drift-check; keep token accumulators.

```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Locate everything
grep -n "TOTAL_BUDGET_LIMIT\|set_budget_limit\|update_budget_from_usage\|budget_remaining\|budget_pct\|openrouter\|requests\\." supervisor/state.py
```

(A) **In `update_budget_from_usage(usage: dict) -> None`:**
- Keep the STATE_LOCK / `_load(st)` / `_save(st)` scaffolding.
- Keep token accumulators: `spent_calls`, `spent_tokens_prompt`, `spent_tokens_completion`, `spent_tokens_cached`.
- REMOVE any cost accumulation (`st["spent_usd"] += ...` etc.) — set cost to zero or remove the field entirely if no caller references it externally.
- REMOVE the entire `if self._call_count % 50 == 0` (or equivalent counter) block that makes an HTTP call to `api.openrouter.ai`. Delete the whole conditional + its body. Also remove any `import requests` at module level if it was added solely for that drift-check (re-check after the strip).

Concrete replacement body (adapt to actual upstream variable names — read first):

```python
def update_budget_from_usage(usage: dict) -> None:
    """Local-only: accumulate token counts; never accumulate cost; never HTTP."""
    with STATE_LOCK:
        st = _load()
        st["spent_calls"] = int(st.get("spent_calls") or 0) + int(usage.get("rounds") or 1)
        st["spent_tokens_prompt"] = int(st.get("spent_tokens_prompt") or 0) + int(usage.get("prompt_tokens") or 0)
        st["spent_tokens_completion"] = int(st.get("spent_tokens_completion") or 0) + int(usage.get("completion_tokens") or 0)
        st["spent_tokens_cached"] = int(st.get("spent_tokens_cached") or 0) + int(usage.get("cached_tokens") or 0)
        # spent_usd intentionally NOT accumulated - Heretek runs on free local inference.
        _save(st)
```

(B) **`budget_remaining()`:**
- Upstream pattern: returns `TOTAL_BUDGET_LIMIT - spent_usd`. With `TOTAL_BUDGET_LIMIT = 0` and `spent_usd = 0`, this returns 0, not inf.
- Replacement: explicitly return `float("inf")`. This makes "budget exhausted" checks (`if budget_remaining() < threshold`) always pass.

```python
def budget_remaining() -> float:
    """Heretek has no budget cap - local inference is free."""
    return float("inf")
```

(C) **`budget_pct()`:**
- Upstream pattern: returns `spent_usd / TOTAL_BUDGET_LIMIT * 100`. With both zero, raises ZeroDivisionError.
- Replacement: explicitly return `0.0`.

```python
def budget_pct() -> float:
    """Heretek has no budget cap - always reports 0% used."""
    return 0.0
```

(D) **`set_budget_limit()`:**
- If the function exists, leave the function in place but make the body a no-op (or just `pass`). Callers (likely `colab_launcher.py` and possibly `supervisor/__main__.py` if we wired it) keep working without changes.

```python
def set_budget_limit(usd: float) -> None:
    """No-op for Heretek - budget is unbounded."""
    pass
```

(E) **Remove `TOTAL_BUDGET_LIMIT`** as a module-level mutable global if it exists, OR leave it as a `0.0` constant. Either is fine; the public functions above don't reference it anymore.

(F) **Verify NO `requests.` calls remain in state.py:**
```bash
grep -n "requests\\." supervisor/state.py
# Must print nothing
```

If `import requests` at module level was solely for the drift-check, remove the import.

Step 2: Verify the module imports and the public surface still works:
```bash
python -c "
from supervisor.state import update_budget_from_usage, budget_remaining, budget_pct
import math
update_budget_from_usage({'prompt_tokens': 100, 'completion_tokens': 50, 'rounds': 1})
r = budget_remaining()
p = budget_pct()
assert math.isinf(r), f'budget_remaining returned {r}, expected inf'
assert p == 0.0, f'budget_pct returned {p}, expected 0.0'
print('OK: budget_remaining=', r, 'budget_pct=', p)
"
```

Step 3: Commit:
```bash
git add supervisor/state.py
git commit -m "refactor(phase-1): neuter supervisor/state.py budget (zero cost, no HTTP, preserve public shape)"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && ! grep -q "openrouter" supervisor/state.py && ! grep -q "requests\." supervisor/state.py && grep -q "def update_budget_from_usage" supervisor/state.py && grep -q "def budget_remaining" supervisor/state.py && grep -q "def budget_pct" supervisor/state.py && python -c "from supervisor.state import update_budget_from_usage, budget_remaining, budget_pct; import math; update_budget_from_usage({'prompt_tokens': 100, 'completion_tokens': 50, 'rounds': 1}); assert math.isinf(budget_remaining()); assert budget_pct() == 0.0"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "openrouter" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits non-zero
    - `grep -q "api\\.openrouter\\.ai" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits non-zero
    - `grep -q "^import requests" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits non-zero (the requests import, if it was solely for drift-check, is removed; if it's used elsewhere in state.py, leave it but verify the drift block is gone)
    - `grep -E "requests\\.(get|post|put|delete)" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits non-zero (no HTTP method calls in state.py)
    - `grep -q "def update_budget_from_usage" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits 0 (public function preserved)
    - `grep -q "def budget_remaining" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits 0
    - `grep -q "def budget_pct" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits 0
    - `grep -q "spent_tokens_prompt\|spent_tokens_completion" /Users/evgeniy/Projects/140526_heretek/supervisor/state.py` exits 0 (token accumulators preserved)
    - `python -c "from supervisor.state import budget_remaining; import math; assert math.isinf(budget_remaining())"` exits 0
    - `python -c "from supervisor.state import budget_pct; assert budget_pct() == 0.0"` exits 0
    - `python -c "from supervisor.state import update_budget_from_usage; update_budget_from_usage({'prompt_tokens': 5, 'completion_tokens': 7, 'rounds': 1})"` exits 0
    - `git log --oneline -1` contains substring `neuter supervisor/state.py budget`
  </acceptance_criteria>
  <done>Budget shape preserved; cost permanently zero; no HTTP calls anywhere in state.py; token accumulators still working; budget_remaining returns inf; budget_pct returns 0.0.</done>
</task>

<task type="auto">
  <name>Task 3: Wire consciousness.py and context.py to new env vars</name>
  <files>
    heretek/consciousness.py,
    heretek/context.py
  </files>
  <read_first>
    - /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py (READ FULLY — locate OUROBOROS_MODEL_LIGHT and any default like "qwen/qwen3.5-plus-02-15"; the BackgroundConsciousness class; reference 01-RESEARCH.md §Code Examples — consciousness.py model env var)
    - /Users/evgeniy/Projects/140526_heretek/heretek/context.py (READ FULLY — locate the context-assembly entry point; reference 01-RESEARCH.md §Phase Requirements LLM-04: "context.py accepts the cap parameter; wiring point identified")
    - /Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-CONTEXT.md (§Integration points — OLLAMA_MODEL_LIGHT, HERETEK_MAX_CONTEXT_TOKENS=32000)
  </read_first>
  <action>
Two related wiring fixes.

**(A) heretek/consciousness.py: rename `OUROBOROS_MODEL_LIGHT` → `OLLAMA_MODEL_LIGHT` and update default.**

After the Plan 02 rename, the env var name was likely changed to `HERETEK_MODEL_LIGHT` by the perl sweep (which replaced `ouroboros` with `heretek` everywhere). We need the env var to be `OLLAMA_MODEL_LIGHT` (per CLAUDE.md §8 and 01-CONTEXT.md §Integration points). Fix it:

```bash
cd /Users/evgeniy/Projects/140526_heretek
grep -n "MODEL_LIGHT" heretek/consciousness.py
# Expected: lines reading os.environ.get("HERETEK_MODEL_LIGHT", "qwen/...something...")
```

Use Edit tool to change:

Before (post-rename state):
```python
os.environ.get("HERETEK_MODEL_LIGHT", "qwen/qwen3.5-plus-02-15")
```

After:
```python
os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
```

Apply this for every occurrence in `consciousness.py`. If the upstream default was a different OpenRouter-style name (e.g., `qwen/qwen3.5-plus-02-15`), replace it with the Ollama tag `qwen3:4b`.

If the file ALSO references `HERETEK_MODEL` (post-rename of `OUROBOROS_MODEL`) for the primary path, replace those reads with `OLLAMA_MODEL` and default `qwen3.6:35b-a3b-q4_K_M`:

Before:
```python
os.environ.get("HERETEK_MODEL", "openai/gpt-5.2")
```

After:
```python
os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
```

**(B) heretek/context.py: wire HERETEK_MAX_CONTEXT_TOKENS cap.**

Read the file first to identify the context-assembly function (typically `build_context(...)` or similar). It should accept a max-tokens parameter. Wire it to read `HERETEK_MAX_CONTEXT_TOKENS` with default 32000:

Find the function that does context assembly and locate the line that establishes the cap. If upstream hardcodes a cap or reads a different env var, replace with:

```python
import os as _os

_DEFAULT_MAX_CONTEXT_TOKENS = 32000

def _max_context_tokens() -> int:
    raw = _os.environ.get("HERETEK_MAX_CONTEXT_TOKENS", str(_DEFAULT_MAX_CONTEXT_TOKENS))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_MAX_CONTEXT_TOKENS
```

Then use `_max_context_tokens()` wherever a context-size cap is applied. If the upstream code already has a similar function with a different name and env var, just rename the env var and adjust the default.

CRITICAL: If `context.py` already has a cap mechanism wired to a different env var (e.g., `OUROBOROS_MAX_TOKENS` → post-rename `HERETEK_MAX_TOKENS`), the cleanest path is: rename the env var key in that function to `HERETEK_MAX_CONTEXT_TOKENS` and set its default to 32000. Don't introduce a parallel mechanism.

Step-by-step:
```bash
cd /Users/evgeniy/Projects/140526_heretek

# Step 1: Locate
grep -n "MODEL_LIGHT\|MODEL\b" heretek/consciousness.py
grep -n "MAX_CONTEXT\|MAX_TOKENS\|max_tokens" heretek/context.py

# Step 2: Edit both files via the Edit tool with concrete before/after blocks

# Step 3: Verify imports
python -c "import heretek.consciousness; import heretek.context; print('OK')"

# Step 4: Verify env-var reads with defaults
python -c "
import os
# Clear any user env that might mask defaults
for k in ('OLLAMA_MODEL', 'OLLAMA_MODEL_LIGHT', 'HERETEK_MAX_CONTEXT_TOKENS', 'HERETEK_MODEL', 'HERETEK_MODEL_LIGHT'):
    os.environ.pop(k, None)
import importlib, heretek.consciousness, heretek.context
importlib.reload(heretek.consciousness)
importlib.reload(heretek.context)
# Read consciousness.py to confirm OLLAMA_MODEL_LIGHT is the env var name
with open('heretek/consciousness.py') as f:
    src = f.read()
assert 'OLLAMA_MODEL_LIGHT' in src, 'consciousness.py missing OLLAMA_MODEL_LIGHT'
assert 'qwen3:4b' in src, 'consciousness.py missing qwen3:4b default'
with open('heretek/context.py') as f:
    src = f.read()
assert 'HERETEK_MAX_CONTEXT_TOKENS' in src, 'context.py missing HERETEK_MAX_CONTEXT_TOKENS'
assert '32000' in src, 'context.py missing 32000 default'
print('OK')
"

# Step 5: Commit
git add heretek/consciousness.py heretek/context.py
git commit -m "feat(phase-1): wire OLLAMA_MODEL_LIGHT in consciousness, HERETEK_MAX_CONTEXT_TOKENS in context"
```
  </action>
  <verify>
    <automated>cd /Users/evgeniy/Projects/140526_heretek && grep -q "OLLAMA_MODEL_LIGHT" heretek/consciousness.py && grep -q "qwen3:4b" heretek/consciousness.py && ! grep -q "HERETEK_MODEL_LIGHT" heretek/consciousness.py && grep -q "HERETEK_MAX_CONTEXT_TOKENS" heretek/context.py && grep -q "32000" heretek/context.py && python -c "import heretek.consciousness; import heretek.context"</automated>
  </verify>
  <acceptance_criteria>
    - `grep -q "OLLAMA_MODEL_LIGHT" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py` exits 0
    - `grep -q "qwen3:4b" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py` exits 0
    - `grep -q "HERETEK_MODEL_LIGHT" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py` exits non-zero (the Plan 02 rename artifact is replaced)
    - `grep -q "OUROBOROS_MODEL_LIGHT" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py` exits non-zero (original is also gone)
    - If consciousness.py also references the primary model env var: `grep -q "OLLAMA_MODEL" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py` exits 0; `! grep -q "HERETEK_MODEL\\b" /Users/evgeniy/Projects/140526_heretek/heretek/consciousness.py`
    - `grep -q "HERETEK_MAX_CONTEXT_TOKENS" /Users/evgeniy/Projects/140526_heretek/heretek/context.py` exits 0
    - `grep -q "32000" /Users/evgeniy/Projects/140526_heretek/heretek/context.py` exits 0
    - `python -c "import heretek.consciousness"` exits 0
    - `python -c "import heretek.context"` exits 0
    - `python -c "import heretek.agent; import heretek.llm; import heretek.consciousness; import heretek.context; import supervisor.state"` exits 0 (the full module web imports cleanly)
    - `git log --oneline -1` contains substring `OLLAMA_MODEL_LIGHT` and `HERETEK_MAX_CONTEXT_TOKENS`
  </acceptance_criteria>
  <done>Background consciousness reads OLLAMA_MODEL_LIGHT (default qwen3:4b); context assembly reads HERETEK_MAX_CONTEXT_TOKENS (default 32000); both modules import cleanly; primary-model env var also normalized to OLLAMA_MODEL if consciousness.py touches it.</done>
</task>

</tasks>

<verification>
After all tasks:
1. `python -c "import heretek; import heretek.llm; import heretek.agent; import heretek.consciousness; import heretek.context; import supervisor.state"` exits 0
2. `grep -q "localhost:11434" heretek/llm.py` and `grep -q "_log_tokens" heretek/llm.py`
3. `python -c "from heretek.llm import _log_tokens; _log_tokens('t', 1, 2)"` creates/appends `logs/tokens.jsonl` with a valid JSONL record
4. `python -c "from supervisor.state import budget_remaining; import math; assert math.isinf(budget_remaining())"` exits 0
5. `grep -q "OLLAMA_MODEL_LIGHT" heretek/consciousness.py` and `grep -q "HERETEK_MAX_CONTEXT_TOKENS" heretek/context.py`
6. `! rg -q "openrouter\\.ai|api\\.openai\\.com|api\\.anthropic\\.com" heretek/ supervisor/`
7. `python scripts/smoke_test.py --static-only` still passes (2 PASS, 0 FAIL, 0 SKIP — test_no_cloud_hosts still green after Plan 04's changes)
8. Three commits land on playground (llm patch, state neuter, consciousness+context wiring)
</verification>

<success_criteria>
- LLM-01: Ollama base URL + api_key=ollama wired in llm.py
- LLM-02: OLLAMA_MODEL default qwen3.6:35b-a3b-q4_K_M
- LLM-03: OLLAMA_MODEL_LIGHT default qwen3:4b in consciousness.py
- LLM-04: HERETEK_MAX_CONTEXT_TOKENS default 32000 in context.py
- LLM-05: No cloud fallback - static grep clean
- FORK-04: Budget public shape preserved; cost zeroed; HTTP drift-check stripped; JSONL token logger writes per-call records
</success_criteria>

<output>
After completion, create `/Users/evgeniy/Projects/140526_heretek/.planning/phases/01-foundation-local-llm/01-04-SUMMARY.md` documenting:
- The before/after diff of LLMClient.__init__ in heretek/llm.py
- The exact upstream `% 50` block that was stripped from supervisor/state.py
- The exact env var lines changed in consciousness.py and context.py
- A sample tokens.jsonl record (from the _log_tokens smoke test invocation)
- Confirmation that `python scripts/smoke_test.py --static-only` still passes (paste stdout)
- Whether any unexpected references to OUROBOROS_* / HERETEK_MODEL_* env vars surfaced outside the expected files
</output>
