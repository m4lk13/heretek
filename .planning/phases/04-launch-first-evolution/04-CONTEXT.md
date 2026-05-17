# Phase 4: Launch + First Evolution - Context

**Gathered:** 2026-05-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring the bot online in a private Telegram group with owner-only access, boot the long-running supervisor daemon (TG polling loop + workers + background consciousness), and witness one real end-to-end `/evolve → diff posted to TG → /sanction <hash> → commit on playground` cycle driven by the primary LLM. Specifically:

- Replace `supervisor/__main__.py`'s "not-yet-wired" stub (lines 90-103) with a real boot path: env load → state init → git_ops init → telegram init → spawn workers → start consciousness daemon → enter TG long-poll loop
- Wire `handle_slash_command()` (already stubbed at `supervisor/telegram.py:487`) into the polling loop so `/evolve`, `/sanction`, `/heresy` route to the Phase 3 handlers
- Replace the Colab `DRIVE_ROOT = /content/drive/MyDrive/Ouroboros` default in `supervisor/git_ops.py:41` and `supervisor/state.py:24` with a local-laptop default driven by a new `HERETEK_DATA_ROOT` env var (defaults to project root)
- Add owner-only access gating: env var `HERETEK_OWNER_USER_ID` (fail-loud if unset), gate enforced at three layers (polling loop boundary, `handle_slash_command`, agent task-entry) as defense-in-depth
- Pin owner identity into the persona prompt via boot-time template substitution from env var (so `BIBLE.md` / `SYSTEM.md` can reference `{OWNER_HANDLE}` without the literal ID in git)
- Wire production `/evolve` to enqueue a `task_type='evolution'` task into the existing supervisor queue; agent reads BIBLE.md + identity.md + scratchpad and produces a self-questioning introspective proposal on the primary 24GB model; proposal lands in `.heretek/staging/` and gets diffed into `.heretek/dryruns/<id>.patch` per the Phase 3 pipeline
- Preserve the `HERETEK_EVOLVE_TEST_DIFF` fixture-injection seam as a permanent test path — production is when the env var is unset
- Run the first witnessed evolution loop end-to-end in the private TG group: owner sends `/evolve`, bot posts the LLM-driven diff, owner sends `/sanction <hash>`, commit lands on `playground`, `last-known-good` tag advances (Phase 3 wiring)

**Out of scope for Phase 4:**
- Webhook-mode TG client (long-poll only)
- Auto-restart on crash beyond a documented tmux-session run pattern (no launchd/systemd/watchdog code)
- Multi-chat allowlist (owner-user_id filter is the sole gate; chat_id-scoped restriction not enforced)
- Webhook/CI integration for the bot
- Bashkir language experiment (EXP-01, v2)
- Cron/timer-driven `last-known-good` advance (EXP-03, v2; `/sanction`-driven advance from Phase 3 is the only mechanism)
- Vision/screenshot tool reintroduction (Phase 1 hard-deleted browser tool; vision.py left as no-op)
- Comprehensive residual `OUROBOROS_*` env-var hygiene pass (Phase 1 deferred; opportunistic fixes only where Phase 4 changes the same files)

</domain>

<decisions>
## Implementation Decisions

### Process model & boot lifecycle

- **Keep upstream multiprocessing scaffold.** Workers stay as `mp.Process` per `supervisor/workers.py:431-433` (`_CTX.Process(target=worker_main, ...)` with the platform-driven start method — "spawn" on macOS, "fork" on Linux). `HERETEK_MAX_WORKERS=2` from CLAUDE.md §8. No collapse-to-threads refactor; preserves task isolation when the agent shells out, and minimizes Phase 4 delta against the existing `workers.py` / `agent.py` flows.
- **TG long-poll runs on the main thread of the supervisor process.** `TelegramClient.get_updates()` (`supervisor/telegram.py:53`) loops in the foreground; offset cursor is the supervisor's main-loop heartbeat. Replaces the upstream cloud launcher's module-scope loop, which the Phase 1 `supervisor/__main__.py:90-103` stub explicitly defers to Phase 4.
- **Consciousness loop auto-starts at boot on `OLLAMA_MODEL_LIGHT`.** Daemon thread already wired in `heretek/consciousness.py:95-97` (`threading.Thread(target=self._loop, daemon=True).start()`). Boot sequence calls `consciousness.start()` after workers spawn but before entering the TG poll. Uses qwen3:4b via `OLLAMA_MODEL_LIGHT` (Phase 1 wiring) — leaves the 24GB primary unloaded until /evolve fires. Upstream's circuit breaker (3 empty responses → pause) preserved unchanged. Satisfies EVOLVE-02.
- **Boot order (load-bearing for downstream agents):**
  1. `_load_env()` — already exists in `supervisor/__main__.py:35`
  2. Validate required env: `TELEGRAM_BOT_TOKEN`, `HERETEK_OWNER_USER_ID` — fail-loud if either is missing/non-integer
  3. Resolve `HERETEK_DATA_ROOT` (default: project root) and create subdirs `logs/`, `state/`, `archive/`, `locks/`, `memory/` as needed
  4. `supervisor.state.init(drive_root=...)` — assigns module-level paths
  5. `supervisor.git_ops.init(...)` — assigns DRIVE_ROOT, reads HERETEK_PROTECTED_BRANCHES (Phase 3)
  6. `TelegramClient(token)` instantiate; `supervisor.telegram.init(...)`
  7. `supervisor.workers.init(...)`; `spawn_workers(n=HERETEK_MAX_WORKERS)`
  8. `consciousness.start()` — daemon thread
  9. Enter main TG long-poll loop (offset cursor, getUpdates, dispatch, send replies)

