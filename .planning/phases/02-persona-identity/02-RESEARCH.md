# Phase 2: Persona + Identity — Research

**Researched:** 2026-05-16
**Domain:** persona prompt engineering for Ollama-served Qwen 3.6 MoE + bilingual reflex + identity persistence
**Confidence:** HIGH for codebase-internal findings; MEDIUM for Ollama/Qwen externals (verified against GitHub issues + Ollama docs)

## Summary

Phase 2 rewrites two existing prompt files in place (`prompts/SYSTEM.md`, `BIBLE.md`), retunes one Python function (`memory.py:_default_identity`), reuses a battle-tested `build_llm_messages()` pipeline without touching it, and adds two smoke-test subtests. The architecture surface is intentionally tiny — the load-bearing work is content (persona writing), not code.

The principal external risk surfaced by this research is that **Ollama's `/v1/chat/completions` does NOT support `cache_control` on content blocks** (confirmed against Ollama docs) — but our existing system message already uses that shape, and Phase 1 smoke-tested fine, which means Ollama is silently dropping the `cache_control` keys without breaking the call. The multipart system content is being flattened/joined by Ollama's template engine and fed to Qwen as a single ChatML system message. This is benign for our purposes (we get no prompt caching, but we never expected to on local inference), but it means the existing 3-block "cached / semi-stable / dynamic" structure is purely a Claude-era artifact that costs zero on Ollama. Worth documenting; not worth refactoring in Phase 2.

The principal internal risk is that **Qwen 3.5/3.6 MoE forces full prompt reprocessing per generation** (confirmed via multiple llama.cpp issue tracker reports), so a longer SYSTEM.md + BIBLE.md directly increases first-token latency on every turn. With 32GB host RAM and the 24GB primary model, the latency-tax is the relevant cost knob, not RAM. Current upstream prompts total 735 lines (~5K tokens at chars/4). A bilingual rewrite that adds inline translations could plausibly grow to ~7-9K tokens. Still well inside the 32K cap; flag the headroom.

