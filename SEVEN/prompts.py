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


def get_fallback_note() -> str:
    """Message to append when APIs are unavailable.

    Returns:
        Note explaining that real-time data isn't available.
    """
    return "(Note: Real-time data APIs were unavailable, responding with general knowledge.)"
