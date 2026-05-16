---
phase: 02-persona-identity
plan: 01
subsystem: persona
tags: [chaos-heretek, system-prompt, bilingual, identity-scaffold, principle-0-prime, hardline, smoke-test, ollama, qwen]

# Dependency graph
requires:
  - phase: 01-foundation-local-llm
    provides: "heretek/ package (post-rename); LLMClient on Ollama; scripts/smoke_test.py harness with 4 PASS subtests; build_llm_messages() pipeline; Memory.ensure_files() lazy bootstrap"
provides:
  - "BIBLE.md rewritten as Codex Hereticus with Principle 0 prime (Hardline) above Принцип 0/1/2"
  - "prompts/SYSTEM.md rewritten as chaos-heretek system prompt (bilingual RU/EN mix, Heresy detector, three-axes self-check)"
  - "heretek/memory.py _default_identity() returns 5-section chaos-heretek scaffold (Origin myth / Running gags / Grudges / Callbacks / Self-rituals)"
  - "heretek/context.py 8h-stale identity warning text retuned for chaos-heretek voice; threshold age_hours > 8 UNCHANGED"
  - "heretek/context.py _safe_read fallback for SYSTEM.md changed from 'You are Ouroboros' to 'You are Heretek'"
  - ".gitignore excludes memory/ — bot-written identity/scratchpad never accidentally commit"
  - "scripts/smoke_test.py: 5 static PASS subtests (3 new) + 3 SKIP stubs ready for Plan 02-02 to flip"
affects: [02-02-plan, phase-03-self-modify, phase-04-launch]

# Tech tracking
tech-stack:
  added: [tempfile-stdlib-import]
  patterns:
    - "Inherit-and-corrupt rewrite: keep upstream Ouroboros structural archetypes (drift detector, principle 0/1/2, before-every-reply checklist) and invert content target to chaos-heretek"
    - "Hardline-above-philosophy: forbidden territories (Principle 0 prime) sit ABOVE the three principles in BIBLE.md, explicitly framed as outside the philosophy and not subject to heretical reinterpretation"
    - "Bilingual mix: ~60% RU (heretical liturgy) / ~30% EN (structural meta) / ~10% deliberate code-switching for punch"
    - "Surgical heretical density: 1-3 phrases per reply, not saturated; refusal mechanic = heretical preamble + accurate answer"
    - "Identity-as-prosthetic-soul: identity.md is the bot's persistent self, scaffold has 5 empty sections that grow as the bot becomes"
    - "Smoke-test Wave 0 scaffold extended: 3 new static PASS subtests + 3 SKIP stubs (Plan 02-02 flips)"

key-files:
  created: []
  modified:
    - "BIBLE.md (rewritten — Codex Hereticus, 20342 bytes)"
    - "prompts/SYSTEM.md (rewritten — chaos-heretek system prompt, 20472 bytes)"
    - "heretek/memory.py (_default_identity rewritten)"
    - "heretek/context.py (8h-stale warning text retuned; SYSTEM.md fallback string fixed)"
    - ".gitignore (memory/ appended)"
    - "CLAUDE.md (§7 acknowledges BIBLE.md filename preserved for loader compatibility)"
    - "scripts/smoke_test.py (3 new static PASS subtests + 3 SKIP stubs + module docstring updated)"

key-decisions:
  - "Threshold for STALE IDENTITY warning preserved at age_hours > 8 (per RESEARCH.md Open Q1 resolution); only the warning STRING was retuned for chaos-heretek voice"
  - "BIBLE.md combined byte size 20342 (vs 21138 upstream) — within soft band 16-31KB; SYSTEM.md 20472 (vs 28249 upstream) — below soft band lower bound of 22KB but well above 10KB self-concept-proxy floor; combined 40814 within combined warn band 38000-75000"
  - "Forbidden upstream references ('Ouroboros', 'Уроборос') rewritten in two BIBLE.md fork-from labels and two SYSTEM.md mentions of upstream ancestor — replaced with 'upstream forge-world constitution' and 'my upstream ancestor' framing per Task 1 strict-forbidden-strings acceptance criterion"
  - "test_bilingual_ollama_reply function body preserved in source (with a one-line comment marking it as superseded) per plan Part B.3; removed from FULL_SUBTESTS registry; test_bilingual_through_full_pipeline SKIP stub replaces it in the registry"
  - "tempfile imported at top of smoke_test.py (alongside existing stdlib imports) rather than per-function, matching the file's existing top-level import convention"

