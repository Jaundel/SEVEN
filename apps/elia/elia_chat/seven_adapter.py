# ============================================================
#  File: seven_adapter.py
#  Project: SEVEN / Elia bridge
#  Description: Thin adapter that lets Elia call the SEVEN router.
#  Author(s): Team SEVEN
#  Date: 2025-11-18
# ============================================================
"""Adapter that wires Elia's chat UI to the SEVEN routing backend."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Sequence

from SEVEN.cloud_model import CloudModelResponse
from SEVEN.local_model import LocalModelResponse
from SEVEN.router import route_prompt

from elia_chat.models import ChatMessage
from elia_chat.runtime_config import RuntimeConfig


@dataclass
class SevenRouteResult:
    """Structured response returned to Elia after routing through SEVEN."""

    text: str
    model_name: str
    latency_s: float
    tokens_used: int | None
    route: str
    source_label: str
    timestamp: datetime.datetime


def call_seven_router(
    messages: Sequence[ChatMessage],
    runtime_config: RuntimeConfig,
    on_status_change: Optional[Callable[[str], None]] = None,
) -> SevenRouteResult:
    """Invoke SEVEN's router with the latest user prompt and context.

    Args:
        messages: Chat history including the latest user message.
        runtime_config: Model configuration and system prompt.
        on_status_change: Optional callback for routing status updates.
    """
    prompt_text = _latest_user_prompt(messages)
    if not prompt_text:
        raise ValueError("No user prompt available for SEVEN routing.")

    context_block = _conversation_context(messages[:-1])
    system_prompt = (runtime_config.system_prompt or "").strip()
    if context_block:
        formatted_context = (
            "Conversation recap (most recent messages):\n"
            f"{context_block}\n"
            "Use this context when responding to the latest user prompt."
        )
        system_prompt = (
            f"{system_prompt}\n\n{formatted_context}".strip()
            if system_prompt
            else formatted_context
        )

    result = route_prompt(
        prompt_text,
        system_prompt=system_prompt or None,
        temperature=runtime_config.selected_model.temperature,
        on_status_change=on_status_change,
    )

    route = "local" if isinstance(result, LocalModelResponse) else "cloud"
    label = _format_source_label(result.model, route)
    return SevenRouteResult(
        text=result.text,
        model_name=result.model,
        latency_s=result.latency_s,
        tokens_used=getattr(result, "tokens_used", None),
        route=route,
        source_label=label,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


def _latest_user_prompt(messages: Sequence[ChatMessage]) -> str:
    """Return the text content for the most recent user message."""
    for message in reversed(messages):
        if message.message.get("role") == "user":
            return _extract_text(message.message.get("content"))
    return ""


def _conversation_context(messages: Sequence[ChatMessage], limit: int = 6) -> str:
    """Format a rolling window of prior exchanges into a plain-text context."""
    lines: list[str] = []
    for chat_message in messages[-limit:]:
        role = chat_message.message.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = _extract_text(chat_message.message.get("content"))
        if not text:
            continue
        prefix = "User" if role == "user" else "SEVEN"
        lines.append(f"{prefix}: {text.strip()}")
    return "\n".join(lines)


def _extract_text(content: Any) -> str:
    """Normalize Litellm message content into a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            text = block.get("text") if isinstance(block, dict) else None
            if text:
                parts.append(str(text))
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def _format_source_label(model_name: str, route: str) -> str:
    """Return a concise label to display in the Elia UI."""
    route_display = "Local" if route == "local" else "Cloud"
    return f"SEVEN · {route_display} ({model_name})"


__all__ = ["call_seven_router", "SevenRouteResult"]
