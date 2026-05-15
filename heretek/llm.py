"""
Heretek — LLM-клиент.

Plan 04 swap: LLMClient now defaults to local Ollama
(http://localhost:11434/v1 with api_key="ollama"). The OpenAI Python SDK is
wire-compatible with Ollama's /v1/chat/completions endpoint, so only the
constructor defaults change; the chat()/vision_query() bodies are preserved.

Model env vars normalized to OLLAMA_* (was OUROBOROS_*):
    OLLAMA_MODEL          primary model    (default: qwen3.6:35b-a3b-q4_K_M)
    OLLAMA_MODEL_LIGHT    background model (default: qwen3:4b)

A best-effort JSONL token logger (_log_tokens) appends one
{ts, model, prompt_tokens, completion_tokens, total} record to
logs/tokens.jsonl after every chat() call. Logging failures are swallowed —
the LLM call path must never break on disk I/O.
"""

from __future__ import annotations

import datetime as _datetime
import json as _json
import logging
import os
import pathlib as _pathlib
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSONL token logger (Plan 04: FORK-04)
# ---------------------------------------------------------------------------

_TOKENS_LOG_PATH = _pathlib.Path("logs/tokens.jsonl")


def _log_tokens(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Append one JSONL record to logs/tokens.jsonl after each LLM call.

    Best-effort: any I/O exception is swallowed so the LLM call path never
    breaks on logging failure. Schema:
        {"ts": "<iso-utc-Z>", "model": "<tag>",
         "prompt_tokens": <int>, "completion_tokens": <int>, "total": <int>}
    """
    try:
        _TOKENS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        prompt = int(prompt_tokens or 0)
        completion = int(completion_tokens or 0)
        record = {
            "ts": _datetime.datetime.utcnow().isoformat() + "Z",
            "model": model,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total": prompt + completion,
        }
        with _TOKENS_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(record) + "\n")
    except OSError:
        # Logging is best-effort; never break the LLM call path.
        pass


def normalize_reasoning_effort(value: str, default: str = "medium") -> str:
    allowed = {"none", "minimal", "low", "medium", "high", "xhigh"}
    v = str(value or "").strip().lower()
    return v if v in allowed else default


def reasoning_rank(value: str) -> int:
    order = {"none": 0, "minimal": 1, "low": 2, "medium": 3, "high": 4, "xhigh": 5}
    return int(order.get(str(value or "").strip().lower(), 3))


def add_usage(total: Dict[str, Any], usage: Dict[str, Any]) -> None:
    """Accumulate usage from one LLM call into a running total."""
    for k in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens", "cache_write_tokens"):
        total[k] = int(total.get(k) or 0) + int(usage.get(k) or 0)
    if usage.get("cost"):
        total["cost"] = float(total.get("cost") or 0) + float(usage["cost"])


class LLMClient:
    """LLM client wired to local Ollama (OpenAI-compatible /v1 endpoint).

    Defaults route to http://localhost:11434/v1 with api_key="ollama".
    Override via OLLAMA_BASE_URL / OLLAMA_API_KEY env vars, or pass explicit
    constructor arguments.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        # Ollama defaults. Ollama ignores the api_key but the OpenAI SDK
        # requires a non-empty string — the literal "ollama" is conventional.
        self._api_key = api_key or os.environ.get("OLLAMA_API_KEY", "ollama")
        self._base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        )
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self._base_url,
                api_key=self._api_key,
            )
        return self._client

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_effort: str = "medium",
        max_tokens: int = 16384,
        tool_choice: str = "auto",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Один вызов LLM. Возвращает: (response_message_dict, usage_dict)."""
        client = self._get_client()
        effort = normalize_reasoning_effort(reasoning_effort)

        extra_body: Dict[str, Any] = {
            "reasoning": {"effort": effort, "exclude": True},
        }

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "extra_body": extra_body,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        resp = client.chat.completions.create(**kwargs)
        resp_dict = resp.model_dump()
        usage = resp_dict.get("usage") or {}
        choices = resp_dict.get("choices") or [{}]
        msg = (choices[0] if choices else {}).get("message") or {}

        # Extract cached_tokens from prompt_tokens_details if available
        if not usage.get("cached_tokens"):
            prompt_details = usage.get("prompt_tokens_details") or {}
            if isinstance(prompt_details, dict) and prompt_details.get("cached_tokens"):
                usage["cached_tokens"] = int(prompt_details["cached_tokens"])

        # Extract cache_write_tokens from prompt_tokens_details if available
        if not usage.get("cache_write_tokens"):
            prompt_details_for_write = usage.get("prompt_tokens_details") or {}
            if isinstance(prompt_details_for_write, dict):
                cache_write = (prompt_details_for_write.get("cache_write_tokens")
                              or prompt_details_for_write.get("cache_creation_tokens")
                              or prompt_details_for_write.get("cache_creation_input_tokens"))
                if cache_write:
                    usage["cache_write_tokens"] = int(cache_write)

        # JSONL token log (best-effort — never break the LLM call path).
        try:
            _log_tokens(
                model=model,
                prompt_tokens=int(usage.get("prompt_tokens") or 0),
                completion_tokens=int(usage.get("completion_tokens") or 0),
            )
        except Exception:
            log.debug("Token logging failed", exc_info=True)

        return msg, usage

    def vision_query(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        model: str = "",
        max_tokens: int = 1024,
        reasoning_effort: str = "low",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Send a vision query to an LLM. Lightweight — no tools, no loop.

        Args:
            prompt: Text instruction for the model
            images: List of image dicts. Each dict must have either:
                - {"url": "https://..."} — for URL images
                - {"base64": "<b64>", "mime": "image/png"} — for base64 images
            model: VLM-capable model ID (Plan 04/05 will plumb local default)
            max_tokens: Max response tokens
            reasoning_effort: Effort level

        Returns:
            (text_response, usage_dict)
        """
        # Build multipart content
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images:
            if "url" in img:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img["url"]},
                })
            elif "base64" in img:
                mime = img.get("mime", "image/png")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{img['base64']}"},
                })
            else:
                log.warning("vision_query: skipping image with unknown format: %s", list(img.keys()))

        messages = [{"role": "user", "content": content}]
        response_msg, usage = self.chat(
            messages=messages,
            model=model,
            tools=None,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
        text = response_msg.get("content") or ""
        return text, usage

    def default_model(self) -> str:
        """Return the primary Ollama model tag from OLLAMA_MODEL env var."""
        return os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")

    def available_models(self) -> List[str]:
        """Return list of available Ollama model tags (de-duped, in order)."""
        models_dict = available_models()
        seen = set()
        out: List[str] = []
        for tag in (models_dict["main"], models_dict["code"], models_dict["light"]):
            if tag and tag not in seen:
                seen.add(tag)
                out.append(tag)
        return out


# ---------------------------------------------------------------------------
# Module-level model registry (Plan 04: LLM-02, LLM-03)
# ---------------------------------------------------------------------------

def available_models() -> Dict[str, str]:
    """Return the Ollama model tag set this Heretek install is wired to use.

    Heretek runs everything on Qwen — no separate code-specialized model —
    so "code" aliases to "main" to keep any upstream caller happy without
    requiring a separate model pull.
    """
    main = os.environ.get("OLLAMA_MODEL", "qwen3.6:35b-a3b-q4_K_M")
    light = os.environ.get("OLLAMA_MODEL_LIGHT", "qwen3:4b")
    return {
        "main": main,
        "code": main,
        "light": light,
    }
