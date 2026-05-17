#!/usr/bin/env python3
"""supervisor/__main__.py — Local CLI entry point for Heretek supervisor.

Replaces upstream's cloud-only launcher script. For local macOS use: loads
.env from the project root, then dispatches to one of the supervisor's run
modes. Run via:

    python -m supervisor              # boot the local Heretek runtime
    python -m supervisor --help       # print usage
    python -m supervisor --smoke      # load supervisor modules without starting Telegram loop

Phase 4: env validation + boot delegation (Plan 04-01).
    Plan 04-01 added env validation + data-root resolution; Plan 04-03 lands
    the polling loop in supervisor/boot.py.

    ``--help`` and ``--smoke`` already work and gate the Plan 01-02 acceptance
    criteria (preserved, not modified by this plan).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_env() -> None:
    """Load .env from the project root if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print(
            "[supervisor] python-dotenv not installed; skipping .env load. "
            "Run: pip install python-dotenv",
            file=sys.stderr,
        )
        return
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[supervisor] loaded {env_path}")
    else:
        print(f"[supervisor] no .env at {env_path}; using shell environment only")


def _print_banner() -> None:
    primary = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
    light = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    print(f"[supervisor] heretek primary={primary} light={light} base={base}")
    owner_id = os.environ.get("HERETEK_OWNER_USER_ID", "<unset>")
    owner_handle = os.environ.get("HERETEK_OWNER_HANDLE", "my Tech-Priest")
    print(f"[supervisor] owner_id={owner_id} owner_handle={owner_handle}")


def _validate_required_env() -> None:
    """Fail-loud validation of required env vars. Called AFTER _load_env().

    Raises SystemExit with a clear message if any required var is unset
    or malformed. Phase 4 owner-only TG bot cannot boot without these.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print(
            "[supervisor] FATAL: TELEGRAM_BOT_TOKEN required (get from @BotFather, "
            "store in .env). See CLAUDE.md §8.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    raw_user_id = os.environ.get("HERETEK_OWNER_USER_ID", "").strip()
    if not raw_user_id:
        print(
            "[supervisor] FATAL: HERETEK_OWNER_USER_ID required (your TG user ID "
            "from @userinfobot, integer). See CLAUDE.md §8.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    try:
        int(raw_user_id)
    except ValueError:
        print(
            f"[supervisor] FATAL: HERETEK_OWNER_USER_ID must be an integer; "
            f"got {raw_user_id!r}.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _resolve_data_root() -> Path:
    """Resolve HERETEK_DATA_ROOT with project-root fallback + boot log line.

    Soft-default: if unset, use the project root (parent of supervisor/).
    Prints a one-liner boot log so the owner sees what got picked.
    """
    raw = os.environ.get("HERETEK_DATA_ROOT", "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
        print(f"[supervisor] HERETEK_DATA_ROOT={root}")
    else:
        root = Path(__file__).resolve().parent.parent
        print(
            f"[supervisor] using repo-root data store at {root}; "
            "set HERETEK_DATA_ROOT to override"
        )
    # Ensure the standard subdirs exist
    for sub in ("logs", "state", "archive", "locks", "memory"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m supervisor",
        description="Heretek supervisor — local boot entry point (replaces colab_launcher.py)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke mode: import supervisor modules without starting the Telegram loop. "
             "Used by scripts/smoke_test.py after Plan 04 wires Ollama.",
    )
    args = parser.parse_args(argv)

    _load_env()
    _print_banner()

    if args.smoke:
        # Verify the package imports cleanly without side-effects.
        try:
            import supervisor  # noqa: F401
            import supervisor.state  # noqa: F401
            import supervisor.workers  # noqa: F401
        except ImportError as exc:
            print(f"[supervisor] smoke FAIL: {exc}", file=sys.stderr)
            return 1
        print("[supervisor] smoke OK: supervisor.{state,workers} import cleanly")
        return 0

    # Validate required env (fail-loud) — Phase 4 cannot boot without these.
    _validate_required_env()

    # Resolve data root + ensure subdirs exist.
    data_root = _resolve_data_root()

    # Delegate the full boot sequence to supervisor.boot.
    # boot.py exists as of Plan 04-03 — this is now a hard import.
    from supervisor import boot
    return boot.run(data_root=data_root)


if __name__ == "__main__":
    sys.exit(main())
