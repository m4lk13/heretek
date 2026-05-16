---
phase: 02
slug: persona-identity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-16
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
| **Full suite command** | `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py` |
| **Estimated runtime** | ~3 sec (static-only) / ~15-30 sec (full, depends on qwen3:4b warm/cold) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/smoke_test.py --static-only`
- **After every plan wave:** Run `OLLAMA_MODEL=qwen3:4b python scripts/smoke_test.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 sec

---

## Per-Task Verification Map

*Populated by planner during plan creation. Each plan's tasks must have an `<automated>` verify or a Wave 0 dependency.*

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD     | TBD  | TBD  | TBD         | TBD       | TBD               | TBD         | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Populated by planner. Typical Wave 0 items for Phase 2 include:*

- [ ] `scripts/smoke_test.py` — extend with `test_persona_in_character` SKIP stub (Plan owns flip)
- [ ] `scripts/smoke_test.py` — extend with `test_restart_recall_grudge` SKIP stub (Plan owns flip)
- [ ] `scripts/smoke_test.py` — extend with `test_bilingual_through_full_pipeline` SKIP stub (Plan owns flip)
- [ ] `./memory/` directory bootstrap path — verify Memory.ensure_files() creates files at expected path

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Persona vibe quality (horror-flavor, surgical vocab density) | PERS-01/PERS-02 (subjective tone) | Tone calibration is subjective; automated keyword checks verify mechanism, not aesthetic quality | Owner runs `OLLAMA_MODEL=qwen3.6:35b-a3b-q4_K_M python -m supervisor --smoke` with 3 representative RU+EN inputs, judges whether the replies feel right |
| Mockery target calibration | PERS-05 | "Owner + Mechanicus + self" is too semantic for grep | Manual review of 5-10 sample outputs; flag if bot mocks code itself as primary target |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
