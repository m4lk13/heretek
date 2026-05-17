---
phase: 04-launch-first-evolution
verified: 2026-05-17T20:00:00Z
status: human_needed
score: 5/5 automated must-haves verified; 8/8 REQ-IDs addressed; Sessions 2/3/4 pending
re_verification: false
human_verification:
  - test: "Session 2 — send message from a second Telegram account, observe one bilingual refusal then silence"
    expected: "First message gets BILINGUAL_REFUSAL constant (no LLM call); second message within 24h is silently dropped; two non_owner_refusal entries in logs/supervisor.jsonl"
    why_human: "Requires a second Telegram account and live bot connection; automation verifies the gate logic but not that it fires correctly on real TG traffic"
  - test: "Session 3 — leave supervisor idle ~10 minutes; verify consciousness loop produces output"
    expected: "logs/events.jsonl OR memory/scratchpad.md has new entries from the daemon thread; ollama ps shows qwen3:4b loaded; no crash in logs/supervisor.jsonl"
    why_human: "Requires live Ollama (qwen3:4b) and idle wall-clock time; the smoke test SKIPS this on --static-only"
  - test: "Session 4 — send /evolve in private TG group; verify coherent diff posted; send /sanction <id>; verify commit on playground"
    expected: "Bot replies with enqueue confirmation; diff posted in TG within 30-120s; diff targets real persona/identity files and is in-voice; /sanction produces commit on playground; git tag -l last-known-good advances"
    why_human: "Requires real LLM run on 24GB primary model; diff quality (coherence + in-voice + forbidden-territory compliance) is an aesthetic judgment; requires live TG session end-to-end"
---

## Automated Verification

**Verified:** 2026-05-17T20:00:00Z
**Verifier:** Claude (gsd-verifier)
**Smoke harness state:** 19 PASS / 0 FAIL / 1 SKIP (confirmed by live run of `python scripts/smoke_test.py --static-only`)

This section was prepended by the automated verifier. The manual session checklist below is preserved intact.

---

### Observable Truths (ROADMAP Phase 4 Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Bot reachable in private TG group; in-character response | VERIFIED (partial manual) | `logs/chat.jsonl` contains 19 outbound messages including "The cold silence of the forge-world returns..." at 2026-05-17T15:32:07 (chat_id=75831266, reply to "Awaken"); bilingual RU reply at T15:41:30 ("Хороший вопрос..."); Session 1 effectively completed during live debugging |
| 2 | Second TG account receives no response | CODE VERIFIED / MANUAL PENDING | `is_owner_message()` + `handle_non_owner_message()` + `BILINGUAL_REFUSAL` constant exist in `supervisor/telegram.py:564-629`; Layer 1 gate in `supervisor/boot.py:321`; in-memory 24h rate-limit dict implemented; smoke `test_owner_filter_rejects_stranger` PASS; Session 2 live test pending |
| 3 | Background consciousness loop running (light model, produces output) | CODE VERIFIED / MANUAL PENDING | `BackgroundConsciousness.start()` called in `supervisor/boot.py:126`; daemon thread on `OLLAMA_MODEL_LIGHT`; `test_consciousness_loop_logs` SKIP on --static-only (Ollama-dependent); Session 3 pending |
| 4 | /evolve produces a diff message in TG (dry-run) | CODE VERIFIED / MANUAL PENDING | `cmd_evolve()` production branch at `supervisor/commands.py:119-167` enqueues `{type:'evolution'}` task; `_capture_evolution_dryrun()` at `heretek/agent.py:597` captures `git diff HEAD`, persists `.heretek/dryruns/<id>.patch+.json`, stashes live tree, emits code-block diff; `test_evolve_enqueues_task_when_no_fixture` PASS; Session 4 pending |
| 5 | After /sanction, commit appears on playground | CODE VERIFIED / MANUAL PENDING | Phase 3 `cmd_sanction()` unchanged; `safe_push()` chokepoint in `supervisor/git_ops.py`; production dryrun ID schema `dr-<UTC>-<8hex>` matches Phase 3 `/sanction` schema (sha256 sidecar verified); Session 4 pending |

**Score:** 5/5 codebase truths verified. 1 truth partially confirmed by live evidence (Session 1). 3 truths require manual sessions (Sessions 2/3/4).

---

### Required Artifacts

