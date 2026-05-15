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
import os
import re
import subprocess
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

# --- Model tag config ---
# Plan 05: bilingual Ollama call uses the SAME tag set the runtime uses.
OLLAMA_PRIMARY = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
OLLAMA_LIGHT = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")

# Cyrillic block (Russian alphabet incl. Ё / ё): U+0400 – U+04FF.
# Latin: basic A-Z / a-z. These are deliberately loose — the smoke test asserts
# only that AT LEAST ONE character of the target script appears in the reply.
# This matches 01-VALIDATION.md's "basic char-class heuristic" — a mixed-script
# reply (e.g. Russian with embedded English tech terms) still PASSes for RU.
_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


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


def check_models_pulled() -> str:
    """Precondition: both Ollama models referenced by the runtime must be
    present in ``ollama list``. Fails loud with the exact ``ollama pull`` lines
    needed to remediate. Owned by Plan 05.

    Runs ONLY in the full suite — ``--static-only`` skips this (so the static
    gate stays a 3-second sanity check that does not require Ollama).
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        print(
            f"{FAIL} check_models_pulled: 'ollama' CLI not found in PATH. "
            f"Install with: brew install ollama"
        )
        return "fail"
    except subprocess.TimeoutExpired:
        print(
            f"{FAIL} check_models_pulled: 'ollama list' timed out after 10s. "
            f"Is the Ollama server running? Try: ollama serve"
        )
        return "fail"

    output = result.stdout or ""
    missing = [tag for tag in (OLLAMA_PRIMARY, OLLAMA_LIGHT) if tag not in output]
    if missing:
        print(f"{FAIL} check_models_pulled: missing models: {missing}")
        print("  Run before retrying:")
        for tag in missing:
            print(f"    ollama pull {tag}")
        return "fail"
    print(f"{PASS} check_models_pulled: both Ollama models present in `ollama list`")
    return "pass"


def _extract_content(response) -> str | None:
    """Best-effort extraction of the assistant text from LLMClient.chat() return.

    heretek.llm.LLMClient.chat() returns a tuple (msg_dict, usage_dict) where
    msg_dict has a 'content' key (post-Plan-04). The fallbacks below cover the
    less likely upstream shapes (raw OpenAI object, raw choices list, single
    tuple) so this helper survives small contract drift.
    """
    # Plan-04 canonical shape: (msg_dict, usage_dict)
    if isinstance(response, tuple) and response:
        first = response[0]
        if isinstance(first, dict):
            content = first.get("content")
            if isinstance(content, str):
                return content
        if isinstance(first, str):
            return first
    # OpenAI SDK object — used pre-Plan-04 or by future callers that bypass chat()
    try:
        return response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError):
        pass
    # Plain dict from .model_dump()
    try:
        return response["choices"][0]["message"]["content"]
    except (TypeError, IndexError, KeyError):
        pass
    return None


def test_bilingual_ollama_reply() -> str:
    """LLM-06 verification: RU prompt -> RU reply, EN prompt -> EN reply
    via heretek.llm.LLMClient against local Ollama. Owned by Plan 05.
    """
    try:
        from heretek.llm import LLMClient
    except ImportError as e:
        print(f"{FAIL} test_bilingual_ollama_reply: cannot import heretek.llm.LLMClient: {e}")
        return "fail"

    try:
        client = LLMClient()
    except Exception as e:
        print(f"{FAIL} test_bilingual_ollama_reply: LLMClient() constructor raised: {type(e).__name__}: {e}")
        return "fail"

    prompts = [
        ("RU", "ответь по-русски одним коротким предложением, без перевода", _CYRILLIC_RE),
        ("EN", "respond in one short English sentence, no translation", _LATIN_RE),
    ]

    all_pass = True
    for lang, prompt, script_re in prompts:
        try:
            response = client.chat(
                model=OLLAMA_PRIMARY,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            err_name = type(e).__name__
            print(
                f"{FAIL} test_bilingual_ollama_reply [{lang}]: chat() raised: "
                f"{err_name}: {e}"
            )
            # Hint on the most common cause: Ollama server crashed/OOM'd while
            # loading a large model. The 24GB qwen3.6:35b-a3b-q4_K_M can OOM
            # on a 32GB host under memory pressure. Probe Ollama liveness so
            # the user knows whether to restart the server or pick a smaller
            # model via OLLAMA_MODEL=qwen3:4b.
            if "Connection" in err_name or "Connection" in str(e):
                try:
                    probe = subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "-m", "5", "http://127.0.0.1:11434/api/tags"],
                        capture_output=True, text=True, timeout=10,
                    )
                    code = (probe.stdout or "").strip()
                except Exception:
                    code = "unknown"
                if code != "200":
                    print(
                        f"  Hint: Ollama is not responding on 127.0.0.1:11434 "
                        f"(probe={code}). The server may have OOM-crashed while "
                        f"loading {OLLAMA_PRIMARY}. Retry with: "
                        f"`ollama serve &` then "
                        f"`OLLAMA_MODEL={OLLAMA_LIGHT} python scripts/smoke_test.py` "
                        f"(use light model on low-RAM hosts)."
                    )
            all_pass = False
            continue

        content = _extract_content(response)
        if not content:
            print(
                f"{FAIL} test_bilingual_ollama_reply [{lang}]: empty/unrecognized "
                f"response shape: {type(response).__name__}"
            )
            all_pass = False
            continue

        if not script_re.search(content):
            preview = content[:120].replace("\n", " ")
            print(
                f"{FAIL} test_bilingual_ollama_reply [{lang}]: reply lacks "
                f"{lang} script chars: {preview!r}"
            )
            all_pass = False
            continue

        preview = content[:120].replace("\n", " ")
        print(
            f"{PASS} test_bilingual_ollama_reply [{lang}]: got {len(content)} chars: "
            f"{preview!r}"
        )

    return "pass" if all_pass else "fail"


# Static subtests run with --static-only (no Ollama dependency, ~3s).
# Full subtests include the Ollama precondition + the real bilingual call.
STATIC_SUBTESTS = [test_package_rename, test_no_cloud_hosts]
FULL_SUBTESTS = STATIC_SUBTESTS + [check_models_pulled, test_bilingual_ollama_reply]


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
