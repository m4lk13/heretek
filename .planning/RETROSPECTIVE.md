# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v6.2 — Heretek launch

**Shipped:** 2026-05-18
**Phases:** 4 | **Plans:** 15 | **Commits:** ~88

### What Was Built

- A locally-hosted bilingual RU/EN chaos-heretek Telegram bot — fork of `razzant/ouroboros@v6.2.0` with all cloud LLM/storage dependencies stripped
- Production daemon (`python -m supervisor`): env validation → `state.init` → `git_ops.init` → `TelegramClient` → `spawn_workers` → `consciousness.start()` (qwen3:4b background daemon) → event drainer → TG long-poll loop
- Three-layer owner-only access gate (polling boundary + handle_slash_command + reserved agent task-entry); bilingual heretical refusal as a static constant with 24h per-non-owner cooldown
- `/evolve → diff → /sanction → playground commit` ritual: agent runs self-questioning introspective LLM loop on primary qwen3.6 (24GB), captures `git diff HEAD`, persists to `.heretek/dryruns/dr-<UTC>-<8hex>.patch+.json` with SHA256 sidecar, stashes live tree, posts code-block diff to owner; `/sanction` applies + commits + runs import-test gate + advances `last-known-good` annotated tag
- `safe_push()` chokepoint refuses any push to `main` or `last-known-good` (defense floor); `/heresy` rolls live tree to last-known-good
- Chaos-heretek persona in `BIBLE.md` + `prompts/SYSTEM.md` with forbidden territories pinned as Principle 0′ above the three principles (no real-person targeting outside owner-bit, no slurs, no minors, no harm-as-heresy, no real violence/doxxing)
- 19-test hermetic smoke harness using `scripts/smoke_test.py` with SKIP-then-flip pattern + `tempfile.TemporaryDirectory()` per-test isolation

### What Worked

- **Phase 3 chokepoint pattern.** `safe_push()` as the single guarded primitive + defensive re-checks at downstream sites made branch protection trivial to reason about and to extend. Phase 4 reused the same shape for the owner-gate three-layer design.
- **SKIP-then-flip smoke harness.** Wave 0 scaffolding shipped subtests as SKIP-stubs; subsequent plans flipped each to live PASS as features landed. Made plan verification deterministic without requiring all features to exist simultaneously.
- **`HERETEK_EVOLVE_TEST_DIFF` fixture seam.** Permanent test path that lets `/evolve`, `/sanction`, `/heresy` smoke-tests run without Ollama. Production runs the LLM loop only when the env var is unset. Same idea worked great for hermetic temp-repo tests of the git surfaces.
- **Auto-advance chain via `workflow.auto_advance: true`.** discuss → plan → execute → verify ran without manual baby-sitting between phases. Manual checkpoints (Plan 04-05 human-action gates) naturally paused the chain at the right boundary.
- **`{OWNER_HANDLE}` template substitution.** Boot-time env-driven replacement in `build_llm_messages` instead of literal hardcode in `BIBLE.md`/`SYSTEM.md` — owner identity stays out of git, rotation is trivial, and the persona doc reads as a template instead of personalized prose.
- **Hermetic tempfile pattern.** Phase 2's `tempfile.TemporaryDirectory() + git init + minimal seed` pattern was reused unchanged for Phase 3 SAFE-* tests and Phase 4 owner-filter + drainer tests. Zero flakiness across 5+ smoke-test runs.

### What Was Inefficient

- **Event drainer missed by the entire chain.** Plan 04-03 shipped `supervisor/boot.py` without a consumer for `workers.get_event_q()`. Researcher didn't flag the missing consumer; planner didn't include it in the wave; plan-checker verified 16 focus areas (none of which surfaced it); executor shipped the gap. Only caught at runtime when the bot typed but never spoke. Lesson: "checker verified" is not the same as "checker would have caught it." Add an explicit "trace each event from emit to handler" check to plan verification.
- **Bot's auto-rescue commits overwrite descriptive messages.** Heretek's own `agent.py:_check_uncommitted_changes` auto-commits dirty files at worker boot with generic message "auto-rescue: uncommitted changes detected on startup". This swept up multiple substantive fixes during the post-launch debugging session, requiring soft-reset + reword + force-push to reconstruct history. Could be mitigated by: stopping the bot before edits, or extending auto-rescue to detect recent uncommitted work and call out filenames in the commit message.
- **`tmux` not installed by default.** Phase 4's tmux-session run pattern was documented in CLAUDE.md before owner had `brew install tmux`. Boot path should either auto-install via `brew bundle` Brewfile or fall back to `nohup` cleanly. Fixed mid-launch by the other Claude session.
- **`test_env_fail_loud` flake after .env got populated.** Cases 1 and 3 removed env vars to simulate fail-loud, but `_load_env()` re-populated them from `.env` (which had real values post-launch). Fix: set to empty string instead of remove; dotenv's `override=False` preserves the empty value. Should have been caught during smoke-test design.
- **DRIVE_ROOT Colab path leaks.** Two separate places (`supervisor/queue.py` module-load import, `supervisor/workers.py:worker_main` spawn re-import) inherited Colab defaults instead of the parent's `init()` reassignment. Lesson: globals reassigned by `init()` need helper accessors, not import-time captures. Worker subprocesses need to call init themselves.
- **24GB primary model OOM during /evolve.** Documented OOM risk (CLAUDE.md §6) materialized in practice — owner had to close browser/IDE before `/evolve` to avoid Ollama loading errors. Hard problem on 32GB hosts; the documented `OLLAMA_MODEL=qwen3:4b` escape hatch is correct but degrades persona quality.