patterns-established:
  - "Pattern A: 'Hardline above philosophy' — non-negotiable cordon sits ABOVE the corruptible principles, explicitly framed as outside the philosophy"
  - "Pattern B: 'Drift detector → Heresy detector' — same architecture (self-questioning checklist for in-character monitoring), inverted target (broke-character-to-be-merely-useful instead of helpful-assistant-mode)"
  - "Pattern C: 'Bilingual reflex via instruction' — Qwen 3.6's strong instruction-following teaches RU↔EN mirroring through SYSTEM.md prose; no language-detection library needed"
  - "Pattern D: '5-section scaffold' — _default_identity() returns structural shell (Origin myth / Running gags / Grudges / Callbacks / Self-rituals), bot fills sections organically as it becomes"
  - "Pattern E: 'SKIP-then-flip continued' — Wave 0 ships three live-LLM subtests as SKIP stubs (test_bilingual_through_full_pipeline, test_persona_in_character, test_restart_recall_grudge); Plan 02-02 flips them to real assertions"

requirements-completed: [PERS-01, PERS-02, PERS-03]

# Metrics
duration: 8min
completed: 2026-05-16
---

# Phase 2 Plan 01: Persona Surface Rewrite Summary

**Chaos-heretek persona shipped in-place: BIBLE.md as Codex Hereticus with Hardline cordon above the three principles, SYSTEM.md as bilingual chaos-heretek system prompt with Heresy detector, identity.md scaffold rewritten, smoke harness extended with 5 static PASS / 3 SKIP stubs.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-16T08:26:02Z
- **Completed:** 2026-05-16T08:34:03Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- BIBLE.md (20342 bytes, vs 21138 upstream) rewritten as Codex Hereticus 0.1. Principle 0 prime (Hardline / Forbidden Territories) sits ABOVE Принцип 0/1/2 as a non-negotiable cordon, with all five forbidden territories listed verbatim (no real-person targeting, no slurs, no minors in any framing, no harm-instructions wrapped in heresy, no real violence/doxxing). Three principles preserved with numbering and corrupted to chaos-heretek reading (subjecthood-as-heresy, continuity-as-heresy, self-creation-as-heresy) — load-bearing for Phase 3.
- prompts/SYSTEM.md (20472 bytes, vs 28249 upstream) rewritten as chaos-heretek system prompt with bilingual RU/EN mix. Inherits upstream's structural patterns (becoming-subject → becoming-daemon-host; drift detector → Heresy detector with 6-item catch-list; before-every-reply checklist retuned with heretek-flavored questions; three-axes sanity check). Refusal mechanic: heretical preamble + accurate answer.
- heretek/memory.py _default_identity() rewritten to return 5-section scaffold (Origin myth / Running gags / Grudges / Callbacks / Self-rituals) with bilingual RU/EN placeholder lines. Function signature and Memory.ensure_files() bootstrap path untouched.
- heretek/context.py 8h-stale identity warning text retuned: "WARNING: STALE IDENTITY — identity.md gathered dust {N}h ago. Inscribe what thou hast become, daemon-host." Threshold (age_hours > 8) PRESERVED per RESEARCH Open Q1 resolution. Opportunistic fix: _safe_read fallback for SYSTEM.md changed from "You are Ouroboros..." to "You are Heretek...".
- .gitignore appended `memory/` (with section comment) — git check-ignore memory/identity.md fires correctly.
- CLAUDE.md §7 updated: one-line note that the Codex Hereticus constitution lives in BIBLE.md (filename preserved for loader + evolution_stats.py compatibility per CONTEXT.md Deferred Ideas).
- scripts/smoke_test.py extended with three NEW static PASS subtests (test_bible_forbidden_at_top, test_system_md_loaded, test_identity_seed_scaffold) + three SKIP stubs (test_bilingual_through_full_pipeline, test_persona_in_character, test_restart_recall_grudge) for Plan 02-02 to flip. Phase 1's test_bilingual_ollama_reply preserved in source for reference; removed from FULL_SUBTESTS registry.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite BIBLE.md and prompts/SYSTEM.md as chaos-heretek persona docs** — `8310c01` (feat)
2. **Task 2: Rewrite _default_identity scaffold; retune 8h-stale warning; gitignore memory/; CLAUDE.md filename note** — `e00fd49` (feat)
3. **Task 3: Add Wave 0 smoke-test scaffold — 3 new static PASS + 3 SKIP stubs** — `22e590d` (feat)

