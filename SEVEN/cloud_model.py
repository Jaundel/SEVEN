# ============================================================
#  File: cloud_model.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Cloud inference adapter targeting Groq and OpenAI backends.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Cloud inference client for SEVEN's OpenAI fallback."""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from local_model import Spinner

LOGGER = logging.getLogger(__name__)
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class CloudModelError(RuntimeError):
    """Raised when the OpenAI cloud call fails."""


@dataclass
class CloudModelResponse:
    """Minimal normalized response for cloud completions."""

    prompt: str
    text: str
    model: str
    latency_s: float
    tokens_used: Optional[int]


def _openai_model() -> str:
    """Return the OpenAI model name from the environment."""
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def _openai_api_key() -> str:
    """Fetch the OpenAI API key or raise if missing."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise CloudModelError("Missing OPENAI_API_KEY environment variable.")
    return key


def ask_cloud(
    prompt: str,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> CloudModelResponse:
    """Forward prompts to OpenAI when local routing escalates.

    Args:
        prompt: Primary user prompt destined for the cloud.
        system_prompt: Optional instruction to prepend.
        temperature: Sampling temperature for the OpenAI completion.
        max_tokens: Maximum completion tokens requested.

    Returns:
        CloudModelResponse with normalized text, latency, and token counts.

    Raises:
        ValueError: If the prompt is empty.
        CloudModelError: When Groq rejects the request or the payload is invalid.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    spinner = Spinner("Processing via OpenAI")
    spinner.start()
    try:
        client = OpenAI(api_key=_openai_api_key())
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        start = time.perf_counter()
        try:
            completion = client.chat.completions.create(
                model=_openai_model(),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # OpenAI SDK raises generic errors
            raise CloudModelError(f"OpenAI request failed: {exc}") from exc
        latency = time.perf_counter() - start

        choice = completion.choices[0]
        text = (
            choice.message.content
            if choice.message and choice.message.content
            else ""
        )
        tokens_used = getattr(completion.usage, "total_tokens", None)

        return CloudModelResponse(
            prompt=prompt,
            text=text.strip(),
            model=completion.model or _openai_model(),
            latency_s=latency,
            tokens_used=tokens_used,
        )
    finally:
        spinner.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print('Usage: python cloud_model.py "your prompt here"')
        sys.exit(1)

    prompt_text = " ".join(sys.argv[1:])
    try:
        response = ask_cloud(prompt_text)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"OpenAI call failed: {exc}")
        sys.exit(1)

    print("=== OpenAI Cloud Test ===")
    print(f"Model:   {response.model}")
    print(f"Latency: {response.latency_s:.2f}s")
    print(f"Tokens:  {response.tokens_used if response.tokens_used is not None else 'N/A'}")
    print(f"Output:  {response.text}")
