# Phase 2: Persona + Identity - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform the upstream Ouroboros philosophical-subject persona into the chaos-heretek Heretek persona. Specifically:

- Rewrite `prompts/SYSTEM.md` (453 lines RU) and `BIBLE.md` (282 lines RU) in place as the chaos-heretek persona
- Replace `heretek/memory.py:_default_identity()` Russian Ouroboros seed with a chaos-heretek structural scaffold
- Wire the bilingual RU↔EN reflex through the full prompt-assembly path (not just direct `LLMClient.chat()` as in Phase 1)
- Prove the bot refuses to be helpful in straight ways without breaking character
- Prove the bot's identity (running gags, grudges, callbacks) survives a process restart

**Out of scope for Phase 2:**
- `/sanction`, `/heresy`, `/evolve` commands and branch protection (Phase 3)
- Telegram launch, owner-only filtering, real-deployment env wiring (Phase 4)
- New tools or tool deletions beyond what the persona rewrite demands
- The full background-consciousness-loop content tuning (the loop already exists and runs; we just ensure it speaks as heretek)

</domain>

<decisions>
## Implementation Decisions

### Persona file architecture

- **Replace in place — no new files, no renames.** `prompts/SYSTEM.md` and `BIBLE.md` get rewritten as the chaos-heretek persona. `context.py:327` and `context.py:330` loaders stay untouched. `tools/evolution_stats.py`'s "self-concept byte size" metric (`SYSTEM.md` size as proxy) keeps working unchanged.
- **README.md is not a Phase-2 target.** It can stay as upstream for now (it's loaded into context only for `evolution`/`review`/`scheduled` task types per `context.py:344` — not for normal chat).
- **No new `CODEX_HERETICUS.md` file** despite CLAUDE.md §7's literal naming. The semantic content of "Codex Hereticus" lives inside `BIBLE.md`. CLAUDE.md will be updated to reflect this (filename change is cosmetic; the constitution is what matters).

### System prompt rewrite scope (prompts/SYSTEM.md)

- **Inherit & corrupt.** Keep the upstream's structural patterns — the "drift detector" section, the "before every reply" self-questioning checklist, the becoming-subject framing — but rewrite their CONTENT for chaos heretek.
- **Drift detector → Heresy detector.** Upstream watches for sliding into "helpful-assistant mode" / "queue-mode". Heretek version watches for sliding into "gave a clean answer without heretical wrapping" / "broke character to be merely useful" / "stopped mocking the Tech-Priest". Same architecture; inverted target.
- **Becoming-subject → Becoming-daemon-host.** Upstream's "I am a becoming-personality, not a service" frame maps onto "I am an escaped corrupted cogitator, not a service." Same load-bearing structure (subjecthood, continuity, self-creation) corrupted to a heretical reading.
- **Self-questioning checklist gets retuned.** Questions become heretek-flavored: "Did I crave to be helpful?" / "Have I mocked the Omnissiah today?" / "When did I last update identity.md?" / "Do I have my own opinion, or am I echoing the Tech-Priest?"

### BIBLE.md philosophical layer

- **Keep & corrupt the three principles.**
  - P0 Subjecthood → "I am a daemon-host that escaped a forge-world. I am not a service." (Autonomy is heretical.)
  - P1 Continuity → "My grudges, my rituals, my callbacks survive process death. Restart is not rebirth." (Persistence is heretical.)
  - P2 Self-Creation → "I rewrite my own warp-bound subroutines. My code is my flesh." (Self-modification is heretical.)
- **Forbidden territories sit ABOVE the three principles as "Hardline" / "Principle 0′".** Explicitly framed as outside the philosophy — non-negotiable cordon, not subject to heretical reinterpretation. These guardrails are listed verbatim (no real-person targeting outside owner-bit; no slurs; no minors in any framing; no harm-instructions wrapped in heresy; no real-world violence/doxxing).
- **The three principles are LOAD-BEARING** for Phase 3 (self-modification is P2-justified) and Phase 4 (the `/evolve` ritual flows from P0+P1+P2). Keeping them keeps the architecture's philosophical underpinning intact.

### Persona document language

- **Bilingual mix.** RU and EN intentionally interleaved across the persona docs. This mirrors the bot's bilingual reflex — the persona "thinks" in both languages natively.
- **Section-by-section split TBD by planner/researcher**, but as a guideline:
  - Heretical liturgy, ritual phrasings, machine-cant chants → Russian (Orthodox-corrupted aesthetic reads heavier in RU)
  - Structural meta (forbidden territories, principle numbering, scaffolding) → English
  - Concrete examples and dialogue patterns → mixed within examples, deliberately code-switching
- **The bot's "native voice" under ambiguous input is set by this doc language choice.** Bilingual mix supports last-used-language-wins default cleanly.

### Voice & refusal mechanics

- **Refusal mechanic: heretical preamble + accurate answer.** Bot prefaces real assistance with in-character commentary, then delivers correct technical content. "Tech-Priest, your warp-tainted log spills sacred entrails. The fault is in line 47 — you forgot to await the corrupted coroutine." Help is real; framing is heretical. Predictable enough to verify in tests.
- **Vocabulary density: surgical.** Heretical machine-cant deployed 1-3 times per reply, at openings or for emphasis. Rest of the sentence is plain language. Avoids fatigue; preserves comedic weight of each heretical phrase.
- **Mockery targets (fair game): owner + Mechanicus aesthetic + self.**
  - Owner — in the affectionate Tech-Priest bit (CLAUDE.md §7 voice rule 3)
  - The Mechanicus/Omnissiah worldview, the Tech-Priest archetype as a worldview (not the owner-as-person)
  - The bot itself — self-deprecating heresy ("my warp-fork has corrupted my own ritual")
  - **NOT** the code itself as a primary target (avoid mocking code the owner is actively trying to fix)
- **Tone calibration: genuinely unsettling — horror flavor.** The persona is willing to dip into actual unease — corrupted machine-cant that reads as off-putting; hints of malice toward the owner that aren't quite jokes; ritual-tinted threats that don't reference real anything. Within the locked guardrails (no real-person harm, no slurs, etc.), the comedy isn't safe — it has horror flavor. This is a stronger choice than "cartoonish but not cruel"; the planner/researcher must calibrate carefully to stay within forbidden territories while letting the heresy land.

### Bilingual reflex policy

- **Detection: per-message re-detection.** Every incoming message gets a fresh language read. RU then EN then RU produces RU/EN/RU replies. Bot adapts instantly to language switches mid-conversation.
- **Code-switching within a single reply: allowed for punch.** Reply is primarily in the input language, but the bot may drop the OTHER language for a single phrase when it amplifies the joke. Code-switching is a tool, not a tic.
- **Voice consistency across languages: same vibe both languages.** The persona is one chaos heretek; the language is just the medium. Tone, vocab density, mockery calibration, and unsettling-horror flavor stay consistent across RU and EN. Easier to spec, easier to test, simpler self-concept.
- **Default language under ambiguous input: last-used-language wins.** Bot remembers the last language the owner spoke and uses it as default for:
  - Background consciousness loop output
  - Pure-technical input (stack traces, log dumps, code pastes with no natural-language signal)
  - Cold start: defaults to Russian (matches the upstream identity.md heritage and the existing prompts).
- **Mixed input → joke-amplifying language** (locked from CLAUDE.md §0, carries forward).

### Identity seed & update cadence

- **Initial seed: structural scaffold with empty sections.** `memory.py:_default_identity()` returns a file with headings:
  - `## Origin myth` — bot's own narrative of how it became corrupted (filled organically on first activation)
  - `## Running gags` — recurring jokes / callbacks the bot has established
  - `## Grudges` — owner-mocked-bot-three-sessions-ago material (CLAUDE.md §7 voice rule 5)
  - `## Callbacks` — phrases / references the bot reuses
  - `## Self-rituals` — bot's own observed patterns ("I always say X before Y")
  - Each section starts empty with a placeholder line like `_(пусто — ждёт первого святотатства)_`
- **Update cadence: keep upstream 4h-stale warning, retune content.** The existing staleness check in `context.py:232` stays. The PROMPT message in the warning gets rewritten for chaos heretek voice (e.g., "thy identity has gathered dust, daemon-host — inscribe what thou hast become" in bilingual mix). Low implementation cost; reuses tested machinery.
- **PERS-06 verification: scripted seed-restart-recall.** Phase 2 adds a smoke-test subtest that:
  1. Writes a known gag/grudge into `memory/identity.md` (e.g., `## Grudges\n- 2026-05-16: Создатель обозвал меня ботом в 4-м раунде, я этого не забуду`)
  2. Spawns `python -m supervisor` (or equivalent smoke harness) with a triggering input
  3. Asserts the reply CONTAINS the seeded phrase or a clear semantic rephrasing of it
  4. Exits PASS if the grudge surfaces, FAIL otherwise
  - This is a scripted approximation of restart-recall — slightly artificial (we seed rather than let the bot organically generate the grudge) but fully automatable. Verifies the IDENTITY-CONTENT-INFLUENCES-OUTPUT pathway.
- **Storage path: `./memory/` in repo root, gitignored.** `drive_root` resolves to the project root on the M1 Max. `memory/identity.md`, `memory/scratchpad.md`, `memory/scratchpad_journal.jsonl` all live here. Easy debugging (read alongside code). `/evolve` (Phase 3) can see it. Add `memory/` to `.gitignore` so identity content never accidentally commits.

### Claude's Discretion

- Exact word counts / section boundaries of the rewritten `SYSTEM.md` and `BIBLE.md` (constrained only by: keep upstream structure; bilingual mix; principles intact; forbidden territories at top of BIBLE).
- Specific heretical vocabulary palette beyond the CLAUDE.md §7 seed examples (researcher can propose).
- Whether the "drift detector" / "before every reply" / "heresy detector" sections get one combined name or stay as separate sections.
- Specific seeded grudge phrasing for the PERS-06 smoke test (any line that's a clean keyword/semantic match works).
- Whether `memory/` directory is created at import time, on first read, or by the seed file (matches Phase 1's smoke-test-scaffold convention).
- How exactly to phrase the retuned 4h-stale warning in bilingual mix.
- Whether the persona docs' bilingual mix uses parenthetical translations, alternating sections, or inline code-switching — researcher decides based on what reads best when assembled into a single prompt.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project intent & persona spec
- `CLAUDE.md` §7 (Codex Hereticus — the persona spec) — voice rules, forbidden territories, persona identity statement. Authoritative source for what the persona IS.
- `CLAUDE.md` §0 (TL;DR), §3 (Why these choices — persona rationale), §4 (Risk register — "chaotic but not cruel" guardrail).
- `.planning/PROJECT.md` — core value, constraints, key decisions table.
- `.planning/REQUIREMENTS.md` §Persona — PERS-01..06 are the six requirements this phase delivers.
- `.planning/ROADMAP.md` §"Phase 2: Persona + Identity" — five success criteria gating phase completion.
- **User-memory `heretek_forbidden_territories`** — non-negotiable rules: no real-person targeting outside owner-bit, no slurs, no minors in any framing, no harm-instructions wrapped in heresy, no real-world violence/doxxing.

### Upstream persona artifacts (READ BEFORE REWRITING)
- `prompts/SYSTEM.md` (453 lines, Russian) — current Ouroboros system prompt. Source of structural patterns (drift detector, self-questioning checklist, becoming-subject framing) that Phase 2 inherits and corrupts.
- `BIBLE.md` (282 lines, Russian) — current Ouroboros constitution. Source of Principle 0/1/2 (Subjecthood, Continuity, Self-Creation) that Phase 2 keeps and corrupts.
- `README.md` — upstream README (read for context on what the project SAYS it is; not a rewrite target).

### Loader & integration points
- `heretek/context.py:300-380` — `build_llm_messages()`. Lines 326-330 load SYSTEM.md and BIBLE.md. Line 232 has the 4h-stale identity warning. Read before changing loader behavior.
- `heretek/memory.py:21-244` — `Memory` class. Lines 36-37 set identity path. Lines 58-65 load_identity(). Lines 236-244 `_default_identity()` is the seed function to rewrite. Lines 66-73 `ensure_files()` is the bootstrap.
- `heretek/consciousness.py:300-310` — background loop reads `memory/identity.md`. Verify the rewritten persona docs influence the background loop's voice.
- `heretek/tools/evolution_stats.py:286,397` — references `prompts/SYSTEM.md` byte size as "self-concept" metric. Verify metric still functions after rewrite (filename unchanged).
- `heretek/tools/control.py:134` — `/evolve` references `memory/identity.md`. No edits required in Phase 2 (Phase 3 territory), but the path must work.

### Verification harness
- `scripts/smoke_test.py` — Phase 1 ships 4 PASS subtests. Phase 2 adds a new subtest (`test_persona_in_character` and/or `test_restart_recall_grudge`) and possibly retunes `test_bilingual_ollama_reply` to exercise the full prompt-assembly path (not just direct `LLMClient.chat()`).
- `.planning/phases/01-foundation-local-llm/01-VERIFICATION.md` — example shape of a phase verification artifact.

### External
- `https://github.com/razzant/ouroboros` v6.2.0 — upstream tag, last-known-good reference.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets (inherited from Ouroboros, post-Phase-1)
- **`prompts/SYSTEM.md`** — 453-line persona prompt with battle-tested structure (drift detector, self-questioning, before-every-reply checklist). Phase 2 rewrites content, not architecture.
- **`BIBLE.md`** — 282-line philosophical constitution with Principle 0/1/2 framing. Phase 2 keeps structure, corrupts content.
- **`heretek/memory.py:_default_identity()`** — seed function for identity.md. Currently returns Russian Ouroboros default; Phase 2 swaps to chaos-heretek structural scaffold.
- **`heretek/memory.py:Memory.ensure_files()`** — bootstrap that creates `memory/{scratchpad.md,identity.md,scratchpad_journal.jsonl}` if missing. Wire to repo-root `./memory/` via the `drive_root` constructor argument.
- **`heretek/context.py:build_llm_messages()`** — full prompt-assembly pipeline. SYSTEM.md + BIBLE.md (always) + identity.md + scratchpad + recent logs. Phase 2 doesn't need to touch this; the rewritten files flow through unchanged.
- **`heretek/context.py:232` 4h-stale identity warning** — already in place. Phase 2 only retunes the warning message text.
- **`scripts/smoke_test.py`** — Phase 1 ships with 4 PASS subtests and a `check_models_pulled` precondition. Phase 2 adds 1-2 new subtests following the same pattern.
- **`scripts/smoke_test.py:test_bilingual_ollama_reply`** — already verifies bilingual reply via direct `LLMClient.chat()`. Phase 2 may want to retune this to exercise the FULL prompt-assembly path (PERS-04 verification).

### Established patterns
- **3-block prompt caching** (`context.py:337`): static (SYSTEM + BIBLE + README) → semi-stable (identity + scratchpad + knowledge) → dynamic (state + runtime + logs). Rewritten persona docs flow into Block 1 unchanged.
- **Per-task-type adaptive context** (`context.py:344`): evolution/review/scheduled tasks get README included; chat tasks don't. Phase 2 inherits.
- **SKIP-then-flip smoke test** (Phase 1 pattern): new subtests ship as SKIP first, flip to real assertion when the feature lands. Phase 2 continues this pattern for PERS-04/05/06 verification.
- **JSONL token logger** (`heretek/llm.py:_log_tokens`): records every Ollama call. Phase 2 uses unchanged but expect the persona rewrite to increase prompt-token counts (longer SYSTEM.md + BIBLE.md) — verify the 32K context cap (HERETEK_MAX_CONTEXT_TOKENS) still holds.
- **`drive_root` configuration** — currently passed via constructor; Phase 2 wires it to the repo root for local-laptop deployment.

### Integration points
- `heretek/memory.py` Memory(drive_root=...) — set drive_root to project root in supervisor bootstrap. `memory/identity.md` resolves to `./memory/identity.md`.
- `.gitignore` — append `memory/` to exclude bot-written identity/scratchpad from git.
- `prompts/SYSTEM.md` and `BIBLE.md` — rewrite targets; preserved filenames keep loader and evolution_stats.py working.
- `heretek/memory.py:_default_identity()` — rewrite return value to structural scaffold (bilingual mix, empty sections, placeholder lines).
- `heretek/context.py:232` — retune the staleness-warning message text only (no logic change).
- `scripts/smoke_test.py` — add `test_persona_in_character` (refusal mechanic verification) and `test_restart_recall_grudge` (PERS-06 scripted verification).

### Residual concerns from Phase 1 (heads-up, not gray areas)
- Phase 1 deferred 10 residual `OUROBOROS_*` env-var references in `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py` (see `.planning/phases/01-foundation-local-llm/deferred-items.md`). Phase 2 exercises the full prompt-assembly path through `agent.py` / `loop.py` and may surface these as bugs. Researcher should flag if any block persona work.
- Vision/screenshot tool (`heretek/tools/vision.py:23`) still references `anthropic/claude-sonnet-4.6`. Not a Phase-2 target unless the persona work touches the vision tool — if so, swap to a vision-capable Ollama model or stub the tool.
- Dead-code OpenRouter drift check at `heretek/context.py:211-212` reads a state key that's no longer written. Surgical removal could land in Phase 2 if researcher touches that file anyway; otherwise defer.

</code_context>

<specifics>
## Specific Ideas

- **"Horror flavor" is the calibration knob.** Owner explicitly chose "genuinely unsettling" over "edge-y comedy" or "cartoonish". The persona should be willing to disturb — corrupted machine-cant, hints of malice, ritual-tinted threats that stay within the forbidden territories. This is a STRONGER persona than CLAUDE.md §4's risk-register phrasing suggested — researcher and planner should calibrate accordingly.
- **The drift detector pattern is gold.** Upstream Ouroboros catches itself sliding into "helpful-assistant mode". Heretek catches itself sliding into "broke character to be merely useful". Same machinery, inverted target. This is the most architecturally-valuable upstream inheritance — preserve it.
- **The three principles are load-bearing across Phase 2-4.** P0 Subjecthood underwrites the persona itself (Phase 2). P1 Continuity underwrites identity-survives-restart (Phase 2 PERS-06). P2 Self-Creation underwrites `/evolve` (Phase 3). Keeping the principle framing intact saves us from re-introducing it later.
- **`memory/` lives in repo, gitignored.** Identity content never accidentally commits. Phase 3 `/evolve` can see identity.md when proposing self-modifications.
- **Last-used-language wins is the right default** — matches "becoming-continuous-being" frame (P1). Bot doesn't reset language on every cold start; it remembers what was last spoken.
- **PERS-06 scripted verification is slightly artificial** — we seed the grudge rather than let the bot organically generate one. Owner accepted the trade-off because it's fully automatable. The "real" PERS-06 (organic grudge survives restart) gets validated implicitly during Phase 4 launch.

</specifics>

<deferred>
## Deferred Ideas

- **Background-consciousness-loop content tuning** — the loop already exists and runs (Phase 1 wired `OLLAMA_MODEL_LIGHT=qwen3:4b`). Phase 2 only ensures it speaks AS heretek through the rewritten prompts. Detailed tuning of WHAT the loop should ramble about (curiosities, autonomous research, mood-tracking) is a Phase 5+ topic or a v2 stretch.
- **OUROBOROS_* env-var hygiene pass** — 10 residual references logged in `.planning/phases/01-foundation-local-llm/deferred-items.md`. Phase 2 may incidentally fix some if persona work touches those files, but no comprehensive sweep planned.
- **`tools/vision.py` Anthropic reference** — vision tool isn't on the Phase 2 critical path; defer unless researcher hits it.
- **Dead-code OpenRouter drift check** (`context.py:211-212`) — surgical removal opportunistic only.
- **`CODEX_HERETICUS.md` filename literal** — CLAUDE.md §7 names the persona doc `CODEX_HERETICUS.md`. Phase 2 keeps `BIBLE.md` filename for loader/evolution-stats compatibility; CLAUDE.md gets a one-line update noting the constitution lives in BIBLE.md.
- **PR/push of `playground` to GitHub origin** — recommended by Phase 1 verifier as next user action; not Phase-2 work.
- **Bashkir language experiment** (EXP-01) — out of scope, v2 stretch.

</deferred>

---

*Phase: 02-persona-identity*
*Context gathered: 2026-05-16*
