# CLAUDE.md — Project Heretek

> A locally-hosted, self-modifying, chaos-heretic Telegram shitposting bot.
> Born from a fork of [razzant/ouroboros](https://github.com/razzant/ouroboros), reborn without the Omnissiah.

**Status:** Phase 1 complete (Foundation + Local LLM) — v0.1.0
**Host:** MacBook Pro 16" M1 Max, 32GB RAM, macOS Tahoe 26.3.1
**Owner:** Tech-Priest (Evgeniy)
**Last updated:** 2026-05-15

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

### Phase 2: Strip and rebrand (Day 2, ~2 hours)

- [ ] Rename `ouroboros/` package → `heretek/`
- [ ] Update `pyproject.toml`, imports, references
- [ ] Remove modules: `tools/github.py`, `tools/review.py`, multi-model review code in `review.py`
- [ ] Neuter budget tracking — replace with token counter that just logs
- [ ] Write `CODEX_HERETICUS.md` (the persona constitution — see section 7)
- [ ] Write `SYSTEM.md` (the system prompt — pulls from CODEX, adds bilingual instruction)
- [ ] Write `identity.md` (initial empty identity, bot fills it over time)

### Phase 3: Self-modify guardrails (Day 3, ~2 hours)

- [ ] Patch `supervisor/git_ops.py`:
  - Branch protection: refuse all operations on `main`
  - All commits go to `playground`
  - Add `--dry-run` mode that posts diff to Telegram instead of committing
- [ ] Patch `tools/control.py` `/evolve` command to default to dry-run
- [ ] Add new Telegram command: `/sanction <commit-hash>` to approve a pending dry-run commit
- [ ] Add `/heresy` command: rollback to `last-known-good` tag

### Phase 4: Launch (Day 3, ~1 hour)

- [ ] Create Telegram bot via @BotFather, save token
- [ ] Create private group, add bot
- [ ] Hardcode your Telegram user ID in `SYSTEM.md` (find via @userinfobot)
- [ ] Set environment variables (see section 8)
- [ ] Run: `python -m supervisor`
- [ ] First test messages — verify persona, language switching, tools

### Phase 5: First evolution cycle (Day 4+)

- [ ] Send `/evolve` — bot should propose a self-modification
- [ ] Review the diff posted to Telegram
- [ ] If chaos-aligned: `/sanction <hash>`
- [ ] If heresy-against-the-bit: ignore, let it queue more proposals
- [ ] Observe what direction it drifts

---

## 6. Current state

**Status: Phase 1 complete — Foundation + Local LLM shipped.**

Last updated: 2026-05-15

What landed in Phase 1:
- Fork of `razzant/ouroboros@v6.2.0` overlaid in-place at the project root; `playground` branch live, `last-known-good` annotated tag at the upstream v6.2.0 commit
- Package renamed `ouroboros/` → `heretek/`; `python -m supervisor` is the local boot entry point
- Hard-deleted: `tools/github.py`, `tools/review.py`, `tools/browser.py`, `tools/health.py`, `tools/search.py`, package-root `review.py`
- Stripped: cloud LLM env-var loaders (OPENROUTER/OPENAI/ANTHROPIC), OpenRouter HTTP drift-check in the budget tracker, Playwright dep
- Wired: Ollama at `http://127.0.0.1:11434/v1` with `api_key="ollama"`; primary `qwen3.6:35b-a3b-q4_K_M` via `OLLAMA_MODEL`; light `qwen3:4b` via `OLLAMA_MODEL_LIGHT`; context cap `HERETEK_MAX_CONTEXT_TOKENS=32000`
- Robustness: `LLMClient` forces IPv4 (httpx does not fall back from IPv6 ::1 to 127.0.0.1 cleanly) and uses `trust_env=False` on its httpx client (bypasses macOS system-wide HTTP proxies that intercept localhost)
- Budget tracker public shape preserved; cost zeroed; per-call token log at `logs/tokens.jsonl` (JSONL with `{ts, model, prompt_tokens, completion_tokens, total}`)
- Smoke test `scripts/smoke_test.py` covers: package rename, no cloud hosts, models-pulled precondition, bilingual RU+EN Ollama reply (RU asserts Cyrillic in reply, EN asserts Latin)

What's next: Phase 2 (Persona + Identity) — author `CODEX_HERETICUS.md` and `SYSTEM.md`, prove the bot has a chaos-heretic voice and persistent identity across restarts.

When resuming:
1. Check this section first.
2. `git log --oneline -20` on `playground` for recent commits.
3. `ollama list` should show both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b`.
4. `python scripts/smoke_test.py --static-only` is the fast-feedback gate (2 PASS, ~3s, no Ollama dependency).
5. `python scripts/smoke_test.py` is the end-to-end gate. On a 32GB host the 24GB primary model can OOM Ollama — set `OLLAMA_MODEL=qwen3:4b` to use the light model for the wire check.
6. Tail `./logs/tokens.jsonl` for per-call token records.

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
TELEGRAM_BOT_TOKEN=<from @BotFather>
HERETEK_OWNER_USER_ID=<your TG user ID from @userinfobot>

# Local LLM
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M
OLLAMA_MODEL_LIGHT=qwen3:4b

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

# Stripped — not needed
# OPENROUTER_API_KEY
# OPENAI_API_KEY
# ANTHROPIC_API_KEY
# TOTAL_BUDGET
```

Store these in `.env` in repo root (gitignored). Use `python-dotenv` to load.

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
- If the owner returns to this and says "where were we" — point them at section 6 first.
