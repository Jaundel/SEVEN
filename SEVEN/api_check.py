# ============================================================
#  File: api_check.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: API check helper that decides if real-time calls are needed before Lemonade.
#  Author(s): Team SEVEN
#  Date: 2025-11-12
# ============================================================
"""Bridge between the local Lemonade client and external real-time APIs."""

from __future__ import annotations

import logging
from typing import List, Tuple

# Support both package and direct script execution
try:
    from .heuristics import detect_api_intent
    from .api_tools import get_crypto_price, get_news, get_weather
    from .local_model import (
        LemonadeClientError,
        LocalModelResponse,
        ask_local,
    )
    from .prompts import build_local_prompt, get_system_prompt_local
except ImportError:
    from heuristics import detect_api_intent
    from api_tools import get_crypto_price, get_news, get_weather
    from local_model import (
        LemonadeClientError,
        LocalModelResponse,
        ask_local,
    )
    from prompts import build_local_prompt, get_system_prompt_local

LOGGER = logging.getLogger(__name__)


def _classify_api_need(prompt: str) -> Tuple[bool, List[str]]:
    """Decide if any APIs are needed using lightweight heuristics."""
    intent = detect_api_intent(prompt)
    if intent:
        return True, [intent]
    return False, []


def _collect_api_data(prompt: str, apis: List[str]) -> List[str]:
    """Call the required APIs and return their friendly summaries."""
    results: List[str] = []
    for api in apis:
        try:
            if api == "weather":
                results.append(f"Weather: {get_weather(prompt)}")
            elif api == "crypto":
                results.append(f"Crypto: {get_crypto_price(prompt)}")
            elif api == "news":
                results.append(f"News: {get_news(prompt)}")
            else:
                LOGGER.info("Unknown API intent '%s' ignored.", api)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("%s API failed: %s", api.capitalize(), exc)
            results.append(f"{api.capitalize()} API error: {exc}")
    return results


def run_api_check(
    prompt: str,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 512,  # Increased from 128 - prompts control brevity, not truncation
) -> LocalModelResponse:
    """Run the API check pipeline and augment the local model when needed."""
    # Use SEVEN Local identity if no custom system prompt provided
    final_system_prompt = system_prompt if system_prompt else get_system_prompt_local()

    needs_api, apis = _classify_api_need(prompt)
    if not needs_api:
        return ask_local(
            prompt,
            system_prompt=final_system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    api_results = _collect_api_data(prompt, apis)
    if api_results:
        api_context = "\n".join(api_results)

        # Build optimized prompt with API data embedded
        synthesis_prompt = build_local_prompt(
            user_query=prompt,
            api_data=api_context,
            allow_richer_context=False,  # Keep answers brief even with API data
        )

        try:
            return ask_local(
                synthesis_prompt,
                system_prompt=final_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LemonadeClientError as exc:
            LOGGER.warning("Synthesis via local model failed (%s). Returning API context.", exc)
            return LocalModelResponse(
                prompt=prompt,
                text=api_context,
                model="api-direct",
                latency_s=0.0,
                tokens_used=None,
                raw={},
            )

    LOGGER.info("APIs were requested but returned no data; falling back to local response.")

    # Build prompt without API data (with a note about unavailability in the query)
    fallback_query = f"{prompt}\n\n(Note: Real-time data APIs were unavailable, respond with general knowledge.)"
    fallback_prompt = build_local_prompt(
        user_query=fallback_query,
        allow_richer_context=False,
    )

    return ask_local(
        fallback_prompt,
        system_prompt=final_system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