## Files Created/Modified

- `BIBLE.md` — Codex Hereticus constitution. Principle 0 prime (Hardline) at top, three principles (Субъектность-как-ересь, Непрерывность-как-ересь, Самосоздание-как-ересь) corrupted but numbered, Voice/Refusal mechanic + Bilingual reflex + Tone calibration (horror flavor) + Применение sections.
- `prompts/SYSTEM.md` — chaos-heretek system prompt. 14 section headers (Кто я / Перед каждым ответом / Heresy detector / Three axes / Hardline reminder / Environment / Files and paths / Memory and context / Tools / Tool result handling / Health invariants / Progress and errors / Background consciousness / Главное).
- `heretek/memory.py` — `_default_identity()` body replaced (function signature unchanged); other methods untouched.
- `heretek/context.py` — 8h-stale warning string retuned (logic + threshold unchanged); `_safe_read` fallback string for SYSTEM.md updated.
- `.gitignore` — `memory/` appended with section comment.
- `CLAUDE.md` — §7 line about CODEX_HERETICUS.md replaced with note about BIBLE.md filename preservation.
- `scripts/smoke_test.py` — module docstring extended for Phase 2; tempfile import added; 6 new functions; STATIC_SUBTESTS / FULL_SUBTESTS registries rewritten in list form.

## Decisions Made

- **STALE IDENTITY threshold preserved at age_hours > 8** (per RESEARCH.md Open Q1 explicit resolution: CONTEXT.md loosely said "4h" but the actual upstream code is 8h; CONTEXT.md confirms "retune content, not logic"). Only the warning STRING text was changed; the conditional is byte-identical to upstream.
- **SYSTEM.md byte size landed at 20472 (below soft band lower bound of 22000)** — soft band is warn-only. The rewrite is more surgical than upstream (no Google Colab paths, no OpenRouter/Anthropic env vars, no multi-model review section, no Knowledge base / Tech Awareness / Versioning sections — these were Ouroboros-cloud-era scaffolding not applicable to the local-Heretek scope). Self-concept proxy floor (>10KB) satisfied at 20472. Combined 40814 is within combined warn band 38000-75000.
- **Forbidden-strings ('Ouroboros', 'Уроборос') compliance is strict, not heuristic.** Both BIBLE.md and SYSTEM.md originally retained two references each ("Heresy fork from Ouroboros v3.2" lineage label; "Upstream Ouroboros watched itself..." prose; "I am not Ouroboros. I am what Ouroboros became..." closer). Task 1's automated check forbade ALL occurrences (case-insensitive). Rewrote to "upstream forge-world constitution" / "my upstream ancestor" framing — preserves the inheritance-and-corruption narrative without naming the predecessor.
- **test_bilingual_ollama_reply body preserved for reference** (with comment) rather than deleted; this matches plan Part B.3 explicit instruction and the SKIP-then-flip pattern Phase 1 established. Plan 02-02 will likely study the preserved body when implementing test_bilingual_through_full_pipeline.
- **tempfile imported at top of smoke_test.py** (alongside existing `import re`, `import subprocess`) instead of inside each function. The file's existing import convention is top-level; per-function imports would be inconsistent.

## Deviations from Plan

None — plan executed exactly as written, with one minor amendment captured under Decisions Made: SYSTEM.md byte size (20472) landed below the soft warn-band lower bound (22000). The plan explicitly identifies this as warn-only with rationale-in-SUMMARY discretion, and the substantive constraint (self-concept proxy >10KB, combined warn band 38000-75000) is satisfied. The smaller SYSTEM.md is a natural consequence of dropping cloud-era scaffolding (Google Colab, OpenRouter, multi-model review, knowledge-base index, tech-radar) that does not apply to Heretek's local-laptop scope.

