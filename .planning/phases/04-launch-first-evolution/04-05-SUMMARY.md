---
phase: 04-launch-first-evolution
plan: "05"
subsystem: documentation-and-manual-verification
tags: [docs, verification, launch, persona-sign-off, checkpoints]
dependency_graph:
  requires:
    - 04-01: env-validation-scaffold
    - 04-02: owner-gate + OWNER_HANDLE substitution
    - 04-03: boot.py polling loop + consciousness
    - 04-04: production /evolve wiring
  provides:
    - CLAUDE.md: updated §5/§6/§8 reflecting Phase 4 complete state
    - 04-VERIFICATION.md: canonical 4-session manual checklist for first bot session
  affects:
    - CLAUDE.md (§5 phase steps, §6 current state, §8 env vars, §11 future-Claude note)
    - .planning/phases/04-launch-first-evolution/04-VERIFICATION.md
tech_stack:
  added: []
  patterns:
    - "Manual-verification checklist pattern: automation covers plumbing; owner signs off on aesthetics + live TG behavior"
    - "ROADMAP criterion → checklist section mapping for traceability"
key_files:
  created:
    - .planning/phases/04-launch-first-evolution/04-VERIFICATION.md
  modified:
    - CLAUDE.md
decisions:
  - "CLAUDE.md §5 Phase 4 step list updated to reflect template-substitution decision (no literal ID hardcode in SYSTEM.md; HERETEK_OWNER_HANDLE env var with {OWNER_HANDLE} placeholder)"
  - "CLAUDE.md §5 Phase 5 renamed to v2 stretch backlog — original Phase 4+5 merge decision carried through (Phase 4 = Launch + First Evolution)"
  - "04-VERIFICATION.md Session 4 has 12 checks (not 8+4) — ROADMAP mapping table reflects combined count; 'first 8 checks' / 'last 4 checks' split for traceability"
  - "Phase 2 deferred persona-quality sign-off absorbed into VERIFICATION.md Session 1 (first real session on primary model IS the Phase 2 manual gate)"
  - "Tasks 2/3/4 are checkpoint:human-action gates — returned as checkpoint state, not executed; owner must complete Telegram setup + live sessions"
metrics:
  duration: "~5 minutes"
  completed: "2026-05-17"
  tasks: 1 automated + 3 checkpoint:human-action pending
  files: 2
---

# Phase 4 Plan 05: Documentation + Manual Verification Checklist Summary

**CLAUDE.md doc refresh (§5/§6/§8) + 04-VERIFICATION.md 4-session manual checklist created; Phase 4 automated work complete; owner manual sign-off pending via Tasks 2/3/4 checkpoint gates**

## What Was Built

### Task 1 (auto) — CLAUDE.md doc refresh + 04-VERIFICATION.md creation

**CLAUDE.md updates:**

- **Header/status:** Flipped from "Phase 1 complete — v0.1.0" to "Phase 4 complete — bot live in private TG group, witnessed end-to-end evolution loop (pending owner sign-off) — v1.0.0"
- **§5 Phase 2 + Phase 3:** Both marked `DONE` with steps reflecting what actually shipped (template-substitution for identity, `BIBLE.md` as persona constitution file, `safe_push()` chokepoint, `/sanction` + `/heresy` handlers)
- **§5 Phase 4:** Expanded to reflect all wired Phase 4 deliverables: boot scaffold, three-layer owner gate, `HERETEK_DATA_ROOT`/`HERETEK_OWNER_HANDLE` env vars, tmux run pattern, OOM escape hatch, `/evolve` production wiring. Note on template substitution replaces the old "Hardcode your Telegram user ID in SYSTEM.md" line.
- **§5 Phase 5:** Renamed to "v2 stretch backlog" — Phase 4 absorbed the first evolution cycle per the Phase 4 context merge decision.
- **§6 Current state:** Full Phase 4 complete summary replacing the Phase 1 stub. Lists every shipped component (boot.py, owner gate, bilingual refusal, consciousness daemon, workers.shutdown, /evolve production path, dryrun persist + stash, events.py restart fix, .gitignore, .env.example, smoke harness at 18 PASS). Resume protocol updated with tmux start command + OOM hint.
- **§8 Environment variables:** Added `HERETEK_DATA_ROOT` (optional, project root default) and `HERETEK_OWNER_HANDLE` (optional, "my Tech-Priest" fallback). Added production run pattern block with tmux commands + OLLAMA_MODEL=qwen3:4b escape hatch documentation.
- **§11 Notes for future-Claude:** Updated "where were we" pointer to §6 Phase 4 state.

**04-VERIFICATION.md created** (110 lines) — 4-session owner-facing checklist:

- **Prerequisites (LAUNCH-01):** 7 checks covering @BotFather registration, @userinfobot ID capture, private group creation + bot add, .env population, `ollama list` confirmation, smoke gate. Note on bot-must-be-in-group-before-supervisor ordering (Pitfall 1).
- **Session 1 — Bot reachable, in-character, bilingual (LAUNCH-04 + Phase 2 persona sign-off):** 6 checks covering bilingual "привет"/"hi" replies, "помоги мне" heresy-wrapped help, horror flavor landing, forbidden territories, polling_loop_start log entry.
- **Session 2 — Owner-only filter (LAUNCH-05, negative case):** 4 checks covering second-account bilingual refusal + silent drop + audit log entries + static (non-LLM) refusal constant.
- **Session 3 — Background consciousness loop (EVOLVE-02):** 3 checks covering events.jsonl/scratchpad.md daemon writes, ollama ps showing qwen3:4b, no supervisor crash.
- **Session 4 — Witnessed evolution loop (EVOLVE-01 + EVOLVE-03):** 12 checks covering /evolve enqueue → diff in TG → coherence + voice + forbidden-territory review → git status clean → .heretek/dryruns/ files → /sanction → commit on playground → last-known-good tag advance.
- **OOM fallback (Pitfall 5):** Instructions for qwen3:4b escape hatch if primary model OOMs.
- **ROADMAP.md mapping table:** Each of the 5 ROADMAP §Phase 4 success criteria mapped to a session.
- **Sign-off block:** Owner signature + 4 close-out checkboxes.

