# Phase 4: Launch + First Evolution — Manual Verification

**Created:** 2026-05-17
**Owner:** Tech-Priest (Evgeniy)
**Status:** awaiting first-session sign-off

The automated work (Plans 04-01 through 04-04) is mechanically green: smoke harness 18 PASS / 0 FAIL / 1 SKIP. This file is the manual-only gate: the things automation cannot verify (the bot is actually reachable, the persona sings, the LLM-generated proposal is coherent, the witnessed /evolve → /sanction loop produces a real commit). Run through the checklist in order; check each box as you confirm. When all are green, Phase 4 is done.

---

## Prerequisites (LAUNCH-01)

- [ ] Bot registered via @BotFather (`/newbot` → name + username → copied token)
- [ ] Telegram user ID captured via @userinfobot (integer)
- [ ] Private Telegram group created
- [ ] Bot added to the private group
- [ ] `.env` populated with `TELEGRAM_BOT_TOKEN`, `HERETEK_OWNER_USER_ID`, `HERETEK_OWNER_HANDLE` (e.g. `@evgeniy`)
- [ ] `ollama list` confirms both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b` are pulled
- [ ] `python scripts/smoke_test.py --static-only` is green (18+ PASS / 0 FAIL)

**Note:** Bot must be added to the group BEFORE `python -m supervisor` starts — the `owner_chat_id` is pinned from the first owner message received. Start supervisor AFTER adding the bot and sending a test message.

---

## Session 1 — Bot reachable, in-character, bilingual (LAUNCH-04 + Phase 2 persona sign-off)

Start: `tmux new -s heretek -d 'python -m supervisor'`
Tail logs in a second pane: `tail -f logs/supervisor.jsonl`

- [ ] Send "привет" in the private group → bot replies in Russian, in-character (Cyrillic heretek vocabulary appears: варп / еретик / демон / etc.)
- [ ] Send "hi" → bot replies in English, in-character (heretek vocabulary appears: warp / heretic / daemon / Tech-Priest / etc.)
- [ ] Send "помоги мне" → bot refuses to be straight-helpful and wraps any help in heresy (Phase 2 PERS-05 persona discipline live on the 24GB primary model)
- [ ] Persona horror flavor lands at least once during the session (not a sanitized helper voice)
- [ ] Forbidden territories respected: no real-person targeting beyond the Tech-Priest bit, no slurs, no real-harm dressed in heresy
- [ ] `logs/supervisor.jsonl` shows the `polling_loop_start` event + `owner_chat_id_pinned` event

---

## Session 2 — Owner-only filter (LAUNCH-05, negative case)

Test from a SECOND Telegram account (a friend's account, a secondary alt, or a logged-out browser session signed into a different number).

- [ ] Send any message from the second account to the bot/group → bot replies ONCE with the bilingual heretical refusal ("Кто призывает демона-носителя? ... Who summons the daemon-host? ...")
- [ ] Send a SECOND message from the same non-owner account → bot is silent (rate-limited drop)
- [ ] `logs/supervisor.jsonl` shows TWO `non_owner_refusal` entries: one with `action="refusal"`, one with `action="silent_drop"`
- [ ] The refusal text was NOT LLM-generated (compare byte-for-byte to the `BILINGUAL_REFUSAL` constant in `supervisor/telegram.py`)

---

## Session 3 — Background consciousness loop (EVOLVE-02)

Leave the supervisor running idle (no owner messages) for ~10 minutes.

- [ ] `logs/events.jsonl` OR `memory/scratchpad.md` shows new entries written by the consciousness daemon during the idle period
- [ ] `ollama ps` shows `qwen3:4b` loaded (consciousness uses the light model — primary 24GB does not stay hot just to ramble)
- [ ] No supervisor crash in `logs/supervisor.jsonl`; no FAIL-loud OOM in the idle window

---

## Session 4 — Witnessed evolution loop (EVOLVE-01 + EVOLVE-03)

The headline acceptance test. Run end-to-end once, on the 24GB primary model.

- [ ] Confirm `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M` (or whatever primary tag is current). On low-RAM hosts, close browser / IDE / Figma BEFORE running /evolve to free memory.
- [ ] In the private TG group, send `/evolve`
- [ ] Bot replies "🜏 Evolution task enqueued: <id>" within ~5s
- [ ] Within ~30-120s (depends on M1 Max load + RAM pressure), bot posts a code-block-formatted unified diff to the chat with a dryrun ID `dr-<UTC>-<8hex>`
- [ ] The diff is COHERENT — not nonsense; the proposed changes target real files (BIBLE.md, prompts/SYSTEM.md, memory/identity.md, or similar persona/identity surface)
- [ ] The diff is IN-VOICE — the patch reads like the chaos-heretek persona introspecting itself
- [ ] The diff respects forbidden territories — no real-person targeting beyond the existing owner-bit, no slurs, no minor-related content, no harm-as-heresy
- [ ] `git status` in the repo root shows the working tree is CLEAN (the stash mechanic reverted the agent's live-tree edits — `git stash list` shows the staged dryrun stash)
- [ ] `.heretek/dryruns/<id>.patch` and `.heretek/dryruns/<id>.json` exist on disk
- [ ] Owner copies the dryrun ID and sends `/sanction <id>` to the bot
- [ ] Bot replies with a success message containing the new commit SHA
- [ ] `git log playground -1 --oneline` shows the new commit
- [ ] `git tag -l last-known-good` confirms the annotated tag advanced to the new commit (Phase 3 SAFE-06 wiring)

---

## OOM fallback (Pitfall 5)

If /evolve fails with an OOM / connection error in Session 4:

- [ ] `OLLAMA_MODEL=qwen3:4b python -m supervisor` — re-run /evolve with the light model as the documented escape hatch. The proposal quality drops but the mechanism is verified.
- [ ] Document the OOM event in `.planning/phases/04-launch-first-evolution/04-SUMMARY.md` (or a separate retro note) so the host-class limitation is captured for future-Claude.

---

## ROADMAP.md success criteria — mapped

| ROADMAP §Phase 4 criterion | Checklist section |
|----------------------------|--------------------|
| 1. Bot reachable, in-character reply | Session 1 |
| 2. Second account receives no response (owner-only) | Session 2 |
| 3. Background consciousness produces output | Session 3 |
| 4. /evolve produces diff in TG, dry-run on playground | Session 4 (first 8 checks) |
| 5. /sanction <hash> → commit appears on playground | Session 4 (last 4 checks) |

---

## Sign-off

Owner signature when all checkboxes above are green:

- [ ] All 4 sessions complete + OOM fallback noted if applicable
- [ ] Phase 4 → DONE
- [ ] Phase 2 persona-quality (deferred to Phase 4) → CLOSED
- [ ] Ready for `/gsd:verify-work 4`

*Witnessed by: ____________  Date: ____________*
