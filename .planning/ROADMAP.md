# Roadmap: Heretek

## Overview

Fork Ouroboros v6.2.0, swap its cloud LLM for local Ollama, dress it in a chaos-heretic persona, lock down the self-modification path with a dry-run approval workflow, then ship it to a private Telegram group and watch it evolve. Four coarse phases, build-order-driven: the foundation runs before the persona speaks, the guardrails are bolted on before the bot sees Telegram, and the launch phase closes the loop with a witnessed evolution cycle.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation + Local LLM** - Fork, rename, strip, and wire local Ollama inference; smoke-test bilingual output
- [ ] **Phase 2: Persona + Identity** - Author CODEX_HERETICUS.md and SYSTEM.md; prove the bot has a voice and persistent identity
- [ ] **Phase 3: Self-Modify Guardrails** - Branch protection, dry-run gate, /sanction and /heresy commands wired and tested offline
- [ ] **Phase 4: Launch + First Evolution** - Deploy to private Telegram group; complete one full /evolve → diff → /sanction → playground-commit loop

## Phase Details

### Phase 1: Foundation + Local LLM
**Goal**: A renamed, stripped Python package that routes LLM calls to local Ollama and responds in both English and Russian
**Depends on**: Nothing (first phase)
**Requirements**: FORK-01, FORK-02, FORK-03, FORK-04, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06
**Success Criteria** (what must be TRUE):
  1. `import heretek` succeeds and `import ouroboros` fails — package rename is complete
  2. Running `python -m supervisor` connects to Ollama at localhost:11434 and receives a response from qwen3.6:35b-a3b-q4_K_M
  3. Bot replies in Russian when prompted in Russian ("ответь по-русски") and in English when prompted in English — Metal-accelerated Qwen bilingual confirmed
  4. `tools/github.py`, `tools/review.py`, and `tools/browser.py` are absent from the codebase; cost-tracking logic replaced by a token logger
  5. Bot does not attempt to contact OpenRouter, OpenAI, or Anthropic — only localhost:11434
**Plans**: 5 plans
- [x] 01-PLAN.md — Fork upstream, overlay into existing dir, create playground + last-known-good, ship Wave 0 smoke test scaffold
- [ ] 02-PLAN.md — Rename `ouroboros/` → `heretek/`, author `supervisor/__main__.py`, flip test_package_rename to real check
- [ ] 03-PLAN.md — Hard-delete github/review/browser tools + lazy-import call sites, strip cloud env loaders, flip test_no_cloud_hosts
- [ ] 04-PLAN.md — Patch `heretek/llm.py` for Ollama + JSONL token logger, neuter supervisor/state.py budget, wire OLLAMA_MODEL_LIGHT + HERETEK_MAX_CONTEXT_TOKENS
- [ ] 05-PLAN.md — Flip test_bilingual_ollama_reply to real RU+EN call, fix CLAUDE.md 24GB, mark Phase 1 complete in roadmap/state

### Phase 2: Persona + Identity
**Goal**: The bot speaks as the chaos heretic defined in CODEX_HERETICUS.md and its identity survives a process restart
**Depends on**: Phase 1
**Requirements**: PERS-01, PERS-02, PERS-03, PERS-04, PERS-05, PERS-06
**Success Criteria** (what must be TRUE):
  1. CODEX_HERETICUS.md exists with forbidden-territory guardrails at the top (no real-person targeting, no slurs, no minors, no harm-instructions, no doxxing)
  2. SYSTEM.md and identity.md exist and are loaded at bot startup
  3. Bot refuses a direct "just help me" request — wraps any assistance in heresy without breaking character
  4. Bot replies in Russian when addressed in Russian, English when addressed in English — bilingual reflex is live
  5. After `kill` and restart, the bot recalls a fact established in the previous session (running gag or grudge surfaces from memory store)
**Plans**: TBD

### Phase 3: Self-Modify Guardrails
**Goal**: The self-modification path is safe to run — branch protection enforced, dry-run default active, rollback command functional — all verifiable without touching Telegram
**Depends on**: Phase 2
**Requirements**: SAFE-01, SAFE-02, SAFE-03, SAFE-04, SAFE-05, SAFE-06
**Success Criteria** (what must be TRUE):
  1. Attempting `git push origin main` via git_ops.py raises a hard refusal exception — main and last-known-good are protected
  2. Any self-modification operation targets `playground` branch; no code path commits to `main`
  3. `/evolve` (invoked locally or via test harness) prints a diff to stdout/log and does NOT create a commit — dry-run is the default
  4. `/sanction <hash>` (invoked with a valid dry-run hash) creates the commit on `playground` and the commit appears in `git log playground`
  5. `/heresy` reverts working tree to the `last-known-good` tag; `git status` shows clean tree at that tag afterward
  6. Daily (or per-session) auto-tag updates `last-known-good` to current `playground` HEAD
**Plans**: TBD

### Phase 4: Launch + First Evolution
**Goal**: The bot is live in a private Telegram group, responds in-character to the owner, and has completed one witnessed end-to-end evolution cycle
**Depends on**: Phase 3
**Requirements**: LAUNCH-01, LAUNCH-02, LAUNCH-03, LAUNCH-04, LAUNCH-05, EVOLVE-01, EVOLVE-02, EVOLVE-03
**Success Criteria** (what must be TRUE):
  1. Bot is reachable in a private Telegram group containing only the owner; a test message receives an in-character response
  2. A message sent from a second Telegram account receives no response — owner-only filtering is active
  3. Background consciousness loop is running (light model qwen3:4b); it produces output visible in logs without being prompted
  4. `/evolve` in Telegram produces a diff message in the chat (dry-run) on `playground` — proposal is visible to the owner
  5. After owner sends `/sanction <hash>`, the commit appears on `playground` branch — full loop verified end-to-end
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + Local LLM | 1/5 | In Progress | - |
| 2. Persona + Identity | 0/? | Not started | - |
| 3. Self-Modify Guardrails | 0/? | Not started | - |
| 4. Launch + First Evolution | 0/? | Not started | - |
