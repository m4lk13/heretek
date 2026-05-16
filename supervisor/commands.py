"""Supervisor — Owner commands: /evolve, /sanction, /heresy.

Handler functions are the canonical implementation. They are called by two
front doors:
  1. supervisor/telegram.py (Phase 4 TG slash-command dispatch — handle_slash_command)
  2. argparse __main__ block in this module (offline test + CLI)

Phase 3 status:
  - cmd_heresy()    — FULLY IMPLEMENTED (Plan 03-02)
  - cmd_evolve()    — STUB (Plan 03-03 ships dry-run pipeline)
  - cmd_sanction()  — STUB (Plan 03-03 ships /sanction with import-test gate)

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
# /evolve — DRY-RUN PROPOSAL (stub in Plan 03-02, full impl in Plan 03-03)
# ---------------------------------------------------------------------------

def cmd_evolve(test_diff_path: Optional[str] = None,
               repo_dir: Optional[pathlib.Path] = None) -> str:
    """Propose a self-modification (dry-run; no commit). STUB — Plan 03-03.

    Plan 03-03 will:
      1. Read HERETEK_EVOLVE_TEST_DIFF env var or test_diff_path argument
      2. Create .heretek/staging/ + .heretek/dryruns/<id>.patch + sidecar JSON
      3. Return the diff text + synthetic dry-run ID
    """
    return (
        "⚠️ NOT_IMPLEMENTED: cmd_evolve() lands in Plan 03-03 (dry-run pipeline). "
        "Phase 3 wave 2 only ships cmd_heresy() and the CLI shim."
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
    parser.add_argument(
        "--repo-dir",
        type=pathlib.Path,
        default=None,
        help="Git repo to operate on (defaults to supervisor.git_ops.REPO_DIR or cwd).",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_evolve = subparsers.add_parser("evolve", help="Propose a self-modification (dry-run).")
    p_evolve.add_argument(
        "--test-diff",
        dest="test_diff",
        default=None,
        help="Path to a fixture patch (bypasses the LLM loop; used by smoke tests).",
    )

    p_sanction = subparsers.add_parser("sanction", help="Approve a pending dry-run by ID.")
    p_sanction.add_argument("hash", help="Dry-run ID (e.g., dr-20260516T143052-a3f8).")

    subparsers.add_parser("heresy", help="Rollback working tree to last-known-good tag.")

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
