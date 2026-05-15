# Requirements: Heretek

**Defined:** 2026-05-14
**Core Value:** A bot the owner enjoys talking to: persistent identity, bilingual RU/EN by reflex, free local inference, self-modification capability gated by an approval workflow.

## v1 Requirements

### Foundation & Fork (FORK)

- [x] **FORK-01**: Fork `razzant/ouroboros` v6.2.0 to GitHub as `<owner>/heretek`, clone locally to `~/code/heretek` (or repo root), create `playground` and `last-known-good` branches
- [x] **FORK-02**: Rename `ouroboros/` Python package to `heretek/`; update `pyproject.toml`, imports, and references
- [ ] **FORK-03**: Remove unneeded modules: `tools/github.py`, `tools/review.py` (multi-model), browser/Playwright tool (`tools/browser.py`)
- [ ] **FORK-04**: Neuter budget tracking — replace cost-calculation logic with a token counter that just logs (local inference is free)

### Local LLM (LLM)

- [ ] **LLM-01**: Patch `heretek/llm.py` to point at Ollama (`http://localhost:11434/v1`, API key literal `"ollama"`)
- [ ] **LLM-02**: Configure primary model `qwen3.6:35b-a3b-q4_K_M` for chat/tool-use via `OLLAMA_MODEL` env var
- [ ] **LLM-03**: Configure secondary model `qwen3:4b` for background consciousness loop via `OLLAMA_MODEL_LIGHT`
- [ ] **LLM-04**: Cap context to 32K tokens initially via `HERETEK_MAX_CONTEXT_TOKENS=32000` to prevent 32GB-host OOM
- [ ] **LLM-05**: Patch fallback chain to use local Ollama models only (no OpenRouter/OpenAI/Anthropic fallback)
- [ ] **LLM-06**: Smoke-test bot replies in both English and Russian via Ollama (verifies Metal acceleration + Qwen bilingual)  <!-- Partial: Plan 01-02 delivered `python -m supervisor` entry point; bilingual reply test gated on Plan 05 -->


### Persona (PERS)

- [ ] **PERS-01**: Write `CODEX_HERETICUS.md` — full persona constitution with non-negotiable forbidden territories at the top (no real-person targeting outside owner-bit, no slurs, no minors in any framing, no harm-instructions wrapped in heresy, no real violence/doxxing)
- [ ] **PERS-02**: Write `SYSTEM.md` — system prompt that pulls from CODEX_HERETICUS.md and adds bilingual reflex instruction
- [ ] **PERS-03**: Write initial `identity.md` (empty/seed file; bot fills it over time via memory.py)
- [ ] **PERS-04**: Bot replies in Russian when addressed in Russian, English when addressed in English, picks the joke-amplifying language when mixed
- [ ] **PERS-05**: Persona stays in character — bot refuses to be helpful in straight ways; wraps help in heresy
- [ ] **PERS-06**: Persistent identity survives restarts — running gags, grudges, callbacks reload from memory store

### Self-Modify Safety (SAFE)

- [ ] **SAFE-01**: `supervisor/git_ops.py` hard-refuses all push/commit operations targeting `main` or `last-known-good` branches
- [ ] **SAFE-02**: All bot self-modifications route to `playground` branch by default
- [ ] **SAFE-03**: `/evolve` command defaults to dry-run mode — bot posts proposed diff to Telegram instead of committing
- [ ] **SAFE-04**: `/sanction <commit-hash>` Telegram command approves a pending dry-run proposal and commits it to `playground`
- [ ] **SAFE-05**: `/heresy` Telegram command rolls the working tree back to the `last-known-good` tag
- [ ] **SAFE-06**: Daily (or per-session) auto-tag of `last-known-good` at current `playground` HEAD so rollback target stays fresh

### Launch (LAUNCH)

