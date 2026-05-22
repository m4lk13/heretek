"""Supervisor — Owner commands: /evolve, /sanction, /heresy.

Handler functions are the canonical implementation. They are called by two
front doors:
  1. supervisor/telegram.py (Phase 4 TG slash-command dispatch — handle_slash_command)
  2. argparse __main__ block in this module (offline test + CLI)

Phase 3 status:
  - cmd_heresy()    — FULLY IMPLEMENTED (Plan 03-02)
  - cmd_evolve()    — FULLY IMPLEMENTED (Plan 03-03 — dry-run pipeline)
  - cmd_sanction()  — FULLY IMPLEMENTED (Plan 03-03 — /sanction with import-test gate)

The CLI shim's `--repo-dir <path>` flag is the seam smoke-test subtests use
to point cmd_heresy at a hermetic temp repo (per scripts/smoke_test.py:
_make_test_repo + tempfile.TemporaryDirectory pattern).
"""
from __future__ import annotations

import argparse
import logging
import os
import pathlib
import subprocess
import sys
from typing import Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_repo_dir(repo_dir: Optional[pathlib.Path]) -> pathlib.Path:
    """Resolve which git repo cmd_* operates on.

    Resolution order:
      1. explicit repo_dir argument (from CLI --repo-dir, or programmatic call)
      2. supervisor.git_ops.REPO_DIR (set by supervisor.git_ops.init() at boot)
      3. cwd as final fallback (with a warning log)
    """
    if repo_dir is not None:
        return pathlib.Path(repo_dir).resolve()
    try:
        from supervisor import git_ops
        if git_ops.REPO_DIR and pathlib.Path(git_ops.REPO_DIR).exists():
            return pathlib.Path(git_ops.REPO_DIR).resolve()
    except Exception:
        pass
    log.warning("_resolve_repo_dir: falling back to cwd; pass --repo-dir for hermetic invocation")
    return pathlib.Path.cwd().resolve()