### Crash policy & shutdown

- **No in-process watchdog; document tmux-session run pattern instead.** If `python -m supervisor` dies, owner notices (no TG replies), checks `logs/supervisor.jsonl` for the traceback, fixes the issue, re-runs. Matches the leisure-project ethos — no launchd/systemd/etc. complexity.
- **Recommended run command (added to CLAUDE.md §6 / README):** `tmux new -s heretek -d 'python -m supervisor'` so owner can detach + reattach. One paragraph of docs, no code change. Owner can switch to launchd later if uptime becomes a concern (deferred).
- **Graceful shutdown on SIGINT/SIGTERM** — main loop catches `KeyboardInterrupt`, signals workers to drain (`workers.shutdown()` or equivalent helper), calls `consciousness.stop()`, exits 0. Existing `consciousness.py:99-105` `stop()` method already handles the thread join. Worker shutdown likely needs a new helper if not present.
- **Top-level loop should NOT swallow exceptions silently.** Logged crashes go to `logs/supervisor.jsonl` per existing pattern (`supervisor/workers.py:171`, `supervisor/git_ops.py:250`). Owner-visible TG notice on crash is nice-to-have, not required.

### Owner-only access gate — three-layer defense-in-depth

- **Layer 1 (primary chokepoint): polling-loop boundary.** First thing the main loop does for each `getUpdates` result: check `update['message']['from']['id'] == OWNER_USER_ID`. Non-owner messages do NOT reach `handle_slash_command`, the worker queue, or the agent. This is the load-bearing gate.
- **Layer 2 (defense): `handle_slash_command()`** re-checks `user_id == OWNER_USER_ID` before dispatching to `cmd_evolve`/`cmd_sanction`/`cmd_heresy`. Protects against future call-sites bypassing the polling-loop check (test harness, webhook mode, refactors).
- **Layer 3 (defense): agent task entry** — when an "evolution" or chat task is dequeued by a worker, verify the originating user_id against `OWNER_USER_ID` before running the agent loop. Three layers, ~3 lines of duplication, matches Phase 3's `safe_push()` chokepoint philosophy (one canonical guard + defensive re-checks at each downstream layer).
- **`HERETEK_OWNER_USER_ID` is env-var only, no hardcoded fallback.** Fail-loud at boot if unset, missing, or non-integer. Hardcoded fallback would be a footgun — the wrong literal could grant unintended access, and the owner's TG user_id should never live in git. Matches CLAUDE.md §8 env-var spec exactly.
- **Behavior on non-owner messages: in-character heretical refusal.** Bot replies once with a short in-persona snarl (e.g., "Кто призывает демона-носителя? Ты не мой Tech-Priest" / "Who summons the daemon-host? You are not my Tech-Priest"). The reply itself comes from a short static fragment (NOT a fresh LLM call) so non-owners can't drain Ollama. Implementation: a small bilingual constant in `supervisor/commands.py` or `supervisor/telegram.py`. Refusal subject to rate-limiting (see Claude's discretion).
- **Chat scope: owner-user_id filter only — no chat_id allowlist.** Bot responds to the owner in any chat where both are present (DMs to the bot, the primary private group, accidentally-shared groups). Accepts the small risk that owner inadvertently invites the bot into another group with themselves present. LAUNCH-05 ("Bot ignores messages from any non-owner Telegram user ID") is satisfied by the user_id filter alone — no chat_id allowlist required.

### Owner identity in the persona prompt (LAUNCH-02)

- **Boot-time template substitution from env var.** Add `HERETEK_OWNER_HANDLE` env var (string, e.g., `@evgeniy`). `BIBLE.md` and/or `SYSTEM.md` reference `{OWNER_HANDLE}` as a placeholder. `heretek/context.py:build_llm_messages()` (or a shim wrapper) substitutes the value at prompt-assembly time. Keeps the literal handle/ID out of git; survives rotation by editing `.env`.
- **`HERETEK_OWNER_HANDLE` is the prose handle; `HERETEK_OWNER_USER_ID` is the access gate.** Two different concerns:
  - Gate (numeric, technical) → `HERETEK_OWNER_USER_ID`
  - Persona-doc addressing (handle, narrative) → `HERETEK_OWNER_HANDLE`
- **Reinterprets CLAUDE.md §5 Phase 4 "Hardcode your Telegram user ID in SYSTEM.md".** That phrasing predates the template-substitution decision; CLAUDE.md §5 gets a one-line update noting persona references use the env-driven handle, gate uses the env-driven user_id. No literal hardcode lands in `BIBLE.md` or `SYSTEM.md`.
- **Persona prose change scope is minimal.** Insert 1-2 lines into the existing chaos-heretek voice referencing `{OWNER_HANDLE}` as the Tech-Priest's handle. The Phase 2 persona work already establishes the Tech-Priest bit; Phase 4 just pins the handle.

