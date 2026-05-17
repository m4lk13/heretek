---
phase: 4
slug: launch-first-evolution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-17
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `scripts/smoke_test.py` (runnable Python script, not pytest — established Phase 1+2+3 pattern) |
| **Config file** | none — Wave 0 adds new SKIP-stub subtests |
| **Quick run command** | `python scripts/smoke_test.py --static-only` |
| **Full suite command** | `python scripts/smoke_test.py` |
| **Estimated runtime** | ~3s static-only; ~30-120s full (Ollama-dependent; OLLAMA_MODEL=qwen3:4b escape hatch) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/smoke_test.py --static-only`
- **After every plan wave:** Run `python scripts/smoke_test.py` (full)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds (static-only target)

---

## Per-Task Verification Map

*Filled in by the planner; one row per task with REQ-ID + automated command.*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-XX-YY | XX | N | REQ-XX | unit | `{command}` | ✅ / ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/smoke_test.py` — add SKIP-stubs for LAUNCH-01..05 + EVOLVE-01..03 (8 new subtests)
- [ ] `scripts/smoke_test.py` — helper: `_make_mock_tg_client()` (records sent messages, simulates get_updates returning seeded updates)
- [ ] `.env.example` — exemplar with required vars (TELEGRAM_BOT_TOKEN, HERETEK_OWNER_USER_ID, HERETEK_OWNER_HANDLE, etc.) so smoke tests can verify boot-time env validation without requiring a real .env

*Wave 0 scaffold ships the subtests as SKIP-stubs; subsequent plans flip each to a real assertion as the feature lands (continues Phase 1/2/3 SKIP-then-flip pattern).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bot reachable in private TG group; in-character response | LAUNCH-04 | Requires real TG bot token + private group + owner's TG account | Create private group, add bot, send "привет" — verify bilingual heretek-voice reply lands |
| Real /evolve produces coherent diff | EVOLVE-01 | Requires primary 24GB Ollama model + agent loop; quality is aesthetic | Send `/evolve` in private group; verify diff posted within ~60s; verify proposal is coherent and in-voice (not nonsense) |
| Background consciousness produces unprompted output | EVOLVE-02 | Requires live Ollama + idle period | Boot supervisor; leave idle ~10 min; tail `logs/state.jsonl` for `consciousness_thought` events |
| Full /evolve → /sanction → commit loop | EVOLVE-03 | Requires real LLM run AND human in-the-loop approval | Run /evolve, get hash, `/sanction <hash>`, verify `git log playground -1` shows the commit + `git tag -l last-known-good` advances |
| Persona quality on 24GB primary model (Phase 2 deferred sign-off) | (Phase 2 acceptance) | Quality is aesthetic; light-model smoke verifies plumbing only | Owner runs one full session in TG: verify horror flavor lands, bilingual reflex works in practice, forbidden territories respected |
| Owner-only filter (negative case) | LAUNCH-05 | Requires a second TG account | From a non-owner account, message the bot — verify in-character heretical refusal (or silent drop after rate-limit) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s (static-only)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
