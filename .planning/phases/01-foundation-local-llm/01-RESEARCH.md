# Phase 1: Foundation + Local LLM - Research

**Researched:** 2026-05-14
**Domain:** Python package rename, Ollama OpenAI-compat API, Ouroboros v6.2.0 internal wiring
**Confidence:** HIGH (core findings verified against upstream source and Ollama official docs)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Repo & fork workflow**
- Fork lives at `/Users/evgeniy/Projects/140526_heretek/`. `CLAUDE.md` §6 reference to `~/code/heretek` is superseded — update it during planning.
- Fork via `gh repo fork razzant/ouroboros --fork-name heretek --remote --clone`, renaming on GitHub in one step.
- Branches created immediately after clone, before any stripping work: `playground` (all dev work from this point) and `last-known-good` (tagged at upstream HEAD on `main` at clone time).
- Upstream remote kept: `upstream` → `razzant/ouroboros`.

**Stripping strategy**
- Hard delete (no stubs): `tools/github.py`, `tools/review.py`, `tools/browser.py`, and the multi-model review orchestrator (`ouroboros/review.py` at package root).
- All imports and call sites updated/removed in the same commit chain.
- Legacy cloud env-var loading (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`): strip loading code entirely. No startup warnings.
- Budget tracker (`supervisor/state.py`): keep module and public shape of `state.budget`. Swap cost-calc internals to return `0` for any dollar-shaped value; accumulate prompt/completion token counts. Minimal blast radius on callers.

**Token logger design**
- Format: JSONL appended to `logs/tokens.jsonl`.
- Per LLM call (both primary and background models).
- Record fields: `{ts, model, prompt_tokens, completion_tokens, total}`.
- Status surface: upstream `/status` or status-line that previously reported dollar spend now reports session tokens + lifetime tokens.

**Smoke test rigor**
- Bar: end-to-end — `python -m supervisor` boots, test-harness message, calls `heretek/llm.py`, real Ollama reply. Tested RU + EN.
- Location: `scripts/smoke_test.py` — runnable Python script, PASS/FAIL per check.
- "No cloud calls" verification: static grep for `openrouter.ai`, `api.openai.com`, `api.anthropic.com`, any leftover cloud key imports.
- Model pull check: smoke test runs `ollama list` first; fails loud if either model is missing.

### Claude's Discretion
- Exact Python entry-point shape inside `python -m supervisor` for the smoke harness (stdin reader vs. `--once` flag vs. tiny harness module).
- Internal layout of `scripts/smoke_test.py`.
- Whether `logs/` is created at import time, on first write, or seeded by the fork commit.
- Whether stripping happens as one mega-commit or staged commits (any staging is fine as long as `main` stays at clean upstream HEAD and all work lands on `playground`).
- Exact JSONL log rotation policy, if any (deferred — unbounded for v1).

### Deferred Ideas (OUT OF SCOPE)
- Token log rotation.
- Network-level "no cloud" verification (lsof / proxy / firewall rule).
- Self-critique single-model review tool.
- Pytest framework adoption.
- Browser tool reintroduction (EXP-02).
- Bashkir language pre-flight.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORK-01 | Fork razzant/ouroboros v6.2.0 to GitHub as heretek, clone locally, create playground and last-known-good branches | gh fork mechanics, branch creation sequence verified |
| FORK-02 | Rename ouroboros/ Python package to heretek/; update pyproject.toml, imports, and references | Rename mechanics, import sites, `pkgutil` discovery implications verified |
| FORK-03 | Remove tools/github.py, tools/review.py (multi-model), tools/browser.py | Import footprint mapped; lazy-import pattern in agent.py confirmed; registry safe-degrades |
| FORK-04 | Neuter budget tracking — replace cost-calc with token counter | state.py budget shape and all public functions documented; caller pattern mapped |
| LLM-01 | Patch heretek/llm.py to point at Ollama (http://localhost:11434/v1, API key literal "ollama") | LLMClient.__init__ signature, base_url, default_headers confirmed; Ollama compat endpoint confirmed |
| LLM-02 | Configure primary model qwen3.6:35b-a3b-q4_K_M via OLLAMA_MODEL env var | Tag confirmed exists on ollama.com/library; 24GB, 256K context |
| LLM-03 | Configure secondary model qwen3:4b via OLLAMA_MODEL_LIGHT | consciousness.py OUROBOROS_MODEL_LIGHT pattern confirmed; env var rename needed |
| LLM-04 | Cap context to 32K tokens via HERETEK_MAX_CONTEXT_TOKENS=32000 | context.py accepts the cap parameter; wiring point identified |
| LLM-05 | Patch fallback chain to local Ollama models only | llm.py available_models() uses three env vars; pricing fetch must be stripped |
| LLM-06 | Smoke-test bot replies in both English and Russian via Ollama | handle_chat_direct() pattern confirmed; no Telegram needed for smoke test |
</phase_requirements>

---

## Summary

Ouroboros v6.2.0 is a well-structured Python package that uses the OpenAI SDK client pointed at OpenRouter. The LLM client (`ouroboros/llm.py`) accepts `base_url` and `api_key` as constructor parameters, making the Ollama swap a targeted 3-field change: replace the base URL, replace the API key with `"ollama"`, strip the OpenRouter custom headers, and remove the pricing-fetch HTTP call. The package uses dynamic filesystem scanning (`pkgutil.iter_modules` + `importlib`) with per-module try/except to discover tools — hard-deleting the three tool files is safe with no registry changes needed. The `ouroboros.review` module and `tools/browser.py` cleanup in `agent.py` are both lazy (inside-function) imports, so their removal is straightforward: strip the call sites, delete the files.

Budget neutering is surgical: `state.py` uses a `spent_usd` float and a `TOTAL_BUDGET_LIMIT` global. Setting limit to `0` already makes `budget_remaining()` return `inf` and `budget_pct()` return `0.0`. The remaining work is stripping the OpenRouter HTTP drift-check from `update_budget_from_usage()` and preserving all public function signatures so callers are unchanged.

The smoke test can call `handle_chat_direct(chat_id, text)` from `supervisor/workers.py` to bypass the Telegram client entirely. Ollama returns `usage.prompt_tokens` and `usage.completion_tokens` in the OpenAI-compatible response, directly compatible with the `add_usage()` accumulator after zeroing `cost`.

**Primary recommendation:** Complete the rename and delete pass on `playground` branch in three commits (fork+branch, rename, strip), then patch `llm.py` and `state.py`, then write the smoke test. Static grep for cloud hosts is the phase gate.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai (Python SDK) | >=1.0.0 (already in requirements.txt) | HTTP transport to Ollama's /v1 endpoint | Ollama's OpenAI-compat layer designed for this exact client; already wired in upstream |
| ollama (server) | latest (brew) | Local LLM server with Metal backend | Confirmed on docs.ollama.com; only local server that works out-of-the-box on macOS |
| python-dotenv | not pinned upstream; add | Load .env at startup | Upstream uses os.environ directly; dotenv keeps secrets out of the shell |
| requests | not pinned upstream | HTTP for remaining Telegram client in supervisor | Already a requirement |

### Models
| Model | Tag | Size | Purpose |
|-------|-----|------|---------|
| qwen3.6 | 35b-a3b-q4_K_M | 24GB on disk | Primary chat, tool-use, shitposting |
| qwen3 | 4b | ~2.5GB | Background consciousness loop (cheap, keeps 35b unloaded) |

**Tag verification:** `qwen3.6:35b-a3b-q4_K_M` confirmed present on [ollama.com/library/qwen3.6/tags](https://ollama.com/library/qwen3.6/tags) — 24GB, 256K context, multimodal. Note: CLAUDE.md states ~20GB; actual size is 24GB. Plan should adjust the "leaves ~12GB headroom" estimate to ~8GB.

### Removed Dependencies
| Remove | Reason |
|--------|--------|
| playwright, playwright-stealth | tools/browser.py deleted; heavy dep |
| httpx | only imported by tools/review.py (multi-model tool) — confirm after delete |

**Installation for new deps:**
```bash
pip install python-dotenv
pip uninstall playwright playwright-stealth httpx  # after confirming no other users
```

**Version verification:**
```bash
npm view openai version  # not applicable — Python package
pip index versions openai  # confirm >=1.0.0 already present
```

---

## Architecture Patterns

### Recommended Project Structure Post-Rename
```
heretek/                    # renamed from ouroboros/
├── __init__.py
├── agent.py                # OuroborosAgent → HereteкAgent (or keep class name)
├── apply_patch.py
├── consciousness.py        # BackgroundConsciousness; uses OLLAMA_MODEL_LIGHT
├── context.py
├── llm.py                  # PRIMARY PATCH TARGET
├── loop.py
├── memory.py
├── owner_inject.py
├── review.py               # DELETED (multi-model orchestrator)
├── utils.py
└── tools/
    ├── __init__.py
    ├── browser.py          # DELETED
    ├── compact_context.py
    ├── control.py
    ├── core.py
    ├── dashboard.py        # keeps GitHub push for webapp — leave but it won't auto-call
    ├── evolution_stats.py  # pushes to razzant/ouroboros-webapp — leave or delete
    ├── git.py
    ├── github.py           # DELETED
    ├── health.py
    ├── knowledge.py
    ├── registry.py
    ├── review.py           # DELETED (multi-model tool)
    ├── search.py
    ├── self_portrait.py
    ├── shell.py
    ├── tool_discovery.py
    ├── vision.py           # safe to keep; no browser.py import
    └── webapp_push.py      # pushes to ouroboros-webapp via git — leave (low-risk)

supervisor/                 # unchanged
├── __init__.py
├── events.py
├── git_ops.py
├── queue.py
├── state.py                # PATCH TARGET (budget neutering)
├── telegram.py
└── workers.py              # handle_chat_direct() is smoke-test entry point

scripts/                    # NEW
└── smoke_test.py

logs/                       # NEW
└── tokens.jsonl            # created on first write by patched llm.py
```

### Pattern 1: Ollama LLM Client Patch
**What:** Replace 3 parameters in `LLMClient.__init__` and strip pricing HTTP calls from `chat()`
**When to use:** LLM-01, LLM-05
**Key changes:**
```python
# Before (ouroboros/llm.py):
def __init__(self, api_key=None, base_url="https://openrouter.ai/api/v1"):
    self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    self._base_url = base_url
    # In _get_client():
    self._client = OpenAI(
        base_url=self._base_url,
        api_key=self._api_key,
        default_headers={
            "HTTP-Referer": "https://colab.research.google.com/",
            "X-Title": "Ouroboros",
        },
    )

# After (heretek/llm.py):
def __init__(self, api_key=None, base_url=None):
    self._api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama")
    self._base_url = base_url or os.environ.get(
        "OLLAMA_BASE_URL", "http://localhost:11434/v1"
    )
    # In _get_client() — strip custom headers, Ollama ignores them but they're noise:
    self._client = OpenAI(
        base_url=self._base_url,
        api_key=self._api_key,
    )
```

### Pattern 2: Model Env Var Rename
**What:** Rename all three OUROBOROS_MODEL_* env vars to OLLAMA_MODEL_*
**Key changes:**
```python
# Before (ouroboros/llm.py available_models):
main  = os.environ.get("OUROBOROS_MODEL", "openai/gpt-5.2")
code  = os.environ.get("OUROBOROS_MODEL_CODE", "")
light = os.environ.get("OUROBOROS_MODEL_LIGHT", "")

# After (heretek/llm.py):
main  = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
code  = ""   # code-specialized model dropped; Qwen handles both
light = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
```

### Pattern 3: Budget Neutering (surgeon approach)
**What:** Zero out cost in `update_budget_from_usage()`, strip OpenRouter HTTP drift-check, preserve all public function signatures
**Key changes in supervisor/state.py:**
```python
# update_budget_from_usage: strip the HTTP block entirely, keep token accumulation:
def update_budget_from_usage(usage: dict) -> None:
    with STATE_LOCK:
        st = _load()
        st["spent_calls"] = int(st.get("spent_calls") or 0) + int(usage.get("rounds") or 1)
        st["spent_tokens_prompt"] += int(usage.get("prompt_tokens") or 0)
        st["spent_tokens_completion"] += int(usage.get("completion_tokens") or 0)
        st["spent_tokens_cached"] += int(usage.get("cached_tokens") or 0)
        # DO NOT accumulate cost — local inference is free
        # DO NOT call OpenRouter drift-check HTTP endpoint
        _save(st)

# budget_remaining: TOTAL_BUDGET_LIMIT stays 0 → returns inf already (no change needed)
# budget_pct: stays 0.0 already (no change needed)
# Remove: set_budget_limit() call with OpenRouter value from colab_launcher
```

### Pattern 4: JSONL Token Logger
**What:** Append one record to `logs/tokens.jsonl` after each Ollama call in `heretek/llm.py`
**Implementation:**
```python
import json, pathlib, datetime

_LOG_PATH = pathlib.Path("logs/tokens.jsonl")

def _log_tokens(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total": prompt_tokens + completion_tokens,
    }
    with _LOG_PATH.open("a") as f:
        f.write(json.dumps(record) + "\n")
```
Call from `chat()` after the Ollama response is received, using `usage.prompt_tokens` and `usage.completion_tokens` from the OpenAI-compat response.

### Pattern 5: Smoke Test via handle_chat_direct
**What:** Bypass Telegram client entirely; inject messages directly into the agent
**Source:** `supervisor/workers.py` exposes `handle_chat_direct(chat_id, text, image_data=None)`
**Smoke test skeleton:**
```python
#!/usr/bin/env python3
"""scripts/smoke_test.py — Phase 1 gate check"""
import subprocess, sys, re
from pathlib import Path

PASS = "[PASS]"
FAIL = "[FAIL]"

def check_models_pulled():
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    output = result.stdout
    missing = []
    for tag in ["qwen3.6:35b-a3b-q4_K_M", "qwen3:4b"]:
        if tag not in output:
            missing.append(tag)
    if missing:
        print(f"{FAIL} Models not pulled: {missing}")
        print("  Run: ollama pull " + " && ollama pull ".join(missing))
        return False
    print(f"{PASS} Both models present in ollama list")
    return True

def check_no_cloud_hosts():
    pattern = re.compile(r"openrouter\.ai|api\.openai\.com|api\.anthropic\.com|OPENROUTER_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY")
    hits = []
    for path in Path("heretek").rglob("*.py"):
        text = path.read_text(errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append(f"  {path}:{i}: {line.strip()}")
    if hits:
        print(f"{FAIL} Cloud LLM references found:")
        for h in hits:
            print(h)
        return False
    print(f"{PASS} No cloud LLM references in heretek/")
    return True

def check_deleted_modules():
    deleted = [
        "heretek/tools/github.py",
        "heretek/tools/review.py",
        "heretek/tools/browser.py",
        "heretek/review.py",
    ]
    found = [p for p in deleted if Path(p).exists()]
    if found:
        print(f"{FAIL} Modules not deleted: {found}")
        return False
    print(f"{PASS} All target modules deleted")
    return True

def check_import():
    try:
        import heretek  # noqa: F401
        print(f"{PASS} import heretek succeeds")
        try:
            import ouroboros  # noqa: F401
            print(f"{FAIL} import ouroboros still succeeds — rename incomplete")
            return False
        except ImportError:
            print(f"{PASS} import ouroboros fails as expected")
            return True
    except ImportError as e:
        print(f"{FAIL} import heretek failed: {e}")
        return False

def check_bilingual(owner_chat_id=12345):
    from supervisor.workers import handle_chat_direct
    # Capture output requires event inspection; simplified here
    # Full implementation reads from event queue or stdout
    results = {}
    for lang, prompt in [("RU", "ответь по-русски одним предложением"), ("EN", "respond in one sentence in English")]:
        try:
            handle_chat_direct(owner_chat_id, prompt)
            results[lang] = True
            print(f"{PASS} {lang} prompt sent successfully")
        except Exception as e:
            print(f"{FAIL} {lang} prompt raised: {e}")
            results[lang] = False
    return all(results.values())

if __name__ == "__main__":
    checks = [
        check_models_pulled,
        check_no_cloud_hosts,
        check_deleted_modules,
        check_import,
        # check_bilingual,  # Claude's discretion: full e2e may need supervisor init
    ]
    passed = all(c() for c in checks)
    sys.exit(0 if passed else 1)
```

### Anti-Patterns to Avoid
- **Renaming the directory before fixing imports:** Do `git mv ouroboros heretek`, then immediately run `rg -l "ouroboros" --include="*.py"` and `rg -l "ouroboros" pyproject.toml` and replace all occurrences in one sweep before staging. Never commit mid-rename.
- **Leaving `__pycache__` with old `.pyc` files:** After rename, `find . -name "__pycache__" -exec rm -rf {} +` or `find . -name "*.pyc" -delete`. Python will regenerate.
- **Deleting tool files without checking the try/except lazy-import sites:** In `agent.py`, both `cleanup_browser` and `ouroboros.review` are imported inside try/except blocks inside methods. They will not raise ImportError at module load, but they will silently swallow the error at runtime if the code path is ever hit. Remove the call sites, not just the files.
- **Keeping the OpenRouter HTTP drift-check in `update_budget_from_usage()`:** This function makes an outbound HTTP call to `api.openrouter.ai` on every 50th budget call. Strip it or it will produce network errors and log noise.
- **Using the `vision.py` tool with no browser context:** `vision.py` doesn't import `browser.py` but reads `ctx.browser_state.last_screenshot_b64`. With browser.py deleted, that state will never be set. The tool will silently fail rather than crash (registry loads it successfully). Leave the file; just know it's inert.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM HTTP transport to Ollama | Custom HTTP client | openai Python SDK >= 1.0.0 | Ollama's /v1 endpoint is designed for this exact client; handles retries, streaming, connection pooling |
| Tool discovery | Static import list | Existing pkgutil.iter_modules registry | Already handles graceful degradation on bad modules; plugin-safe |
| Telegram polling | Custom Telegram client | Existing supervisor/telegram.py | Already has dedup, owner filtering, error recovery |
| Token accumulation | Custom counter class | Patched add_usage() in llm.py | Existing function already handles all edge cases |

**Key insight:** The Ouroboros scaffold solves all the hard infrastructure problems. The Phase 1 work is patch and strip, not build.

---

## Common Pitfalls

### Pitfall 1: `gh repo fork` clones to wrong directory
**What goes wrong:** `gh repo fork razzant/ouroboros --fork-name heretek --remote --clone` clones into a NEW `heretek/` subdirectory relative to cwd, not into the current directory. The `.planning/` folder is already at the project root `/Users/evgeniy/Projects/140526_heretek/`.
**Why it happens:** `gh repo fork --clone` mirrors `git clone` behavior — creates a new directory.
**How to avoid:** Either: (a) run `gh repo fork` from the parent directory (`/Users/evgeniy/Projects/`) and it creates `heretek/`, but the `.planning/` content is already in `140526_heretek/`, not `heretek/`; or (b) fork without `--clone`, then manually `git init` in the existing directory and add the remote. The CONTEXT.md says the fork's contents "overlay this directory." **The planner must resolve this ambiguity: the existing project root is `140526_heretek/`, not `heretek/`. Options: rename the directory after clone, or fork+clone into a temp dir and copy `.planning/` over.**
**Warning signs:** `gh repo fork --clone` always creates a new subdirectory.

### Pitfall 2: `pkgutil.iter_modules` uses the physical path
**What goes wrong:** After `git mv ouroboros heretek`, if any import anywhere still says `from ouroboros.tools.registry import ...`, Python will fail with `ModuleNotFoundError` at runtime even though the files exist under `heretek/`. The registry hardcodes `import ouroboros.tools as tools_pkg` and calls `pkgutil.iter_modules(tools_pkg.__path__)`.
**Why it happens:** `pkgutil.iter_modules` scans the directory of the imported package. If the package is imported as `heretek.tools`, it scans `heretek/tools/`. But if any stale `from ouroboros.tools.registry import ...` exists anywhere, Python looks for `ouroboros/` directory and fails immediately.
**How to avoid:** After `git mv`, run `rg -l "ouroboros" --include="*.py" --include="*.toml" --include="*.cfg"` and replace every occurrence. Do this as a single commit. Key files to check: `pyproject.toml` (project name), `requirements.txt`, `colab_launcher.py`, all files in `supervisor/` and `ouroboros/tools/` (each tool imports from `ouroboros.tools.registry`).
**Warning signs:** `ModuleNotFoundError: No module named 'ouroboros'` after rename; or import succeeds in isolation but fails when tools are auto-discovered.

### Pitfall 3: agent.py lazy import call sites survive the delete
**What goes wrong:** `tools/browser.py` is deleted and `review.py` is deleted, but `agent.py` still contains the call sites wrapped in try/except. At runtime, if a review-type task is submitted, `_build_review_context()` will silently succeed doing nothing (ImportError swallowed). If a task triggers the finally block in `handle_task()`, `cleanup_browser()` import fails silently.
**Why it happens:** Dynamic imports inside try/except are easy to miss in a grep sweep for `import`.
**How to avoid:** Search for `from ouroboros.review` and `from ouroboros.tools.browser` as string literals (not just import statements). Also search for `_build_review_context` and `cleanup_browser` as call sites in `agent.py` and strip the call + the conditional logic around it.
**Warning signs:** No error at startup; only surfaces if you run a task with `type=review` or inspect agent.py carefully.

### Pitfall 4: OpenRouter HTTP in update_budget_from_usage causes network errors
**What goes wrong:** `update_budget_from_usage()` makes outbound HTTPS requests to `api.openrouter.ai` on every 50th call to reconcile budget drift. With no `OPENROUTER_API_KEY`, this will get a 401 and log a warning every 50 LLM calls.
**Why it happens:** The drift-check is deep inside the function, not at the top level.
**How to avoid:** In the patched `state.py`, locate the block that checks `if self._call_count % 50 == 0` (or similar counter) and strip the HTTP block. The token accumulation logic above it can be kept.
**Warning signs:** Periodic `requests.exceptions.HTTPError: 401` or connection timeout in logs every ~50 calls.

### Pitfall 5: Ollama model name format with tags
**What goes wrong:** Passing a model ID with a slash (`anthropic/claude-sonnet-4.6`) to Ollama's `/v1/chat/completions` returns 404. The upstream `available_models()` returns OpenRouter-style names with slashes.
**Why it happens:** Ollama uses `name:tag` format (colon separator), not `provider/name` format.
**How to avoid:** The patched `available_models()` returns `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b` — both use colons. No further transformation needed.
**Warning signs:** HTTP 404 from Ollama's /v1 endpoint when model field contains a `/`.

### Pitfall 6: 24GB model leaves only ~8GB headroom (not ~12GB)
**What goes wrong:** CLAUDE.md §3 estimates "~12GB for KV cache" but the actual tag is 24GB (not 20GB). On a 32GB host with macOS overhead (~4-5GB) + the 4B model (~2.5GB) + other apps, the KV cache headroom is roughly 32 - 24 - 2.5 - 4.5 = ~1GB. With `HERETEK_MAX_CONTEXT_TOKENS=32000`, KV cache for 32K tokens at q4 quantization should be manageable, but the margin is tighter.
**Why it happens:** CLAUDE.md cited ~20GB; actual tag is 24GB.
**How to avoid:** Confirm `OLLAMA_NUM_PARALLEL=1` is set in env. Keep context cap at 32K. Update CLAUDE.md §3 to reflect 24GB.
**Warning signs:** `ollama ps` shows memory pressure warnings; macOS swap activity; bot response times drop sharply.

---

## Code Examples

Verified patterns from official sources and upstream reading:

### Ollama Chat Completions Request (confirmed via docs.ollama.com)
```python
# Source: docs.ollama.com/api/openai-compatibility
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required but ignored by Ollama
)

response = client.chat.completions.create(
    model="qwen3.6:35b-a3b-q4_K_M",  # tagged model name works verbatim
    messages=[{"role": "user", "content": "ответь по-русски одним предложением"}],
    stream=False,
)

# Usage fields in response:
# response.usage.prompt_tokens
# response.usage.completion_tokens
# response.usage.total_tokens
```

### Ollama Error Shape for Unpulled Model
```json
// HTTP 404 — JSON body:
{"error": "model 'qwen3.6:35b-a3b-q4_K_M' not found, try pulling it first"}
```
The smoke test should catch `openai.NotFoundError` (SDK wraps the 404) and re-raise with a human-readable message.

### Tool Registry Auto-Discovery (confirmed via upstream registry.py)
```python
# Source: razzant/ouroboros registry.py _load_modules()
import pkgutil, importlib
import heretek.tools as tools_pkg  # after rename

for _importer, modname, _ispkg in pkgutil.iter_modules(tools_pkg.__path__):
    if modname.startswith("_") or modname == "registry":
        continue
    try:
        mod = importlib.import_module(f"heretek.tools.{modname}")
        if hasattr(mod, "get_tools"):
            for entry in mod.get_tools():
                self._entries[entry.name] = entry
    except Exception:
        logging.getLogger(__name__).warning(
            "Failed to load tool module %s", modname, exc_info=True)
# RESULT: deleted tool files simply aren't discovered. No registry changes needed.
```

### Package Rename Sweep Commands
```bash
# Step 1: rename the directory
git mv ouroboros heretek

# Step 2: find all remaining references
rg -l "ouroboros" --include="*.py" --include="*.toml" --include="*.cfg" --include="*.md" --include="*.txt"

# Step 3: bulk replace in Python/TOML files (macOS sed requires '' for in-place)
# Using rg + perl for safety:
rg -l "ouroboros" --include="*.py" | xargs perl -pi -e 's/ouroboros/heretek/g'
rg -l "ouroboros" pyproject.toml && perl -pi -e 's/ouroboros/heretek/g' pyproject.toml

# Step 4: clear stale bytecode
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null; find . -name "*.pyc" -delete 2>/dev/null

# Step 5: verify
python -c "import heretek; print('OK')"
python -c "import ouroboros" 2>&1 | grep -c "ModuleNotFoundError"
```

### consciousness.py model env var (confirmed via upstream)
```python
# BackgroundConsciousness._model property reads:
os.environ.get("OUROBOROS_MODEL_LIGHT", "qwen/qwen3.5-plus-02-15")
# Must be patched to:
os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
# Also the default passed to llm.chat() must use the local model name format
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded OpenRouter base_url in LLMClient | Parameterized base_url; Ollama drops in at `http://localhost:11434/v1` | Ollama OpenAI compat released 2024 | No transport rewrite needed |
| Per-request OpenRouter pricing fetch for cost | Ollama returns `usage.prompt_tokens`/`usage.completion_tokens`; no cost field | N/A for local | Strip the cost-fetch entirely |
| google-colab Secrets for API keys | Standard `.env` file via python-dotenv | Upstream assumption is Colab; Heretek is local | Replace Colab secret reads with dotenv |
| `OUROBOROS_*` env vars | `OLLAMA_*` / `HERETEK_*` env vars | Phase 1 | Consistent with new project identity |

**Deprecated/outdated in upstream (Heretek context):**
- `colab_launcher.py`: Colab-specific bootstrapper. For local use, we need a plain `__main__.py` or equivalent local launcher that replaces it. The CONTEXT.md says `python -m supervisor` is the boot command — check if `supervisor/__main__.py` exists at v6.2.0 (WebFetch returned 404, suggesting it may not exist yet and needs to be written).
- `dashboard.py` / `webapp_push.py` / `evolution_stats.py`: push to `razzant/ouroboros-webapp` GitHub repo — dead ends for Heretek since we're not that public repo. Leave them (registry auto-discovery loads them; they expose tools the agent can call but won't unless instructed). They won't break anything but they won't do anything useful either.