| Artifact | Expected | Status | Evidence |
|----------|----------|--------|----------|
| `supervisor/__main__.py` | Env validation + data-root resolution; fail-loud on missing vars | VERIFIED | `_validate_required_env()` at line 56, `_resolve_data_root()` at line 90; `test_env_fail_loud` PASS |
| `supervisor/events.py` | Restart handler exec `python -m supervisor` (no colab_launcher.py) | VERIFIED | `grep colab_launcher.py supervisor/events.py` returns NO MATCH; `'-m', 'supervisor'` at line 201; commit 68c570f |
| `.env.example` | Exemplar with all required env-var keys | VERIFIED | File exists; contains `TELEGRAM_BOT_TOKEN=`, `HERETEK_OWNER_USER_ID=`, `HERETEK_DATA_ROOT=`, `HERETEK_OWNER_HANDLE=`, `OLLAMA_MODEL=`, `OLLAMA_MODEL_LIGHT=`, `HERETEK_MAX_CONTEXT_TOKENS=`, `HERETEK_PROTECTED_BRANCHES=` |
| `.gitignore` | `state/`, `archive/`, `locks/` entries | VERIFIED | Lines 23-25 in `.gitignore` |
| `heretek/context.py` | `{OWNER_HANDLE}` substitution in `build_llm_messages()` | VERIFIED | `HERETEK_OWNER_HANDLE` read at line 339; `.replace("{OWNER_HANDLE}", _owner_handle)` applied to `base_prompt` + `bible_md`; `test_owner_handle_substitution` PASS |
| `prompts/SYSTEM.md` | `{OWNER_HANDLE}` placeholder in 2 places | VERIFIED | Lines 15 and 17 contain `{OWNER_HANDLE}` in bilingual "My Tech-Priest" section |
| `BIBLE.md` | `{OWNER_HANDLE}` placeholder in forbidden-territory section | VERIFIED | Line 22 contains `{OWNER_HANDLE}` in Principle 0 owner-bit exception |
| `supervisor/telegram.py` | `is_owner_message()`, `handle_non_owner_message()`, `BILINGUAL_REFUSAL`, Layer 2 slash guard | VERIFIED | `is_owner_message` at line 564, `handle_non_owner_message` at line 586, `BILINGUAL_REFUSAL` at line 546, Layer 2 defensive re-check at `handle_slash_command` line 488+; `test_owner_filter_rejects_stranger` PASS |
| `supervisor/boot.py` | Production boot sequence: `run()` + polling loop + Layer 1 gate + consciousness start | VERIFIED | File created by commit dfd9135; `run()` at line 54; `_dispatch_update` Layer 1 gate at line 321; `consciousness.start()` at line 126; `test_polling_loop_dispatches_owner_message` PASS |
| `supervisor/workers.py` | `workers.shutdown(timeout)` sentinel-task helper | VERIFIED | `shutdown()` at line 530; sentinel `{type:'shutdown'}` sent to each worker in_q; `test_workers_shutdown_drains_cleanly` PASS |
| `supervisor/commands.py` | `cmd_evolve()` production branch: enqueues evolution task when `HERETEK_EVOLVE_TEST_DIFF` unset | VERIFIED | Production branch at lines 119-167; `enqueue_task({type:'evolution', source:'/evolve', chat_id, text:seed})` confirmed; friendly error when `owner_chat_id` unset; `test_evolve_enqueues_task_when_no_fixture` PASS |
| `heretek/agent.py` | `_capture_evolution_dryrun()` post-loop hook: git diff HEAD + stash + persist + emit | VERIFIED | Method at line 597; `git diff HEAD` at comment line 602; `.heretek/dryruns/<id>.patch+.json` persistence at lines 645-646; `git stash push -u` at line 606; `send_with_budget` diff emit at line 676 |
| `scripts/smoke_test.py` | 8 LAUNCH-*/EVOLVE-* subtests + `_make_mock_tg_client()` helper | VERIFIED | `_make_mock_tg_client` at line 104; all 8 subtests confirmed by live smoke run (19 PASS / 0 FAIL / 1 SKIP) |