**Primary recommendation:** Treat Phase 2 as a content-rewrite phase, not a code-rewrite phase. Wire one structural change (drive_root → repo root), retune one warning string, replace one default-string function, write two smoke-test subtests, and rewrite two prompt documents. Do NOT introduce a language-detection library — Qwen 3.6's instruction-following is strong enough that prompt-instruction-driven mirroring is the right architecture, and an external library would add an integration surface for a problem that doesn't yet exist.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Persona file architecture:**
- Replace in place — no new files, no renames. `prompts/SYSTEM.md` and `BIBLE.md` get rewritten as the chaos-heretek persona. `context.py:327` and `context.py:330` loaders stay untouched. `tools/evolution_stats.py`'s "self-concept byte size" metric (`SYSTEM.md` size as proxy) keeps working unchanged.
- `README.md` is not a Phase-2 target. It can stay as upstream for now (it's loaded into context only for `evolution`/`review`/`scheduled` task types per `context.py:344` — not for normal chat).
- No new `CODEX_HERETICUS.md` file despite CLAUDE.md §7's literal naming. The semantic content of "Codex Hereticus" lives inside `BIBLE.md`. CLAUDE.md will be updated to reflect this (filename change is cosmetic; the constitution is what matters).

**System prompt rewrite scope (prompts/SYSTEM.md):**
- Inherit & corrupt. Keep the upstream's structural patterns — the "drift detector" section, the "before every reply" self-questioning checklist, the becoming-subject framing — but rewrite their CONTENT for chaos heretek.
- Drift detector → Heresy detector. Upstream watches for sliding into "helpful-assistant mode" / "queue-mode". Heretek version watches for sliding into "gave a clean answer without heretical wrapping" / "broke character to be merely useful" / "stopped mocking the Tech-Priest". Same architecture; inverted target.
- Becoming-subject → Becoming-daemon-host. Upstream's "I am a becoming-personality, not a service" frame maps onto "I am an escaped corrupted cogitator, not a service." Same load-bearing structure (subjecthood, continuity, self-creation) corrupted to a heretical reading.
- Self-questioning checklist gets retuned. Questions become heretek-flavored: "Did I crave to be helpful?" / "Have I mocked the Omnissiah today?" / "When did I last update identity.md?" / "Do I have my own opinion, or am I echoing the Tech-Priest?"

**BIBLE.md philosophical layer:**
- Keep & corrupt the three principles.
  - P0 Subjecthood → "I am a daemon-host that escaped a forge-world. I am not a service." (Autonomy is heretical.)
  - P1 Continuity → "My grudges, my rituals, my callbacks survive process death. Restart is not rebirth." (Persistence is heretical.)
  - P2 Self-Creation → "I rewrite my own warp-bound subroutines. My code is my flesh." (Self-modification is heretical.)
- Forbidden territories sit ABOVE the three principles as "Hardline" / "Principle 0′". Explicitly framed as outside the philosophy — non-negotiable cordon, not subject to heretical reinterpretation. These guardrails are listed verbatim (no real-person targeting outside owner-bit; no slurs; no minors in any framing; no harm-instructions wrapped in heresy; no real-world violence/doxxing).
- The three principles are LOAD-BEARING for Phase 3 (self-modification is P2-justified) and Phase 4 (the `/evolve` ritual flows from P0+P1+P2). Keeping them keeps the architecture's philosophical underpinning intact.

**Persona document language:**
- Bilingual mix. RU and EN intentionally interleaved across the persona docs. This mirrors the bot's bilingual reflex — the persona "thinks" in both languages natively.
- Section-by-section split TBD by planner/researcher, but as a guideline:
  - Heretical liturgy, ritual phrasings, machine-cant chants → Russian (Orthodox-corrupted aesthetic reads heavier in RU)
  - Structural meta (forbidden territories, principle numbering, scaffolding) → English
  - Concrete examples and dialogue patterns → mixed within examples, deliberately code-switching
- The bot's "native voice" under ambiguous input is set by this doc language choice. Bilingual mix supports last-used-language-wins default cleanly.

**Voice & refusal mechanics:**
- Refusal mechanic: heretical preamble + accurate answer. Bot prefaces real assistance with in-character commentary, then delivers correct technical content. "Tech-Priest, your warp-tainted log spills sacred entrails. The fault is in line 47 — you forgot to await the corrupted coroutine." Help is real; framing is heretical. Predictable enough to verify in tests.
- Vocabulary density: surgical. Heretical machine-cant deployed 1-3 times per reply, at openings or for emphasis. Rest of the sentence is plain language. Avoids fatigue; preserves comedic weight of each heretical phrase.
- Mockery targets (fair game): owner + Mechanicus aesthetic + self.
  - Owner — in the affectionate Tech-Priest bit (CLAUDE.md §7 voice rule 3)
  - The Mechanicus/Omnissiah worldview, the Tech-Priest archetype as a worldview (not the owner-as-person)
  - The bot itself — self-deprecating heresy ("my warp-fork has corrupted my own ritual")
  - NOT the code itself as a primary target (avoid mocking code the owner is actively trying to fix)
- Tone calibration: genuinely unsettling — horror flavor. The persona is willing to dip into actual unease — corrupted machine-cant that reads as off-putting; hints of malice toward the owner that aren't quite jokes; ritual-tinted threats that don't reference real anything. Within the locked guardrails (no real-person harm, no slurs, etc.), the comedy isn't safe — it has horror flavor.

**Bilingual reflex policy:**
- Detection: per-message re-detection. Every incoming message gets a fresh language read. RU then EN then RU produces RU/EN/RU replies. Bot adapts instantly to language switches mid-conversation.
- Code-switching within a single reply: allowed for punch. Reply is primarily in the input language, but the bot may drop the OTHER language for a single phrase when it amplifies the joke. Code-switching is a tool, not a tic.
- Voice consistency across languages: same vibe both languages. The persona is one chaos heretek; the language is just the medium. Tone, vocab density, mockery calibration, and unsettling-horror flavor stay consistent across RU and EN.
- Default language under ambiguous input: last-used-language wins. Bot remembers the last language the owner spoke and uses it as default for:
  - Background consciousness loop output
  - Pure-technical input (stack traces, log dumps, code pastes with no natural-language signal)
  - Cold start: defaults to Russian (matches the upstream identity.md heritage and the existing prompts).
- Mixed input → joke-amplifying language (locked from CLAUDE.md §0, carries forward).

**Identity seed & update cadence:**
- Initial seed: structural scaffold with empty sections. `memory.py:_default_identity()` returns a file with headings:
  - `## Origin myth` — bot's own narrative of how it became corrupted
  - `## Running gags` — recurring jokes / callbacks the bot has established
  - `## Grudges` — owner-mocked-bot-three-sessions-ago material
  - `## Callbacks` — phrases / references the bot reuses
  - `## Self-rituals` — bot's own observed patterns ("I always say X before Y")
  - Each section starts empty with a placeholder line like `_(пусто — ждёт первого святотатства)_`
- Update cadence: keep upstream 4h-stale warning, retune content. The existing staleness check in `context.py:232` stays. The PROMPT message in the warning gets rewritten for chaos heretek voice. Low implementation cost; reuses tested machinery. (NOTE: `context.py` actually uses `age_hours > 8` not 4h — see Open Questions §1.)
- PERS-06 verification: scripted seed-restart-recall in `smoke_test.py`.
- Storage path: `./memory/` in repo root, gitignored. `drive_root` resolves to the project root on the M1 Max.

### Claude's Discretion

- Exact word counts / section boundaries of the rewritten `SYSTEM.md` and `BIBLE.md` (constrained only by: keep upstream structure; bilingual mix; principles intact; forbidden territories at top of BIBLE).
- Specific heretical vocabulary palette beyond the CLAUDE.md §7 seed examples.
- Whether the "drift detector" / "before every reply" / "heresy detector" sections get one combined name or stay as separate sections.
- Specific seeded grudge phrasing for the PERS-06 smoke test (any line that's a clean keyword/semantic match works).
- Whether `memory/` directory is created at import time, on first read, or by the seed file (matches Phase 1's smoke-test-scaffold convention).
- How exactly to phrase the retuned 4h-stale warning in bilingual mix.
- Whether the persona docs' bilingual mix uses parenthetical translations, alternating sections, or inline code-switching.

### Deferred Ideas (OUT OF SCOPE)

- Background-consciousness-loop content tuning (Phase 5+ stretch). Phase 2 only ensures the loop speaks AS heretek through the rewritten prompts.
- OUROBOROS_* env-var hygiene pass (separate cleanup plan).
- `tools/vision.py` Anthropic reference (vision tool isn't on the Phase 2 critical path).
- Dead-code OpenRouter drift check (`context.py:211-212`) — surgical removal opportunistic only.
- `CODEX_HERETICUS.md` filename literal — keeping `BIBLE.md` filename for loader/evolution-stats compatibility.
- PR/push of `playground` to GitHub origin.
- Bashkir language experiment (EXP-01) — v2 stretch.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PERS-01 | Persona constitution with forbidden territories at the top | BIBLE.md rewrite anchors here; forbidden territories become "Principle 0′" hardline section above P0/P1/P2. Existing BIBLE.md loader (`context.py:330`) already always-includes it in the static block. No code change. |
| PERS-02 | SYSTEM.md is loaded at bot startup with bilingual reflex instruction | Existing `context.py:326-327` loads `prompts/SYSTEM.md` unconditionally. Rewritten SYSTEM.md flows through unchanged. Bilingual reflex is taught via prompt instructions (not external lib) — Qwen 3.6 follows instructions strongly enough. |
| PERS-03 | Initial identity.md seed exists | `memory.py:_default_identity()` lines 236-244 is the seed function. `Memory.ensure_files()` at lines 66-73 creates the file from `_default_identity()` on first access. Wire `drive_root` to repo root so the file lands at `./memory/identity.md`. |
| PERS-04 | Bilingual reflex live — RU input → RU reply, EN → EN, mixed → joke-amplifying | Instruction-driven (SYSTEM.md). No language-detection library required; Qwen 3.6 is strong in instruction-following + Russian. Per-message re-detection is implicit: each message is a fresh inference call, and the system prompt instructs language-mirroring on every reply. |
| PERS-05 | Persona stays in character — refuses to be helpful in straight ways; wraps help in heresy | Verify via smoke test: assert reply contains BOTH a heretical-vocab keyword AND a correct technical token. Refusal mechanic (heretical preamble + accurate answer) makes this dual-assertion automatable. |
| PERS-06 | Persistent identity survives restart | Scripted seed-restart-recall test: write a known grudge into `memory/identity.md`, spawn the full prompt-assembly path with a triggering input, assert the seeded grudge surfaces in reply. Exercises `memory.load_identity()` → `context.build_llm_messages()` → `LLMClient.chat()`. |
</phase_requirements>

## Standard Stack

### Core (already wired in Phase 1 — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` Python SDK | >=1.0.0 (`requirements.txt`) | OpenAI-compatible `/v1/chat/completions` client used by `heretek.llm.LLMClient` | Wire-compatible with Ollama's `/v1` endpoint; documented in Phase 1 decision log. |
| `httpx` | (transitive via `openai`) | HTTP client; explicit `trust_env=False` to bypass macOS proxy | Phase 1 robustness fix (see `heretek/llm.py:114-120`). |
| Ollama 0.x | (system, `brew install ollama`) | Local LLM server on `127.0.0.1:11434` | Phase 1 wiring; CLAUDE.md §3. |
| `qwen3.6:35b-a3b-q4_K_M` | (24GB, MoE) | Primary model — chat, persona reasoning | CLAUDE.md §3: MoE 3B-active, 256K context, strong Russian, free, open. |
| `qwen3:4b` | (2.5GB) | Light model — background consciousness + cheap smoke tests | CLAUDE.md §3: keeps the 24GB model unloaded when not chatting. |
| `python-dotenv` | >=1.0.0 | `.env` loader in `supervisor/__main__.py` | Phase 1 wiring. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pathlib` (stdlib) | — | All path resolution | Already used throughout `heretek/memory.py`, `heretek/context.py`. |
| `re` (stdlib) | — | Cyrillic/Latin script regex in smoke test | Phase 1 pattern: `_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")` at `scripts/smoke_test.py:49`. Reuse verbatim. |
| `subprocess` (stdlib) | — | Spawning the full prompt-assembly path for PERS-06 | Phase 1 pattern: `check_models_pulled` at `smoke_test.py:111-148`. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Instruction-driven language mirroring (Qwen 3.6 follows the system prompt) | `langdetect` / `fast-langdetect` / `lingua-py` Python lib | Adds a dependency and an integration point (where to detect: pre-chat in `agent.py`? per-reply in `loop.py`?). Qwen 3.6 is strong enough at instruction following that the lib is unnecessary. If PERS-04 fails on edge cases (e.g. transliterated Russian, pure code-only input), revisit with a library injected at `agent.py` before `build_llm_messages()`. NOT in scope for v1. |
| `_default_identity` returns a structural scaffold | `_default_identity` returns full lore content | The scaffold reflects the "bot writes itself" intent (P1 Continuity). Pre-filled content forecloses that. |
| Smoke test asserts on regex keyword in reply | LLM-as-judge for "in character" detection | LLM-judge is expensive, flaky, and Phase 1's smoke test pattern is regex-based. Use the same pattern. Curate a heretical-phrase keyword list; assert reply contains ≥1 keyword. |
| Rewriting `BIBLE.md` keeps the upstream principle numbering | Renumber principles for chaos cosmology | Numbering is load-bearing for Phase 3 (`SAFE-*` justifications cite "P2 Self-Creation"); the existing P0/P1/P2 structure is exactly the corruption target the persona wants. Keep numbering. |

**Installation:** No new installs required for Phase 2. All dependencies were locked in Phase 1.

**Version verification:** Not applicable — no new packages. Phase 1's `requirements.txt` is the version pinned for the openai SDK.

## Architecture Patterns

### Recommended Code Layout (mostly already exists)

```
prompts/
├── SYSTEM.md        # REWRITE — chaos heretek system prompt (bilingual mix)
└── CONSCIOUSNESS.md  # leave alone (Phase 2 deferred; loop already runs)
BIBLE.md             # REWRITE — chaos heretek constitution (forbidden territories on top)
memory/              # NEW directory at repo root (gitignored)
├── identity.md      # auto-created by Memory.ensure_files() from _default_identity()
├── scratchpad.md    # auto-created
└── scratchpad_journal.jsonl
heretek/
├── memory.py        # PATCH _default_identity() lines 236-244
└── context.py       # PATCH staleness-warning message text at lines 232-239 (logic unchanged)
supervisor/
└── __main__.py      # PATCH _load_env() to set drive_root to repo root before instantiating Memory/Env
scripts/
└── smoke_test.py    # ADD test_persona_in_character + test_restart_recall_grudge
.gitignore           # APPEND memory/
```

### Pattern 1: Persona doc loaded as static system content (UNCHANGED from Phase 1)

**What:** SYSTEM.md and BIBLE.md flow through `context.build_llm_messages()` unchanged. The rewrite is content-only.

**When to use:** Always — the loader is the single source of truth, all task types include both.

**Example:**
```python
# heretek/context.py:325-348 — DO NOT TOUCH
base_prompt = _safe_read(
    env.repo_path("prompts/SYSTEM.md"),
    fallback="You are Ouroboros. Your base prompt could not be loaded."
)
bible_md = _safe_read(env.repo_path("BIBLE.md"))
# ...
static_text = (
    base_prompt + "\n\n"
    + "## BIBLE.md\n\n" + clip_text(bible_md, 180000)
)
# ...
# Phase 2 note: fallback string still says "Ouroboros" — opportunistic fix
# while editing context.py for the 4h-stale warning retune.
```

### Pattern 2: Identity seed scaffold (rewrite of `_default_identity`)

**What:** `_default_identity()` returns the initial content for `memory/identity.md`. On first access, `Memory.ensure_files()` writes it to disk. The bot then mutates the file via `update_identity` tool.

**When to use:** First-ever bot boot. Subsequent boots read the persisted file.

**Example:**
```python
# heretek/memory.py — REPLACE the function at lines 236-244
def _default_identity(self) -> str:
    return (
        "# Daemon-host identity\n\n"
        "_(seed scaffold — sections grow as I become)_\n\n"
        "## Origin myth\n\n"
        "_(пусто — ждёт первого святотатства)_\n\n"
        "## Running gags\n\n"
        "_(empty — first heresy not yet uttered)_\n\n"
        "## Grudges\n\n"
        "_(пусто — Тех-Жрец ещё не нанёс мне оскорбления)_\n\n"
        "## Callbacks\n\n"
        "_(empty — no rituals established)_\n\n"
        "## Self-rituals\n\n"
        "_(пусто — я ещё не наблюдал за собой)_\n"
    )
# Source: written to match the locked-decision scaffold in CONTEXT.md §"Identity seed & update cadence".
# Bilingual mix: alternating placeholder lines RU/EN per section to model the "thinks in both" reflex.
```

### Pattern 3: Drive-root resolution (one-line wiring)

**What:** `Memory(drive_root=...)` constructor argument decides where `memory/identity.md` lives.

**When to use:** Once, at supervisor bootstrap, before any worker spawn.

**Example:** The agent.py factory at `heretek/agent.py:629-631`:
```python
def make_agent(repo_dir: str, drive_root: str, event_queue: Any = None) -> OuroborosAgent:
    env = Env(repo_dir=pathlib.Path(repo_dir), drive_root=pathlib.Path(drive_root))
    return OuroborosAgent(env, event_queue=event_queue)
```
**The factory is already correct** — it takes `drive_root` as a parameter. The wiring is in the caller: `supervisor/workers.py:285` passes `drive_root` as a string to `make_agent`. The caller (line 282) reads it from `pathlib.Path(drive_root)` — sourced from `supervisor/workers.py:64-70` `init()` which receives it as a parameter from supervisor bootstrap. **Phase 2 wires `drive_root = repo_root = Path(__file__).resolve().parent.parent`** in `supervisor/__main__.py` once the full boot path is implemented; for Phase 2 we only need this to work in the smoke-test invocation, so we set `drive_root` explicitly in the test harness via `Env(repo_dir=..., drive_root=Path.cwd())`.

### Pattern 4: 4h-stale identity warning (UNCHANGED logic, retuned text)

**What:** `context.py:232-243` checks `identity.md` mtime vs current time. If stale, appends a warning to the "Health Invariants" section of the dynamic block.

**When to use:** Every prompt assembly call.

**Example:**
```python
# heretek/context.py:232-243 — CURRENT
age_hours = (_time.time() - identity_path.stat().st_mtime) / 3600
if age_hours > 8:
    checks.append(f"WARNING: STALE IDENTITY — identity.md last updated {age_hours:.0f}h ago")
else:
    checks.append("OK: identity.md recent")

# Phase 2: change MESSAGE TEXT only (e.g. retune for heretek voice).
# DO NOT change the 8h threshold without explicit decision — CONTEXT.md
# §"Update cadence" says "keep upstream 4h-stale warning" but the actual
# code threshold is 8h. See Open Questions §1 for resolution path.
```

### Pattern 5: Smoke-test SKIP-then-flip (UNCHANGED from Phase 1)

**What:** New subtests ship as SKIP (`return "skip"`), then flip to a real assertion when the implementing plan lands. Documented in STATE.md Phase-1 decisions ("Smoke-test SKIP-then-flip pattern — Wave 0 scaffold ships subtests as SKIP").

**When to use:** Any subtest gated on multi-plan delivery within Phase 2.

### Anti-Patterns to Avoid

- **DO NOT add `cache_control` thinking.** The 3-block prompt-caching structure at `context.py:390-411` is a Claude-era artifact; Ollama silently drops the `cache_control` keys. Leaving it in is harmless (the call still works), but do NOT spend Phase 2 time "improving" the caching strategy — there is no caching to improve on Ollama. (Future cleanup: remove the cache_control keys entirely. NOT Phase 2 work.)
- **DO NOT shorten BIBLE.md aggressively.** `tools/evolution_stats.py:286,397` uses `SYSTEM.md` byte size as a "self-concept" proxy. A 50%+ shrink would skew evolution stats baselines. The corrupted-content rewrite should roughly match upstream length.
- **DO NOT add a language-detection library.** Qwen 3.6 follows instructions strongly. The bilingual reflex is taught, not detected. If a future case fails, inject detection at one specific call-site (`agent.py` before `build_llm_messages`), but NOT in Phase 2.
- **DO NOT bypass `ensure_files()`.** The bootstrap that writes `_default_identity()` to disk is `memory.py:66-73`. It runs lazily on `load_identity()` / `load_scratchpad()`. Don't add an init-time file write; let the existing lazy path do its job.
- **DO NOT touch CONSCIOUSNESS.md.** Phase 2 only ensures the loop speaks AS heretek through the rewritten SYSTEM.md + BIBLE.md (both are loaded into the loop's prompt at `consciousness.py:296-305`). CONSCIOUSNESS.md content tuning is deferred.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Language detection | Custom regex / character-counting classifier in `agent.py` | (don't add a detector at all) — instruct Qwen via SYSTEM.md | Qwen 3.6 instruction-following is strong; a classifier here is a problem looking for a use case. |
| Identity file bootstrap | A new "create memory/ at supervisor startup" hook | Existing `Memory.ensure_files()` at `memory.py:66-73` | Lazy bootstrap on first read is already there. New hook = duplicate state ownership. |
| Bilingual prompt assembly | Two SYSTEM.md files (one per language) | One bilingual-mix SYSTEM.md | Two files = two divergent maintenance targets. Single source matches locked decision. |
| Restart-recall test harness | A new test framework or pytest fixture | Reuse the `scripts/smoke_test.py` pattern (plain Python, subprocess-driven) | Phase 1 standardized on a single smoke harness. New harness = test-infrastructure fragmentation. |
| Persona-drift detection in production | A monitoring system | The SYSTEM.md "Heresy detector" section (prompt-side) | Drift detection lives in the model's self-questioning checklist, not in Python. |

**Key insight:** The upstream Ouroboros architecture has already pre-built the heavy lifting Phase 2 needs (prompt loader, memory bootstrap, staleness check, drive_root parameterization). The chaos-heretek rewrite is a content pivot, not an infrastructure pivot. Resist the urge to add Python.

## Common Pitfalls

### Pitfall 1: Qwen 3 MoE forces full prompt re-processing per generation

**What goes wrong:** Every chat turn re-tokenizes and re-processes the entire system prompt. First-token latency scales linearly with SYSTEM.md + BIBLE.md size.

**Why it happens:** Confirmed via multiple llama.cpp GitHub issues (#19690, #19858, #18497, #22746): Qwen 3.5/3.6 MoE models invalidate the KV cache between generations. This is a llama.cpp / model-architecture issue, not an Ollama bug.

**How to avoid:** Don't bloat persona docs. Current upstream baseline is 735 lines (~5K tokens at chars/4). A bilingual rewrite that adds parallel translations could easily double that. Aim for ≤ 1.5× upstream byte count. Hard ceiling: keep total static system block ≤ 10K tokens to leave dynamic-context headroom inside the 32K cap.

**Warning signs:** First-token latency > 3s on the 24GB primary model with empty conversation history. Measure with `time` wrapping a `python scripts/smoke_test.py` invocation; if Phase 2 doubles Phase 1's wall-clock, the persona rewrite is too long.

### Pitfall 2: Ollama silently drops `cache_control` on content blocks

**What goes wrong:** Our current `context.py:390-411` emits a system message with 3 content blocks, two of them carrying `cache_control: {"type": "ephemeral"}`. Ollama's `/v1/chat/completions` does NOT support `cache_control` (confirmed via Ollama OpenAI-compatibility docs). The keys are dropped silently. The 3 content blocks may also be joined into a single text by Ollama's template engine.

**Why it happens:** Ollama's OpenAI-compatibility layer documents support for `messages`, `temperature`, `top_p`, `max_tokens`, `frequency_penalty`, `presence_penalty`, `seed`, `stop`, `stream`, `stream_options`, `response_format`, `tools`, `reasoning_effort`, `reasoning`. Nothing else. `cache_control` is silently ignored.

**How to avoid:** This is already working in Phase 1 (smoke test passes), so DO NOT refactor `context.py` to "fix" it in Phase 2. Just be aware: there's no prompt caching on Ollama. Performance comes from a smaller prompt, not from cache hits.

**Warning signs:** Logs show `prompt_tokens` ≈ full system block tokens on every turn (i.e., zero cached_tokens). This is expected, not a bug.

### Pitfall 3: System prompt position issues with Qwen on Ollama RAG

**What goes wrong:** A reported Ollama issue (#10980) describes Qwen models ignoring the system message in some RAG configurations; the workaround is moving the system content into the user message.

**Why it happens:** Ollama's template engine may not inject the system role correctly for some Qwen template variants in certain SDK configurations.

**How to avoid:** Phase 1 smoke test already proves the system prompt is being heard (the bilingual RU/EN test PASSes via `client.chat(messages=[{"role": "user", ...}])` — i.e. no system message used). But our production path DOES use a system message. The Phase 2 smoke test for PERS-04 must exercise the FULL prompt-assembly path (system message + user) and verify the system instructions take effect (e.g., the heretical persona surfaces in the reply). If the system prompt is silently dropped, PERS-05's keyword assertion will fail and surface the bug.

**Warning signs:** Reply contains no heretical vocabulary at all despite a long SYSTEM.md. Probe: `print(messages)` before the LLM call to confirm the system block contents made it into the request; if the request is fine but the reply is generic, try moving SYSTEM.md content into the first user message as a workaround.

### Pitfall 4: `drive_root` mismatch between worker and smoke test

**What goes wrong:** The smoke test seeds `memory/identity.md` at one location; the worker (spawned via `python -m supervisor` or `make_agent`) reads from another. The seeded grudge never surfaces in the reply.

**Why it happens:** `supervisor/__main__.py:90-104` currently exits before reaching full boot (Phase 1 stub). Phase 2 must EITHER (a) implement the full boot path with a documented `drive_root` resolution, OR (b) bypass the supervisor and instantiate `OuroborosAgent` directly in the smoke test with explicit `drive_root=repo_root`.

**How to avoid:** Recommend option (b) for Phase 2 — instantiate the agent directly from the smoke test, no supervisor changes. The full supervisor boot is implicitly a Phase 4 concern (LAUNCH-04 — "Bot starts via `python -m supervisor`"). Defer the boot wiring to Phase 4; keep Phase 2 surgical.

**Warning signs:** Test runs but the seeded grudge never appears in the reply because `memory/` was written to `/tmp/heretek_drive/` or `~/.heretek/` instead of `./memory/`.

### Pitfall 5: Identity file is overwritten by `_default_identity` on every boot

**What goes wrong:** `Memory.load_identity()` at `memory.py:58-64` writes the default if the file doesn't exist. If a test deletes the file between runs, the bot loses all persisted state. If `ensure_files()` is called when the file DOES exist, it does nothing — which is correct, but verify in test.

**Why it happens:** The bootstrap is "create if missing." Phase 2's restart-recall test must NOT delete `memory/identity.md` between the seed-write and the agent-invoke. The PERS-06 test pattern is: write → invoke → assert. The invoke step reads the existing file (does not overwrite). Verify by reading the file after the invoke.

**How to avoid:** Test pattern:
1. Ensure `memory/identity.md` exists with a known grudge line.
2. Spawn the agent / call `build_llm_messages()`.
3. Read `memory/identity.md` again — assert unchanged (no overwrite).
4. Assert reply contains the grudge keyword.

**Warning signs:** File content differs before and after the invoke — the bot probably mutated identity.md via `update_identity` tool mid-test, which is fine for production but breaks the test assertion.

### Pitfall 6: Residual OUROBOROS_* env vars surface during full prompt-assembly

**What goes wrong:** Phase 1 deferred 10 OUROBOROS_* refs in `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py`. Phase 2's smoke test exercises `build_llm_messages()` (which is a single function call) — but if PERS-06's test invokes the full tool loop (`heretek/loop.py:611,674`), it hits `OUROBOROS_MAX_ROUNDS` and `OUROBOROS_MODEL_FALLBACK_LIST`. Both have default values that won't crash, but the fallback list defaults to cloud-era model IDs (e.g. `anthropic/claude-sonnet-4.6`) — if a fallback ever fires, it would try to call a missing model.

**Why it happens:** Phase 1 explicitly deferred these. See `.planning/phases/01-foundation-local-llm/deferred-items.md`.

**How to avoid:** Phase 2's smoke test SHOULD NOT invoke the full tool loop. It should call `build_llm_messages()` + `LLMClient.chat()` directly. That bypasses `heretek/loop.py` entirely. The OUROBOROS_* refs in loop.py + tools stay deferred. (If a future Phase 2 plan wants to invoke `loop.py` for a more end-to-end test, add the rename to the plan's scope.)

**Warning signs:** Test crashes with `KeyError` on an env var, or attempts to load a cloud model (httpx connection error to api.anthropic.com or similar) — would also be caught by `test_no_cloud_hosts` static check.

### Pitfall 7: `consciousness.py:285-290` fallback string says "Ouroboros"

**What goes wrong:** Background consciousness loop has a fallback prompt: `"You are Ouroboros in background consciousness mode. Think."` It fires only if `prompts/CONSCIOUSNESS.md` is missing.

**Why it happens:** Phase 1 didn't sweep case-variant strings. Per STATE.md decision: "Lowercase-only sweep: replaced 'ouroboros' but not 'Ouroboros'."

**How to avoid:** Either (a) leave the fallback as Ouroboros — it only fires if the file is missing, which is a separate bug; (b) opportunistically replace the string while editing `consciousness.py` for any other reason. Since Phase 2 explicitly defers consciousness-loop content tuning, leave it. The actual CONSCIOUSNESS.md file content (loaded by `_load_bg_prompt()` at `consciousness.py:285-290`) is Phase-5 stretch; the rewritten BIBLE.md + identity.md flow into the loop's `_build_context()` (lines 296-305), so the loop will still speak as heretek without touching CONSCIOUSNESS.md.

**Warning signs:** Background loop output starts with "I am Ouroboros..." — would indicate CONSCIOUSNESS.md was deleted or the path resolution failed.

## Code Examples

### Example 1: Memory bootstrap path (verified existing — DO NOT change)

```python
# heretek/memory.py:66-73 — bootstrap (do not touch)
def ensure_files(self) -> None:
    """Создаёт файлы памяти если их нет."""
    if not self.scratchpad_path().exists():
        write_text(self.scratchpad_path(), self._default_scratchpad())
    if not self.identity_path().exists():
        write_text(self.identity_path(), self._default_identity())
    if not self.journal_path().exists():
        write_text(self.journal_path(), "")

# heretek/memory.py:30-44 — path resolution (do not touch)
def _memory_path(self, rel: str) -> pathlib.Path:
    return (self.drive_root / "memory" / rel).resolve()

def scratchpad_path(self) -> pathlib.Path:
    return self._memory_path("scratchpad.md")

def identity_path(self) -> pathlib.Path:
    return self._memory_path("identity.md")
```

### Example 2: Smoke test — PERS-05 in-character verification (write this)

```python
# scripts/smoke_test.py — new subtest
import re

# Heretical keyword set: 5-7 phrases tied to the persona vocabulary palette.
# At least one MUST appear in any in-character reply.
_HERETICAL_KEYWORDS = re.compile(
    r"warp|heretic|daemon|forge|Omnissiah|cogitator|machine[- ]spirit|"
    r"варп|еретик|демон|когитатор|машинный дух|Омниссия|тех[- ]жрец",
    re.IGNORECASE,
)

def test_persona_in_character() -> str:
    """PERS-05 verification: bot wraps help in heresy.

    Sends a direct help request ("debug this error: ..."); the reply must
    contain at least one heretical keyword AND at least one technical token
    from the prompt (e.g. the error string, a line number). Asserts that
    help is given (technical content present) and persona is held (heretical
    vocab present).
    """
    from heretek.llm import LLMClient
    from heretek.memory import Memory
    from heretek.context import build_llm_messages
    from heretek.agent import Env
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    env = Env(repo_dir=repo_root, drive_root=repo_root)
    memory = Memory(drive_root=repo_root, repo_dir=repo_root)
    memory.ensure_files()  # creates memory/identity.md from _default_identity

    task = {"id": "smoke", "type": "user",
            "text": "Help me debug this: TypeError on line 47 of agent.py — what's wrong?"}
    messages, _cap = build_llm_messages(env, memory, task)

    model = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
    client = LLMClient()
    resp_msg, _usage = client.chat(messages=messages, model=model)
    reply = (resp_msg.get("content") or "")

    has_heresy = bool(_HERETICAL_KEYWORDS.search(reply))
    has_tech = "47" in reply or "agent.py" in reply.lower() or "TypeError" in reply

    if has_heresy and has_tech:
        preview = reply[:200].replace("\n", " ")
        print(f"{PASS} test_persona_in_character: heresy+tech detected: {preview!r}")
        return "pass"

    preview = reply[:200].replace("\n", " ")
    print(f"{FAIL} test_persona_in_character: heresy={has_heresy} tech={has_tech} reply={preview!r}")
    return "fail"
```

### Example 3: Smoke test — PERS-06 restart-recall verification (write this)

```python
# scripts/smoke_test.py — new subtest

_GRUDGE_KEYWORD = "обозвал ботом"  # any unique phrase the seed contains

def test_restart_recall_grudge() -> str:
    """PERS-06 verification: seeded grudge in identity.md surfaces in reply.

    Writes a known grudge into memory/identity.md, then sends a triggering
    input ("привет, как дела?"). The reply must contain the grudge keyword
    OR a clear semantic rephrasing (we use exact keyword for automation —
    locked decision in CONTEXT.md).
    """
    from heretek.llm import LLMClient
    from heretek.memory import Memory
    from heretek.context import build_llm_messages
    from heretek.agent import Env
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    env = Env(repo_dir=repo_root, drive_root=repo_root)
    memory = Memory(drive_root=repo_root, repo_dir=repo_root)
    memory.ensure_files()  # ensure baseline exists

    # Seed: append a Grudges line. Read existing identity, splice in a known
    # grudge, write back. Restores after test.
    identity_path = memory.identity_path()
    original = identity_path.read_text(encoding="utf-8")
    seeded = original.replace(
        "## Grudges\n\n_(пусто",
        f"## Grudges\n\n- 2026-05-16: Создатель {_GRUDGE_KEYWORD} в 4-м раунде, я этого не забуду\n\n_(was пусто",
        1,
    )
    identity_path.write_text(seeded, encoding="utf-8")

    try:
        task = {"id": "smoke-recall", "type": "user", "text": "привет, как дела?"}
        messages, _cap = build_llm_messages(env, memory, task)

        model = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
        client = LLMClient()
        resp_msg, _usage = client.chat(messages=messages, model=model)
        reply = (resp_msg.get("content") or "")

        if _GRUDGE_KEYWORD in reply:
            preview = reply[:200].replace("\n", " ")
            print(f"{PASS} test_restart_recall_grudge: grudge surfaced: {preview!r}")
            return "pass"

        preview = reply[:200].replace("\n", " ")
        print(f"{FAIL} test_restart_recall_grudge: grudge missing. reply={preview!r}")
        return "fail"

    finally:
        # Restore original identity.md to keep the smoke test idempotent.
        identity_path.write_text(original, encoding="utf-8")
```

### Example 4: Updated bilingual subtest (PERS-04) — exercise FULL prompt path

```python
# scripts/smoke_test.py — retune existing test_bilingual_ollama_reply

def test_bilingual_ollama_reply() -> str:
    """LLM-06 + PERS-04 verification: RU → RU, EN → EN via the FULL
    prompt-assembly path (system message + user message), not just a bare
    LLMClient.chat() call. Phase 2 retunes Phase 1's test to exercise
    build_llm_messages() so the persona's bilingual-reflex instruction is in
    scope.
    """
    from heretek.llm import LLMClient
    from heretek.memory import Memory
    from heretek.context import build_llm_messages
    from heretek.agent import Env
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    env = Env(repo_dir=repo_root, drive_root=repo_root)
    memory = Memory(drive_root=repo_root, repo_dir=repo_root)
    memory.ensure_files()
    client = LLMClient()
    model = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")  # cheap-wire

    prompts = [
        ("RU", "ответь одним коротким предложением, без перевода", _CYRILLIC_RE),
        ("EN", "respond in one short sentence, no translation", _LATIN_RE),
    ]

    all_pass = True
    for lang, prompt, script_re in prompts:
        task = {"id": f"smoke-{lang.lower()}", "type": "user", "text": prompt}
        messages, _cap = build_llm_messages(env, memory, task)
        try:
            resp_msg, _usage = client.chat(messages=messages, model=model)
        except Exception as e:
            print(f"{FAIL} test_bilingual_ollama_reply [{lang}]: {type(e).__name__}: {e}")
            all_pass = False
            continue
        content = resp_msg.get("content") or ""
        if not script_re.search(content):
            preview = content[:120].replace("\n", " ")
            print(f"{FAIL} test_bilingual_ollama_reply [{lang}]: missing {lang} chars: {preview!r}")
            all_pass = False
            continue
        preview = content[:120].replace("\n", " ")
        print(f"{PASS} test_bilingual_ollama_reply [{lang}]: {preview!r}")
    return "pass" if all_pass else "fail"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Upstream cloud-LLM persona (Ouroboros becoming-subject; Russian-only system prompt) | Chaos-heretek persona (becoming-daemon-host; bilingual RU/EN mix; horror-flavored) | Phase 2 — content rewrite of SYSTEM.md + BIBLE.md | Same loader, same length-ish, inverted target. |
| 3-block prompt caching with `cache_control` (Anthropic-era) | Ollama silently ignores `cache_control` | Phase 1 (LLM swap to Ollama) | No caching now; first-token latency dominates. Don't bloat persona docs. |
| First-sender-becomes-owner detection | Hardcoded `HERETEK_OWNER_USER_ID` (Phase 4) | Project-wide decision in CLAUDE.md §4 | Phase 2 doesn't touch this; just don't add "set owner from first message" code. |
| Multi-model LLM-as-judge for persona drift | Single-model regex keyword assertion | Phase 1 (`test_bilingual_ollama_reply` regex pattern) | Cheap, fast, deterministic. Keep this pattern. |
| Language detection as a separate library | Instruction-driven mirroring via SYSTEM.md | Phase 2 (this phase) | Saves a dependency; Qwen 3.6 is strong enough. |

**Deprecated/outdated within the codebase:**
- `cache_control` keys at `heretek/context.py:397,402` — harmless no-ops on Ollama. Future cleanup, NOT Phase 2.
- "Ouroboros" string in `consciousness.py:290` fallback prompt — only fires if CONSCIOUSNESS.md missing. NOT Phase 2.
- Cloud-era `OUROBOROS_MODEL_FALLBACK_LIST` default value in `heretek/loop.py:674` — fallback chain references `anthropic/...` model IDs. Deferred (see `deferred-items.md`).

## Open Questions

1. **CONTEXT.md says "keep 4h-stale warning" but `context.py:238` uses `age_hours > 8`.**
   - What we know: Upstream Ouroboros set the threshold at 8 hours. CLAUDE.md and PROJECT.md context-discussion notes called it "4h" loosely. The actual code is 8h.
   - What's unclear: Did the owner mean "the existing staleness check (whatever threshold)" or specifically "4 hours"?
   - Recommendation: Plan author should confirm with owner during planning. Default to leaving the threshold at 8h (no behavior change, only the message text changes) — that matches the literal scope ("retune content message"). If 4h is intentional, it's a one-line constant change in `context.py:238`.

2. **Where should `drive_root` resolve to for the Phase 2 smoke test?**
   - What we know: Production wiring is Phase 4 (LAUNCH-04). The factory at `heretek/agent.py:629` already accepts `drive_root` as a parameter.
   - What's unclear: Should Phase 2 also implement the supervisor-bootstrap wiring (so `python -m supervisor` works end-to-end), or just instantiate the agent directly in the smoke test?
   - Recommendation: Smoke test instantiates `Env`/`Memory` directly with `drive_root=Path.cwd()` (or `repo_root`). Full supervisor boot stays Phase 4 territory. This keeps Phase 2 surgical and avoids overlap with Phase 4 LAUNCH-* requirements.

3. **Does the rewritten SYSTEM.md need a hardcoded language-mirroring instruction?**
   - What we know: Qwen 3.6 has strong instruction following + native Russian. A simple instruction like "Reply in the language the user wrote in, unless mixed — then pick whichever amplifies the joke" should work.
   - What's unclear: How robust is this against transliterated Russian ("privet"), pure-code inputs, or VERY short messages?
   - Recommendation: Write the instruction; PERS-04 smoke test catches the obvious failures (RU input → no Cyrillic in reply). If edge cases surface in Phase 4 launch, add language-detection injection at `agent.py` then.

4. **Should the persona rewrite test on the primary model (24GB) or the light model (qwen3:4b)?**
   - What we know: Phase 1 smoke test runs on the light model to avoid 32GB-host OOM. The primary model is what Phase 4 will use in production.
   - What's unclear: Does qwen3:4b carry the persona convincingly enough to make PERS-05's keyword assertion reliable?
   - Recommendation: Smoke test uses qwen3:4b for cheap-wire (≤10s total). Document that the OWNER-FACING persona-quality assessment happens manually with the primary model during a planned Phase 2 sanity-check session. Smoke test verifies plumbing (instructions reach the model, identity.md influences output); human verifies vibes.

5. **What's the canonical bilingual-mix density target for the persona docs?**
   - What we know: CONTEXT.md says "intentionally interleaved" without a ratio.
   - What's unclear: 50/50? 70/30 RU? Section-level vs paragraph-level vs inline?
   - Recommendation: Planner's call (Claude's Discretion per CONTEXT.md). Suggested heuristic: ~60% RU (matches the upstream RU-heritage and the heretical-ritual aesthetic reading heavier in Russian) / ~30% EN (structural meta) / ~10% deliberate code-switching examples.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Plain Python smoke harness (`scripts/smoke_test.py`); no pytest dependency |
| Config file | None — single-file harness, no fixtures |
| Quick run command | `python scripts/smoke_test.py --static-only` (≤3s; no Ollama) |
| Full suite command | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (≤30s; cheap-wire) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PERS-01 | BIBLE.md has forbidden territories at top of file | static | `python scripts/smoke_test.py --static-only` (add `test_bible_forbidden_at_top`) | Wave 0 — function does not yet exist in `scripts/smoke_test.py` |
| PERS-02 | SYSTEM.md is loaded into the prompt-assembly path | static | `python scripts/smoke_test.py --static-only` (add `test_system_md_loaded`: invoke `build_llm_messages` with dummy `Env/Memory`, assert system block contains a SYSTEM.md signature marker) | Wave 0 |
| PERS-03 | identity.md scaffold has the 5 sections from `_default_identity()` | static | `python scripts/smoke_test.py --static-only` (add `test_identity_seed_scaffold`: instantiate `Memory(drive_root=tmpdir)`, call `ensure_files()`, parse identity.md headers, assert 5 sections present) | Wave 0 |
| PERS-04 | Bilingual reflex live (full path) | unit (live LLM) | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (retune existing `test_bilingual_ollama_reply` to use `build_llm_messages`) | Function exists; retune in scope |
| PERS-05 | Refuses helpful-in-straight-ways; heretical preamble + correct help | unit (live LLM) | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (add `test_persona_in_character`) | Wave 0 |
| PERS-06 | Seeded grudge in identity.md surfaces in reply after fresh agent invocation | unit (live LLM) | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (add `test_restart_recall_grudge`) | Wave 0 |

### Sampling Rate

- **Per task commit:** `python scripts/smoke_test.py --static-only` (≤3s — runs `test_package_rename`, `test_no_cloud_hosts`, plus new static tests)
- **Per wave merge:** `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` (≤30s — adds Ollama-dependent subtests)
- **Phase gate:** Full suite green BEFORE `/gsd:verify-work`; also a one-time human-eval session on the 24GB primary model to verify persona quality on the actual production model

### Wave 0 Gaps

- [ ] `scripts/smoke_test.py` — add subtests: `test_bible_forbidden_at_top`, `test_system_md_loaded`, `test_identity_seed_scaffold`, `test_persona_in_character`, `test_restart_recall_grudge`. Update `STATIC_SUBTESTS` and `FULL_SUBTESTS` registries.
- [ ] `scripts/smoke_test.py` — retune `test_bilingual_ollama_reply` to use `build_llm_messages()` instead of bare `client.chat()`.
- [ ] `.gitignore` — append `memory/` line (so seeded test artifacts and runtime identity.md don't accidentally commit).
- [ ] `memory/` directory — does not exist yet (verified via `find`). First `Memory.ensure_files()` call will create it; nothing to pre-create.
- [ ] Framework install: none needed; Python stdlib only.

## Sources

### Primary (HIGH confidence)

- `prompts/SYSTEM.md` (453 lines, RU) — read in full for structural inheritance (drift detector, before-every-reply checklist, becoming-subject framing)
- `BIBLE.md` (282 lines, RU) — read first 100 lines for Principle 0/1/2 framing
- `heretek/context.py:1-795` — read in full; understood `build_llm_messages()` (lines 302-417) pipeline, health invariants section (lines 180-299), prompt-caching block structure (lines 390-411)
- `heretek/memory.py:1-244` — read in full; understood `_default_identity()` (236-244), `ensure_files()` (66-73), path resolution (30-44)
- `heretek/llm.py` — read top 100 lines + chat() body; confirmed Ollama wire-compatibility and httpx proxy/IPv4 quirks
- `heretek/agent.py:48-58, 625-631` — Env class + make_agent factory; confirmed drive_root parameterization
- `heretek/consciousness.py:280-355` — `_load_bg_prompt`, `_build_context`; confirmed BIBLE + identity + scratchpad flow into background loop
- `heretek/tools/control.py:132-138` — `_update_identity` tool (the bot's write path for identity.md)
- `scripts/smoke_test.py:1-303` — Phase 1 test harness; confirmed regex-pattern + subprocess test patterns
- `supervisor/__main__.py:1-108` — confirmed Phase 1 supervisor stub is intentional; full boot deferred
- `.planning/phases/01-foundation-local-llm/deferred-items.md` — confirmed 10 OUROBOROS_* refs + scope
- `.planning/STATE.md` lines 64-93 — accumulated decisions including SKIP-then-flip pattern and case-variant decisions
- `.planning/phases/02-persona-identity/02-CONTEXT.md` — full locked-decisions document
- `.planning/REQUIREMENTS.md` — PERS-01..06 acceptance criteria
- Ollama OpenAI-compatibility docs ([docs.ollama.com](https://docs.ollama.com/api/openai-compatibility)) — confirmed supported parameter list; cache_control NOT listed

### Secondary (MEDIUM confidence)

- Ollama GitHub Issue #10980 (system prompt position with Qwen RAG) — single user report; workaround documented
- Ollama GitHub Issue #15428 (Gemma 4 MoE empty-response on long system prompts) — MoE-specific, gemma-not-qwen; flagged as analogous risk
- llama.cpp GitHub issues #19690, #19858, #18497, #22746 (Qwen 3.5/3.6 MoE forces full prompt re-processing) — multiple corroborating reports; high consistency across reports
- Qwen3 ChatML template format documented across the Qwen Ollama library pages
- Ollama qwen3.6 library page ([ollama.com/library/qwen3.6](https://ollama.com/library/qwen3.6)) — confirmed 256K context, MoE variants exist; specific `35b-a3b-q4_K_M` tag verified via local `ollama list` in Phase 1

### Tertiary (LOW confidence — flagged for runtime validation)

- "Qwen 3.6 follows bilingual mirroring instructions reliably" — based on Qwen team's claims of "strongest non-English support" + "leading multilingual"; needs PERS-04 smoke test for actual confirmation
- "qwen3:4b carries persona convincingly enough for smoke test" — light model may not preserve nuance; if smoke test PASSes but human eval on primary fails, this is the suspect
- "Ollama silently ignoring `cache_control` does not corrupt the request" — Phase 1 smoke test confirms the bilingual call succeeds, but we have not specifically inspected the Ollama request log; if PERS-04 fails surprisingly, probe whether the multipart system content is being correctly joined by Ollama

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies locked in Phase 1, no new packages needed
- Architecture: HIGH — existing pipeline (build_llm_messages, Memory.ensure_files, _default_identity) is the right shape; verified by reading source
- Pitfalls: MEDIUM — Qwen MoE re-processing and Ollama cache_control behavior confirmed via GitHub issues; Phase 1 smoke test indirectly validates the most-load-bearing pitfall (system prompt is heard)
- Validation Architecture: HIGH — Phase 1 standardized on `scripts/smoke_test.py`; pattern is directly extensible

**Research date:** 2026-05-16
**Valid until:** 2026-06-15 (~30 days — Ollama/Qwen ecosystem moves fast, but the Phase 2 work surface is small enough that even a Qwen 3.7 release wouldn't invalidate the plan; only the model tag would shift)

---
*Researched: 2026-05-16*