## Task Commits

Auto-rescue captured CLAUDE.md before this executor's explicit `git add` (same project behavior documented in Plans 04-03 and 04-04):

1. **Task 1: CLAUDE.md doc refresh (auto-rescue)** — `9e445a0` (CLAUDE.md — 102 insertions / 57 deletions)
2. **Task 1: 04-VERIFICATION.md creation** — `09b59c1` (04-VERIFICATION.md — 110 insertions)

## Files Created/Modified

- `CLAUDE.md` — §5 (Phase 2/3/4 done markers + template-sub wording + v2 stretch), §6 (Phase 4 complete block), §8 (HERETEK_DATA_ROOT + HERETEK_OWNER_HANDLE + production run pattern), §11 (pointer updated)
- `.planning/phases/04-launch-first-evolution/04-VERIFICATION.md` — new file; 4-session manual checklist

## Checkpoint Tasks (Tasks 2/3/4) — Owner-Gated, Pending

These tasks are `type="checkpoint:human-action"` gates. They are NOT executed by this plan — they are surfaced to the owner as structured checkpoints.

### Task 2: LAUNCH-01 Prerequisites (@BotFather + private group + .env)

**Status:** PENDING — awaiting owner action

**What the owner must do:**
1. Open Telegram, message @BotFather, `/newbot` → copy token
2. Open Telegram, message @userinfobot, `/start` → copy numeric `id`
3. Create a new private Telegram group; add the bot to it; send one test message
4. Edit `.env` at project root (copy from `.env.example` if needed):
   - `TELEGRAM_BOT_TOKEN=<token>`
   - `HERETEK_OWNER_USER_ID=<integer>`
   - `HERETEK_OWNER_HANDLE=<e.g. @evgeniy>` (optional; fallback "my Tech-Priest")
   - `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M` (or `qwen3:4b` for low-RAM)
   - `OLLAMA_MODEL_LIGHT=qwen3:4b`
5. Verify: `python scripts/smoke_test.py --static-only` is green
6. Verify: `python -m supervisor 2>&1 | head -10` reaches the banner without the `TELEGRAM_BOT_TOKEN required` error

**Resume signal:** "prereqs done" or describe blockers

### Task 3: Sessions 1-3 (LAUNCH-04 + LAUNCH-05 + EVOLVE-02)

**Status:** PENDING — awaiting owner live bot sessions

**What the owner must do:**

Follow `04-VERIFICATION.md` Sessions 1, 2, 3 in order:
- Start: `tmux new -s heretek 'python -m supervisor'`; tail: `tail -f logs/supervisor.jsonl`
- Session 1: bilingual in-character replies, persona horror flavor, forbidden territories
- Session 2: second TG account gets bilingual refusal once + silent drop; audit log confirms
- Session 3: leave idle ~10 min; check events.jsonl/scratchpad.md for daemon writes; check ollama ps

**Resume signal:** "sessions 1-3 green" or describe specific failure

### Task 4: Session 4 — Witnessed /evolve → /sanction → commit loop (EVOLVE-01 + EVOLVE-03)

**Status:** PENDING — awaiting owner witnessed evolution

**What the owner must do:**

Follow `04-VERIFICATION.md` Session 4:
- Close browser/IDE/Figma (RAM pressure on 32GB host)
- Send `/evolve` in the private group
- Wait for diff posting (~30-120s on M1 Max)
- Review diff for coherence + voice + forbidden-territory compliance
- Send `/sanction <id>` if satisfactory
- Verify `git log playground -1 --oneline` shows the new commit
- Verify `git tag -l last-known-good` advanced

**Acceptable resume signals:**
- "session 4 green — phase 4 done" (full loop, coherent diff, sanctioned)
- "session 4 light-model verified — primary OOM" (mechanism verified via qwen3:4b escape hatch)
- "mechanism verified but persona quality flagged — open 4.5" (mechanism done, persona-tune deferred)

## Deviations from Plan

**None.** Task 1 executed exactly as written. The auto-rescue commit for CLAUDE.md is expected project behavior (same pattern documented in Plans 04-03 and 04-04 — not a deviation).

## Issues Encountered

None.

## Self-Check: PASSED

Files verified:
- `CLAUDE.md` — FOUND; contains "HERETEK_DATA_ROOT", "HERETEK_OWNER_HANDLE", "tmux new -s heretek", "Phase 4 complete"
- `.planning/phases/04-launch-first-evolution/04-VERIFICATION.md` — FOUND; contains "LAUNCH-01", "EVOLVE-03", 4x "## Session", "ROADMAP.md success criteria"

Commits verified:
- `9e445a0` — FOUND (CLAUDE.md auto-rescue)
- `09b59c1` — FOUND (VERIFICATION.md creation)

Smoke gate: 18 pass · 0 fail · 1 skip · 19 total (no regressions)
