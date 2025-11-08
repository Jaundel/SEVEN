# ============================================================
#  File: prompts.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Prompt templates and guardrails for classification and answers.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Prompt templates and guardrails for SEVEN's classifier and responder."""


def get_classification_prompt() -> None:
    """Build the classifier prompt for EASY/HARD/UNSAFE routing.

    Args:
        None: Inputs such as examples or policies will be sourced internally later.

    Returns:
        None: The template string or data structure will be provided in future iterations.

    Raises:
        None.

    TODO:
        * Encode concise instructions covering energy-aware priority.
        * Supply few-shot examples spanning EASY, HARD, and UNSAFE categories.
        * Include guardrails for rejecting disallowed or energy-intensive tasks.
        * Version prompts so router can audit historical changes.
    """
    pass


def get_answer_prompt() -> None:
    """Assemble answer-generation templates for local and cloud models.

    Args:
        None: Context such as user persona or tone will be wired in later.

    Returns:
        None: Template payloads will be returned once defined.

    Raises:
        None.

    TODO:
        * Provide system prompts for efficiency-focused assistance.
        * Tailor instructions per target model (Ollama vs. Groq/OpenAI).
        * Embed energy-reporting reminders for response formatting.
        * Offer hooks for localization or accessibility adjustments.
    """
    pass


if __name__ == "__main__":
    get_classification_prompt()
    get_answer_prompt()