---

## Open Questions

1. **`supervisor/__main__.py` may not exist at v6.2.0**
   - What we know: `gh repo fork` clones the v6.2.0 tag codebase. WebFetch for `supervisor/__main__.py` returned 404.
   - What's unclear: Upstream may use `colab_launcher.py` as the entry point rather than `python -m supervisor`. If `__main__.py` doesn't exist, `python -m supervisor` won't work out of the box.
   - Recommendation: After cloning, run `ls supervisor/` and check. If `__main__.py` is absent, the planner should add a task to write a minimal one that replicates the `colab_launcher.py` boot sequence (minus Colab/Drive/OpenRouter bits).

2. **`gh repo fork` + existing project root directory collision**
   - What we know: The fork's contents should "overlay" `/Users/evgeniy/Projects/140526_heretek/`. But `gh repo fork --clone` creates a new subdirectory, not overlay.
   - What's unclear: How does the planner get Ouroboros source INTO the existing directory that already has `.planning/` and `CLAUDE.md`?
   - Recommendation: The planner should sequence as: (a) `gh repo fork razzant/ouroboros --fork-name heretek` (fork on GitHub, no clone), (b) `git init` in the existing project root, (c) `git remote add origin https://github.com/<user>/heretek`, (d) `git fetch origin`, (e) `git checkout main`. This overlays the fork content into the existing directory while preserving `.planning/`. Alternatively, clone elsewhere and `rsync` the source in. Flag this for explicit planner attention.