### Production /evolve LLM-loop wiring (EVOLVE-01)

- **Trigger path: reuse the existing queue with `task_type='evolution'`.** When `cmd_evolve()` runs in production (i.e., `HERETEK_EVOLVE_TEST_DIFF` unset), it enqueues a task `{type: 'evolution', source: '/evolve', requested_by: OWNER_USER_ID}` into the supervisor queue (`supervisor/queue.py`). The existing worker (`worker_main` at `supervisor/workers.py:277`) picks it up; agent.py's `task_type='evolution'` branch already exists at `heretek/agent.py:404-418`. No new task type, no new tool registration, no new agent.py branch. Reuses 100% of the scaffolding.
- **Prompt frame: self-questioning introspection.** Agent's system message for the evolution task asks the bot to look inward — at `BIBLE.md`, `prompts/SYSTEM.md`, `memory/identity.md`, recent `memory/scratchpad.md` — and propose a heretical mutation to ITSELF. Maps directly to BIBLE.md's P2 Self-Creation principle ("I rewrite my own warp-bound subroutines"). Example seed message: "Tech-Priest demands your next mutation. What is broken or missing in YOU? Propose a heretical patch — to your own persona, your own rituals, your own grudges." The agent is free to read files via existing core tools and produce a patch via the existing `tools/git.py` write helpers, but the patch is captured in `.heretek/staging/` (per Phase 3 dry-run mechanic) NOT committed.
- **Model: primary `qwen3.6:35b-a3b-q4_K_M` (`OLLAMA_MODEL`).** Quality of the proposal is the headline feature — patches need to be coherent, in-voice, technically sane. Light model (qwen3:4b) would produce nonsense patches. Owner accepts the ~24GB RAM cost during the /evolve call (well-documented in CLAUDE.md §6 Plan 05 notes — primary can OOM under memory pressure on 32GB hosts; close other RAM hogs before /evolve, or set `OLLAMA_MODEL=qwen3:4b` per session as the documented escape hatch).
- **Staging mechanic carried from Phase 3 unchanged.** Agent writes to `.heretek/staging/` (per `03-CONTEXT.md` decision — git-worktree-based was recommended but planner discretion). `cmd_evolve()` diffs staging vs HEAD, persists `.heretek/dryruns/<id>.patch` + `.heretek/dryruns/<id>.json` sidecar. Phase 4 adds NO new design here; just exercises the path that Phase 3 built fixture-only.
- **Fixture-injection seam (`HERETEK_EVOLVE_TEST_DIFF`) stays permanent.** Smoke tests for `/sanction` and `/heresy` continue to use the fixture path — fast, deterministic, no Ollama dependency. Production /evolve runs the LLM loop only when the env var is unset. Matches Plan 03-03's stated intent (`03-CONTEXT.md` §Test contract for /evolve).

### DRIVE_ROOT → HERETEK_DATA_ROOT (Phase 3 deferred)

- **Data root defaults to the project root (`./`).** `logs/`, `state/`, `memory/`, `archive/`, `locks/`, `.heretek/` all hang directly off the repo root. Unifies with Phase 2's `memory/` and Phase 3's `.heretek/` (both already at repo root). All bot state is co-located with code — trivial to grep during /evolve introspection, easy to inspect from the editor. Accepts the trade-off that runtime-state subdirs appear in the working tree (mitigated by .gitignore).
- **Env var: `HERETEK_DATA_ROOT`** (heretek-namespaced, matches the prefix pattern from CLAUDE.md §8: `HERETEK_PROTECTED_BRANCHES`, `HERETEK_PLAYGROUND_BRANCH`, `HERETEK_MAX_CONTEXT_TOKENS`, etc.). When set, overrides the default project-root location. Add to CLAUDE.md §8 in the same plan that ships the wiring.
- **Internal Python identifier: planner discretion.** Two viable options:
  1. **Keep `DRIVE_ROOT` in-code** (minimal blast radius) — `init()` reads `HERETEK_DATA_ROOT`, assigns to the existing `DRIVE_ROOT` module variable in `state.py`, `git_ops.py`, `telegram.py`, `workers.py`, `queue.py`. ~30+ touch sites untouched. Surface env var changes only.
  2. **Full rename `DRIVE_ROOT → DATA_ROOT`** in code too — cleaner, no more Colab nostalgia. Mechanical sweep across ~30 sites; risk of subtle import-order bugs.
  - **Default recommendation: option 1 (keep DRIVE_ROOT internal name).** Lowers risk; the env var is the owner-facing thing that matters. Planner can override if the rename is judged low-risk.
