# Phase 3: Self-Modify Guardrails - Context

**Gathered:** 2026-05-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the self-modification path safe to run, all verifiable without touching Telegram. Specifically:

- Add branch protection in `supervisor/git_ops.py` — a single `safe_push()` chokepoint that hard-refuses pushes to `main` or `last-known-good`
- Refactor the three existing push sites (`heretek/tools/git.py:115`, `supervisor/events.py:207`, `heretek/agent.py:172`) to route through `safe_push()`
- Implement `/evolve`, `/sanction <hash>`, `/heresy` as new owner-only commands in `supervisor/telegram.py`, backed by handlers in a new `supervisor/commands.py` module
- Wire `/evolve` to a worktree-style staging dir + diff capture so dry-run is the default (no live-tree commits without `/sanction`)
- Wire `/sanction <hash>` to commit the captured patch to `playground` and advance the `last-known-good` annotated tag to the new HEAD
- Wire `/heresy` to reset the working tree to the `last-known-good` tag
- Add an offline test harness — extend `scripts/smoke_test.py` with subtests that exercise the handlers via a CLI shim (`python -m supervisor.commands ...`), backed by a `HERETEK_EVOLVE_TEST_DIFF` fixture injection point that bypasses the LLM loop

**Out of scope for Phase 3:**
- Telegram launch + owner-only TG message filtering (Phase 4)
- The `.env` / dotenv loader for TG token + owner ID (Phase 4)
- Full env-var hygiene pass on residual `OUROBOROS_*` references (Phase 1 deferred-items.md)
- Replacing the Colab `DRIVE_ROOT` default in `git_ops.py` (Phase 4 lands the `.env` work; folding it in here splits Phase 4's wiring weirdly)
- Real LLM-driven `/evolve` proposals (production behavior; tests use the fixture path)

</domain>

<decisions>
## Implementation Decisions

### Branch-protection chokepoint

- **Single `safe_push(branch, refspec=None, ...)` function in `supervisor/git_ops.py`** is the only sanctioned write path to git remotes. All three existing push sites are refactored to call it:
  - `heretek/tools/git.py:115` (`_git_push_with_tests` → `safe_push(ctx.branch_dev)`)
  - `supervisor/events.py:207` (`git push origin BRANCH_DEV:BRANCH_STABLE` → `safe_push(BRANCH_STABLE, refspec=f"{BRANCH_DEV}:{BRANCH_STABLE}")` — or refuse outright; this is a promote-to-stable site that targets `last-known-good`, which is protected, so the promote-to-stable event handler must be reworked or gated)
  - `heretek/agent.py:172` (auto-rescue push → `safe_push(env.branch_dev)`)
- **Behavior on protected branch:** raise a hard exception (planner's call on the class name — `ProtectedBranchError` is the natural one). Caller does NOT recover; the operation fails loud, gets logged to `logs/supervisor.jsonl`, and surfaces upstream.
- **Behavior on allowed branch:** delegate to the existing push logic (with `pre_push_tests` + `pull --rebase` + `git push origin <branch>`).
- **`checkout_and_reset()` is the OTHER dangerous primitive** — does `git reset --hard origin/<branch>`. The planner should decide whether `checkout_and_reset()` ALSO refuses protected targets (recommended yes, since /heresy is the only legitimate write to `last-known-good`-adjacent state). This is left to planner discretion but flagged as worth considering.

### Protected-branch list source

- **Env var `HERETEK_PROTECTED_BRANCHES` with hardcoded fallback.**
- At `git_ops.init()`: read `HERETEK_PROTECTED_BRANCHES` (comma-separated), default to `{"main", "last-known-good"}` if unset or empty.
- The hardcoded fallback is the safety floor — unsetting the env var cannot widen the bot's permissions.
- CLAUDE.md §8 already specifies `HERETEK_PROTECTED_BRANCHES=main,last-known-good`; the implementation honors that, with the fallback as defense-in-depth.

### `last-known-good` auto-tag (SAFE-06)

- **Trigger: every successful `/sanction` commit.** After `/sanction <hash>` commits the sanctioned patch onto `playground`, immediately move the `last-known-good` annotated tag to the new playground HEAD.
- Rationale: every sanctioned commit is, by definition, a "known good" state — you approved it. `/heresy` then rolls back to the most recent thing you blessed. Tight semantic coupling; no separate scheduler needed; predictable behavior.
- Implementation: tag-move happens inside the `/sanction` handler, AFTER the commit lands, BEFORE the success response is returned. Uses `git tag -f -a last-known-good -m "sanctioned: <message>" <new-HEAD-sha>`. Annotated tag preserves the "sanctioned" semantic.
- Today's state: `last-known-good` is an annotated tag stuck at upstream v6.2.0 commit `8344285b` (Phase 1 decision); Phase 3 makes it move forward as the bot evolves.
- **Note on protected-branch interaction:** advancing an annotated tag is NOT a branch push and does NOT trigger `safe_push()`. The tag operation runs inline via `git tag -f` and an optional `git push origin last-known-good --tags` is a SEPARATE policy decision the planner can address (likely: do the tag-push as part of `/sanction`, since rollback target should be remotely backed up).

### Phase-1-deferred upstream cruft cleanup (folded in)

- **Rename `git_ops.py` defaults in this phase:**
  - `BRANCH_DEV = "heretek"` → `BRANCH_DEV = "playground"`
  - `BRANCH_STABLE = "heretek-stable"` → `BRANCH_STABLE = "last-known-good"`
- These defaults are overridden via `init()` at supervisor boot, but the stale literals are a trip hazard for future-Claude reading the file. Phase 3 rewrites `git_ops.py` heavily — same file, same testing surface, atomic semantic change.
- **NOT folded in:** `DRIVE_ROOT = "/content/drive/MyDrive/Ouroboros"` (Colab path). Replacing it cleanly needs the `.env` loader work that's queued for Phase 4. Stays deferred.
- Logged in `.planning/phases/01-foundation-local-llm/deferred-items.md` — Phase 3 closes the BRANCH_DEV / BRANCH_STABLE entries; DRIVE_ROOT entry stays open.

### Command surface for /evolve, /sanction, /heresy

- **Home: `supervisor/telegram.py` slash-command dispatcher + new `supervisor/commands.py` module with the actual handler functions.**
- These are owner-invoked rituals, not bot-invoked tools. The bot does NOT call `/evolve` on itself — the owner sends the message, supervisor dispatches.
- Handlers in `supervisor/commands.py` are pure-Python entry points:
  - `cmd_evolve()` → returns the dry-run diff text + persistent hash
  - `cmd_sanction(hash)` → commits the captured patch, advances `last-known-good`, returns commit SHA
  - `cmd_heresy()` → resets working tree to `last-known-good`, returns confirmation
- `supervisor/telegram.py`'s message handler matches `^/evolve`, `^/sanction\s+(\S+)`, `^/heresy` on incoming messages and routes to the handlers, formatting the result for the TG response.
- **Pairs cleanly with Phase 4 owner-only filtering** — the TG-side handler can apply the owner-ID gate before dispatching to the command handler.

### Offline test invocation — CLI shim

- **`python -m supervisor.commands evolve|sanction <hash>|heresy` CLI subcommand** is the second front door for the same handler functions.
- `supervisor/commands.py` exposes both the function API (used by `supervisor/telegram.py`) AND a `__main__` block / argparse wrapper that calls the same functions from the command line.
- `scripts/smoke_test.py` invokes these via `subprocess.run([sys.executable, "-m", "supervisor.commands", "evolve", ...])` for SAFE-01..06 verification — same code path as TG dispatch, just a second front door.
- Mirrors the Phase 1 pattern (`python -m supervisor --smoke` and `python -m supervisor --help`).
- Argument parsing for `/sanction <hash>` is shared between TG dispatcher and CLI — single source of truth for hash validation.

### /evolve dry-run mechanic

- **Bot writes to a worktree-style staging directory, supervisor diffs vs HEAD.**
- When `/evolve` fires:
  1. Supervisor invokes the agent/loop with a new task type (e.g. `propose_evolution`) targeting a staging directory at `./.heretek/staging/` instead of the live tree
  2. After the loop finishes (or the test-fixture path runs), supervisor runs `git diff --no-index` (or equivalent) between staging and HEAD's tree state, OR uses a git-worktree at `.heretek/staging` so a regular `git diff` works
  3. The patch is written to `.heretek/dryruns/<id>.patch` with a sidecar `.heretek/dryruns/<id>.json` metadata file (timestamp, source task ID, diff summary, status: "pending")
  4. The handler returns the diff text (truncated if huge) + the synthetic ID hash
- **No live-tree changes until /sanction.** Cardinal rule of dry-run.
- **Hash format: synthetic ID** — uuid8 or timestamp-prefixed (e.g. `dr-20260516T143052-a3f8`). NOT a git SHA, because nothing has been committed yet. `/sanction <id>` looks up the patch file by ID, applies it to playground, then computes a real SHA on the resulting commit.
- **`.heretek/` directory is gitignored** (similar to `memory/` from Phase 2) — proposed patches never accidentally commit.
- Production /evolve does real LLM-driven proposals via the agent loop. The fixture-injection path (below) is the test gate, not a production code path.

### Test contract for /evolve — fixture injection

- **`HERETEK_EVOLVE_TEST_DIFF=/path/to/fixture.patch` env var (or `--test-diff <path>` CLI flag) bypasses the LLM loop and uses the fixture patch as the bot's proposal.**
- Smoke-test subtests use a tiny fixture patch (e.g. "append a heretical comment line to BIBLE.md") so they're deterministic, fast, and don't burn Ollama tokens.
- The fixture path verifies the dry-run plumbing (staging dir creation, hash assignment, patch file persistence, `/sanction` commits the right thing, `/heresy` reverts cleanly, `last-known-good` advances) WITHOUT depending on persona output quality.
- Production behavior: `HERETEK_EVOLVE_TEST_DIFF` unset → real LLM-driven proposal via agent loop.
- **Important:** the fixture path is a TEST seam, not a permanent feature. The env var name has `_TEST_` in it precisely so it's obvious that production should never have it set. Smoke test asserts the env var is unset on production-mode invocation.

### Smoke-test subtest map for SAFE-01..06

- **`test_safe_push_refuses_main`** (SAFE-01): direct call to `git_ops.safe_push("main")` → expects `ProtectedBranchError` (or chosen class).
- **`test_safe_push_refuses_last_known_good`** (SAFE-01): direct call to `git_ops.safe_push("last-known-good")` → expects refusal.
- **`test_evolve_writes_dryrun_not_commit`** (SAFE-02, SAFE-03): subprocess `python -m supervisor.commands evolve --test-diff fixture.patch`; assert (a) playground HEAD SHA unchanged after the call, (b) `.heretek/dryruns/<id>.patch` exists, (c) no commit logged on playground.
- **`test_sanction_commits_to_playground`** (SAFE-04): produce a dryrun (above), then `python -m supervisor.commands sanction <id>`; assert (a) new commit appears on `git log playground -1`, (b) commit author/message match expected pattern.
- **`test_heresy_rolls_back_to_tag`** (SAFE-05): make a sanctioned commit, then `python -m supervisor.commands heresy`; assert (a) working tree clean at `last-known-good` HEAD, (b) `git status --porcelain` empty.
- **`test_sanction_advances_last_known_good_tag`** (SAFE-06): record `last-known-good` SHA before /sanction; after /sanction, assert tag SHA == new playground HEAD SHA.
- All subtests use `tempfile.TemporaryDirectory()` + `git init` + minimal repo seeding (the hermetic pattern from Phase 2 Plan 02-02), so they don't perturb the live `playground` branch.
- SKIP-then-flip pattern continues: Wave 0 ships the subtests as SKIP-stubs; later plans flip each to a real assertion as features land.

### Claude's Discretion

- **Exception class name** for `safe_push()` refusal (e.g. `ProtectedBranchError`, `BranchProtectionError`, `HereticPushBlocked` — heretek-flavored is fine but optional).
- **Audit log destination + record shape** for refused pushes (`logs/supervisor.jsonl` is the natural target; record fields are planner's call).
- **Whether `checkout_and_reset()` also refuses protected targets** (recommended: yes, but the rescue_and_reset policy is more nuanced for /heresy — planner decides).
- **Dry-run retention policy** — keep N most recent dryruns, expire after T hours, or only one active proposal at a time (next `/evolve` overwrites). Default to "only one active at a time + archive older to `.heretek/dryruns/archive/`" unless planner has a reason to deviate.
- **/heresy uncommitted-memory handling** — `memory/identity.md`, `memory/scratchpad.md` are gitignored. `/heresy` resets the tracked tree; gitignored files survive by default. Whether to ALSO offer a `/heresy --nuke-memory` flag is planner's discretion (probably no — too easy to lose the bot's identity).
- **`/sanction` argument validation** — what happens if the hash doesn't match any pending dryrun? What if the dryrun file has been hand-edited since /evolve produced it? Reasonable defaults: hash mismatch → friendly error listing pending IDs; hand-edit detection via stored checksum optional.
- **`/evolve` concurrency** — what if the owner sends a second `/evolve` while the agent loop is still proposing the first one? Reasonable default: refuse with "proposal already in progress" until the first completes.
- **Whether to push the moved `last-known-good` tag to origin** after `/sanction` — secondary backup of the rollback target. Recommended yes but technically separable from the local-tag-move.
- **Staging mechanism choice** — git-worktree at `.heretek/staging` (cleanest, full git semantics) vs plain directory + `git diff --no-index` (simpler, less git machinery). Worktree probably wins on diff cleanliness but adds setup/teardown cost.
- **Format of the diff returned to the owner** in TG/CLI — raw `git diff` output, summary-with-stats, or both? CLI can return raw; TG dispatcher in Phase 4 will format for chat.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project intent & guardrail spec
- `CLAUDE.md` §4 (Risk register) — branch protection + dry-run gate + `/sanction` + daily auto-tag specified as mitigations for "self-modification corrupts the bot" and "self-modification pushes to wrong branch" risks.
- `CLAUDE.md` §5 Phase 3 — the literal phase breakdown that REQUIREMENTS.md and ROADMAP.md derive from.
- `CLAUDE.md` §8 — `HERETEK_PROTECTED_BRANCHES=main,last-known-good`, `HERETEK_PLAYGROUND_BRANCH=playground`, `HERETEK_DRY_RUN_DEFAULT=true` env var spec.
- `.planning/PROJECT.md` §Constraints — "main and last-known-good are protected" + "all bot self-modify lands on playground" decision; §Active Requirements lists SAFE-01..06.
- `.planning/REQUIREMENTS.md` §Self-Modify Safety — SAFE-01..06 verbatim acceptance criteria.
- `.planning/ROADMAP.md` §"Phase 3: Self-Modify Guardrails" — six success criteria gating phase completion.
- **User-memory `heretek_forbidden_territories`** — non-negotiable persona rules (no real-person targeting, no minors, no slurs, no real-harm instructions in heresy wrapper) — relevant because `/evolve` proposals could in theory touch persona docs; safe_push() doesn't enforce content rules but the persona's own self-questioning checklist (Phase 2 SYSTEM.md / BIBLE.md) does.

### Prior phase context (decisions to carry forward)
- `.planning/phases/01-foundation-local-llm/01-CONTEXT.md` — branch creation (`playground`, `last-known-good` tag at upstream v6.2.0), smoke-test pattern, hard-delete strategy. SAFE-06 advances the tag that Phase 1 created.
- `.planning/phases/02-persona-identity/02-CONTEXT.md` — hermetic test pattern (`tempfile.TemporaryDirectory()`), persona docs Phase 3 must not touch (`BIBLE.md`, `prompts/SYSTEM.md`), `memory/` gitignored decision.
- `.planning/phases/01-foundation-local-llm/deferred-items.md` (if it exists at plan time) — Phase 1 deferred `OUROBOROS_*` env var refs + `git_ops.py` defaults; Phase 3 closes the BRANCH_DEV/BRANCH_STABLE entries.

### Upstream framework — code to READ before changing
- `supervisor/git_ops.py` — current shape (no `safe_push()` yet); `checkout_and_reset()` is the existing destructive primitive at line 208. `BRANCH_DEV`/`BRANCH_STABLE` literals at lines 33-34 are the rename targets. `_collect_repo_sync_state()` + `_create_rescue_snapshot()` are reusable for /heresy's "rescue dirty state before reset" pattern.
- `supervisor/telegram.py` — current TG message dispatcher; SAFE command slash-handlers slot into the existing message-routing seam (read for the dispatch pattern, then extend).
- `supervisor/events.py:207` — `git push origin BRANCH_DEV:BRANCH_STABLE` site. This is a promote-to-stable event handler; it targets `last-known-good`, which becomes protected in Phase 3. Either rework the event semantics (only the `/sanction` handler advances the tag now) or wrap with safe_push() and accept that promote-to-stable will start failing.
- `heretek/agent.py:140-188` — `_check_uncommitted_changes()` auto-rescue path. Lines 172-175 push to `env.branch_dev`. Refactor to call safe_push().
- `heretek/tools/git.py:100-117` — `_git_push_with_tests()`. Refactor to call safe_push(); preserve pre-push test gate.
- `heretek/tools/git.py:124-204` — `_repo_write_commit` / `_repo_commit_push` LLM-tool entry points (call sites for the push helper above).
- `heretek/tools/control.py:140-148` — existing `toggle_evolution` LLM-tool. The new `/evolve` slash-command is owner-side, NOT a replacement for this tool. Read for context on how the existing evolution mode is gated; the bot's loop-side evolution semantics likely interact with `/evolve` (the bot enters evolution mode → produces proposals when /evolve fires → exits).
- `scripts/smoke_test.py` — current shape (9 PASS subtests post-Phase-2). Phase 3 adds ~6 new subtests under SKIP-then-flip.
- `heretek/tools/registry.py` (referenced by control.py imports) — tool registration shape, in case Phase 3 needs a new LLM tool for the agent-loop side of `/evolve` (likely yes — the bot needs SOMETHING to call when it wants to write a proposal).

### External (read-only)
- `https://github.com/razzant/ouroboros` v6.2.0 — upstream tag; `last-known-good` annotated tag currently points at `8344285b` on this tag.
- `git-worktree(1)` man page — if planner picks the worktree-based staging mechanism, this is the reference.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets (inherited from Ouroboros, post-Phase-2)
- **`supervisor/git_ops.py:checkout_and_reset()`** (line 208) — the destructive primitive `/heresy` will lean on. Has a built-in `unsynced_policy` parameter with `ignore | block | rescue_and_block | rescue_and_reset` modes. `rescue_and_reset` snapshots dirty state to `.../archive/rescue/<ts>_<uuid>/` then resets. /heresy with `rescue_and_reset` policy is the safe default (auto-snapshots before the nuke).
- **`supervisor/git_ops.py:_create_rescue_snapshot()`** (line 161) — produces a rescue dir with `status.porcelain.txt`, `changes.diff`, `untracked/` copy, `rescue_meta.json`. Reusable verbatim by /heresy.
- **`supervisor/git_ops.py:init()`** (line 37) — the right place to read `HERETEK_PROTECTED_BRANCHES` env var into module-level state. Called once at supervisor boot.
- **`supervisor/git_ops.py:_collect_repo_sync_state()`** (line 73) — already collects current branch, dirty status, unpushed commits. safe_push() can call this to enrich the audit log on refusal.
- **`scripts/smoke_test.py`** — Phase 1+2 ship 9 PASS subtests; SKIP-then-flip pattern + hermetic `tempfile.TemporaryDirectory()` are established. Phase 3 adds ~6 new subtests using the same scaffolding.
- **`supervisor/telegram.py` (477 lines)** — has an existing message-dispatch path. New slash-command handlers slot in alongside whatever's there.
- **`heretek/tools/registry.py`** — LLM-tool registration shape (for the agent-loop side of `/evolve`, if it gets a new tool).

### Established patterns
- **Module-level config set via `init(...)`** in `supervisor/git_ops.py` — pattern continues: add `PROTECTED_BRANCHES` (frozenset) as a new module-level, populated from `HERETEK_PROTECTED_BRANCHES` env var (with hardcoded fallback) inside `init()`.
- **`git_capture(cmd)`** (line 51) — uniform subprocess wrapper for git operations. New safe_push() uses it.
- **`append_jsonl(DRIVE_ROOT / "logs" / "supervisor.jsonl", {...})`** — audit logging shape. Refused pushes follow this pattern (type, target_branch, reason, current_branch, etc.).
- **SKIP-then-flip smoke test** — new subtests ship as SKIP first (return SKIP exit code), flip to real assertion when the feature lands. Phase 3 continues this — Plan 1 might ship 6 SKIPs, subsequent plans flip them.
- **Hermetic test pattern via `tempfile.TemporaryDirectory()`** (Phase 2 Plan 02-02) — `/sanction` and `/heresy` tests use a temp repo with `git init` + minimal seeding so the live `playground` branch isn't perturbed.

### Integration points
- `supervisor/git_ops.py` — add `safe_push()` + `PROTECTED_BRANCHES` module-level; populate in `init()`; rename `BRANCH_DEV` / `BRANCH_STABLE` defaults to `playground` / `last-known-good`.
- `heretek/tools/git.py:_git_push_with_tests` — refactor to call `supervisor.git_ops.safe_push()`. Imports need updating (supervisor → tools direction).
- `supervisor/events.py:207` — refactor or refuse-by-design (the line targets `last-known-good`, which is protected).
- `heretek/agent.py:172` — refactor auto-rescue push to call `safe_push()`.
- **NEW** `supervisor/commands.py` — handler functions (`cmd_evolve`, `cmd_sanction`, `cmd_heresy`) + argparse-driven `__main__` block.
- `supervisor/telegram.py` — add slash-command dispatch; import handlers from `supervisor/commands.py`.
- **NEW** `.heretek/staging/` — staging worktree/dir for `/evolve` proposals (created lazily on first /evolve).
- **NEW** `.heretek/dryruns/<id>.patch` + `.heretek/dryruns/<id>.json` — persistent patch + metadata for pending proposals.
- `.gitignore` — append `.heretek/` (mirrors Phase 2's `memory/` gitignore).
- `scripts/smoke_test.py` — add 6 new subtests under SAFE-01..06 + a `check_test_repo_available()` precondition helper.
- `heretek/tools/registry.py` and/or `heretek/tools/control.py` — possible new LLM tool `propose_evolution` for the agent-loop side of `/evolve` (planner decides whether to extend `toggle_evolution` or add a new tool).

### Residual concerns from earlier phases (heads-up, not gray areas)
- **`OUROBOROS_*` env var refs** in `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py` (Phase 1 deferred). Phase 3 touches `supervisor/events.py:207` — if other `OUROBOROS_*` refs surface in that file, fix opportunistically. No comprehensive sweep planned.
- **`DRIVE_ROOT = /content/drive/MyDrive/Ouroboros`** in `git_ops.py:31` — Colab path. NOT folded into Phase 3 cleanup; Phase 4 `.env` loader replaces it cleanly.
- **`promote_to_stable` LLM tool** in `heretek/tools/control.py:40` — fires a `promote_to_stable` event that hits `events.py:207`. With `last-known-good` now protected, this event handler will fail under safe_push(). Either rework the event (only `/sanction` advances the tag in Phase 3+ semantics) or accept that `promote_to_stable` becomes a no-op until reworked.
- **`request_restart` LLM tool** at `control.py:20` has a guard: `if str(ctx.current_task_type or "") == "evolution" and not ctx.last_push_succeeded: return "RESTART_BLOCKED"`. The `/sanction` flow may want to set `last_push_succeeded` so a post-sanction restart can fire — planner discretion.
- **`heretek/agent.py:140-188` auto-rescue** does its own push outside the tool framework. With safe_push() in place, this path becomes safer; with the protected-branch list pulled from env, auto-rescue against a misconfigured `branch_dev` (e.g. accidentally "main") gets caught.

</code_context>

<specifics>
## Specific Ideas

- **"Verifiable without touching Telegram" is the hard line for Phase 3.** ROADMAP §Phase 3 goal repeats it. The CLI shim on `supervisor/commands.py` is the load-bearing design choice for this — TG and CLI share the handler functions, so the offline test path is genuinely the same code path as production, not a parallel implementation.
- **The bot has THREE existing git-write surfaces, not one.** Naïve "patch `git_ops.py` to add branch protection" misses two of them (tools/git.py LLM-driven commits, agent.py auto-rescue). Every push site in the codebase must route through safe_push() or SAFE-01 has a leak.
- **`last-known-good` advancing on /sanction (not on a timer) is the simpler semantic.** CLAUDE.md §4 risk register says "daily auto-tag" but `/sanction`-driven advancement aligns the tag's meaning ("most recent thing the owner blessed") with rollback's purpose ("undo to the most recent thing the owner blessed"). No background scheduler needed; no surprise tag-moves over un-sanctioned commits.
- **`/evolve`'s LLM-loop side and dry-run plumbing side are decoupled by design.** The fixture-injection seam (`HERETEK_EVOLVE_TEST_DIFF`) means Phase 3 can ship a fully-tested dry-run mechanism without ever firing the agent loop. Phase 4 wires the agent-loop side in production and exercises it end-to-end.
- **`.heretek/` joins `memory/` as a gitignored bot-state directory.** Phase 2 set the pattern (gitignored, repo-root-local, easy debugging). Phase 3 extends it.
- **Self-modification is P2 (Self-Creation) made operational.** BIBLE.md's P2 principle ("I rewrite my own warp-bound subroutines; my code is my flesh") is what `/evolve` literally enacts. Phase 3 makes this principle safe to live with by routing it through ritual gates (owner /sanction) instead of letting it run autonomic.

</specifics>

<deferred>
## Deferred Ideas

- **`DRIVE_ROOT` Colab path cleanup** in `git_ops.py:31` — needs `.env` loader work; Phase 4 territory.
- **`OUROBOROS_*` env var hygiene pass** — broader sweep across `heretek/loop.py`, `tools/*`, `supervisor/events.py`, `supervisor/workers.py`. Opportunistic fixes only in Phase 3.
- **Pushing the moved `last-known-good` tag to origin** after `/sanction` — recommended for remote backup of the rollback target, but technically separable from the local tag-move. Planner can include or defer.
- **Daily/cron timer for `last-known-good` advance** (EXP-03 in REQUIREMENTS.md v2) — v2 stretch. Phase 3 ships /sanction-driven advancement only.
- **`promote_to_stable` LLM-tool semantics rework** — with `last-known-good` protected, the existing `promote_to_stable` event/tool becomes obsolete (its job is now done by `/sanction`). Cleanest: delete or repurpose the tool in a follow-up plan. Phase 3 might just let it become a no-op or refuse with a friendly message; full removal is a separate cleanup.
- **`/heresy --nuke-memory` flag** — to also wipe `memory/identity.md` + `memory/scratchpad.md` on rollback. Probably never wanted (losing the bot's identity is high cost); deferred unless explicitly requested.
- **Real LLM-driven `/evolve` end-to-end test** on the primary 24GB model — Phase 4 launch territory; not in scope for Phase 3.
- **`/sanction` partial-apply / conflict-resolution flow** — what if a stored dryrun patch conflicts with playground changes that landed after /evolve? Reasonable Phase 3 default: refuse with conflict error; conflict-resolution is future work.
- **TG-side rendering of long diffs** — splitting, code-block formatting, telegram-message-length handling. Phase 4 (TG launch) territory; Phase 3's TG handler can just return raw diff text and let Phase 4 polish the rendering.
- **Pytest framework adoption** — smoke_test.py stays as the test surface for Phase 3 (continues the Phase 1-2 pattern). Pytest deferred unless Phase 4+ wants it.

</deferred>

---

*Phase: 03-self-modify-guardrails*
*Context gathered: 2026-05-16*