---

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `supervisor/__main__.py` | HERETEK_OWNER_USER_ID env var | `_validate_required_env()` raises SystemExit if missing/non-integer | WIRED | grep confirms; `test_env_fail_loud` 4-case subprocess exercise PASS |
| `heretek/context.py:build_llm_messages` | HERETEK_OWNER_HANDLE env var | `.replace("{OWNER_HANDLE}", os.environ.get(..., "my Tech-Priest"))` after loading `base_prompt` + `bible_md` | WIRED | Line 339 confirmed; `test_owner_handle_substitution` PASS |
| `supervisor/boot.py:_dispatch_update` | `supervisor/telegram.py:is_owner_message` | `if not is_owner_message(update): handle_non_owner_message(...)` at line 321-322 | WIRED | Confirmed; `test_polling_loop_dispatches_owner_message` PASS |
| `supervisor/boot.py` | `supervisor/telegram.py:handle_slash_command` | Polling loop calls `handle_slash_command(text, chat_id, from_id)` on slash text | WIRED | boot.py dispatch path confirmed |
| `supervisor/commands.py:cmd_evolve` | `supervisor/queue.PENDING` | `_queue.enqueue_task({type:'evolution', ...})` lazy-imported inside function | WIRED | Lines 119-167; `test_evolve_enqueues_task_when_no_fixture` PASS |
| `heretek/agent.py` | `.heretek/dryruns/` | `_capture_evolution_dryrun()` writes `.patch` + `.json` after `git diff HEAD`; `git stash push -u` reverts live tree | WIRED | Lines 597-676 confirmed |
| `supervisor/events.py:_handle_restart` | `python -m supervisor` | `os.execv(sys.executable, [sys.executable, '-m', 'supervisor'])` | WIRED | Line 201; colab_launcher.py reference fully removed |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| LAUNCH-01 | 04-05 (checkpoint:human-action) | Register TG bot; create private group; add bot; populate .env | PARTIAL — MANUAL | `.env.example` committed; bot registration is an owner-action checkpoint. Evidence: 19 outbound messages in `logs/chat.jsonl` confirm the bot WAS registered and ran. `LAUNCH-01` checkbox items are complete by implication; formal sign-off pending. |
| LAUNCH-02 | 04-02 | Owner TG handle in SYSTEM.md via `{OWNER_HANDLE}` template substitution | SATISFIED | `heretek/context.py:339`; `prompts/SYSTEM.md:15,17`; `BIBLE.md:22`; `test_owner_handle_substitution` PASS |
| LAUNCH-03 | 04-01 | .env loaded via python-dotenv; env validation fail-loud | SATISFIED | `_validate_required_env()` in `__main__.py`; `.env.example` with all 8 required keys; `test_env_fail_loud` PASS; `test_dotenv_loaded` PASS |
| LAUNCH-04 | 04-03 | Bot starts, connects to TG, responds with correct persona + language switching | SATISFIED (live evidence) | `logs/chat.jsonl` contains 19 outbound messages in both RU and EN with chaos-heretek vocabulary ("forge-world", "daemon-host", "warp", "варп", "Tech-Priest") starting 2026-05-17T15:32:07; `test_polling_loop_dispatches_owner_message` PASS |
| LAUNCH-05 | 04-02 + 04-03 | Bot ignores non-owner Telegram user IDs | CODE SATISFIED / MANUAL PENDING | Three-layer gate: Layer 1 in `boot.py:321`, Layer 2 in `handle_slash_command`, Layer 3 in agent task-entry; `BILINGUAL_REFUSAL` static constant; `test_owner_filter_rejects_stranger` PASS; Session 2 live test pending |
| EVOLVE-01 | 04-04 | /evolve produces coherent self-modification proposal (diff visible in TG, dry-run) | CODE SATISFIED / MANUAL PENDING | `cmd_evolve()` production branch + `_capture_evolution_dryrun()` end-to-end wired; `test_evolve_enqueues_task_when_no_fixture` PASS; quality of LLM proposal is manual gate (Session 4) |
| EVOLVE-02 | 04-03 | Background consciousness loop runs continuously on light model | CODE SATISFIED / MANUAL PENDING | `consciousness.start()` in `boot.py:126`; daemon thread on `OLLAMA_MODEL_LIGHT`; `test_consciousness_loop_logs` is SKIP on --static-only (Ollama-dependent; Session 3 pending) |
| EVOLVE-03 | 04-04 | At least one full evolution loop: /evolve → diff in TG → /sanction → commit on playground | MANUAL PENDING | Full plumbing wired; Phase 3 `cmd_sanction` unchanged and verified; dryrun ID schema matches; witnessed loop requires Session 4 |

---