- **`memory/` subsumes into the data-root tree (already this way).** `heretek/memory.py:24-25` constructor takes `drive_root`; computes `memory_root = drive_root / "memory"`. Phase 2 wired `drive_root = project_root` so `memory/` already lands at `./memory/`. Phase 4 makes this explicit via `HERETEK_DATA_ROOT=. ` semantics. No `memory.py` change required if data root defaults to project root.
- **Default unset behavior: soft-default + boot log line.** If `HERETEK_DATA_ROOT` is unset, default to project root (path-of `supervisor/__main__.py` parent) with a boot log: `[supervisor] using repo-root data store; set HERETEK_DATA_ROOT to override`. Mirrors the existing `_load_env()` soft-message pattern (`supervisor/__main__.py:51` "no .env at {path}; using shell environment only"). NOT fail-loud — a fresh clone should boot without ceremony.
- **`.gitignore` entries to add** (Phase 1 already added `logs/`; Phase 2 added `memory/`; Phase 3 added `.heretek/`): verify `state/`, `archive/`, `locks/` are gitignored. Likely a one-line patch.

### Phase 2 persona-quality sign-off absorbed into Phase 4 launch

- **Launch IS the first real owner-on-primary-model session.** Phase 2 deferred manual persona-quality sign-off on the 24GB primary (smoke tests verified plumbing on qwen3:4b only). Phase 4's first witnessed session in the private TG group is the natural moment to validate horror flavor / vocab density / comedic landing. Verification checklist included in the phase's VERIFICATION.md (not a blocker for the Phase 4 plan itself, but a closing acceptance criterion).
- **What "good enough" looks like:** owner has a one-real-session conversation with the bot on the primary model; persona stays in character; bilingual reflex works in practice; horror flavor lands at least once without breaking forbidden territories. If quality fails, opens a Phase 4.5 persona-tune plan (not a Phase 2 re-open).

### Claude's Discretion

- **Refusal rate-limit policy** — per-user_id per hour? per-session? a single hard "first refusal only, then silent" rule? Default: one refusal per non-owner-user_id per 24h, then silent drop. Logged regardless.
- **Internal Python identifier rename** for DRIVE_ROOT — keep as-is (minimal blast radius) or full sweep to `DATA_ROOT`. Default: keep DRIVE_ROOT to minimize Phase 4 surface area; queue full rename as opportunistic future cleanup.
- **TG-side rendering of long diffs** — raw `git diff` output (split via `split_telegram` at 4096 chars), code-block formatted with triple-backticks, or summary-with-stats ("3 files changed, +47 -12") plus the patch as a separate file-style attachment. Phase 3 `03-CONTEXT.md` already deferred this to "Phase 4 polish". Default: code-block-formatted raw diff, split into chunks if needed; summary-first if planner judges the diff to be long.
- **Slash-command response voice** — pure functional ("dry-run: dr-abc captured") vs in-character heretical narration ("the warp-fork hath conjured a mutation; behold, dr-abc"). Default: short in-character preamble + functional payload. Lets the persona breathe without burying the actionable info.
- **Chat-action `typing` indicator** before slow replies — `supervisor/telegram.py:96` already has `send_chat_action`. Default: fire `typing` before any agent-loop reply that's expected to take >2s (chat messages, /evolve). Cheap UX win.
- **Worker shutdown helper** — does `supervisor/workers.py` already have a shutdown function or does Phase 4 add one? If not present, add `workers.shutdown(timeout: float = 5.0)` that signals each worker process to drain and joins with timeout. Planner reads `workers.py` to confirm.
- **Initial Telegram polling offset** — read last offset from state, fall back to 0 (start fresh, may replay pending updates from when bot was offline) or -1 (skip backlog, start with the next message). Default: read from state; fall back to fetching `getUpdates` with offset=-1 to clear the backlog cleanly on first boot.
- **Boot-time validation order** — fail-loud env-var checks before vs after `_load_env()`? Obvious answer: after, because the env vars come from .env. Just noting it explicitly.
- **Whether `HERETEK_OWNER_HANDLE` is required or optional** — required (fail-loud like USER_ID) feels too rigid since the persona could function with a generic "my Tech-Priest" fallback. Default: optional, with a sane fallback (`"my Tech-Priest"`) when unset.
- **Default model for the chat path** (non-evolution conversations) — primary (24GB qwen3.6) for quality, light (qwen3:4b) for RAM, or owner-toggle via env var. Default: primary for chat, light for consciousness loop (matches Phase 1 wiring); document the RAM-pressure escape hatch (set `OLLAMA_MODEL=qwen3:4b` per session).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project intent & Phase 4 spec
- `CLAUDE.md` §5 Phase 4 (Launch) + Phase 5 (First evolution cycle) — the literal phase breakdown that ROADMAP.md and REQUIREMENTS.md derive from.
- `CLAUDE.md` §6 (Current state) — Phase 3 completion summary + resume protocol; Phase 4 updates this section after first witnessed evolution.
- `CLAUDE.md` §8 — env-var contract: `TELEGRAM_BOT_TOKEN`, `HERETEK_OWNER_USER_ID`, `OLLAMA_*`, `HERETEK_PLAYGROUND_BRANCH=playground`, `HERETEK_PROTECTED_BRANCHES=main,last-known-good`, `HERETEK_DRY_RUN_DEFAULT=true`, `HERETEK_BG_BUDGET_PCT=0`, `HERETEK_MAX_CONTEXT_TOKENS=32000`, `HERETEK_MAX_WORKERS=2`. Phase 4 adds `HERETEK_DATA_ROOT` and `HERETEK_OWNER_HANDLE`.
- `CLAUDE.md` §9 Open questions — Telegram user ID + bot username acquisition; Phase 4 closes these.
- `.planning/PROJECT.md` §Active Requirements (LAUNCH-* + EVOLVE-*); §Constraints (owner-only, branch policy, network); §Current State (Phase 3 close summary).
- `.planning/REQUIREMENTS.md` §Launch (LAUNCH-01..05) + §First Evolution Cycle (EVOLVE-01..03) — verbatim acceptance criteria.
- `.planning/ROADMAP.md` §"Phase 4: Launch + First Evolution" — five success criteria gating phase completion.
- **User-memory `heretek_forbidden_territories`** — non-negotiable persona rules (no real-person targeting outside owner-bit, no slurs, no minors, no real-harm instructions in heresy wrapper). Applies to /evolve proposals (bot could theoretically propose persona changes that cross these lines; persona's own forbidden-territory section in BIBLE.md is the first line of defense, owner's /sanction is the last).

