---
phase: 1
slug: foundation-local-llm
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Runnable Python script (`scripts/smoke_test.py`) + CLI greps. No pytest in Phase 1 (per CONTEXT decision — lower-ceremony for a leisure project). |
| **Config file** | none — script is self-contained |
| **Quick run command** | `python scripts/smoke_test.py --static-only` (greps + imports only, no Ollama call) |
| **Full suite command** | `python scripts/smoke_test.py` (full end-to-end incl. RU+EN Ollama calls) |
| **Estimated runtime** | ~3s static; ~20–60s full (first-token latency on a cold primary model) |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/smoke_test.py --static-only` (static checks only — fast, no Ollama dependency)
- **After every plan wave:** Run `python scripts/smoke_test.py` (full — only meaningful once LLM swap lands in the wave that ships it)
- **Before `/gsd:verify-work`:** Full suite must be green (RU reply + EN reply + no cloud-host strings)
- **Max feedback latency:** 60 seconds (full); 3 seconds (static)

---

## Per-Task Verification Map

> Filled by the planner. Each task gets a row mapping it to a requirement and an automated check.
> Phase 1 verification leans on: `import` checks (rename), `git ls-files`/`test -f` (deletions), `rg`/`grep` of source for forbidden strings (cloud hosts, dead imports), `ollama list` (precondition), `python scripts/smoke_test.py` (end-to-end).

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| _to be filled by planner_ | | | | | | | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 establishes the verification harness before any stripping/patching:

- [ ] `scripts/smoke_test.py` — stub with three named subtests: `test_package_rename`, `test_no_cloud_hosts`, `test_bilingual_ollama_reply`. Stubs return SKIP (exit 2) until each requirement lands; final task in each downstream plan flips its corresponding subtest from SKIP to a real assertion.
- [ ] `scripts/smoke_test.py --static-only` flag — runs only `test_package_rename` + `test_no_cloud_hosts` (no Ollama dependency). Used for fast per-task feedback.
- [ ] `logs/` directory creation guard — `scripts/smoke_test.py` must not fail if `logs/tokens.jsonl` doesn't exist yet (deferred until the token-logger task ships it).

*If existing infrastructure could cover this: it cannot. This is a greenfield fork with no test harness inherited beyond what upstream Ouroboros provides (which we are not pytest-bridging in Phase 1).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bilingual reply quality (not just *some* RU/EN reply but coherent ones) | LLM-04 | Quality is subjective; smoke test only asserts that a reply was received and looks like the target language (basic char-class heuristic). | Run `python scripts/smoke_test.py`, eyeball the printed RU and EN responses. PASS if a fluent Russian and a fluent English sentence appear. FAIL if either is garbled, in the wrong language, or empty. |
| Metal acceleration is actually engaged (vs CPU fallback) | LLM-02 (implicit — perf concern) | Ollama doesn't expose backend choice in API responses; must read `ollama ps` or process info. | After smoke test, run `ollama ps` and confirm `qwen3.6:35b-a3b-q4_K_M` shows a non-trivial GPU memory footprint (Metal backend on macOS). |
| `last-known-good` tag points at the right upstream commit | FORK-02 | Tag correctness is git-state, not Python-runnable. | `git tag -v last-known-good` and confirm SHA matches upstream `razzant/ouroboros@v6.2.0` head at clone time. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (smoke harness, static-mode flag, logs-dir guard)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s (full) / 3s (static)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