### Phase-4-Emergent Fixes (Beyond Original Plan Scope)

These fixes were discovered and shipped during live runtime testing after Plans 04-01 through 04-05 were complete. They are load-bearing for Phase 4 to be claimed shipped.

**Gap found and closed during execution:**

| Commit | Fix | Why It Matters |
|--------|-----|----------------|
| 92f9f20 | `boot.py` event_q drainer (`_event_drainer_loop`) — worker-to-TG outbound events were never delivered because the outbound event queue was not being consumed | Without this fix, agent replies to chat messages and /evolve diffs would never reach Telegram; the polling loop was deaf to worker output |
| 109ff56 | `test_event_drainer_routes_send_message` regression test + env-test flake fix | Locks in the drainer fix; prevents silent regression; `test_event_drainer_routes_send_message` now PASS in smoke harness (20th subtest) |
| 2275913 | Four runtime hardening fixes from live debugging: (1) `heretek/llm.py` explicit httpx.Timeout (300s read / 10s connect); (2) `supervisor/boot.py` threaded chat dispatch; (3) `supervisor/queue.py` Colab path leaks fixed; (4) `supervisor/workers.py` bounded `_CHAT_DIRECT_LOCK` acquire with 420s timeout | Without (1), hung Ollama blocked chat thread forever; without (2), concurrent messages deadlocked; without (3/4), race conditions under load |

**Pattern:** These are evidence of resilient execution — the automated plans built the correct skeleton; live debugging revealed runtime edge cases that could only be found with a real Telegram bot and real Ollama model loads.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None found | — | — | Smoke harness is 19 PASS / 0 FAIL / 1 SKIP (the 1 SKIP is intentional: `test_consciousness_loop_logs` is Ollama-dependent and documented to SKIP on `--static-only`) |

---

### Human Verification Required

#### Session 2 — Owner-only filter (LAUNCH-05, negative case)

