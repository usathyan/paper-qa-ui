#!/usr/bin/env python3
"""
Quick connectivity test for LiteLLM to ensure an LLM call succeeds independently of the UI.

Usage:
  # For OpenRouter (recommended here)
  export OPENROUTER_API_KEY=sk-or-...
  python scripts/test_litellm.py --model openrouter/google/gemini-2.5-flash-lite --question "What is PICALM's role in AD?"

  # Or use another supported provider/model and key
  export OPENAI_API_KEY=sk-...
  python scripts/test_litellm.py --model gpt-4o-mini --question "..."

Notes:
- For OpenRouter models, this script sets api_base to https://openrouter.ai/api/v1
- Timeouts are set so failures return fast with a readable message
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, List

import litellm


def extract_content(resp: Any) -> str:
    """Best-effort extraction of content across LiteLLM response shapes."""
    try:
        # OpenAI-style dict
        if isinstance(resp, dict):
            choices = resp.get("choices")
            if isinstance(choices, list) and choices:
                message_any: Any = choices[0].get("message")
                if isinstance(message_any, dict) and isinstance(
                    message_any.get("content"), str
                ):
                    return str(message_any["content"])
            # Direct content (some providers)
            content_direct: Any = resp.get("content")
            if isinstance(content_direct, str):
                return str(content_direct)
        # Attr-style
        choices2: Any = getattr(resp, "choices", None)
        if isinstance(choices2, list) and choices2:
            message2: Any = getattr(choices2[0], "message", None)
            if isinstance(message2, dict):
                c = message2.get("content")
                if isinstance(c, str):
                    return c
            c2 = getattr(message2, "content", None)
            if isinstance(c2, str):
                return c2
        content_attr = getattr(resp, "content", None)
        if isinstance(content_attr, str):
            return str(content_attr)
    except Exception:
        pass
    return ""


def configure_litellm(model: str) -> None:
    # Use OPENROUTER_API_KEY by default, else OPENAI_API_KEY / provider-specific
    api_key = (
        os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("LITELLM_API_KEY")
    )
    if not api_key:
        print(
            "ERROR: Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)
    litellm.api_key = api_key
    if model.startswith("openrouter/"):
        # Route via OpenRouter
        litellm.api_base = "https://openrouter.ai/api/v1"


def run_sync(model: str, question: str, timeout: float) -> int:
    configure_litellm(model)
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Return a very short answer.",
        },
        {"role": "user", "content": f"Question: {question}"},
    ]
    t0 = time.time()
    print(f"INFO: calling litellm.completion(model={model})", flush=True)
    try:
        resp = litellm.completion(model=model, messages=messages, timeout=timeout)
    except Exception as e:
        print(f"ERROR: completion failed: {e}", file=sys.stderr)
        return 2
    content = extract_content(resp)
    elapsed = time.time() - t0
    print(f"INFO: success in {elapsed:.2f}s\n---\n{content}\n---")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Quick LiteLLM connectivity test")
    ap.add_argument(
        "--model",
        default=os.getenv("LITELLM_MODEL", "openrouter/google/gemini-2.5-flash-lite"),
    )
    ap.add_argument(
        "--question",
        default="Rewrite this question to be concise and retrieval-ready: What is PICALM's role in AD?",
    )
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()
    return run_sync(args.model, args.question, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
