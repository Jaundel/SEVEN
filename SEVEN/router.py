# ============================================================
#  File: router.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Prompt classification and routing to local or cloud models.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Prompt classification and routing logic for SEVEN's energy-aware workflow.

Usage:
    from router import route_prompt

    response = route_prompt("What is 2+2?")
    print(response.text)  # Uses local model for simple queries

    response = route_prompt("Write a detailed essay on AI", use_cloud=True)
    print(response.text)  # Forces cloud model for complex tasks
"""

from __future__ import annotations

import logging
import sys
from typing import Optional, Union

from cloud_model import CloudModelError, CloudModelResponse, ask_cloud
from local_model import LemonadeClientError, LocalModelResponse, ask_local

LOGGER = logging.getLogger(__name__)


def route_prompt(
    prompt: str,
    *,
    use_cloud: bool = False,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 128,
) -> Union[LocalModelResponse, CloudModelResponse]:
    """Route prompts to local or cloud models with automatic fallback.

    Args:
        prompt: User prompt to execute.
        use_cloud: If True, route to cloud. If False, try local first (default: False).
        system_prompt: Optional system instruction.
        temperature: Sampling temperature (0.0-1.0).
        max_tokens: Maximum tokens to generate.

    Returns:
        LocalModelResponse or CloudModelResponse with .text, .model, .latency_s, etc.

    Raises:
        ValueError: If prompt is empty.
        CloudModelError: If cloud-only mode fails or all backends fail.

    Energy Savings:
        By default, uses local model (Lemonade Server) for energy efficiency.
        Falls back to cloud if local fails. Set use_cloud=True to skip local.

    TODO:
        * Add automatic complexity classification (EASY/HARD) using heuristics.
        * Integrate prompts.get_classification_prompt for ML-based routing.
        * Track energy metrics and routing decisions for analytics.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    # Route to cloud directly if requested
    if use_cloud:
        LOGGER.info("Routing to cloud (use_cloud=True)")
        return ask_cloud(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Default: Try local first (energy-efficient), fallback to cloud
    LOGGER.info("Routing to local model (energy-saving mode)")
    try:
        return ask_local(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except LemonadeClientError as exc:
        LOGGER.warning("Local model failed (%s). Falling back to cloud.", exc)
        try:
            return ask_cloud(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except CloudModelError as cloud_exc:
            raise CloudModelError(
                f"All backends failed. Local: {exc}, Cloud: {cloud_exc}"
            ) from cloud_exc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print('Usage: python router.py "your prompt here"')
        print('       python router.py "your prompt" --cloud  # Force cloud')
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    force_cloud = "--cloud" in args
    if force_cloud:
        args.remove("--cloud")

    test_prompt = " ".join(args)

    try:
        result = route_prompt(test_prompt, use_cloud=force_cloud)
        print("\n=== SEVEN Router ===")
        print(f"Model:   {result.model}")
        print(f"Latency: {result.latency_s:.2f}s")
        print(f"Tokens:  {result.tokens_used if result.tokens_used else 'N/A'}")
        print(f"\nResponse:\n{result.text}")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Routing failed: {exc}")
        sys.exit(1)
