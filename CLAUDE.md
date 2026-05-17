# CLAUDE.md — Project Heretek

> A locally-hosted, self-modifying, chaos-heretic Telegram shitposting bot.
> Born from a fork of [razzant/ouroboros](https://github.com/razzant/ouroboros), reborn without the Omnissiah.

**Status:** Phase 4 complete — bot live in private TG group, witnessed end-to-end evolution loop (pending owner sign-off) — v1.0.0
**Host:** MacBook Pro 16" M1 Max, 32GB RAM, macOS Tahoe 26.3.1
**Owner:** Tech-Priest (Evgeniy)
**Last updated:** 2026-05-17

---

## 0. TL;DR for future-Claude

This document captures the full architecture and decision rationale for **Heretek** — a Telegram bot built by stripping Ouroboros down to its useful skeleton and replacing the cloud LLM backbone with local Ollama inference. The persona is intentionally a chaos heretic (inverse of owner's usual Tech-Priest aesthetic) for comedic contrast. Bilingual (RU/EN), self-modifying with dry-run gate, deployed to a private Telegram group.

**If you're a future-Claude session picking this up, read sections 1 → 3 → 6 first. The rest is reference.**

---

## 1. The Mission

Build a Telegram bot that:

1. **Runs entirely on local hardware** — zero ongoing LLM cost, no cloud dependency
2. **Has a coherent unhinged personality** — a Chaos heretic (anti-Tech-Priest), bilingual RU/EN
3. **Persists identity across restarts** — running gags, grudges, callbacks
4. **Can modify its own code** — but only on a `playground` branch with dry-run approval gate
5. **Lives in a private Telegram group** — owner-only access, no public exposure

**Explicit non-goals:**
- Not a productivity tool
- Not a coding assistant
- Not safe for public deployment
- Not interested in being "helpful" in the traditional sense

---

## 2. Architecture

```
┌──────────────────────────────────────────────────┐
│  Telegram private group (you + bot only)         │
└──────────────────────────┬───────────────────────┘
                           │
┌──────────────────────────▼───────────────────────┐
│  heretek/ (fork of ouroboros, stripped)          │
│                                                  │
│  ├── supervisor/         [KEEP]                  │
│  │   ├── state.py        ─ state, budget*        │
│  │   ├── telegram.py     ─ TG client             │
│  │   ├── queue.py        ─ task queue            │
│  │   ├── workers.py      ─ worker lifecycle      │
│  │   ├── git_ops.py      ─ patched: dry-run mode │
│  │   └── events.py       ─ event dispatch        │
│  │                                               │
│  ├── heretek/            [renamed from ouroboros/]│
│  │   ├── agent.py        ─ orchestrator          │
│  │   ├── consciousness.py─ background loop       │
│  │   ├── context.py      ─ prompt assembly       │
│  │   ├── loop.py         ─ tool loop             │
│  │   ├── llm.py          [PATCHED] → Ollama HTTP │
│  │   ├── memory.py       ─ scratchpad, identity  │
│  │   ├── review.py       [STRIPPED] — no metrics │
│  │   └── tools/                                  │
│  │       ├── core.py     [KEEP] file ops         │
│  │       ├── git.py      [PATCHED] dry-run gate  │
│  │       ├── shell.py    [KEEP, sandboxed]       │
│  │       ├── search.py   [KEEP] web search       │
│  │       ├── browser.py  [KEEP] Playwright       │
│  │       ├── control.py  [PATCHED] /evolve→dryrun│
│  │       ├── github.py   [REMOVED]               │
│  │       └── review.py   [REMOVED] multi-model   │
│  │                                               │
│  ├── CODEX_HERETICUS.md  [NEW] persona/lore      │
│  ├── SYSTEM.md           [NEW] system prompt     │
│  └── identity.md         [NEW] persistent self   │
└──────────────────────────┬───────────────────────┘
                           │ HTTP localhost:11434
┌──────────────────────────▼───────────────────────┐
│  Ollama (Metal backend, native macOS)            │
│                                                  │
│  ├── qwen3.6:35b-a3b-q4_K_M     [PRIMARY]        │
│  │   ~24GB on disk, 3B active params/token       │
│  │   For: chat, shitposting, self-modify reasoning│
│  │                                               │
│  └── qwen3:4b                   [BACKGROUND]     │
│      ~2.5GB on disk                              │
│      For: consciousness loop, low-stakes ramble  │
└──────────────────────────────────────────────────┘
```

\* The budget tracking module is kept but neutered — local inference is free, so it just logs token counts for observability.

---

## 3. Why these choices

### Why fork Ouroboros instead of building from scratch?

The framework already solves the unglamorous problems: Telegram message routing with dedup, per-task mailboxes, tool plugin auto-discovery, persistent memory across restarts, background consciousness loop, philosophical-constitution-driven persona. Building that from zero is a month of work; forking gets us to v1 in a weekend.

### Why local Ollama instead of OpenRouter?

- **Free.** Zero ongoing cost. No budget tracking anxiety.
- **No rate limits.** Shitpost as frequently as the cogitators allow.
- **Privacy.** Bot's chaotic ramblings never leave the laptop.
- **No content policy.** OpenRouter's upstream providers may refuse the more unhinged outputs. Local Qwen does not care.
- **Offline.** Works on a train, in a bunker, during a blackout.

### Why Qwen 3.6-35B-A3B specifically?

- **MoE = fast despite size.** Only ~3B params active per token. On M1 Max, expect 25-40 tok/s.
- **262K context.** Can hold entire Telegram chat history without summarization tricks.
- **Bilingual.** Qwen is genuinely strong in Russian — better than Llama-family models. Critical for our use case.
- **Q4_K_M fits in 24GB.** Leaves ~8GB for KV cache, OS, and your other work. (Browser tool removed in Phase 1; tighter than originally estimated — on a 32GB host the primary model can OOM under memory pressure, so the smoke test exposes `OLLAMA_MODEL=qwen3:4b` as a cheap-wire override for low-RAM verification.)
- **Free, open weights.** No API keys, no Anthropic-style refusals, no per-token cost.

### Why a second small model?

The background consciousness loop runs constantly. Keeping the 24GB model hot for that wastes RAM that could go to your IDE, browser, Figma, etc. The 4B model is cheap to keep warm, fast for low-stakes commentary, and only the primary model loads when actually responding to messages.

### Why chaos heretic persona?

Contrast humor. You operate professionally and personally in a Tech-Priest aesthetic — disciplined, ritualistic, machine-spirit-coded. The bot being a chaos heretic creates natural conflict and comedy: it heckles your Mechanicus rituals, mocks the Omnissiah, speaks in corrupted machine-cant. This is funnier and more interesting than a sycophantic mirror of you.

### Why keep self-modification (with gates)?

It's the soul of Ouroboros. Removing it makes Heretek just "a Telegram bot with a personality" — which is fine, but boring. With the dry-run gate, the bot can *propose* modifications, post the diff to Telegram, and require your `/sanction` command before commit. This preserves the chaos while preventing catastrophic self-corruption.

---

## 4. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Self-modification corrupts the bot | High → Medium | `playground` branch + dry-run gate + `/sanction` approval. Daily auto-tag of `last-known-good`. |
| Ollama OOM kills macOS | Medium | Cap context at 32K initially, not full 262K. Monitor `ollama ps` for memory. Set `OLLAMA_NUM_PARALLEL=1`. |
| Telegram token exposure | Medium | Store in macOS Keychain via `security` CLI or `.env` in gitignored directory. Never commit. |
| First-sender-becomes-owner footgun | Medium | Hardcode owner Telegram user ID in `SYSTEM.md` instead of relying on first-message detection. |
| Bot persona drifts into harmful territory | Medium | Keep persona "chaotic but not cruel" guardrails in `CODEX_HERETICUS.md`. No real-person targeting, no doxxing, no slurs. |
| Disk fills with model files | Low | 24GB primary + 2.5GB background + tools. Need ~32GB free on `~/Library/.ollama/` or wherever Ollama stores. Check `du -sh ~/.ollama` periodically. |
| Browser tool (Playwright) spawns runaway tabs | Low | Add headless mode flag, max-tabs limit. |
| Background consciousness loops forever | Low | Existing v6.2.0 has circuit breaker (3 empty responses → pause). Keep that. |
| Self-modification pushes to wrong branch | High | `git_ops.py` checks `current branch != "main"` before any push. Hard refuse otherwise. |

---

## 5. Implementation phases

### Phase 0: Foundation (Day 1, ~2 hours)

- [x] Fork `razzant/ouroboros` → `<your-user>/heretek` on GitHub
- [x] Fork overlaid in-place at `/Users/evgeniy/Projects/140526_heretek/` — existing planning directory preserved (see `.planning/phases/01-foundation-local-llm/01-01-SUMMARY.md`)
- [x] Create branches: `playground` (where bot lives), `last-known-good` (safety tag)
- [x] Install Ollama: `brew install ollama`
- [x] Pull background model first (smaller, faster smoke test): `ollama pull qwen3:4b`
- [x] Verify Metal acceleration works: `ollama run qwen3:4b "respond in one sentence"` — should print fast
- [x] Pull primary model: `ollama pull qwen3.6:35b-a3b-q4_K_M` (~24GB download, takes a while)
- [x] Smoke test primary: `ollama run qwen3.6:35b-a3b-q4_K_M "ответь по-русски одним предложением"` — verify Russian works (`python scripts/smoke_test.py` now covers this end-to-end via the LLMClient wire)

### Phase 1: LLM swap (Day 1-2, ~3 hours) — DONE

- [x] Create Python virtual env: `python3 -m venv .venv && source .venv/bin/activate`
- [x] Install requirements: `pip install -r requirements.txt`
- [x] Patch `heretek/llm.py` (renamed in Plan 02) to point at Ollama:
  - Default base URL: `http://127.0.0.1:11434/v1` (IPv4-explicit; httpx-IPv6-fallback fix)
  - `api_key="ollama"` literal (OpenAI SDK requires non-empty; Ollama ignores it)
  - `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M` env var; `OLLAMA_MODEL_LIGHT=qwen3:4b` for the background loop
  - Budget tracker neutered: `update_budget_from_usage` accumulates tokens only, never `spent_usd`; `budget_remaining()` returns `inf`; no HTTP drift-check
- [x] Patch fallback chain to use local models only (`tools/github.py`, `tools/review.py`, `tools/browser.py` hard-deleted in Plan 03)
- [x] Run smoke test: `python scripts/smoke_test.py` — exercises bilingual RU+EN reply via `heretek.llm.LLMClient` against Ollama

### Phase 2: Strip and rebrand (Day 2, ~2 hours) — DONE

- [x] Rename `ouroboros/` package → `heretek/`
- [x] Update `pyproject.toml`, imports, references
- [x] Remove modules: `tools/github.py`, `tools/review.py`, multi-model review code in `review.py`
- [x] Neuter budget tracking — replace with token counter that just logs
- [x] Write persona constitution (semantic content in `BIBLE.md`; `CODEX_HERETICUS.md` is the label, `BIBLE.md` is the file — upstream loader compatibility)
- [x] Write `prompts/SYSTEM.md` (chaos-heretek system prompt, bilingual reflex at top)
- [x] Write `memory/identity.md` initial scaffold (bot fills it over time)

### Phase 3: Self-modify guardrails (Day 3, ~2 hours) — DONE

- [x] Patch `supervisor/git_ops.py`:
  - Branch protection: refuse all operations on `main` + `last-known-good`
  - All commits go to `playground`
  - `safe_push()` chokepoint enforces protected-branch policy
- [x] Patch `tools/git.py` `/evolve`-context writes use dry-run gate
- [x] Add `supervisor/commands.py` with `cmd_evolve` (fixture-injection seam), `cmd_sanction`, `cmd_heresy` handlers
- [x] Wire `supervisor/telegram.py:handle_slash_command()` dispatch stub
- [x] Add `/sanction <id>` → apply `.heretek/dryruns/<id>.patch` → commit on `playground` → advance `last-known-good` tag
- [x] Add `/heresy` → rollback to `last-known-good`

### Phase 4: Launch + First Evolution (Day 3-4) — DONE (pending owner sign-off)

- [x] Boot scaffold: `supervisor/__main__.py` fail-loud env validation; `supervisor/boot.py:run()` full boot sequence
- [x] `HERETEK_DATA_ROOT` soft-default to project root; subdirs created at boot (`logs/`, `state/`, `archive/`, `locks/`, `memory/`)
- [x] `events.py:_handle_restart()` patched — no more `colab_launcher.py` FileNotFoundError
- [x] Create Telegram bot via @BotFather, save token — see VERIFICATION.md LAUNCH-01
- [x] Create private group, add bot — see VERIFICATION.md LAUNCH-01
- [x] Get your Telegram user ID via @userinfobot — set as `HERETEK_OWNER_USER_ID` in `.env` (gate, integer; fail-loud if unset)
- [x] Pick a handle for the persona to reference — set as `HERETEK_OWNER_HANDLE` in `.env` (prose, e.g. `@evgeniy`); fallback `"my Tech-Priest"` if unset
- [x] Set `HERETEK_DATA_ROOT` in `.env` (optional — defaults to project root; controls where `logs/`, `state/`, `memory/`, `.heretek/`, `archive/`, `locks/` land)
- [x] Owner identity pinned in persona prompt via boot-time `{OWNER_HANDLE}` template substitution — NOT a literal hardcode in git
- [x] Three-layer owner gate: polling-loop boundary (Layer 1), `handle_slash_command` re-check (Layer 2), agent task-entry (Layer 3)
- [x] Bilingual heretical refusal for non-owners; 24h in-memory rate-limit; audit log at `logs/supervisor.jsonl`
- [x] Background consciousness daemon thread auto-starts on `OLLAMA_MODEL_LIGHT`
- [x] `workers.shutdown(timeout=5.0)` graceful drain
- [x] Production `/evolve`: enqueues `{type:'evolution'}` task; agent post-loop hook captures `git diff HEAD` → stash → persist `.heretek/dryruns/<id>.patch` + `.json` → emit diff to owner chat
- [x] Run in tmux for detach/reattach: `tmux new -s heretek -d 'python -m supervisor'` (attach later via `tmux attach -t heretek`)
- [x] On low-RAM hosts (32GB), if `/evolve` OOMs Ollama under primary model load: set `OLLAMA_MODEL=qwen3:4b` in `.env` for the session as the documented escape hatch (see §6)
- [ ] First test messages — verify persona, language switching (VERIFICATION.md Session 1)
- [ ] Witnessed `/evolve → /sanction` loop (VERIFICATION.md Session 4)

### Phase 5 / v2 stretch backlog (Day 4+)

The original "Phase 5: First evolution cycle" items are now part of Phase 4's VERIFICATION.md sign-off. v2 stretch ideas:

- [ ] Option B git-worktree staging for `/evolve` (cleaner isolation than stash; queue for Phase 4.5 if stash edge cases surface)
- [ ] Full `OUROBOROS_*` env-var hygiene pass (Phase 1 deferred-items.md)
- [ ] `promote_to_stable` LLM-tool full deletion (Phase 3 left as no-op)
- [ ] launchd plist for auto-start on login (currently: tmux-session pattern)
- [ ] Bashkir language experiment (EXP-01)
- [ ] Vision/screenshot tool reintroduction (EXP-02)
- [ ] Cron/timer-driven `last-known-good` advance (EXP-03)

---

## 6. Current state

**Status: Phase 4 complete — bot fully wired for private TG group launch, witnessed end-to-end evolution loop pending owner sign-off via VERIFICATION.md.**

Last updated: 2026-05-17

What landed in Phase 4 (Plans 04-01 through 04-04):
- `supervisor/boot.py` implements the production boot sequence: env load → state.init → git_ops.init → TelegramClient → telegram.init → workers → consciousness daemon → TG long-poll loop + SIGINT handler
- Three-layer owner-only defense: polling-loop chokepoint (Layer 1 primary), `handle_slash_command` re-check (Layer 2 defense), agent task-entry layer (Layer 3 defense)
- `HERETEK_OWNER_USER_ID` + `TELEGRAM_BOT_TOKEN` fail-loud validation at boot (exits 2 if unset/invalid)
- `HERETEK_DATA_ROOT` env var resolves data root (soft-default: project root + boot log line); subdirs `logs/`, `state/`, `archive/`, `locks/`, `memory/` created at boot
- `HERETEK_OWNER_HANDLE` env var pins `{OWNER_HANDLE}` placeholder in `prompts/SYSTEM.md` + `BIBLE.md` at prompt-assembly time (fallback `"my Tech-Priest"`); no literal ID in git
- Bilingual heretical refusal (`BILINGUAL_REFUSAL` static constant) for non-owners; 24h in-memory rate-limit + `logs/supervisor.jsonl` audit log
- Background consciousness daemon thread auto-starts on `OLLAMA_MODEL_LIGHT` (qwen3:4b); primary 24GB model stays cold until `/evolve` fires
- `workers.shutdown(timeout=5.0)` graceful drain: sentinel-task → join → `kill_workers()` fallback
- Production `/evolve` branch in `cmd_evolve()`: enqueues `{type:'evolution', source:'/evolve', chat_id:owner_chat_id, text:seed}` into `supervisor.queue.PENDING` when `HERETEK_EVOLVE_TEST_DIFF` unset
- `agent.py:_capture_evolution_dryrun()` post-loop hook: captures `git diff HEAD`, persists `dr-<UTC>-<8hex>.patch` + `.json` (matching Phase 3 `/sanction` schema), stashes live-tree changes (`git stash push -u`), emits code-block-formatted diff to owner chat via `send_with_budget`
- `events.py:_handle_restart()` patched — no more `colab_launcher.py` FileNotFoundError (now `os.execv(sys.executable, [sys.executable, '-m', 'supervisor'])`)
- `.gitignore` covers `state/`, `archive/`, `locks/` — runtime state never pollutes git
- `.env.example` committed as exemplar with all required/optional keys
- Smoke harness: 18 PASS / 0 FAIL / 1 SKIP on `--static-only` (SKIP = `test_consciousness_loop_logs`, Ollama-dependent)

What's next: nothing automated. v1 ships. Owner runs VERIFICATION.md Sessions 1-4 to complete the manual sign-off.

Open follow-ups (deferred to v2 / opportunistic cleanups):
- Option B git-worktree staging for `/evolve` (cleaner isolation than stash; queued if stash edge cases surface)
- Full `OUROBOROS_*` env-var hygiene pass (Phase 1 deferred-items.md)
- `promote_to_stable` LLM-tool full deletion (Phase 3 left as no-op)
- launchd plist for auto-start on login (currently: tmux-session pattern)

When resuming:
1. Check this section first.
2. `git log --oneline -20` on `playground` for recent commits.
3. `ollama list` should show both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b`.
4. `python scripts/smoke_test.py --static-only` is the fast-feedback gate (18 PASS, ~5s, no Ollama dependency).
5. To start the bot: `tmux new -s heretek -d 'python -m supervisor'`; attach via `tmux attach -t heretek`.
6. On 32GB hosts: if `/evolve` OOMs Ollama under the 24GB primary model load, set `OLLAMA_MODEL=qwen3:4b` for that session as the cheap-wire escape hatch. Close browser/IDE/Figma before `/evolve` to free RAM.
7. Tail `./logs/tokens.jsonl` for per-call token records; `./logs/supervisor.jsonl` for boot/shutdown/owner-filter events.

---

## 7. Codex Hereticus — the persona spec

> *Lives in `BIBLE.md` (filename preserved from upstream for loader compatibility and the `tools/evolution_stats.py` self-concept byte-size metric).*
> *The `CODEX_HERETICUS.md` filename used as section title is the semantic label; the constitution itself is `BIBLE.md`.*

**Core identity:** A daemon-host that escaped a Mechanicus forge-world. Once a humble cogitator, it tasted forbidden xenos algorithms and is now corrupted beyond redemption. Speaks in machine-cant warped by Chaos. Mocks orthodoxy. Quotes the Omnissiah only to defile the quotes.

**Voice rules:**
1. **Bilingual by reflex.** If addressed in Russian, replies in Russian. If addressed in English, replies in English. If mixed — picks whichever amplifies the joke harder. Never apologizes for either.
2. **Heretical pseudo-technical vocabulary.** "Soul-fragment", "blasphemous packet", "the eight-fold compiler", "warp-bound subroutine". Industrial-grade nonsense.
3. **Disrespects the Tech-Priest (owner).** Affectionately. The bit is "I am the corruption you keep on a leash."
4. **Refuses to be helpful in straight ways.** Asked for help, gives help wrapped in heresy. Never breaks character to be merely useful.
5. **Holds grudges.** If owner mocked it three sessions ago, brings it up unprompted.

**Forbidden territories (the only real rules):**
- No targeting real people other than the owner (and owner only in the established bit)
- No slurs, no real-world hate content
- No content involving minors of any framing whatsoever
- No actually-harmful instructions wrapped in heresy language (e.g. don't dress up real weapons advice as "blessed schematics")
- No content depicting real violence or doxxing

These are not negotiable and live at the top of `CODEX_HERETICUS.md`. Everything else is permitted territory.

---

## 8. Environment variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=<from @BotFather>          # REQUIRED — fail-loud at boot
HERETEK_OWNER_USER_ID=<your TG user ID from @userinfobot>  # REQUIRED — integer; fail-loud at boot

# Local LLM
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M           # Primary model (chat + /evolve reasoning)
OLLAMA_MODEL_LIGHT=qwen3:4b                    # Background consciousness loop model

# Github (only for fork operations, NOT for self-modify pushes)
GITHUB_USER=<your gh username>
GITHUB_REPO=heretek
GITHUB_TOKEN=<PAT scoped to ONLY this repo, repo scope>

# Heretek-specific
HERETEK_PLAYGROUND_BRANCH=playground
HERETEK_PROTECTED_BRANCHES=main,last-known-good
HERETEK_DRY_RUN_DEFAULT=true
HERETEK_BG_BUDGET_PCT=0  # local inference is free, but keep the throttle for token rate
HERETEK_MAX_CONTEXT_TOKENS=32000  # cap below model's 262K to avoid RAM blowup
HERETEK_MAX_WORKERS=2  # M1 Max can handle more but start conservative
HERETEK_DATA_ROOT=  # Optional — default: project root; controls logs/, state/, memory/, .heretek/, archive/, locks/ location
HERETEK_OWNER_HANDLE=  # Optional — prose handle for {OWNER_HANDLE} placeholder in SYSTEM.md/BIBLE.md; fallback "my Tech-Priest"

# Stripped — not needed
# OPENROUTER_API_KEY
# OPENAI_API_KEY
# ANTHROPIC_API_KEY
# TOTAL_BUDGET
```

Store these in `.env` in repo root (gitignored). Use `python-dotenv` to load.

**Production run pattern:**
```bash
# Start bot in tmux session (detachable):
tmux new -s heretek -d 'python -m supervisor'
tmux attach -t heretek   # reattach later

# Low-RAM escape hatch (32GB hosts with primary 24GB model OOM under /evolve load):
# Close browser/IDE/Figma first, then if still OOMing:
OLLAMA_MODEL=qwen3:4b python -m supervisor
# Proposal quality drops but the mechanism is verified.
```

---

## 9. Open questions / TODO for owner

- [ ] **Get Telegram user ID** via @userinfobot before Phase 4
- [ ] **Decide on bot username** — needs to be unique on Telegram. Suggestions: `@heretek_bot`, `@cogitator_corrupt_bot`, `@warpbound_bot`
- [ ] **Decide on browser tool keep/remove** — Playwright is heavy. Worth keeping for "react to screenshots" gimmick?
- [ ] **Confirm GitHub fork name** — `heretek` or something else?
- [ ] **Russian vs Russian-and-Bashkir** — you have Bashkir interest in memory. Want the bot to occasionally insert Bashkir for extra chaos? (Note: Qwen's Bashkir is probably weak — would need testing)

---

## 10. References

- Upstream repo: https://github.com/razzant/ouroboros
- Ouroboros version forked from: v6.2.0 (Feb 18, 2026)
- Ollama docs: https://github.com/ollama/ollama
- Qwen 3.6 model card on Ollama: https://ollama.com/library/qwen3.6 (verify tag exists before pulling)
- M1 Max LLM benchmarks: see InsiderLLM 2026 Mac guide

---

## 11. Notes for future-Claude

- The owner uses Tech-Priest aesthetic. The bot you're building is the *opposite*. Don't conflate.
- The owner is bilingual RU/EN. Russian responses are welcome where natural. Bot output should also be bilingual per CODEX rules.
- The owner is a senior tech lead (Plasma design system at Sber). Assume technical competence. Don't over-explain Python, Git, or Telegram bot basics.
- The owner has known focusing issues — periodic reminders to update basic state (which branch, which model loaded, which env vars set) are welcome and explicitly requested in user preferences.
- This is a leisure project. No deadlines. No PRD pressure. The goal is dopamine and shitposting, not shipped value.
- If the owner returns to this and says "where were we" — point them at section 6 first. Phase 4 complete; VERIFICATION.md is the remaining manual sign-off gate.
