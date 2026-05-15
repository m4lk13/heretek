#!/usr/bin/env python3
"""scripts/smoke_test.py — Phase 1 verification harness.

Wave 0 scaffold: subtests return SKIP (exit 2) until the plan that owns the
requirement flips them to a real check.

Usage:
    python scripts/smoke_test.py                  # full suite (includes Ollama-dependent tests)
    python scripts/smoke_test.py --static-only    # static checks only (no Ollama, ~3s)

Exit codes:
    0  all subtests PASS (or all run subtests PASS with no FAIL)
    1  at least one FAIL
    2  reserved (per-subtest SKIP marker; never the final exit code)
"""
from __future__ import annotations

import argparse
import sys

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

# Each subtest returns one of: "pass", "fail", "skip".


def test_package_rename() -> str:
    """FORK-02 verification: import heretek succeeds; import heretek fails.

    Owned by Plan 02 (package rename). Currently SKIP.
    """
    print(f"{SKIP} test_package_rename — not yet implemented (Plan 02 will flip this)")
    return "skip"


def test_no_cloud_hosts() -> str:
    """LLM-01 + LLM-05 verification: no openrouter.ai / api.openai.com /
    api.anthropic.com strings or cloud-LLM key references inside heretek/.

    Owned by Plan 03 (strip) + Plan 04 (LLM swap). Currently SKIP.
    """
    print(f"{SKIP} test_no_cloud_hosts — not yet implemented (Plan 03/04 will flip this)")
    return "skip"


def test_bilingual_ollama_reply() -> str:
    """LLM-06 verification: RU prompt → RU reply, EN prompt → EN reply
    through heretek.llm against local Ollama. Owned by Plan 05. Currently SKIP.
    """
    print(f"{SKIP} test_bilingual_ollama_reply — not yet implemented (Plan 05 will flip this)")
    return "skip"


STATIC_SUBTESTS = [test_package_rename, test_no_cloud_hosts]
FULL_SUBTESTS = STATIC_SUBTESTS + [test_bilingual_ollama_reply]


def main() -> int:
    parser = argparse.ArgumentParser(description="Heretek Phase 1 smoke test")
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Run only static subtests (no Ollama dependency, ~3s)",
    )
    args = parser.parse_args()

    subtests = STATIC_SUBTESTS if args.static_only else FULL_SUBTESTS

    results: list[tuple[str, str]] = []
    for fn in subtests:
        outcome = fn()
        results.append((fn.__name__, outcome))

    # Summary
    n_pass = sum(1 for _, o in results if o == "pass")
    n_fail = sum(1 for _, o in results if o == "fail")
    n_skip = sum(1 for _, o in results if o == "skip")
    print()
    print(f"Summary: {n_pass} pass · {n_fail} fail · {n_skip} skip · {len(results)} total")

    # Exit 1 if any FAIL; otherwise 0 (SKIP is acceptable until plan ships)
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