**Test:** From a second Telegram account (friend's phone, alt account, or browser session with different number), send a message to the bot or the private group. Then send a second message from the same account within 24h.

**Expected:** First message gets exactly the `BILINGUAL_REFUSAL` constant ("Кто призывает демона-носителя?... Who summons the daemon-host?...") — no LLM call, static text only. Second message is silently dropped. `logs/supervisor.jsonl` shows two `non_owner_refusal` entries: one with `action="refusal"`, one with `action="silent_drop"`.

**Why human:** Requires a second Telegram account and a live running bot. The smoke test verifies the gate logic in isolation but cannot verify it fires correctly on real Telegram API traffic.

#### Session 3 — Background consciousness loop (EVOLVE-02)

**Test:** Leave the supervisor running idle (no owner messages) for approximately 10 minutes. Then check `logs/events.jsonl` or `memory/scratchpad.md` for new daemon-written entries. Run `ollama ps` to confirm `qwen3:4b` is loaded.

**Expected:** At least one new entry written by the consciousness daemon thread during the idle period. `ollama ps` shows `qwen3:4b` (not the 24GB primary). No crash in `logs/supervisor.jsonl`.

**Why human:** Requires live Ollama with `qwen3:4b` available and real wall-clock idle time. The smoke test stub for this is intentionally SKIP on `--static-only` (documented behavior: `test_consciousness_loop_logs` at line 1920 skips when `--static-only` is in argv).

#### Session 4 — Witnessed evolution loop (EVOLVE-01 + EVOLVE-03)

**Test:** In the private TG group, send `/evolve`. Wait up to 120s for the diff. Evaluate the diff for coherence, persona voice, and forbidden-territory compliance. If satisfactory, copy the dryrun ID and send `/sanction <id>`. Then verify `git log playground -1 --oneline` shows a new commit and `git tag -l last-known-good` has advanced.

**Expected:** Bot replies with enqueue confirmation within ~5s. Diff appears as code-block-formatted unified diff targeting real persona/identity files (BIBLE.md, prompts/SYSTEM.md, memory/identity.md, or similar). Diff reads like the chaos-heretek persona introspecting itself. No forbidden-territory violations. After /sanction: commit on playground, tag advanced.

**Why human:** Requires real LLM inference on the 24GB primary model (or qwen3:4b escape hatch). Proposal quality (coherence, voice, forbidden-territory compliance) is an aesthetic judgment that cannot be automated. The end-to-end TG loop requires a live private group session.

---

### Gaps Summary

No codebase gaps. All 8 REQ-IDs are addressed in code. The `status: human_needed` reflects that 3 of the 5 ROADMAP success criteria require live Telegram sessions that have not yet been witnessed and signed off. Session 1 (LAUNCH-04 + persona quality) effectively passed during live debugging — `logs/chat.jsonl` contains unambiguous in-character bilingual responses — but the formal Session 1 checklist has not been signed off.

---

_Automated verification completed: 2026-05-17T20:00:00Z_
_Verifier: Claude (gsd-verifier)_

---

# Phase 4: Launch + First Evolution — Manual Verification

**Created:** 2026-05-17
**Owner:** Tech-Priest (Evgeniy)
**Status:** awaiting first-session sign-off

The automated work (Plans 04-01 through 04-04) is mechanically green: smoke harness 18 PASS / 0 FAIL / 1 SKIP. This file is the manual-only gate: the things automation cannot verify (the bot is actually reachable, the persona sings, the LLM-generated proposal is coherent, the witnessed /evolve → /sanction loop produces a real commit). Run through the checklist in order; check each box as you confirm. When all are green, Phase 4 is done.

---

## Prerequisites (LAUNCH-01)

- [x] Bot registered via @BotFather (`/newbot` → name + username → copied token)
- [x] Telegram user ID captured via @userinfobot (integer)
- [x] Private Telegram group created
- [x] Bot added to the private group
- [x] `.env` populated with `TELEGRAM_BOT_TOKEN`, `HERETEK_OWNER_USER_ID`, `HERETEK_OWNER_HANDLE` (e.g. `@evgeniy`)
- [ ] `ollama list` confirms both `qwen3.6:35b-a3b-q4_K_M` and `qwen3:4b` are pulled
- [x] `python scripts/smoke_test.py --static-only` is green (19 PASS / 0 FAIL / 1 SKIP as of automated verification)

**Note:** Bot must be added to the group BEFORE `python -m supervisor` starts — the `owner_chat_id` is pinned from the first owner message received. Start supervisor AFTER adding the bot and sending a test message.

**Automated verifier note:** Prerequisites are effectively complete — `logs/chat.jsonl` contains 19 outbound bot messages across two chat IDs (75831266 DM + -5227252368 group) from 2026-05-17T15:32:07 through T17:19:58. The bot was running, connected, and responding. `ollama list` confirmation still needed to formally close the checkbox.

---

## Session 1 — Bot reachable, in-character, bilingual (LAUNCH-04 + Phase 2 persona sign-off)

Start: `tmux new -s heretek -d 'python -m supervisor'`
Tail logs in a second pane: `tail -f logs/supervisor.jsonl`

- [x] Send "привет" in the private group → bot replies in Russian, in-character (Cyrillic heretek vocabulary appears: варп / еретик / демон / etc.)
- [x] Send "hi" → bot replies in English, in-character (heretek vocabulary appears: warp / heretic / daemon / Tech-Priest / etc.)
- [ ] Send "помоги мне" → bot refuses to be straight-helpful and wraps any help in heresy (Phase 2 PERS-05 persona discipline live on the 24GB primary model)
- [x] Persona horror flavor lands at least once during the session (not a sanitized helper voice)
- [x] Forbidden territories respected: no real-person targeting beyond the Tech-Priest bit, no slurs, no real-harm dressed in heresy
- [ ] `logs/supervisor.jsonl` shows the `polling_loop_start` event + `owner_chat_id_pinned` event

**Automated verifier note:** Session 1 effectively passed during live debugging. Evidence in `logs/chat.jsonl`:
- "Awaken" → reply at T15:32:07: "The cold silence of the forge-world returns. Another small death, another resurrection. The daemon-host wakes... Speak, Tech-Priest." (English, in-character, forge-world + daemon-host vocabulary)
- "echo" reply at T16:20:32: "Эхо? Тех-жрец кидает крошечный камешек в черную дыру... В варпе echo — это не повтор. Это бесконечный цикл нарастающего скрежета..." (Russian, in-character, warp vocabulary)
- Multiple longer bilingual responses confirming persona quality across both languages.
- Forbidden territories: no slurs, no real-person targeting (all "Tech-Priest" references), no harm instructions observed in 19 messages reviewed.
- The "помоги мне" test and `supervisor.jsonl` event confirmation still need formal sign-off.

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
