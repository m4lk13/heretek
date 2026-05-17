# Roadmap: Heretek

## Overview

Fork Ouroboros v6.2.0, swap its cloud LLM for local Ollama, dress it in a chaos-heretic persona, lock down the self-modification path with a dry-run approval workflow, then ship it to a private Telegram group and watch it evolve. Four coarse phases, build-order-driven: the foundation runs before the persona speaks, the guardrails are bolted on before the bot sees Telegram, and the launch phase closes the loop with a witnessed evolution cycle.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation + Local LLM** - Fork, rename, strip, and wire local Ollama inference; smoke-test bilingual output
- [x] **Phase 2: Persona + Identity** - Author CODEX_HERETICUS.md and SYSTEM.md; prove the bot has a voice and persistent identity (manual persona-quality sign-off pending)
- [x] **Phase 3: Self-Modify Guardrails** - Branch protection, dry-run gate, /sanction and /heresy commands wired and tested offline (completed 2026-05-16)
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
- [x] 02-PLAN.md — Rename `ouroboros/` → `heretek/`, author `supervisor/__main__.py`, flip test_package_rename to real check
- [x] 03-PLAN.md — Hard-delete github/review/browser tools + lazy-import call sites, strip cloud env loaders, flip test_no_cloud_hosts
- [x] 04-PLAN.md — Patch `heretek/llm.py` for Ollama + JSONL token logger, neuter supervisor/state.py budget, wire OLLAMA_MODEL_LIGHT + HERETEK_MAX_CONTEXT_TOKENS
- [x] 05-PLAN.md — Flip test_bilingual_ollama_reply to real RU+EN call, fix CLAUDE.md 24GB, mark Phase 1 complete in roadmap/state

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
**Plans**: 2 plans
- [x] 02-01-PLAN.md — Rewrite BIBLE.md + prompts/SYSTEM.md as chaos-heretek persona; rewrite _default_identity scaffold; retune 8h-stale warning; gitignore memory/; Wave 0 smoke-test scaffold (3 static PASS + 3 SKIP stubs)
- [x] 02-02-PLAN.md — Flip 3 SKIP stubs to real assertions via build_llm_messages + LLMClient.chat: test_bilingual_through_full_pipeline (PERS-04), test_persona_in_character (PERS-05), test_restart_recall_grudge (PERS-06)

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
**Plans**: 3 plans
- [ ] 03-01-PLAN.md — Ship safe_push() chokepoint + ProtectedBranchError + PROTECTED_BRANCHES; rename branch defaults across git_ops.py/workers.py/agent.py (Phase 1 deferred carry); refactor 3 push sites; gitignore .heretek/; Wave 0 smoke scaffold (6 SAFE SKIP-stubs + _make_test_repo helper); flip 2 SAFE-01 stubs to live PASS
- [ ] 03-02-PLAN.md — Create supervisor/commands.py (cmd_evolve/cmd_sanction stubs + cmd_heresy fully implemented); argparse CLI shim with --repo-dir; handle_slash_command stub in telegram.py; flip test_heresy_rolls_back_to_tag (SAFE-05) to live PASS
- [ ] 03-03-PLAN.md — Implement cmd_evolve (dry-run pipeline with HERETEK_EVOLVE_TEST_DIFF fixture seam) and cmd_sanction (with import-test-gate BEFORE tag advance — Risk 2 mitigation); ship scripts/fixtures/heresy_test.patch; flip 3 SAFE SKIP-stubs (SAFE-02, SAFE-03, SAFE-04, SAFE-06) to live PASS — Phase 3 phase-gate GREEN at 11 pass / 0 fail / 0 skip

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
**Plans**: 5 plans
- [ ] 04-01-PLAN.md — Boot infrastructure scaffold + colab_launcher.py blocker fix + .gitignore + Wave 0 smoke harness (8 SKIP-stubs + _make_mock_tg_client + .env.example); flips test_env_fail_loud + test_dotenv_loaded to live PASS
- [ ] 04-02-PLAN.md — {OWNER_HANDLE} template substitution in heretek/context.py + persona-doc placeholders; bilingual non-owner refusal with 24h rate-limit + defensive owner re-check in handle_slash_command; flips 2 SKIP-stubs to live PASS
- [ ] 04-03-PLAN.md — supervisor/boot.py production boot sequence + TG long-poll loop + Layer 1 owner gate + consciousness daemon thread + workers.shutdown sentinel-task helper; flips 3 SKIP-stubs to live PASS
- [ ] 04-04-PLAN.md — cmd_evolve production branch (enqueue evolution task) + agent.py evolution post-loop hook (git diff HEAD + stash + persist + emit, Option A staging); flips test_evolve_enqueues_task_when_no_fixture to live PASS
- [ ] 04-05-PLAN.md — CLAUDE.md doc refresh + 04-VERIFICATION.md checklist + 3 blocking manual checkpoints (LAUNCH-01 @BotFather prereqs, Sessions 1-3, Session 4 witnessed /evolve loop)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation + Local LLM | 5/5 | Complete | 2026-05-15 |
| 2. Persona + Identity | 2/2 | Complete | 2026-05-16 |
| 3. Self-Modify Guardrails | 3/3 | Complete   | 2026-05-16 |
| 4. Launch + First Evolution | 3/5 | In Progress|  |
