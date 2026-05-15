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
from pathlib import Path

# When invoked as `python scripts/smoke_test.py`, sys.path[0] is the scripts/
# directory, not the project root — so `import heretek` would fail with
# ModuleNotFoundError. Prepend the project root explicitly so the harness
# behaves the same regardless of cwd.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"

# Each subtest returns one of: "pass", "fail", "skip".


def test_package_rename() -> str:
    """FORK-02 verification: ``import heretek`` succeeds; ``import ouroboros`` fails.

    Owned by Plan 02 (package rename). Flipped to a real check in 01-02.
    """
    try:
        import heretek  # noqa: F401
    except ImportError as e:
        print(f"{FAIL} test_package_rename: `import heretek` raised: {e}")
        return "fail"
    try:
        import ouroboros  # noqa: F401
    except ImportError:
        print(
            f"{PASS} test_package_rename: import heretek OK; "
            f"import ouroboros raises ModuleNotFoundError as expected"
        )
        return "pass"
    print(f"{FAIL} test_package_rename: `import ouroboros` still succeeds — rename incomplete")
    return "fail"


def test_no_cloud_hosts() -> str:
    """LLM-01 + LLM-05 verification: no cloud-LLM host strings or env var
    names anywhere in the heretek/ or supervisor/ source trees.

    Owned by Plan 03 (strip — static check) + Plan 04 (runtime check via
    test_bilingual_ollama_reply).
    """
    import re

    pattern = re.compile(
        r"openrouter\.ai|api\.openai\.com|api\.anthropic\.com|"
        r"OPENROUTER_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY"
    )
    hits: list[str] = []
    for root in ("heretek", "supervisor"):
        root_path = Path(root)
        if not root_path.exists():
            continue
        for path in root_path.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"  {path}:{i}: {line.strip()}")

    if hits:
        print(f"{FAIL} test_no_cloud_hosts: cloud LLM references found:")
        for h in hits:
            print(h)
        return "fail"
    print(f"{PASS} test_no_cloud_hosts: no cloud LLM references in heretek/ or supervisor/")
    return "pass"


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