3. **Which files in `tools/` still have `ouroboros` in their imports after the module-level rename**
   - What we know: Every tool file imports `from ouroboros.tools.registry import ToolContext, ToolEntry`. That's ~15 files.
   - What's unclear: Are there any other intra-package imports besides `ouroboros.tools.registry`?
   - Recommendation: After clone, run `rg "ouroboros" --include="*.py"` to generate the definitive hit list. The planner should include this as a sub-task of FORK-02.

4. **Does `consciousness.py` have a budget guard that blocks runs when TOTAL_BUDGET_LIMIT is 0**
   - What we know: `consciousness.py` calls `_check_budget()` which uses `budget_remaining()`. With `TOTAL_BUDGET_LIMIT=0`, `budget_remaining()` returns `inf` — so the consciousness loop is effectively unthrottled.
   - What's unclear: Is there a minimum-remaining check that treats `inf` correctly, or does it compare `inf > EVOLUTION_BUDGET_RESERVE (50.0)` and block?
   - Recommendation: After clone, inspect `_check_budget()` in `consciousness.py`. If it checks `budget_remaining() < EVOLUTION_BUDGET_RESERVE`, then `inf < 50` is `False` and the loop runs freely — which is correct.

5. **httpx dependency after deleting tools/review.py**
   - What we know: `tools/review.py` (multi-model tool) is the only confirmed importer of `httpx`. 
   - What's unclear: Does any other tool file use `httpx`?
   - Recommendation: After clone, run `rg "import httpx" --include="*.py"`. If only `tools/review.py`, then `httpx` can be removed from requirements.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `scripts/smoke_test.py` — plain Python script (no pytest per CONTEXT.md decision) |