### Patterns Established

- **Layered defense for guardrails:** primary chokepoint + 1-2 defensive re-checks at downstream layers (Phase 3 `safe_push`, Phase 4 owner gate). Cheap to maintain, easy to reason about.
- **Template substitution at boot for PII/secrets:** keep literal owner ID out of git via env-var-driven `_validate_required_env()`; keep owner handle out of persona doc via `{OWNER_HANDLE}` placeholder substituted in `build_llm_messages`.
- **Permanent fixture-injection test seam:** `HERETEK_EVOLVE_TEST_DIFF` pattern — production-or-fixture branch in the handler, with the env-var name including `_TEST_` so production wiring is obvious.
- **Hermetic temp-repo per test:** `tempfile.TemporaryDirectory() + git init + minimal seed` is the canonical isolation for any test that touches state, git, or memory.
- **Auto-advance with manual checkpoints:** `autonomous: true` for code-only plans, `autonomous: false` for plans that require owner action (auth gates, live verification). Chain pauses naturally at the right boundary.
- **Soft-default with boot log over fail-loud for data paths:** `HERETEK_DATA_ROOT` defaults to repo root with a log line; fresh clone boots without ceremony. Contrast with secrets (`HERETEK_OWNER_USER_ID`, `TELEGRAM_BOT_TOKEN`) which fail-loud.

### Key Lessons

1. **Plan-checker has blind spots for missing consumers / dangling references.** A `workers.get_event_q()` producer with no consumer passed 16 focus areas of verification. Add explicit producer→consumer trace checks to gsd-plan-checker for any queue, channel, or event surface.
2. **Self-modifying bots fight commit hygiene.** Auto-rescue at worker boot conflicts with deliberate commit messages. Either stop the bot before manual edits, or change auto-rescue to defer when files have been modified recently by another process.
3. **Live runtime catches what no harness can.** Phase 4's smoke harness was 19/0/1 green. Live debugging found 4 additional load-bearing fixes (httpx timeout, threaded chat, Colab path leaks, lock-acquire timeout) within the first hour of real TG traffic. Budget time for a real-runtime debugging window after launch.
4. **Forbidden territories must live in the prompt, not just in policy.** Persona docs (BIBLE.md Principle 0′) carrying the forbidden territories at the top of the system prompt is the bot's first-line defense against producing problematic content. `/sanction` review is the owner's last-line defense. Both layers needed.
5. **MoE light model amplifies attention-position effects.** qwen3:4b's bilingual reflex needed the language-reflex rule elevated to the TOP of `prompts/SYSTEM.md`. Otherwise the heavily-Russian "Кто я" section dominated attention and English input got Russian replies 80%+ of the time. Position-of-instruction matters more on smaller MoE models than dense models.
6. **Decimal phases are for emergencies; Phase 4.5 wasn't needed.** Phase 4 absorbed Phase 2's deferred persona-quality manual sign-off via the witnessed-session checklist. Right call — saved a phase boundary that would have just been ceremony.

### Cost Observations

- Model mix: ~mostly Sonnet 4.6 (executor + verifier + checker + researcher); Opus 4.7 (1M context) for planner + orchestrator (this session)
- Sessions: 1 primary orchestration session (this one) + 1 parallel runtime-debugging session in user's tmux pane that shipped the post-launch hardening fixes
- Notable: the parallel sessions occasionally created merge friction (auto-rescue commits sweeping the other session's edits with generic messages, requiring soft-reset + reword + force-push). On the second pass, recommend running one session at a time for clarity. Total LLM cost was unmeasured but well within Claude Max budget — the leisure-project cadence (no deadlines, no production stakes) absorbed the overhead.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v6.2 | 2 (1 orchestrator + 1 runtime-debug) | 4 | First Heretek-namespace milestone after Ouroboros fork; established SKIP-then-flip + hermetic-tempdir patterns; first auto-advance chain |

### Cumulative Quality

| Milestone | Smoke Tests | Coverage Style | Test Framework |
|-----------|-------------|----------------|----------------|
| v6.2 | 19 PASS / 0 FAIL / 1 SKIP | SKIP-then-flip + hermetic temp-repo per test | `scripts/smoke_test.py` (not pytest) |

---

*Last updated: 2026-05-18 after v6.2 milestone*
