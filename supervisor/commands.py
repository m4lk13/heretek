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

    # 2. Resolve patch source
    env_diff = os.environ.get("HERETEK_EVOLVE_TEST_DIFF", "").strip()
    source_path = test_diff_path or (env_diff if env_diff else None)
    if not source_path:
        return (
            "⚠️ EVOLVE_REFUSED: no patch source provided. "
            "Phase 3 supports fixture-injection only — set HERETEK_EVOLVE_TEST_DIFF "
            "or pass --test-diff <path>. Production LLM-loop /evolve is Phase 4 territory."
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
# /sanction — APPROVE PENDING DRY-RUN (stub in Plan 03-02, full impl in Plan 03-03)
# ---------------------------------------------------------------------------

def cmd_sanction(dryrun_id: str,
                 repo_dir: Optional[pathlib.Path] = None) -> str:
    """Apply a pending dry-run patch and commit to playground. STUB — Plan 03-03.

    Plan 03-03 will:
      1. Look up .heretek/dryruns/<id>.patch by dryrun_id; verify SHA256 against sidecar
      2. Apply patch to playground (git apply)
      3. Run import test (supervisor.git_ops.import_test) — refuse with error if import fails
      4. Commit with message "sanctioned: <id>"
      5. Advance last-known-good annotated tag to new HEAD via `git tag -f -a`
      6. Best-effort `git push origin last-known-good --tags --force-with-lease`
    """
    return (
        f"⚠️ NOT_IMPLEMENTED: cmd_sanction({dryrun_id!r}) lands in Plan 03-03. "
        "Phase 3 wave 2 only ships cmd_heresy() and the CLI shim."
    )


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