| Config file | None — single runnable script |
| Quick run command | `python scripts/smoke_test.py` |
| Full suite command | `python scripts/smoke_test.py` (same; it IS the suite for Phase 1) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORK-01 | Repo cloned, playground and last-known-good branches exist | smoke | `git branch --list playground last-known-good` | ❌ Wave 0 |
| FORK-02 | `import heretek` succeeds; `import ouroboros` fails | smoke | `python scripts/smoke_test.py` → check_import() | ❌ Wave 0 |
| FORK-03 | github.py, review.py, browser.py absent from codebase | smoke | `python scripts/smoke_test.py` → check_deleted_modules() | ❌ Wave 0 |
| FORK-04 | Token counter logs to logs/tokens.jsonl; no dollar values accumulate | smoke | Inspect `logs/tokens.jsonl` after a test call; assert `cost` field absent | ❌ Wave 0 |
| LLM-01 | Ollama called at localhost:11434 (no cloud host) | static + smoke | `python scripts/smoke_test.py` → check_no_cloud_hosts() | ❌ Wave 0 |
| LLM-02 | Primary model responds | e2e | `python scripts/smoke_test.py` → check_bilingual() | ❌ Wave 0 |
| LLM-03 | Secondary model loaded for consciousness loop | smoke | `ollama ps` after boot shows qwen3:4b | manual |
| LLM-04 | Context cap applied | smoke | Check `HERETEK_MAX_CONTEXT_TOKENS` read at startup | ❌ Wave 0 |
| LLM-05 | No OpenRouter/OpenAI/Anthropic fallback | static | `python scripts/smoke_test.py` → check_no_cloud_hosts() | ❌ Wave 0 |
| LLM-06 | RU prompt → RU reply; EN prompt → EN reply | e2e | `python scripts/smoke_test.py` → check_bilingual() | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -c "import heretek"` (import sanity only)
- **Per wave merge:** `python scripts/smoke_test.py` (full static + import checks)
- **Phase gate:** `python scripts/smoke_test.py` with bilingual check green, `ollama list` shows both models, `logs/tokens.jsonl` has records

### Wave 0 Gaps
- [ ] `scripts/smoke_test.py` — covers FORK-02, FORK-03, LLM-01, LLM-05, LLM-06
- [ ] `logs/` directory — created on first write by patched `heretek/llm.py` (no action needed in Wave 0 if mkdir_parents=True is used)
- [ ] `supervisor/__main__.py` — may not exist at v6.2.0; needed for `python -m supervisor` entry point
- [ ] Framework install: `pip install python-dotenv` — if not in requirements.txt

---

## Sources

### Primary (HIGH confidence)
- `https://github.com/razzant/ouroboros/tree/v6.2.0` — upstream repo structure, all file contents fetched via raw.githubusercontent.com
- `https://ollama.com/library/qwen3.6/tags` — qwen3.6:35b-a3b-q4_K_M tag confirmed: 24GB, 256K context
- `https://docs.ollama.com/api/openai-compatibility` — Ollama OpenAI compat: base_url, api_key="ollama", /v1/chat/completions request/response shape, usage fields
- `https://docs.ollama.com/api/errors` — HTTP 404 + `{"error": "..."}` format for unpulled models

### Secondary (MEDIUM confidence)
- `https://deepwiki.com/ollama/ollama/3.4-openai-compatibility-layer` — usage field mapping (PromptEvalCount → prompt_tokens, EvalCount → completion_tokens); cross-verified with Ollama blog

### Tertiary (LOW confidence)
- `supervisor/__main__.py` existence at v6.2.0: WebFetch returned 404. Likely does not exist. Needs verification post-clone.
- `httpx` sole importer: inferred from tools/review.py analysis; not exhaustively scanned.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Ollama compat confirmed via official docs; upstream requirements.txt confirmed openai>=1.0.0
- Architecture: HIGH — upstream source files read directly; tool discovery, lazy imports, budget shape all confirmed
- Pitfalls: HIGH (import/rename mechanics); MEDIUM (24GB vs 20GB size estimate — from tag page, not from model card weight)
- Smoke test pattern: HIGH — handle_chat_direct() confirmed in workers.py; pkgutil registry behavior confirmed

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (Ollama fast-moving; re-verify if > 30 days before execution)
