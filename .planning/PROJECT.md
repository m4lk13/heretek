# Heretek

## What This Is

Heretek is a locally-hosted, self-modifying Telegram shitposting bot built by forking [razzant/ouroboros](https://github.com/razzant/ouroboros) v6.2.0, stripping it down to its useful skeleton, and replacing the cloud LLM backbone with local Ollama inference. It lives in a private Telegram group with a single user (the owner) and runs a "chaos heretic" persona — the deliberate inverse of the owner's usual Tech-Priest aesthetic — for comedic contrast.

## Core Value

A bot the owner enjoys talking to: persistent identity (running gags, callbacks, grudges), bilingual RU/EN by reflex, free local inference, and self-modification capability gated by an approval workflow so it stays interesting without self-corrupting.

## Requirements

### Validated

- [x] Bot runs entirely on local hardware via Ollama (zero ongoing LLM cost, no cloud dependency) — Validated in Phase 1: foundation-local-llm
- [x] Primary model `qwen3.6:35b-a3b-q4_K_M` for chat, secondary `qwen3:4b` for background consciousness loop — Validated in Phase 1
- [x] All upstream tools kept (file ops, shell, search) except: browser/Playwright removed, GitHub tool removed, multi-model review removed — Validated in Phase 1
- [x] Bilingual reply by reflex: RU → RU, EN → EN, mixed → whichever amplifies the joke — Validated in Phase 1 (smoke test PASS for both languages via qwen3:4b), strengthened in Phase 2 through full prompt-assembly pipeline
- [x] Coherent chaos-heretic persona — Mechanicus-flavor mocked, bilingual RU/EN, holds grudges, refuses to be helpful in straight ways — Validated in Phase 2: persona-identity (test_persona_in_character + test_bilingual_through_full_pipeline PASS; pending manual persona-vibe sign-off on 24GB primary model)
- [x] Persistent identity across restarts (memory.py + identity.md continue working from upstream) — Validated in Phase 2 (test_restart_recall_grudge PASS — seeded grudge surfaces after restart)

### Active

- [ ] Self-modification on `playground` branch only, dry-run by default, `/sanction <hash>` approval to commit
- [ ] Telegram private-group deployment — owner-only access, owner ID hardcoded (no first-sender footgun)
- [ ] Branch protection: `git_ops.py` hard-refuses pushes to `main` or `last-known-good`
- [ ] `/heresy` rollback command — revert to `last-known-good` tag

### Out of Scope

- Public deployment — owner-only private group, no public TG bot
- Productivity / coding-assistant use — anti-feature; bot must refuse to be helpful in straight ways
- Cloud LLM fallback (OpenRouter, OpenAI, Anthropic) — defeats local/free/offline goal
- Cloud-hosted runtime (Railway, Fly, cloud VPS) — local laptop only
- Browser/Playwright tool — runaway-tab risk, heavy dep, not worth it for a shitposting bot
- Multi-model review / cost tracking from upstream — local inference is free
- Bashkir language support in v1 — Qwen's Bashkir quality unknown, can add as experiment later
- Public docs / contribution guides — leisure project, single user

## Context

- **Upstream:** Fork of `razzant/ouroboros` v6.2.0 (Feb 18, 2026). Framework already solves: TG message routing with dedup, per-task mailboxes, tool plugin auto-discovery, persistent memory across restarts, background consciousness loop, philosophical-constitution-driven persona.
- **Host hardware:** MacBook Pro 16" M1 Max, 32GB RAM, macOS Tahoe 26.3.1. Ollama runs native with Metal backend.
- **Model rationale:** Qwen 3.6 MoE = ~3B active params per token, ~25-40 tok/s on M1 Max, 262K context window, genuinely strong Russian (better than Llama-family), Q4_K_M fits in ~20GB leaving headroom for KV cache + the owner's other work.
- **Persona spec lives in:** `CODEX_HERETICUS.md` (to be written in Phase 2). Hard guardrails: no real-person targeting outside the owner-bit, no slurs, no minors in any framing, no harm-instructions dressed as heresy, no real-world violence/doxxing.
- **Full architecture diagram, risk register, and phase breakdown:** `CLAUDE.md` at repo root.

## Constraints

- **Tech stack**: Python (inherited from Ouroboros), Ollama HTTP API on `localhost:11434`, OpenAI-compatible client pointed at Ollama. — Forced by upstream.
- **Hardware**: 32GB RAM ceiling. — Caps context to 32K tokens initially (well below model's 262K) to prevent OOM. `OLLAMA_NUM_PARALLEL=1`.
- **Branch policy**: `main` and `last-known-good` are protected. All bot self-modify lands on `playground`. — Prevents catastrophic self-corruption.
- **Network**: Telegram requires outbound to `api.telegram.org`. Everything else can be offline. — Owner values "works on a train" property.
- **Persona guardrails**: Non-negotiable forbidden territories in `CODEX_HERETICUS.md`. — Bit only works if chaos stays cartoonish.
- **Deadline**: None. Leisure project. — Goal is dopamine, not shipped value.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fork Ouroboros, don't build from scratch | Framework solves the unglamorous parts (TG routing, memory, consciousness loop). Weekend to v1 vs month from zero. | — Pending |
| Local Ollama, not OpenRouter | Free, no rate limits, no content-policy refusals, privacy, works offline. | — Pending |
| Qwen 3.6-35B-A3B primary + Qwen 3:4B background | MoE = fast despite size; strong RU; 4B keeps background loop from hogging the 20GB model RAM. | — Pending |
| Chaos heretic persona (anti-Tech-Priest) | Contrast humor with owner's Mechanicus aesthetic. Funnier than a sycophantic mirror. | — Pending |
| Keep self-mod, gate with `playground` + dry-run + `/sanction` | Self-modification is the soul of Ouroboros. Removing it makes Heretek boring. Gates prevent corruption. | — Pending |
| Remove browser/Playwright tool | Heavy dep, runaway-tab risk, marginal value for shitposting. | — Pending |
| RU/EN only in v1, no Bashkir | Qwen's Bashkir quality unknown. Defer to experiment phase. | — Pending |
| GH repo name = `heretek` | Matches CLAUDE.md, kebab-clean, short. | — Pending |
| Defer TG token + owner ID to Phase 4 | Phases 0-3 don't need them; grab right before launch. | — Pending |
| Cap context to 32K initially | Avoid RAM blowup on 32GB host before profiling. Can raise later. | — Pending |

## Current State

Phase 2 (persona-identity) complete: `BIBLE.md` and `prompts/SYSTEM.md` rewritten in place as the chaos-heretek persona (forbidden territories above keep-and-corrupted Принцип 0/1/2; bilingual RU+EN mix; inherited drift-detector → heresy-detector pattern). `heretek/memory.py:_default_identity()` ships a 5-section identity scaffold. `heretek/context.py` 8h-stale warning retuned for chaos-heretek voice. `memory/` gitignored. `python scripts/smoke_test.py` runs **9 PASS / 0 FAIL**: bilingual reflex through full prompt-assembly path, refusal-in-character (heretical preamble + accurate answer), and seeded-grudge restart-recall all verified live via `qwen3:4b`. Manual persona-vibe sign-off on the 24GB primary model is the only remaining Phase 2 gate before Phase 3 (Self-Modify Guardrails).

---
*Last updated: 2026-05-16 after Phase 2 completion*