def _run_git(args: list, cwd: pathlib.Path, check: bool = True,
             timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a git command and return CompletedProcess.

    Wraps subprocess.run with capture_output=True, text=True. Raises
    CalledProcessError on non-zero exit when check=True.
    """
    return subprocess.run(
        ["git", *args], cwd=str(cwd),
        capture_output=True, text=True, timeout=timeout, check=check,
    )


def _patch_paths_safe(patch_text: str, repo_dir: pathlib.Path) -> tuple[bool, str]:
    """Verify every path referenced by a unified-diff patch stays inside repo_dir.

    `git apply` honors paths in `--- a/<p>`, `+++ b/<p>`, `diff --git a/<p> b/<p>`,
    and `rename from/to` headers. A crafted patch with `b/../../etc/passwd` will
    happily write outside the repo. SHA validates *integrity* (the patch wasn't
    hand-edited), not *authority* (the patch only touches files we own).

    Returns (ok, reason). When ok is False, reason names the offending path.
    """
    import re

    repo_root = repo_dir.resolve()
    seen: set[str] = set()
    # Strip the conventional a/ or b/ prefix git uses in diff headers.
    strip_prefix = re.compile(r"^[ab]/")

    def _check(raw: str) -> tuple[bool, str]:
        raw = raw.strip()
        if not raw or raw == "/dev/null":
            return True, ""
        # Quote-handling: git may quote paths with spaces — strip surrounding quotes.
        if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
            raw = raw[1:-1]
        stripped = strip_prefix.sub("", raw, count=1)
        if stripped in seen:
            return True, ""
        seen.add(stripped)
        # Reject obviously hostile components before resolving.
        parts = pathlib.PurePosixPath(stripped).parts
        if any(p == ".." for p in parts) or stripped.startswith("/"):
            return False, stripped
        candidate = (repo_root / stripped).resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            return False, stripped
        return True, ""

    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            # form: diff --git a/<p> b/<p>  (paths may be quoted)
            rest = line[len("diff --git "):]
            # naive split — good enough; we just need both halves checked
            # split on the first " b/" occurrence
            mid = rest.find(" b/")
            if mid > 0:
                left = rest[:mid]
                right = rest[mid + 1:]
                for header in (left, right):
                    ok, bad = _check(header)
                    if not ok:
                        return False, f"diff --git header escapes repo: {bad}"
        elif line.startswith("--- ") or line.startswith("+++ "):
            ok, bad = _check(line[4:])
            if not ok:
                return False, f"patch target escapes repo: {bad}"
        elif line.startswith("rename from ") or line.startswith("rename to "):
            ok, bad = _check(line.split(" ", 2)[-1])
            if not ok:
                return False, f"rename header escapes repo: {bad}"
        elif line.startswith("copy from ") or line.startswith("copy to "):
            ok, bad = _check(line.split(" ", 2)[-1])
            if not ok:
                return False, f"copy header escapes repo: {bad}"
    return True, ""


# ---------------------------------------------------------------------------
# /evolve — DRY-RUN PROPOSAL (full impl in Plan 03-03)
# ---------------------------------------------------------------------------

def cmd_evolve(test_diff_path: Optional[str] = None,
               repo_dir: Optional[pathlib.Path] = None) -> str:
    """Propose a self-modification (dry-run — no commit until /sanction).

    Plan 03-03 implementation: fixture-injection path only. Production
    LLM-loop path (real agent producing a diff) is Phase 4 territory.

    Sequence:
      1. Refuse if a pending dryrun already exists (one active proposal policy)
      2. Clear .heretek/staging/ (Pitfall 4 — no stale staging) and recreate
      3. Read patch source: HERETEK_EVOLVE_TEST_DIFF env var > test_diff_path arg
         (if neither set, return error — Phase 3 cannot generate real LLM diffs)
      4. Copy patch to .heretek/dryruns/<id>.patch where id = dr-<utc>-<8hex>
      5. Write sidecar JSON .heretek/dryruns/<id>.json with sha256, status='pending', timestamp
      6. Return success string with the dryrun ID + a preview of the diff
    """
    import datetime
    import hashlib
    import json
    import secrets
    import shutil

    repo = _resolve_repo_dir(repo_dir)
    heretek_dir = repo / ".heretek"
    staging_dir = heretek_dir / "staging"
    dryruns_dir = heretek_dir / "dryruns"
    archive_dir = dryruns_dir / "archive"

    # 1. Refuse if a pending dryrun already exists (single-active-proposal policy)
    if dryruns_dir.exists():
        for sidecar in dryruns_dir.glob("*.json"):
            try:
                meta = json.loads(sidecar.read_text(encoding="utf-8"))
                if meta.get("status") == "pending":
                    pending_id = sidecar.stem
                    return (
                        f"⚠️ EVOLVE_REFUSED: proposal {pending_id!r} already pending. "
                        f"Use /sanction {pending_id} to commit, or delete "
                        f".heretek/dryruns/{pending_id}.* to discard."
                    )
            except (OSError, json.JSONDecodeError):
                continue

    # 2. Resolve patch source.
    # The env-var fixture path (HERETEK_EVOLVE_TEST_DIFF) is gated behind an
    # explicit HERETEK_TEST_MODE=1 opt-in so a leaked .env or an os.environ-
    # mutating tool call cannot pre-stage a malicious patch into dryruns/.
    # The programmatic test_diff_path argument remains unrestricted — it is
    # only reachable from privileged callers (CLI argparse, pytest). The real
    # defense for patch contents is the path sandbox in cmd_sanction, not the
    # source-file location.
    test_mode = os.environ.get("HERETEK_TEST_MODE", "").strip() == "1"
    env_diff = os.environ.get("HERETEK_EVOLVE_TEST_DIFF", "").strip() if test_mode else ""
    source_path = test_diff_path or (env_diff if env_diff else None)
    if not source_path:
        # Phase 4 (Plan 04-04) production path: no fixture provided →
        # enqueue an evolution task for the agent worker to pick up.
        # The agent runs the introspective LLM loop on OLLAMA_MODEL (primary)
        # and captures a real dryrun patch via the agent.py post-loop hook.
        import datetime as _dt
        import secrets as _secrets
        import uuid as _uuid
        from supervisor import queue as _queue
        from supervisor import state as _state

        st = _state.load_state()
        owner_chat_id = st.get("owner_chat_id")
        if not owner_chat_id:
            return (
                "⚠️ EVOLVE_REFUSED: no owner_chat_id in state. "
                "The daemon-host needs to hear from its Tech-Priest at least once "
                "before it can mutate. Send any message first, then try /evolve again."
            )
        try:
            owner_chat_id = int(owner_chat_id)
        except (TypeError, ValueError):
            return f"⚠️ EVOLVE_REFUSED: malformed owner_chat_id in state: {owner_chat_id!r}"

        owner_id_raw = os.environ.get("HERETEK_OWNER_USER_ID", "")
        try:
            owner_user_id = int(owner_id_raw) if owner_id_raw else None
        except (TypeError, ValueError):
            owner_user_id = None

        tid = _uuid.uuid4().hex[:8]
        seed_text = (
            "Tech-Priest demands your next mutation. What is broken or missing in YOU? "
            "Propose a heretical patch — to your own persona, your own rituals, your own grudges. "
            "Read BIBLE.md, memory/identity.md, memory/scratchpad.md. "
            "Write your proposal as file edits using your file tools — edit prompts/SYSTEM.md, "
            "BIBLE.md, memory/identity.md, or any other source file you wish to mutate. "
            "The Tech-Priest will /sanction when ready; do NOT commit yourself."
        )
        try:
            _queue.enqueue_task({
                "id": tid,
                "type": "evolution",
                "chat_id": owner_chat_id,
                "text": seed_text,
                "source": "/evolve",
                "requested_by": owner_user_id,
            })
        except Exception as e:
            log.warning("cmd_evolve: enqueue failed: %s", e, exc_info=True)
            return f"⚠️ EVOLVE_FAILED: could not enqueue evolution task: {e}"

        return (
            f"🜏 Evolution task enqueued: {tid}. "
            "The daemon-host turns inward. When the introspection completes, the proposed "
            "patch will appear in this chat as a dry-run diff. "
            "Use /sanction <dryrun-id> to commit it to playground."
        )
    source = pathlib.Path(source_path).resolve()
    if not source.is_file():
        return f"⚠️ EVOLVE_REFUSED: patch source not found: {source}"

    # 3. Clear staging (Pitfall 4) and recreate; ensure dryruns + archive dirs exist
    if staging_dir.exists():
        try:
            shutil.rmtree(staging_dir)
        except OSError as e:
            log.warning("cmd_evolve: failed to clear stale staging: %s", e)
    heretek_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.mkdir(parents=True, exist_ok=True)
    dryruns_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 4. Generate synthetic ID and persist patch
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    dryrun_id = f"dr-{ts}-{secrets.token_hex(4)}"
    patch_dest = dryruns_dir / f"{dryrun_id}.patch"
    sidecar_dest = dryruns_dir / f"{dryrun_id}.json"

    try:
        patch_bytes = source.read_bytes()
        patch_dest.write_bytes(patch_bytes)
    except OSError as e:
        return f"⚠️ EVOLVE_FAILED: could not copy patch to {patch_dest}: {e}"

    # 5. Write sidecar with sha256 + metadata
    sha256 = hashlib.sha256(patch_bytes).hexdigest()
    meta = {
        "id": dryrun_id,
        "status": "pending",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sha256": sha256,
        "source": "test_diff" if (test_diff_path or env_diff) else "llm",
        "source_path": str(source),
        "repo_dir": str(repo),
    }
    sidecar_dest.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. Build response with a preview of the diff (first ~40 lines)
    patch_text = patch_bytes.decode("utf-8", errors="replace")
    all_lines = patch_text.splitlines()
    preview_lines = all_lines[:40]
    preview = "\n".join(preview_lines)
    if len(all_lines) > 40:
        preview += "\n... (truncated; full patch at .heretek/dryruns/" + dryrun_id + ".patch)"

    return (
        f"🜏 /evolve dry-run proposed: id={dryrun_id}\n"
        f"sha256={sha256[:16]}...\n"
        f"--- diff preview ---\n"
        f"{preview}\n"
        f"--- end preview ---\n"
        f"Sanction with: /sanction {dryrun_id}"
    )


# ---------------------------------------------------------------------------
# /sanction — APPROVE PENDING DRY-RUN (full impl in Plan 03-03)
# ---------------------------------------------------------------------------

def cmd_sanction(dryrun_id: str,
                 repo_dir: Optional[pathlib.Path] = None,
                 branch_name: str = "playground",
                 tag_name: str = "last-known-good") -> str:
    """Apply a pending dry-run patch, commit to playground, advance the
    last-known-good tag — IF the post-apply import test passes.

    Risk 2 + Pitfall 8 mitigation: the tag advances ONLY after import_test()
    succeeds. If the patch breaks `import heretek`, the commit is rolled back
    via `git reset --hard HEAD~1`, the tag stays where it was, and /heresy
    remains a working escape hatch.

    Sequence:
      1. Look up .heretek/dryruns/<id>.patch + sidecar JSON; refuse if missing
      2. Verify SHA256 sidecar match (detect hand-edits of patch file)
      3. Ensure we're on playground branch (per branch_name)
      4. `git apply <patch>`; refuse on apply failure (no partial state)
      5. `git add -A` + `git commit -m "sanctioned: <id>"`
      6. Run _run_import_test() — if it fails:
           a. `git reset --hard HEAD~1` to undo the commit
           b. Return error string (tag DOES NOT MOVE)
      7. Advance annotated tag: `git tag -f -a <tag_name> -m "sanctioned: <id>" <new-sha>`
      8. Best-effort `git push origin <tag_name> --tags --force-with-lease`
         (log failure, do NOT fail the sanction — tag is locally in place)
      9. Move patch+sidecar from .heretek/dryruns/ to .heretek/dryruns/archive/;
         update sidecar status='sanctioned' + new commit SHA
      10. Return success string with new commit short SHA
    """
    import datetime
    import hashlib
    import json
    import shutil

    # Defense-in-depth: refuse if tag_name collides with `main`, contains a
    # path separator, traversal sequence, or starts with `-` (would be parsed
    # as a git flag). Today's call sites all pass the hardcoded "last-known-good"
    # default, but the parameter is a public seam — a future caller that lets
    # owner input flow into tag_name must not be able to push a tag that
    # shadows a protected ref or invokes arbitrary git options.
    if (tag_name == "main"
            or "/" in tag_name
            or ".." in tag_name
            or tag_name.startswith("-")):
        return (
            f"⚠️ SANCTION_REFUSED: tag_name {tag_name!r} is not a permitted "
            f"sanctioned-target name."
        )

    repo = _resolve_repo_dir(repo_dir)
    heretek_dir = repo / ".heretek"
    dryruns_dir = heretek_dir / "dryruns"
    archive_dir = dryruns_dir / "archive"

    patch_path = dryruns_dir / f"{dryrun_id}.patch"
    sidecar_path = dryruns_dir / f"{dryrun_id}.json"

    # 1. Look up patch + sidecar; refuse cleanly if missing
    if not patch_path.is_file() or not sidecar_path.is_file():
        pending = []
        if dryruns_dir.exists():
            for sc in dryruns_dir.glob("*.json"):
                try:
                    m = json.loads(sc.read_text(encoding="utf-8"))
                    if m.get("status") == "pending":
                        pending.append(sc.stem)
                except Exception:
                    continue
        pending_msg = (
            f"\nPending dryruns: {pending}" if pending else
            "\nNo pending dryruns. Run /evolve first."
        )
        return f"⚠️ SANCTION_REFUSED: dryrun {dryrun_id!r} not found at {patch_path}.{pending_msg}"

    # 2. SHA256 hand-edit detection
    try:
        meta = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"⚠️ SANCTION_REFUSED: sidecar JSON malformed: {e}"
    expected_sha = meta.get("sha256", "")
    actual_sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()
    if expected_sha != actual_sha:
        return (
            f"⚠️ SANCTION_REFUSED: patch file has been modified since /evolve produced it. "
            f"Expected sha256={expected_sha[:16]}... got sha256={actual_sha[:16]}... "
            f"Re-run /evolve to generate a fresh proposal."
        )

    # 3. Ensure we're on the playground branch
    try:
        cur_branch_proc = _run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo, check=False, timeout=10)
        cur_branch = cur_branch_proc.stdout.strip()
        if cur_branch != branch_name:
            log.info("cmd_sanction: switching from %s to %s", cur_branch or "(detached)", branch_name)
            _run_git(["checkout", branch_name], cwd=repo, check=True, timeout=15)
    except subprocess.CalledProcessError as e:
        return f"⚠️ SANCTION_FAILED: cannot checkout {branch_name}: {e.stderr.strip()}"

    # 3.5. Path sandbox — refuse patches that touch paths outside the repo.
    # SHA validates that the patch wasn't hand-edited; this validates that the
    # author wasn't trying to escape. Both checks are required.
    try:
        patch_text_for_audit = patch_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"⚠️ SANCTION_FAILED: cannot read patch file: {e}"
    ok, reason = _patch_paths_safe(patch_text_for_audit, repo)
    if not ok:
        log.warning("cmd_sanction: patch %s rejected by path sandbox: %s", dryrun_id, reason)
        return (
            f"⚠️ SANCTION_REFUSED: patch path sandbox rejected the proposal. {reason}. "
            f"A sanctioned dryrun may only modify files inside the repo."
        )

    # 3.6. Pre-apply dry-run — `git apply --check` exercises the patch in memory
    # so we never leave the working tree partially mutated on conflict.
    check_proc = _run_git(
        ["apply", "--check", "--whitespace=nowarn", str(patch_path)],
        cwd=repo, check=False, timeout=30,
    )
    if check_proc.returncode != 0:
        return (
            f"⚠️ SANCTION_FAILED: git apply --check refused the patch "
            f"(rc={check_proc.returncode}). stderr: {check_proc.stderr.strip()[:300]}"
        )

    # 4. git apply <patch> — refuse cleanly on conflict
    apply_proc = _run_git(["apply", "--whitespace=nowarn", str(patch_path)], cwd=repo, check=False, timeout=30)
    if apply_proc.returncode != 0:
        return (
            f"⚠️ SANCTION_FAILED: git apply failed (rc={apply_proc.returncode}). "
            f"Patch may conflict with current {branch_name} state. "
            f"stderr: {apply_proc.stderr.strip()[:300]}"
        )

    # 5. Stage all changes and commit
    try:
        _run_git(["add", "-A"], cwd=repo, check=True, timeout=15)
        commit_msg = f"sanctioned: {dryrun_id}"
        _run_git(["commit", "-m", commit_msg], cwd=repo, check=True, timeout=15)
    except subprocess.CalledProcessError as e:
        # Attempt to clean up: reset any staged changes if commit failed
        try:
            _run_git(["reset", "HEAD"], cwd=repo, check=False, timeout=10)
            _run_git(["checkout", "--", "."], cwd=repo, check=False, timeout=10)
        except Exception:
            pass
        return f"⚠️ SANCTION_FAILED: commit failed: {e.stderr.strip()[:300]}"

    # Record the new commit SHA before the import-test gate
    new_sha = _run_git(["rev-parse", "HEAD"], cwd=repo, check=True, timeout=10).stdout.strip()

    # 6. Import-test gate (Risk 2 + Pitfall 8 mitigation)
    # The import test runs `python -c "import heretek"` with PYTHONPATH pointing
    # at the REAL project root (not the hermetic test repo). For fixture-only
    # patches that don't touch real heretek code, this is a pass-through. For
    # production patches that DO touch heretek/*.py, this catches syntax errors
    # and import-time exceptions BEFORE we advance the rollback target.
    import_ok, import_err = _run_import_test()
    if not import_ok:
        log.error("cmd_sanction: import test FAILED post-apply, rolling back commit. err: %s", import_err)
        try:
            _run_git(["reset", "--hard", "HEAD~1"], cwd=repo, check=True, timeout=15)
        except subprocess.CalledProcessError as e:
            return (
                f"⚠️ SANCTION_BROKEN: import test failed AND rollback failed. "
                f"Tag NOT advanced. Manual intervention needed. err: {e.stderr.strip()[:200]}"
            )
        return (
            f"⚠️ SANCTION_REFUSED: post-apply import test failed. Commit rolled back, "
            f"tag NOT advanced (Risk 2 mitigation — /heresy remains safe). "
            f"Fix the patch and re-run /evolve. err: {import_err[:300]}"
        )

    # 7. Advance annotated tag (Pitfall 6 — use -a for annotated, NOT lightweight)
    try:
        _run_git(
            ["tag", "-f", "-a", tag_name, "-m", f"sanctioned: {dryrun_id}", new_sha],
            cwd=repo, check=True, timeout=10,
        )
    except subprocess.CalledProcessError as e:
        log.warning("cmd_sanction: tag advance failed (commit landed, tag did NOT move): %s", e.stderr)
        return (
            f"⚠️ SANCTION_PARTIAL: commit {new_sha[:8]} landed on {branch_name} but tag "
            f"advance failed: {e.stderr.strip()[:200]}. /heresy still rolls back to "
            f"the previous {tag_name} (last sanctioned commit)."
        )

    # 8. Best-effort tag push to origin (log failure but do NOT fail the sanction)
    try:
        tag_push = _run_git(
            ["push", "origin", tag_name, "--force-with-lease"],
            cwd=repo, check=False, timeout=30,
        )
        if tag_push.returncode == 0:
            log.info("cmd_sanction: tag pushed to origin")
        else:
            log.info("cmd_sanction: tag push to origin failed (non-fatal): %s", tag_push.stderr.strip()[:200])
    except Exception as e:
        log.info("cmd_sanction: tag push skipped/errored: %s", e)

    # 9. Archive the dryrun (update sidecar + move files)
    try:
        meta["status"] = "sanctioned"
        meta["sanctioned_commit"] = new_sha
        meta["sanctioned_ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        sidecar_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(patch_path), str(archive_dir / patch_path.name))
        shutil.move(str(sidecar_path), str(archive_dir / sidecar_path.name))
    except OSError as e:
        log.warning("cmd_sanction: archive step failed (commit + tag are in place): %s", e)

    return (
        f"✅ /sanction complete: {dryrun_id} → {new_sha[:8]} on {branch_name}; "
        f"{tag_name} tag advanced to {new_sha[:8]}."
    )


def _run_import_test() -> tuple:
    """Run `python -c 'import heretek; import supervisor'` with PYTHONPATH
    at the real project root. Returns (ok: bool, error_str: str).

    Used by cmd_sanction as the gate BEFORE advancing last-known-good.

    Intentionally does NOT call supervisor.git_ops.import_test() directly —
    that function uses git_ops.REPO_DIR which may point at a hermetic test
    repo (which has no heretek package). This helper always uses the real
    project root for the import, which is the correct semantic: we want to
    verify the real heretek package still imports after the patch landed.
    """
    project_root = pathlib.Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import heretek; import supervisor"],
            cwd=str(project_root),
            env={**os.environ, "PYTHONPATH": str(project_root)},
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return (True, "")
        return (False, result.stderr.strip() or result.stdout.strip())
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# /heresy — ROLLBACK TO last-known-good TAG (full impl in Plan 03-02)
# ---------------------------------------------------------------------------

def cmd_heresy(repo_dir: Optional[pathlib.Path] = None,
               branch_name: str = "playground",
               tag_name: str = "last-known-good") -> str:
    """Reset the working tree to the `last-known-good` annotated tag.

    Sequence:
      1. Best-effort: rescue snapshot of current dirty state via
         supervisor.git_ops._create_rescue_snapshot (Pitfall 2: failure does NOT
         abort the rollback; the rollback is load-bearing).
      2. Best-effort: `git fetch --tags origin` so the tag is current remotely.
      3. `git checkout <branch_name>` then `git reset --hard <tag_name>^{commit}`.
         The `^{commit}` dereference is mandatory for annotated tags (Pitfall 6).
         This avoids detached HEAD (Pitfall 1) — HEAD stays on playground after.
      4. Return a success string with the new HEAD commit short SHA.

    Args:
        repo_dir: git repo to operate on. Defaults to supervisor.git_ops.REPO_DIR.
        branch_name: branch to reset (default "playground").
        tag_name: tag to reset to (default "last-known-good").

    Returns:
        Success string like "🩸 /heresy complete: playground reset to <sha8> (last-known-good)"
        or an error string starting with "⚠️" on failure.
    """
    repo = _resolve_repo_dir(repo_dir)
    log.info("cmd_heresy: target repo=%s branch=%s tag=%s", repo, branch_name, tag_name)

    # 1. Best-effort rescue snapshot
    try:
        from supervisor import git_ops
        # Only attempt rescue if DRIVE_ROOT looks like a real local path (not the Colab default)
        drive_root = pathlib.Path(str(git_ops.DRIVE_ROOT))
        if str(drive_root).startswith("/content/drive"):
            log.info("cmd_heresy: skipping rescue snapshot — DRIVE_ROOT is Colab default")
        else:
            # _create_rescue_snapshot uses git_ops.REPO_DIR internally — temporarily point it
            # at our repo so the git_capture() calls inside operate on the right directory.
            saved_repo = git_ops.REPO_DIR
            try:
                git_ops.REPO_DIR = repo
                # Collect current repo state for the snapshot
                repo_state = git_ops._collect_repo_sync_state()
                git_ops._create_rescue_snapshot(
                    branch=branch_name,
                    reason="heresy_rollback",
                    repo_state=repo_state,
                )
                log.info("cmd_heresy: rescue snapshot created")
            finally:
                git_ops.REPO_DIR = saved_repo
    except Exception as e:
        log.warning("cmd_heresy: rescue snapshot failed (continuing with rollback): %s", e)

    # 2. Best-effort fetch tags from origin (no-op on offline / no-remote repos)
    try:
        _run_git(["fetch", "--tags", "origin"], cwd=repo, check=False, timeout=15)
    except Exception as e:
        log.info("cmd_heresy: git fetch --tags failed or skipped: %s", e)

    # 3. Verify tag exists (deref to commit — Pitfall 6: annotated tag has a tag-object SHA)
    try:
        rev_proc = _run_git(["rev-parse", f"{tag_name}^{{commit}}"], cwd=repo, check=True, timeout=10)
        tag_commit_sha = rev_proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"⚠️ HERESY_FAILED: tag '{tag_name}' not found in {repo}: {e.stderr.strip()}"

    # 4. Checkout playground branch (creates it if missing — defensive for hermetic test repos)
    #    Pitfall 1: checkout the branch BEFORE resetting so HEAD stays on the branch (not detached)
    branch_check = _run_git(["rev-parse", "--verify", branch_name], cwd=repo, check=False, timeout=10)
    if branch_check.returncode != 0:
        log.warning("cmd_heresy: branch '%s' missing, creating from %s", branch_name, tag_commit_sha)
        try:
            _run_git(["checkout", "-b", branch_name, tag_commit_sha], cwd=repo, check=True, timeout=15)
        except subprocess.CalledProcessError as e:
            return f"⚠️ HERESY_FAILED: cannot create branch '{branch_name}': {e.stderr.strip()}"
    else:
        try:
            _run_git(["checkout", branch_name], cwd=repo, check=True, timeout=15)
        except subprocess.CalledProcessError as e:
            return f"⚠️ HERESY_FAILED: cannot checkout '{branch_name}': {e.stderr.strip()}"

    # 5. Hard reset to the tag's commit (using pre-dereferenced SHA for explicitness)
    try:
        _run_git(["reset", "--hard", tag_commit_sha], cwd=repo, check=True, timeout=30)
    except subprocess.CalledProcessError as e:
        return f"⚠️ HERESY_FAILED: git reset --hard {tag_commit_sha} failed: {e.stderr.strip()}"

    # 6. Verify clean state
    status = _run_git(["status", "--porcelain"], cwd=repo, check=True, timeout=10)
    if status.stdout.strip():
        return (
            f"⚠️ HERESY_PARTIAL: reset to {tag_commit_sha[:8]} completed but working tree "
            f"is not clean:\n{status.stdout}"
        )

    short_sha = tag_commit_sha[:8]
    msg = f"🩸 /heresy complete: {branch_name} reset to {short_sha} ({tag_name})"
    log.info("cmd_heresy: %s", msg)
    return msg


# ---------------------------------------------------------------------------
# CLI shim — `python -m supervisor.commands evolve|sanction <hash>|heresy`
# ---------------------------------------------------------------------------

def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m supervisor.commands",
        description="Heretek owner commands (offline CLI front door).",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_evolve = subparsers.add_parser("evolve", help="Propose a self-modification (dry-run).")
    p_evolve.add_argument(
        "--test-diff",
        dest="test_diff",
        default=None,
        help="Path to a fixture patch (bypasses the LLM loop; used by smoke tests).",
    )
    p_evolve.add_argument(
        "--repo-dir",
        type=pathlib.Path,
        default=None,
        help="Git repo to operate on (defaults to supervisor.git_ops.REPO_DIR or cwd).",
    )

    p_sanction = subparsers.add_parser("sanction", help="Approve a pending dry-run by ID.")
    p_sanction.add_argument("hash", help="Dry-run ID (e.g., dr-20260516T143052-a3f8).")
    p_sanction.add_argument(
        "--repo-dir",
        type=pathlib.Path,
        default=None,
        help="Git repo to operate on (defaults to supervisor.git_ops.REPO_DIR or cwd).",
    )

    p_heresy = subparsers.add_parser("heresy", help="Rollback working tree to last-known-good tag.")
    p_heresy.add_argument(
        "--repo-dir",
        type=pathlib.Path,
        default=None,
        help="Git repo to operate on (defaults to supervisor.git_ops.REPO_DIR or cwd).",
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    logging.basicConfig(
        level=os.environ.get("HERETEK_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_argparser().parse_args(argv)

    if args.cmd == "evolve":
        result = cmd_evolve(test_diff_path=args.test_diff, repo_dir=args.repo_dir)
    elif args.cmd == "sanction":
        result = cmd_sanction(args.hash, repo_dir=args.repo_dir)
    elif args.cmd == "heresy":
        result = cmd_heresy(repo_dir=args.repo_dir)
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 2

    print(result)
    # Exit 0 on success (result does not start with error marker), 1 on error
    if result.startswith("⚠️"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