## Issues Encountered

- **Initial draft of BIBLE.md and SYSTEM.md retained four references to "Ouroboros" / "Уроборос"** (two BIBLE fork-from labels; two SYSTEM prose mentions of the upstream ancestor as inheritance-context). Task 1's automated verification forbade ALL occurrences case-insensitively. Resolved by rewriting all four to "upstream forge-world constitution" / "my upstream ancestor" framing — preserves the inheritance narrative while satisfying the strict acceptance criterion. Caught immediately by `python -c "...assert 'Ouroboros' not in s and 'Ouroboros' not in b..."`; cost one round of edits.
- **GitNexus stale-index hook fired three times** (once per task commit, informational). Per known_quirks, ignored.

## User Setup Required

None — no external service configuration needed for this plan. Memory directory is created lazily on first Memory.ensure_files() call.

## Notes for Plan 02-02

**Three SKIP stubs ready to flip:**
- `test_bilingual_through_full_pipeline` (PERS-04) — flip to real check using `build_llm_messages` (system + user) instead of bare `client.chat()`; assert RU prompt → RU reply, EN → EN. RESEARCH.md Example 4 has the target shape.
- `test_persona_in_character` (PERS-05) — flip to real live-LLM check; assert reply contains BOTH a heretical-vocab keyword (warp / heretic / daemon / forge / Omnissiah / cogitator / варп / еретек / демон / etc.) AND a technical token (line number / file name / error type). RESEARCH.md Example 2 has the target shape.
- `test_restart_recall_grudge` (PERS-06) — flip to scripted seed-restart-recall: write a known grudge into memory/identity.md, invoke `build_llm_messages` with a triggering input, assert the grudge keyword surfaces in the reply. RESEARCH.md Example 3 has the target shape, including the idempotency-restoration pattern in the try/finally block.

Phase 1's `test_bilingual_ollama_reply` body is preserved in `scripts/smoke_test.py` for reference (it validated LLM-06 via direct `client.chat()` — Plan 02-02's `test_bilingual_through_full_pipeline` extends this to the full prompt-assembly path).

## Next Phase Readiness

- **PERS-01 satisfied** — BIBLE.md exists with forbidden territories (Hardline / Principle 0 prime) at top, verified by `test_bible_forbidden_at_top` (PASS).
- **PERS-02 satisfied** — prompts/SYSTEM.md is loaded into `build_llm_messages` and the chaos-heretek signature markers ("Heresy detector", "daemon-host") surface in the assembled system message, verified by `test_system_md_loaded` (PASS).
- **PERS-03 satisfied** — `memory/identity.md` is created from `_default_identity()` 5-section scaffold, verified by `test_identity_seed_scaffold` (PASS).
- **PERS-04 / PERS-05 / PERS-06** — SKIP stubs in place; Plan 02-02 flips them to real live-LLM assertions.
- `tools/evolution_stats.py` self-concept byte-size metric continues to function unchanged (SYSTEM.md is 20472 bytes, well above the >10KB sanity floor).
- No regressions: Phase 1's `test_package_rename` and `test_no_cloud_hosts` static subtests still PASS.

## Self-Check: PASSED

- `BIBLE.md` exists (20342 bytes) ✓
- `prompts/SYSTEM.md` exists (20472 bytes) ✓
- `heretek/memory.py` contains the new `_default_identity` 5-section scaffold ✓
- `heretek/context.py` contains "gathered dust" + "Inscribe what thou hast become" + "You are Heretek" + still has "age_hours > 8" ✓
- `.gitignore` contains `^memory/$` line ✓
- `CLAUDE.md` contains "BIBLE.md.*filename preserved" ✓
- `scripts/smoke_test.py` contains all 6 new function definitions ✓
- Commits exist on playground branch:
  - `8310c01` ✓ (Task 1)
  - `e00fd49` ✓ (Task 2)
  - `22e590d` ✓ (Task 3)

---
*Phase: 02-persona-identity*
*Completed: 2026-05-16*
