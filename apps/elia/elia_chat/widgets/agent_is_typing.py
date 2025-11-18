from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import Reactive, reactive
from textual.widgets import LoadingIndicator, Label


# Map routing status codes to user-friendly messages
STATUS_MESSAGES = {
    "local_starting": "SEVEN Local is working...",
    "api_fetching": "Fetching real-time data...",
    "local_uncertain_escalating": "Escalating to cloud due to uncertainty...",
    "cloud_processing": "SEVEN Cloud is processing...",
}


class ResponseStatus(Vertical):
    """
    A widget that displays the status of the response from the agent.
    """

    message: Reactive[str] = reactive("Agent is responding", recompose=True)

    def compose(self) -> ComposeResult:
        yield Label(f" {self.message}")
        yield LoadingIndicator()

    def set_awaiting_response(self) -> None:
        self.message = "Awaiting response"
        self.add_class("-awaiting-response")
        self.remove_class("-agent-responding")

    def set_agent_responding(self) -> None:
        self.message = "Agent is responding"
        self.add_class("-agent-responding")
        self.remove_class("-awaiting-response")

    def set_status(self, status_code: str) -> None:
        """Update status message based on SEVEN routing status code."""
        self.message = STATUS_MESSAGES.get(status_code, "Processing...")
        self.add_class("-agent-responding")
        self.remove_class("-awaiting-response")
