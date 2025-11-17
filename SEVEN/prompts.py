# ============================================================
#  File: prompts.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Prompt templates for API synthesis and system instructions.
#  Author(s): Team SEVEN
#  Date: 2025-11-16
# ============================================================
"""Centralized prompt templates for SEVEN's energy-aware routing system.

This module contains all prompt engineering logic, making it easy to:
- Update prompts without touching routing code
- A/B test different prompt strategies
- Maintain consistency across the codebase
"""

from __future__ import annotations


def get_api_synthesis_prompt(api_data: str, user_query: str) -> str:
    """Generate prompt for synthesizing API data with user query.

    Used when real-time data (weather, news, crypto) needs to be
    combined with user's question using the local model.

    Args:
        api_data: Formatted string containing API results (e.g., "Weather: 15 deg C, sunny")
        user_query: Original user question (e.g., "What's the weather in Toronto?")

    Returns:
        Formatted prompt string ready to send to the model.

    Example:
        >>> api_data = "Weather: The weather in Paris is clear with 15 deg C."
        >>> query = "What's the weather in Paris?"
        >>> prompt = get_api_synthesis_prompt(api_data, query)
        >>> # Send prompt to model...
    """
    return f"""Based on this real-time data, answer the user's question naturally.

Real-time data:
{api_data}

User question: {user_query}

Provide a clear, concise answer using the freshest data above."""


def get_system_prompt_local() -> str:
    """System prompt optimized for small local models.

    Designed to encourage concise, accurate responses from
    energy-efficient local SLMs.

    Returns:
        System prompt string for local model initialization.
    """
    return (
        "You are a helpful AI assistant. "
        "Be concise, accurate, and energy-efficient in your responses. "
        "If you don't know something, say so clearly."
    )


def get_system_prompt_cloud() -> str:
    """System prompt for cloud models (OpenAI, Groq).

    Can be more detailed since cloud models have higher capacity
    and we're already paying for the inference.

    Returns:
        System prompt string for cloud model initialization.
    """
    return (
        "You are an energy-efficient AI assistant. "
        "Provide accurate, well-structured, and helpful answers. "
        "Be thorough but concise. "
        "If you're uncertain about something, express your uncertainty clearly."
    )


def build_local_prompt(
    user_query: str,
    api_data: str | None = None,
    risk_hint: str | None = None,
    allow_richer_context: bool = False,
    escalate_immediately: bool = False,
) -> str:
    """Construct a context-aware prompt for the local SLM.

    Args:
        user_query: The user's raw query text.
        api_data: Optional block of real-time data to ground the answer.
        risk_hint: Optional note about why this topic is risky (e.g., "pop culture").
        allow_richer_context: When True, permit slightly longer answers (up to 3 sentences).
        escalate_immediately: When True, force the model to decline so heuristics can escalate.

    Returns:
        A formatted prompt string ready to send to the local model.
    """
    system_header = (
        "You are SEVEN's local assistant. "
        "Prioritize accuracy, honesty, and energy efficiency."
    )

    if escalate_immediately:
        return (
            f"{system_header}\n\n"
            "This query exceeds the safe local knowledge boundary.\n"
            'Respond exactly with: "I\'m not sure - please use the cloud model."\n\n'
            f"User question: {user_query}"
        )

    instructions: list[str] = []
    if allow_richer_context:
        instructions.append(
            "You may use up to three sentences when the answer is obvious from stable public knowledge."
        )
    else:
        instructions.append("Respond in one short sentence to avoid drifting into speculation.")

    if risk_hint:
        instructions.append(
            f"This topic ({risk_hint}) is prone to hallucinations; keep the answer minimal and stick to clear facts."
        )

    instructions.extend(
        [
            'Only answer if the result follows directly from the question or the API_DATA section. Otherwise reply "I\'m not sure."',
            "Never invent facts about people, organizations, or current events.",
        ]
    )

    guidelines = "\n".join(f"- {rule}" for rule in instructions)
    api_block = ""
    if api_data and api_data.strip():
        api_block = f"API_DATA:\n{api_data.strip()}\n\n"

    prompt = (
        f"{system_header}\n\n"
        "Guidelines:\n"
        f"{guidelines}\n\n"
        f"{api_block}"
        f"User question: {user_query}"
    )
    return prompt


def get_fallback_note() -> str:
    """Message to append when APIs are unavailable.

    Returns:
        Note explaining that real-time data isn't available.
    """
    return "(Note: Real-time data APIs were unavailable, responding with general knowledge.)"