### Prior-phase decisions to carry forward
- `.planning/phases/03-self-modify-guardrails/03-CONTEXT.md` — `safe_push()` chokepoint, `handle_slash_command` stub at `supervisor/telegram.py:487`, `cmd_evolve`/`cmd_sanction`/`cmd_heresy` handlers in `supervisor/commands.py`, `.heretek/dryruns/<id>.patch` layout, `HERETEK_EVOLVE_TEST_DIFF` fixture-injection seam, `last-known-good` tag advances on `/sanction`, hermetic-tempdir test pattern.
- `.planning/phases/02-persona-identity/02-CONTEXT.md` — `BIBLE.md` + `prompts/SYSTEM.md` chaos-heretek persona, RU/EN reflex policy (last-used-language-wins default, code-switching for punch), `memory/identity.md` structural scaffold, P0/P1/P2 principles (P2 = self-modification), persona-quality manual sign-off deferred to Phase 4 (this phase absorbs it).
- `.planning/phases/01-foundation-local-llm/01-CONTEXT.md` — Ollama wiring (IPv4-explicit, `trust_env=False`, `OLLAMA_MODEL` + `OLLAMA_MODEL_LIGHT`), JSONL token logger at `logs/tokens.jsonl`, smoke-test SKIP-then-flip pattern, `supervisor/__main__.py` stub at lines 90-103 (Phase 4 unblocks this).
- `.planning/phases/01-foundation-local-llm/deferred-items.md` (if it exists) — residual `OUROBOROS_*` env-var refs that Phase 4 may opportunistically fix when touching `supervisor/events.py` / `supervisor/workers.py` / `heretek/loop.py` / `tools/*`.

