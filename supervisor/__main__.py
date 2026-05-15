#!/usr/bin/env python3
"""supervisor/__main__.py — Local CLI entry point for Heretek supervisor.

Replaces upstream's cloud-only launcher script. For local macOS use: loads
.env from the project root, then dispatches to one of the supervisor's run
modes. Run via:

    python -m supervisor              # boot the local Heretek runtime (Phase 1: stub)
    python -m supervisor --help       # print usage
    python -m supervisor --smoke      # load supervisor modules without starting Telegram loop

Background (Plan 01-02 of phase 01-foundation-local-llm):
    At v6.2.0 upstream, ``supervisor/__init__.py`` is empty and there is no
    ``run()``, ``start()``, or ``main()`` entry function in the supervisor
    package. The entire boot sequence lives at module scope in the upstream
    launcher script and is gated on cloud-LLM secrets and remote-storage
    mounting — none of which work on a local macOS host.

    Plan 03 strips the cloud-specific modules; Plan 04 swaps the LLM client
    to Ollama; Plan 05 wires the actual local boot loop in here. Until then,
    the default ``python -m supervisor`` invocation prints a clear
    "not-yet-wired" notice and exits with code 2.

    ``--help`` and ``--smoke`` already work and gate the Plan 02 acceptance
    criteria.
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
        # Plan 05 will fully wire this; for Plan 02 we just verify the package
        # imports cleanly without side-effects.
        try:
            import supervisor  # noqa: F401
            import supervisor.state  # noqa: F401
            import supervisor.workers  # noqa: F401
        except ImportError as exc:
            print(f"[supervisor] smoke FAIL: {exc}", file=sys.stderr)
            return 1
        print("[supervisor] smoke OK: supervisor.{state,workers} import cleanly")
        return 0

    # Full boot path. Upstream v6.2.0 puts the entire boot sequence at module
    # scope in the cloud launcher script and requires cloud-LLM secrets and
    # remote-storage mounting — neither of which work locally. Plan 03 (strip)
    # and Plan 04 (LLM swap) will produce a clean local boot path that lives
    # here. Until then we print the status and exit 2.
    print(
        "[supervisor] full boot not yet wired. Phase 01 status:\n"
        "  - Plan 02 (this plan): supervisor/__main__.py shell + --help + --smoke\n"
        "  - Plan 03:             strip cloud-LLM modules, GitHub tools, multi-model review\n"
        "  - Plan 04:             swap heretek/llm.py to Ollama; replace cloud-LLM key gate\n"
        "  - Plan 05:             wire the actual local main loop here (replaces upstream launcher)\n"
        "Run `python -m supervisor --smoke` to verify package imports.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