- [ ] **LAUNCH-01**: Register Telegram bot via @BotFather; create private group; add bot with owner-only membership
- [ ] **LAUNCH-02**: Hardcode owner Telegram user ID in `SYSTEM.md` (no first-sender-becomes-owner detection)
- [ ] **LAUNCH-03**: Environment variables loaded from gitignored `.env` via `python-dotenv` (TELEGRAM_BOT_TOKEN, HERETEK_OWNER_USER_ID, OLLAMA_*, HERETEK_*)
- [ ] **LAUNCH-04**: Bot starts via `python -m supervisor`, connects to Telegram, listens to private group, responds with correct persona + language switching
- [ ] **LAUNCH-05**: Bot ignores messages from any non-owner Telegram user ID

### First Evolution Cycle (EVOLVE)

- [ ] **EVOLVE-01**: `/evolve` command produces a coherent self-modification proposal (diff visible in Telegram, on `playground`, dry-run)
- [ ] **EVOLVE-02**: Background consciousness loop (`heretek/consciousness.py`) runs continuously using the light model, throttled by the existing v6.2.0 circuit breaker (3 empty responses → pause)
- [ ] **EVOLVE-03**: At least one full evolution loop completed end-to-end: `/evolve` → diff in TG → `/sanction <hash>` → commit visible on `playground`

## v2 Requirements

### Stretch / Experiments

- **EXP-01**: Bashkir language experimental support (test Qwen quality first; quality unknown)
- **EXP-02**: Vision/screenshot reaction capability (would require re-adding a slimmer browser tool or using a multimodal model)
- **EXP-03**: Auto-`last-known-good` cron tag job (timer-driven, not session-driven)
- **EXP-04**: Web search tool re-enable via local-friendly search backend (DDG, SearXNG)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public Telegram deployment | Owner-only private group is the design — no public exposure |
| Productivity / coding-assistant features | Anti-feature; bot must refuse to be helpful in straight ways |
| Cloud LLM fallback (OpenRouter / OpenAI / Anthropic) | Defeats local/free/offline goal; CLAUDE.md §3 |
| Cloud-hosted runtime | Local laptop only; "works on a train" is a design value |
| Browser/Playwright tool | Heavy dep, runaway-tab risk, marginal value for shitposting bot |
| Multi-model review | Local inference makes cost-comparison review pointless |
| Bashkir support in v1 | Qwen quality unknown — defer to v2 experiment |
| Public docs / contribution guides | Leisure project, single user |
| Cost tracking / budget enforcement | Local inference is free; token logging only for observability |

## Traceability

Populated by roadmapper. Each requirement maps to exactly one phase.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FORK-01 | Phase 1 | Complete |
| FORK-02 | Phase 1 | Complete |
| FORK-03 | Phase 1 | Pending |
| FORK-04 | Phase 1 | Pending |
| LLM-01 | Phase 1 | Pending |
| LLM-02 | Phase 1 | Pending |
| LLM-03 | Phase 1 | Pending |
| LLM-04 | Phase 1 | Pending |
| LLM-05 | Phase 1 | Pending |
| LLM-06 | Phase 1 | Partial (Plan 01-02 entry point; Plan 05 bilingual test) |
| PERS-01 | Phase 2 | Pending |
| PERS-02 | Phase 2 | Pending |
| PERS-03 | Phase 2 | Pending |
| PERS-04 | Phase 2 | Pending |
| PERS-05 | Phase 2 | Pending |
| PERS-06 | Phase 2 | Pending |
| SAFE-01 | Phase 3 | Pending |
| SAFE-02 | Phase 3 | Pending |
| SAFE-03 | Phase 3 | Pending |
| SAFE-04 | Phase 3 | Pending |
| SAFE-05 | Phase 3 | Pending |
| SAFE-06 | Phase 3 | Pending |
| LAUNCH-01 | Phase 4 | Pending |
| LAUNCH-02 | Phase 4 | Pending |
| LAUNCH-03 | Phase 4 | Pending |
| LAUNCH-04 | Phase 4 | Pending |
| LAUNCH-05 | Phase 4 | Pending |
| EVOLVE-01 | Phase 4 | Pending |
| EVOLVE-02 | Phase 4 | Pending |
| EVOLVE-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-14*
*Last updated: 2026-05-14 — traceability populated by roadmapper*