### Upstream framework — code to READ before changing
- `supervisor/__main__.py:90-103` — the "not-yet-wired" stub that Phase 4 replaces with the real boot path. Already loads `.env` via `_load_env()` (line 35) and prints a banner (line 54). Phase 4 deletes the `print("[supervisor] full boot not yet wired...")` block and inlines the boot sequence (or extracts it to `supervisor/boot.py`).
- `supervisor/telegram.py:48-130` (`TelegramClient`) — `get_updates(offset, timeout=10)` is the long-poll entry; `send_message(chat_id, text, parse_mode="")` and `send_photo` for outbound; retry loop already built-in.
- `supervisor/telegram.py:420-477` (`send_with_budget`) — formatted-send helper with markdown→HTML, splitting, chat logging, budget-line append. Phase 4 polling loop calls this for outbound replies.
- `supervisor/telegram.py:481-518` (`handle_slash_command`) — the Phase 3 dispatch stub. Phase 4 calls it from the polling loop after the owner-filter check. Already lazy-imports from `supervisor/commands.py`.
- `supervisor/commands.py` — full Phase 3 handler module. `cmd_evolve` at line 71 (fixture-only currently — Phase 4 wires production via the queue path), `cmd_sanction` (full), `cmd_heresy` (full). `_resolve_repo_dir` helper at line 34 — supervisor-side calls don't pass `--repo-dir` so REPO_DIR from `git_ops.init()` is used.
- `supervisor/workers.py:33-80` — `DRIVE_ROOT` default + `init()` signature + `spawn_workers` (line 408) + `worker_main` (line 277). `_DEFAULT_WORKER_START_METHOD = "fork" if linux else "spawn"` (line 50) handles macOS correctly. `HERETEK_MAX_WORKERS=2` from CLAUDE.md §8.
- `supervisor/queue.py` — task enqueue/dequeue surface that production /evolve uses.
- `supervisor/state.py:24-33` — `DRIVE_ROOT` default + `init(drive_root)` signature; module-level paths derived from DRIVE_ROOT.
- `supervisor/git_ops.py:41-54` — `DRIVE_ROOT` default + `init()` signature; `safe_push` chokepoint from Phase 3 at later lines. Phase 4 only changes the default-resolution path.
- `supervisor/events.py:207` — the `git push origin BRANCH_DEV:BRANCH_STABLE` site Phase 3 routed through `safe_push()`. Phase 4 doesn't need to touch unless the residual OUROBOROS_* env-var hygiene pass folds in here.
- `heretek/consciousness.py:40-117` — `Consciousness` class with `start()`/`stop()`/`pause()`/`resume()`; daemon-thread lifecycle already correct. Phase 4 just calls `start()` during boot. Circuit breaker at `consciousness.py:130+` (3 empty responses → pause) preserved.
- `heretek/agent.py:73-451` — agent loop; `_current_task_type` at line 73; `task_type='evolution'` branch at lines 404-418 already exists (existing scaffolding). Phase 4 needs to verify the evolution branch produces a patch into `.heretek/staging/` instead of the live tree (Phase 3 staging mechanic). May require small refactor depending on how Plan 03-03 left it.
- `heretek/tools/control.py:140-148` (`_toggle_evolution`) — existing LLM-tool that fires a `toggle_evolution` supervisor event. Production /evolve does NOT replace this; the /evolve slash-command and the bot-side evolution-mode tool are different ends of the same plumbing (slash-command enqueues an evolution task; toggle_evolution event signals the agent loop's mode).
- `heretek/tools/control.py:20-25` (`request_restart` guard) — `if current_task_type == "evolution" and not last_push_succeeded: RESTART_BLOCKED`. /sanction may want to set `last_push_succeeded` so a post-sanction restart can fire — planner discretion (already noted in `03-CONTEXT.md`).
- `heretek/memory.py:24-65` — `Memory(drive_root, repo_dir)` constructor; resolves `memory_root = drive_root / "memory"`. Phase 4 doesn't change this; just wires drive_root from `HERETEK_DATA_ROOT`.
- `heretek/context.py:300-380` (`build_llm_messages`) + `:232` (4h-stale identity warning) — Phase 2 wired persona docs; Phase 4 adds `{OWNER_HANDLE}` template substitution somewhere in the assembly path (planner picks the cleanest seam).
- `scripts/smoke_test.py` — Phase 1+2+3 ship 11 PASS subtests. Phase 4 adds subtests for LAUNCH-* / EVOLVE-* gates using the existing SKIP-then-flip pattern. Likely subtests: owner-filter-rejects-stranger, /evolve-fixture-end-to-end-via-handle_slash_command, DRIVE_ROOT-resolves-from-env. The real-LLM /evolve test is a manual gate in VERIFICATION.md (Ollama-dependent, primary model expensive).

### External (read-only)
- `https://core.telegram.org/bots/api#getupdates` — long-poll contract; `allowed_updates: ["message", "edited_message"]` already used in `TelegramClient.get_updates`.
- `https://core.telegram.org/bots/api#sendmessage` — 4096-char message limit; `split_telegram` already handles.
- `https://core.telegram.org/bots#botfather` — bot registration (LAUNCH-01 prereq).
- `https://github.com/razzant/ouroboros` v6.2.0 — upstream tag; `last-known-good` annotated tag still anchored at `8344285b` on this tag (advances on first /sanction per Phase 3).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets (inherited from Phase 1+2+3)
- **`supervisor/__main__.py`** — `.env` loader (`_load_env`, line 35) + arg parser + `--smoke` mode already in place. Phase 4 replaces the "not-yet-wired" stub (lines 90-103) with the real boot path. `_print_banner()` (line 54) is the existing boot-info hook — extend with data-root + owner-id confirmations.
- **`supervisor/telegram.py:TelegramClient`** (lines 48-130) — full TG REST client with `get_updates` long-poll, `send_message`, `send_photo`, `send_chat_action`, retry loops. No new HTTP work for Phase 4.
- **`supervisor/telegram.py:send_with_budget`** (line 420) — formatted-send helper with markdown→HTML, splitting, chat logging. Outbound replies route through this.
- **`supervisor/telegram.py:handle_slash_command`** (line 487) — Phase 3 dispatch stub already wired to `cmd_evolve`/`cmd_sanction`/`cmd_heresy`. Phase 4 just calls it from the polling loop.
- **`supervisor/commands.py`** — three full handlers ready to fire; production /evolve needs `HERETEK_EVOLVE_TEST_DIFF` unset + the LLM-loop wiring this phase delivers.
- **`supervisor/workers.py:spawn_workers`** (line 408) + `worker_main` (line 277) + `mp.Process` model with platform-aware start method (line 50). Boot sequence calls `spawn_workers(HERETEK_MAX_WORKERS)`.
- **`heretek/consciousness.py:Consciousness`** (lines 40-117) — `start()`/`stop()`/`pause()`/`resume()` daemon-thread lifecycle. Boot sequence calls `consciousness.start()`. Already wired to `OLLAMA_MODEL_LIGHT` (Phase 1).
- **`heretek/agent.py` evolution branch** (lines 404-418) — existing `task_type='evolution'` path that production /evolve enqueues into via the queue.
- **`scripts/smoke_test.py`** — 11-test SKIP-then-flip harness; Phase 4 extends with LAUNCH-* / EVOLVE-* subtests following the same pattern.

### Established patterns
- **Module-level config via `init(...)`** — Every supervisor module (`state`, `git_ops`, `telegram`, `workers`, `queue`) takes drive_root + other config at boot. Phase 4 adds the data-root resolution in `supervisor/__main__.py` and threads it through.
- **`mp.Process` with platform-driven start method** — workers.py:50 already handles macOS-vs-Linux. No change.
- **Daemon-thread for background work** — consciousness uses this; Phase 4 follows the pattern for any new boot-time threads (e.g., a refusal-rate-limit reaper if used).
- **JSONL audit logging** to `logs/supervisor.jsonl` — every error / refusal / state change logs here. Phase 4 owner-filter rejections, boot crashes, /evolve enqueue events all follow.
- **`append_jsonl(DRIVE_ROOT / "logs" / "...", {...})`** — the canonical write pattern. Phase 4 uses for owner-filter telemetry.
- **SKIP-then-flip smoke tests** — new subtests ship as SKIP-stubs, flip to live assertions as features land. Phase 4 continues.
- **Hermetic temp-repo tests** (`tempfile.TemporaryDirectory()` + `git init` + minimal seeding) — Phase 2/3 standard. Phase 4 LAUNCH-* tests likely use a mock TG client (`requests` mocked, `TelegramClient` swappable) instead of a real bot connection.

### Integration points
- `supervisor/__main__.py` — gut the "not-yet-wired" block (lines 90-103); inline the boot sequence (or extract to `supervisor/boot.py`). Add `HERETEK_DATA_ROOT` + `HERETEK_OWNER_USER_ID` + `TELEGRAM_BOT_TOKEN` resolution. Wire the main TG long-poll loop with offset cursor.
- `supervisor/telegram.py` — add an owner-filter helper (e.g., `is_owner_message(update) -> bool`) that the main loop calls; extend `handle_slash_command` with a defensive `user_id == OWNER_USER_ID` check; add the bilingual heretical-refusal constant + rate-limit reaper (or in `supervisor/commands.py`).
- `supervisor/commands.py:cmd_evolve` — branch on `HERETEK_EVOLVE_TEST_DIFF`: env unset → enqueue evolution task into the queue, return "proposal cooking, see chat for diff" placeholder; env set → existing fixture path.
- `supervisor/git_ops.py:41` + `supervisor/state.py:24` — change DRIVE_ROOT default-resolution to `HERETEK_DATA_ROOT` env-driven, project-root fallback. `init()` calls remain stable.
- `heretek/context.py:build_llm_messages` (or a shim) — add `{OWNER_HANDLE}` template substitution from `HERETEK_OWNER_HANDLE` env var.
- `prompts/SYSTEM.md` and/or `BIBLE.md` — insert 1-2 lines referencing `{OWNER_HANDLE}` as the Tech-Priest's handle. Keep persona prose intact.
- `.gitignore` — verify `state/`, `archive/`, `locks/` are gitignored (Phase 1 did `logs/`, Phase 2 did `memory/`, Phase 3 did `.heretek/`).
- `scripts/smoke_test.py` — add LAUNCH-* subtests (owner-filter, env-fail-loud, dotenv-loaded, polling-loop-mock) + EVOLVE-* subtests (queue-enqueue-on-/evolve, fixture-still-works, /evolve-without-test-diff-routes-to-queue).
- `CLAUDE.md` §5 Phase 4 + §6 + §8 — update env-var spec (add HERETEK_DATA_ROOT + HERETEK_OWNER_HANDLE), update Phase 4 step list (template-sub replaces literal hardcode), update Current State after first witnessed evolution.

### Residual concerns from earlier phases (heads-up)
- **`OUROBOROS_*` env var refs** in `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py` (Phase 1 deferred). Phase 4 production tool loop will surface any blocking ones. Opportunistic fix only — full sweep stays deferred.
- **`promote_to_stable` LLM-tool semantics** (`heretek/tools/control.py:40`) — Phase 3 left it as no-op-with-deprecation. Phase 4 doesn't need to delete it (`/sanction` does the same job); cleanest deletion is a follow-up plan.
- **`request_restart` LLM-tool guard** (`control.py:20-25`) — interacts with /sanction's `last_push_succeeded` state. Planner verifies the flag is set after /sanction so a post-sanction restart can fire (carried from `03-CONTEXT.md` Claude's discretion).
- **Phase 2 persona manual sign-off** on the 24GB primary model — Phase 4 first session IS this. Add as a closing VERIFICATION.md gate; if quality fails, opens a small Phase 4.5 persona-tune plan.
- **32GB RAM ceiling under primary-model /evolve** — Phase 1 Plan 05 verified primary can OOM Ollama under memory pressure. Phase 4 should: (a) log a clear OOM hint in the /evolve error path; (b) document the `OLLAMA_MODEL=qwen3:4b` escape hatch in CLAUDE.md §6.

