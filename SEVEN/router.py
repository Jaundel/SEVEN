# ============================================================
#  File: router.py
#  Project: SEVEN (Sustainable Energy via Efficient Neural-routing)
#  Description: Prompt classification and routing to local or cloud models.
#  Author(s): Team SEVEN
#  Date: 2025-11-07
# ============================================================
"""Prompt classification and routing logic for SEVEN's energy-aware workflow."""


def route_prompt() -> None:
    """Classify prompts and select the appropriate inference target.

    Args:
        None: Router inputs will include prompt text and context in future iterations.

    Returns:
        None: Routing decisions and responses will be returned upstream later.

    Raises:
        None.

    TODO:
        * Use prompts.get_classification_prompt to label EASY/HARD/UNSAFE cases.
        * Dispatch EASY prompts to local_model.ask_local for energy savings.
        * Escalate HARD prompts to cloud_model.ask_cloud with metadata logging.
        * Filter UNSAFE prompts and record rejection reasons for audits.
    """
    pass


if __name__ == "__main__":
    route_prompt()
