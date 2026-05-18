# Milestones

## v6.2 Heretek launch (Shipped: 2026-05-18)

**Delivered:** A locally-hosted bilingual RU/EN chaos-heretek Telegram shitposting bot with a witnessed self-modification approval loop, forked from `razzant/ouroboros@v6.2.0` and stripped of all cloud dependencies.

**Phases completed:** 4 phases, 15 plans, ~88 commits

**Stats:**
- Timeline: 2026-05-14 → 2026-05-18 (5 days)
- Python LOC: 13,647 across `heretek/`, `supervisor/`, `scripts/`
- Smoke harness: 19 PASS / 0 FAIL / 1 SKIP (consciousness Ollama-gated)
- Host: MacBook Pro M1 Max 32GB, macOS Tahoe 26.3.1, Ollama native (Metal)
- Bot: `@evil_engine_number_9bot` in private TG group with owner `@jj_headsets` (user_id 75831266)

**Key accomplishments:**

1. **Phase 1 — Foundation + Local LLM (5 plans):** Forked Ouroboros v6.2.0, renamed `ouroboros/` → `heretek/` package, hard-deleted `tools/github.py` + `tools/review.py` + `tools/browser.py`, wired `LLMClient` to Ollama at `127.0.0.1:11434/v1` (IPv4-explicit + `trust_env=False` to bypass macOS system proxies), neutered budget tracker to JSONL token logger at `logs/tokens.jsonl`. Smoke-harness scaffold with bilingual RU+EN end-to-end test.
2. **Phase 2 — Persona + Identity (2 plans):** Rewrote `BIBLE.md` (282 lines) and `prompts/SYSTEM.md` (~21KB) as chaos-heretek persona with horror flavor + corrupted Mechanicus aesthetic. Forbidden territories pinned as Principle 0′ above the three principles. Bilingual reflex elevated to TOP of system prompt (qwen3:4b attention quirk). Identity scaffold + 8h-stale warning. PERS-06 grudge-recall verified via hermetic tempfile pattern.
3. **Phase 3 — Self-Modify Guardrails (3 plans):** `safe_push()` chokepoint in `supervisor/git_ops.py` raises `ProtectedBranchError` before any subprocess call for `main` / `last-known-good`. `cmd_evolve()` writes `.heretek/dryruns/<id>.patch` + SHA256 sidecar with zero git calls. `cmd_sanction()` does SHA256 tamper check → apply → commit → import-test gate → annotated-tag advance (with `reset --hard HEAD~1` rollback on test failure). `cmd_heresy()` rolls working tree to `last-known-good`. All 6 SAFE-* tests live-PASS via hermetic temp-repo fixtures.
4. **Phase 4 — Launch + First Evolution (5 plans):** `supervisor/boot.py` ships the production daemon (env validation fail-loud → state.init → git_ops.init → TelegramClient → spawn_workers → consciousness.start → event drainer → TG long-poll). Three-layer owner gate (`is_owner_message` at polling boundary; defensive re-check in `handle_slash_command`; Layer 3 reserved at agent task-entry). `BILINGUAL_REFUSAL` static constant (no LLM call) with 24h per-user_id cooldown. `{OWNER_HANDLE}` template substitution from `HERETEK_OWNER_HANDLE` env. Production `/evolve` enqueues `{type:'evolution'}` task; `agent.py:_capture_evolution_dryrun()` captures `git diff HEAD`, persists `dr-<UTC>-<8hex>.patch+.json`, stashes live tree, posts code-block diff. First witnessed `/evolve → /sanction → commit` loop landed 2026-05-18.

**Emergent fixes (runtime debugging from live sessions):**

- Event drainer for `workers.get_event_q()` — Plan 04-03's boot.py omitted the consumer; bot typed but never replied. Fixed via daemon thread routing through `supervisor.events.dispatch_event`. Regression-tested via `test_event_drainer_routes_send_message`.
- httpx explicit timeouts (`connect=10s read=300s write=30s pool=10s`) — without them, a hung Ollama blocked the chat thread forever.
- Threaded chat dispatch (`run_chat_direct_threaded` + `_CHAT_DIRECT_LOCK`) — synchronous `handle_chat_direct` froze the whole bot on one stuck LLM call.
- Colab path leak in `supervisor/queue.py` — `from supervisor.state import QUEUE_SNAPSHOT_PATH` froze the import at module-load. Switched to `_queue_snapshot_path()` helper that reads fresh each call.
- mp.Process worker initialization — spawn workers re-import modules fresh and never inherited `state.init` / `git_ops.init` from parent. Workers crashed on every git invocation with `/content/heretek_repo` not found. Workers now call init themselves.
- Bounded `_CHAT_DIRECT_LOCK.acquire(timeout=420)` — if a wedged LLM call holds the lock past httpx's 300s read timeout, new messages get "daemon busy" reply instead of piling up forever.
- `events.py:_handle_restart()` was execing the deleted `colab_launcher.py` — patched to `python -m supervisor` in Plan 04-01.

**Key decisions:**

- Fork Ouroboros instead of building from scratch (framework solves the unglamorous parts: TG routing, memory, consciousness loop, tool plugins).
- Local Ollama instead of OpenRouter (free, no rate limits, no content-policy refusals, privacy, offline).
- Qwen 3.6-35B-A3B primary + Qwen 3-4B background (MoE = ~3B active params/token; strong RU; Q4_K_M fits in ~24GB).
- Chaos heretic persona (anti-Tech-Priest contrast comedy with owner's Mechanicus aesthetic).
- Keep self-modification gated with `playground` branch + dry-run + `/sanction` ritual (P2 Self-Creation principle made operational).
- `HERETEK_OWNER_USER_ID` env-var only, no hardcoded fallback (footgun prevention).
- `{OWNER_HANDLE}` template substitution instead of literal hardcode in BIBLE/SYSTEM (rotation-friendly, no PII in git).
- `HERETEK_DATA_ROOT` defaults to repo root (everything greppable; `state/`, `archive/`, `locks/`, `logs/`, `memory/`, `.heretek/`, `task_results/` all gitignored).
- tmux session as the v1 production-run pattern (no launchd/systemd complexity for a leisure project).

**Technical debt incurred:**

- `tools/vision.py` left as no-op (deferred from Phase 1 strip).
- `promote_to_stable` LLM tool became no-op after Phase 3 (`/sanction` does its job now); not yet deleted.
- Residual `OUROBOROS_*` env-var references in `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py` — fixed opportunistically in Phase 4 worker_main, full sweep deferred.
- DRIVE_ROOT internal Python identifier kept (env-facing var is `HERETEK_DATA_ROOT`); full rename deferred as low-risk cleanup.
- Bot auto-rescue path generates generic commit messages on dirty file sweep (manual reword required for descriptive history; force-pushed once for v6.2).
- Smoke harness is `scripts/smoke_test.py` (NOT pytest); migrating to pytest deferred unless v6.3+ wants it.

**Deferred to v6.3+ stretch:**

- EXP-01 Bashkir language support (Qwen quality unknown)
- EXP-02 Vision/screenshot reaction (would re-add a slimmer browser tool or use a multimodal model)
- EXP-03 Cron-driven `last-known-good` advance (timer-based vs `/sanction`-driven)
- EXP-04 Web search tool re-enable via local-friendly backend (DDG, SearXNG)
- In-process watchdog vs tmux-only crash policy
- launchd plist for autostart on login
- Manual persona-quality sign-off session formalization

---