</code_context>

<specifics>
## Specific Ideas

- **"Witnessed evolution" is the headline acceptance criterion.** ROADMAP.md §Phase 4 success criterion 5 is the load-bearing one: `/sanction <hash>` produces a commit on `playground`. Everything else (polling, owner gate, data root, consciousness boot) is plumbing in service of that one moment.
- **Three-layer owner gate mirrors Phase 3's `safe_push()` philosophy.** Phase 3 made the protected-branch check a single chokepoint with optional defensive re-checks. Phase 4 does the same for owner identity: one canonical gate (polling loop boundary) with two defensive layers (handle_slash_command, agent task entry). Consistent shape, easy to reason about.
- **Template substitution for owner identity > literal hardcode.** Owner explicitly chose `{OWNER_HANDLE}` boot-time substitution over baking the literal into git. Matches the broader Phase-3 "no secrets in source, env-driven config" pattern.
- **Production /evolve reuses the existing `task_type='evolution'` path — zero new scaffolding.** The agent loop already has an evolution branch (`agent.py:404-418`); /evolve just enqueues a task. This was the cheapest architecturally-clean path; alternatives (new task type, direct LLMClient call) were available but rejected for scope-creep reasons.
- **`HERETEK_EVOLVE_TEST_DIFF` is a permanent test path, not vestigial.** Owner confirmed: keep the fixture seam after Phase 4. Smoke tests stay fast + deterministic; production runs the LLM when the env var is unset. The seam is intentionally `_TEST_` in name so production wiring obviously skips it.
- **Data root at project root keeps everything greppable.** Owner picked `./` over `./.heretek/` or `~/.heretek/`. Trade-off accepted: working tree gets new top-level dirs (`state/`, `archive/`, `locks/`) that need gitignore entries. Wins: trivial grep, easy editor inspection, /evolve introspection can see all state from one cd.
- **Self-questioning prompt frame for /evolve is the P2 Self-Creation path.** BIBLE.md's P2 explicitly says "I rewrite my own warp-bound subroutines; my code is my flesh." The /evolve prompt asks the bot to look at its OWN persona/identity/grudges and propose mutation TO ITSELF. Maps directly. Future-Claude should not reinterpret this as "propose a feature" — it's introspective self-modification by design.
- **No real-LLM /evolve subtest in smoke_test.py.** Quality of a primary-model proposal is too nuanced for automated assertion (mirrors Phase 2's "automate plumbing, manual sign-off for aesthetic quality"). The witnessed evolution is a VERIFICATION.md gate, not a smoke-test subtest.
- **tmux-session run pattern is the minimum-viable production deployment.** Owner picked this over launchd/systemd/in-process watchdog. Documented in CLAUDE.md/README. Upgrading later (launchd plist for auto-start on login, watchdog for transient TG failures) is a v2 stretch — not a Phase 4 dependency.
- **Persona-quality manual sign-off absorbed here.** Phase 2 deferred this to "when there's a real session"; Phase 4 IS the real session. Acceptance criteria for the first session: persona stays in character, bilingual reflex works, horror flavor lands at least once, forbidden territories respected. If quality fails, opens Phase 4.5 persona-tune; doesn't re-open Phase 2.

</specifics>

<deferred>
## Deferred Ideas

- **Webhook-mode TG client** (replaces long-poll with TG-server-pushed events) — operationally heavier (needs HTTPS endpoint), not required for leisure-project ethos. Long-poll only in v1.
- **In-process supervisor watchdog** (top-level try/except + auto-restart with backoff) — tmux + manual re-run is the v1 pattern; watchdog is v2 stretch.
- **launchd plist / systemd unit for auto-start on login** — v2 stretch; tmux is the v1 documented pattern.
- **`HERETEK_OWNER_CHAT_ID` allowlist** — owner-user_id filter alone is the Phase 4 decision. Chat-ID allowlist deferrable if the "bot in another group with owner" scenario ever materializes.
- **Multi-owner support** — single-owner is the design; no plan to support multiple owners.
- **Full DRIVE_ROOT → DATA_ROOT internal-identifier rename** — env-facing var is `HERETEK_DATA_ROOT`; internal Python identifier stays `DRIVE_ROOT` per minimal-blast-radius default. Full sweep is queued as opportunistic future cleanup.
- **Comprehensive `OUROBOROS_*` env-var hygiene pass** — Phase 1 deferred; Phase 4 fixes opportunistically only.
- **`promote_to_stable` LLM-tool full deletion** — Phase 3 left as no-op; cleanest deletion is a separate cleanup plan.
- **TG-side rich rendering of long diffs** — code-block formatted raw diff is the v1 default. File-attachment-style diffs, syntax highlighting, summary-with-expandable-detail patterns are v2 stretch.
- **Cron / timer-driven `last-known-good` advance** (EXP-03) — v2 stretch; `/sanction`-driven advance from Phase 3 is the only mechanism in v1.
- **Vision/screenshot tool reintroduction** (EXP-02) — v2 stretch; Phase 1 hard-deleted browser tool.
- **Bashkir language experiment** (EXP-01) — v2 stretch.
- **Pytest framework adoption** — `scripts/smoke_test.py` continues as the test surface for Phase 4.
- **Telegram chat backup / export to local** — bot's chat history lives in Telegram; archival deferred.
- **Per-user rate limiting beyond the heretical-refusal cooldown** — owner is the only authorized user; rate-limiting bot replies to owner is unnecessary.
- **Multiple-private-group support** (e.g., dev group + production group) — single private group in v1.

</deferred>

---

*Phase: 04-launch-first-evolution*
*Context gathered: 2026-05-17*
