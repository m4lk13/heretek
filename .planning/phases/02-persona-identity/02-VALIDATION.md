---
phase: 02
slug: persona-identity
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-16
last_updated: 2026-05-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | runnable Python script (scripts/smoke_test.py) — same pattern as Phase 1 |
| **Config file** | none — script is self-contained |
| **Quick run command** | `python scripts/smoke_test.py --static-only` |
| **Full suite command** | `OLLAMA_MODEL_LIGHT=qwen3:4b python scripts/smoke_test.py` |
| **Estimated runtime** | ~3 sec (static-only) / ~20-40 sec (full, depends on qwen3:4b warm/cold + Qwen MoE re-tokenization overhead per RESEARCH.md Pitfall 1) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/smoke_test.py --static-only`
- **After every plan wave:** Run `OLLAMA_MODEL_LIGHT=qwen3:4b python scripts/smoke_test.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 40 sec

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01 Task 1 (rewrite BIBLE.md + prompts/SYSTEM.md) | 02-01 | 1 | PERS-01, PERS-02 | static (size + content checks) | `python -c "import pathlib; ...assert 'Heresy detector' in SYSTEM, 'Principle 0 prime' in BIBLE..."` (full snippet in plan `<verify>`) | ⬜ pending (Task 1 of Plan 01 creates the files) | ⬜ pending |
| 02-01 Task 2 (rewrite _default_identity + retune warning + gitignore + CLAUDE.md) | 02-01 | 1 | PERS-03 | static (ensure_files + grep) | `python -c "from heretek.memory import Memory; ...assert scaffold sections..." && grep gathered\ dust heretek/context.py && grep ^memory/$ .gitignore && grep "BIBLE.md.*filename" CLAUDE.md` | ⬜ pending | ⬜ pending |
| 02-01 Task 3 (Wave 0 smoke-test scaffold) | 02-01 | 1 | PERS-01, PERS-02, PERS-03 (static); PERS-04, PERS-05, PERS-06 (SKIP stubs) | static + skip | `python scripts/smoke_test.py --static-only` (expect "5 pass · 0 fail · 0 skip · 5 total") | ⬜ pending | ⬜ pending |
| 02-02 Task 1 (flip test_bilingual_through_full_pipeline) | 02-02 | 2 | PERS-04 | unit (live LLM via build_llm_messages) | `OLLAMA_MODEL_LIGHT=qwen3:4b python -c "from scripts import smoke_test; assert smoke_test.test_bilingual_through_full_pipeline() == 'pass'"` | requires Plan 01 complete | ⬜ pending |
| 02-02 Task 2 (flip test_persona_in_character) | 02-02 | 2 | PERS-05 | unit (live LLM) | `OLLAMA_MODEL_LIGHT=qwen3:4b python -c "from scripts import smoke_test; assert smoke_test.test_persona_in_character() == 'pass'"` | requires Plan 01 complete | ⬜ pending |
| 02-02 Task 3 (flip test_restart_recall_grudge) | 02-02 | 2 | PERS-06 | unit (live LLM with seeded identity.md) | `OLLAMA_MODEL_LIGHT=qwen3:4b python -c "from scripts import smoke_test; assert smoke_test.test_restart_recall_grudge() == 'pass'"` | requires Plan 01 complete | ⬜ pending |
| 02-02 phase gate | 02-02 | 2 | ALL (PERS-01..06) | full suite | `OLLAMA_MODEL_LIGHT=qwen3:4b python scripts/smoke_test.py` (expect "9 pass · 0 fail · 0 skip · 9 total") | requires Plan 02 complete | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 ships as part of Plan 01 Task 3 (the smoke-test scaffold extension).

- [ ] `scripts/smoke_test.py` — add `test_bible_forbidden_at_top` as real static PASS check (Plan 01 Task 3)
- [ ] `scripts/smoke_test.py` — add `test_system_md_loaded` as real static PASS check (Plan 01 Task 3)
- [ ] `scripts/smoke_test.py` — add `test_identity_seed_scaffold` as real static PASS check (Plan 01 Task 3)
- [ ] `scripts/smoke_test.py` — add `test_persona_in_character` SKIP stub (Plan 01 Task 3; Plan 02 Task 2 flips to real check)
- [ ] `scripts/smoke_test.py` — add `test_restart_recall_grudge` SKIP stub (Plan 01 Task 3; Plan 02 Task 3 flips to real check)
- [ ] `scripts/smoke_test.py` — add `test_bilingual_through_full_pipeline` SKIP stub (Plan 01 Task 3; Plan 02 Task 1 flips to real check)
- [ ] `scripts/smoke_test.py` — update STATIC_SUBTESTS to length 5; update FULL_SUBTESTS to length 9 (Plan 01 Task 3)
- [ ] `./memory/` directory — bot-written runtime state path. Not pre-created. `Memory(drive_root=...).ensure_files()` creates it lazily; tests use tempfile.TemporaryDirectory for hermetic runs.
- [ ] `.gitignore` — `memory/` excluded (Plan 01 Task 2)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona vibe quality (horror flavor, surgical vocab density) | PERS-01/PERS-02 (subjective tone) | Tone calibration is subjective; automated keyword checks verify mechanism, not aesthetic quality | Owner runs `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M python -m supervisor --smoke` (or an equivalent direct-instantiation harness) with 3 representative RU+EN inputs, judges whether the replies feel right. Defer until Phase 4 supervisor boot is wired, or run an ad-hoc Python session calling `build_llm_messages` + `LLMClient.chat` against the primary model. |
| Mockery target calibration | PERS-05 | "Owner + Mechanicus + self" is too semantic for grep | Manual review of 5-10 sample outputs; flag if bot mocks code itself as primary target. |
| Bilingual mix density of persona docs (60/30/10 RU/EN/code-switch) | PERS-02 | Word-counting per language is approximate; reading flow matters more than ratio | Owner skims the rewritten BIBLE.md + prompts/SYSTEM.md after Plan 01 lands, flags any section that reads jarringly mono-lingual or saturated. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 40s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved by plan-phase (2026-05-16)
