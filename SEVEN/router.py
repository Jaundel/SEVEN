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

from api_check import run_api_check
from cloud_model import CloudModelError, CloudModelResponse, ask_cloud
from heuristics import classify_query_type, response_shows_uncertainty
from local_model import LemonadeClientError, LocalModelResponse, ask_local
from prompts import build_local_prompt, get_system_prompt_local

LOGGER = logging.getLogger(__name__)


def route_prompt(
    prompt: str,
    *,
    use_cloud: bool = False,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 512,  # Increased from 128 - prompts control brevity, not truncation
    enable_realtime_apis: bool = True,
    auto_escalate: bool = True,
) -> Union[LocalModelResponse, CloudModelResponse]:
    """Route prompts to local or cloud models with intelligent pre/post-routing.

    Args:
        prompt: User prompt to execute.
        use_cloud: If True, route to cloud. If False, try local first (default: False).
        system_prompt: Optional system instruction.
        temperature: Sampling temperature (0.0-1.0).
        max_tokens: Maximum tokens to generate.
        enable_realtime_apis: If True, augment local responses with real-time APIs when needed.
        auto_escalate: If True, retry with cloud if local shows uncertainty (default: True).

    Returns:
        LocalModelResponse or CloudModelResponse with .text, .model, .latency_s, etc.

    Raises:
        ValueError: If prompt is empty.
        CloudModelError: If cloud-only mode fails or all backends fail.

    Energy Optimizations:
        1. Pre-routing heuristics save inferences on obvious cloud-only queries
        2. Uses local model by default (Lemonade Server) for energy efficiency
        3. Post-routing validation catches model uncertainty and auto-escalates
        4. Falls back to cloud only when necessary
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    # Forced cloud mode (skip all local attempts)
    if use_cloud:
        LOGGER.info("Routing to cloud (use_cloud=True)")
        return ask_cloud(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Pre-routing heuristics (zero cost)
    classification = classify_query_type(prompt)
    LOGGER.info(
        "Pre-routing classification: %s (%s)",
        classification["route"],
        classification["reason"],
    )
    needs_realtime_data = classification["route"] == "API_CHECK"

    # Route to cloud if obviously too complex for local model
    if classification["route"] == "CLOUD":
        LOGGER.info("Pre-routing to cloud (complexity heuristic)")
        return ask_cloud(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Try local model (energy-efficient default)
    LOGGER.info("Routing to local model (energy-saving mode)")
    try:
        # Only use API pipeline if realtime data is actually needed
        if needs_realtime_data and enable_realtime_apis:
            LOGGER.info("Real-time data required; augmenting via API pipeline")
            local_response = run_api_check(
                prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            if needs_realtime_data and not enable_realtime_apis:
                LOGGER.info("Real-time data needed but APIs disabled; using local knowledge only")

            # Build optimized prompt with anti-hallucination instructions
            optimized_prompt = build_local_prompt(
                user_query=prompt,
                allow_richer_context=False,  # Force brief answers to reduce hallucination
            )

            # Use SEVEN Local identity as system prompt if none provided
            final_system_prompt = system_prompt if system_prompt else get_system_prompt_local()

            local_response = ask_local(
                optimized_prompt,
                system_prompt=final_system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Post-routing validation (zero cost)
        if auto_escalate and response_shows_uncertainty(local_response):
            LOGGER.info("Local response shows uncertainty, escalating to cloud")
            try:
                return ask_cloud(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except CloudModelError as cloud_exc:
                LOGGER.warning(
                    "Cloud escalation failed (%s), returning local response anyway",
                    cloud_exc,
                )
                return local_response

        return local_response

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
