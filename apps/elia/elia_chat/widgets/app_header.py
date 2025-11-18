from typing import TYPE_CHECKING, cast
from importlib.metadata import version, PackageNotFoundError
from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.signal import Signal
from textual.widget import Widget
from textual.widgets import Label, Static

from rich.text import Text
from pyfiglet import Figlet
from elia_chat.config import EliaChatModel
from elia_chat.models import get_model
from elia_chat.runtime_config import RuntimeConfig


def _get_version() -> str:
    """Get the version of elia_chat, with fallback if not installed."""
    try:
        return version("elia_chat")
    except PackageNotFoundError:
        # Fallback version when running from source without installation
        return "1.10.0-dev"


def _create_project_seven_logo() -> Text:
    """Generate PROJECT SEVEN ASCII logo with gradient.

    Creates a multi-line ASCII art logo using pyfiglet with a purple-to-cyan
    gradient inspired by the cli.py design.

    Returns:
        Rich Text object with gradient-styled ASCII art.
    """
    fig = Figlet(font='banner3-D')
    ascii_art = fig.renderText('PROJECT SEVEN')

    lines = ascii_art.split('\n')
    text = Text()

    # Gradient colors: purple to cyan
    start_color = (106, 0, 255)  # #6a00ff
    end_color = (0, 234, 255)    # #00eaff

    # Count non-empty lines for gradient calculation
    non_empty_lines = [line for line in lines if line.strip()]
    num_lines = len(non_empty_lines)

    line_index = 0
    for line in lines:
        if line.strip():
            # Calculate gradient ratio for this line
            ratio = line_index / max(num_lines - 1, 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            text.append(line + '\n', style=f'rgb({r},{g},{b})')
            line_index += 1
        else:
            text.append('\n')

    return text


if TYPE_CHECKING:
    from elia_chat.app import Elia


class AppHeader(Widget):
    COMPONENT_CLASSES = {"app-title", "app-subtitle"}

    def __init__(
        self,
        config_signal: Signal[RuntimeConfig],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.config_signal: Signal[RuntimeConfig] = config_signal
        self.elia = cast("Elia", self.app)

    def on_mount(self) -> None:
        def on_config_change(config: RuntimeConfig) -> None:
            self._update_selected_model(config.selected_model)

        self.config_signal.subscribe(self, on_config_change)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="cl-header-container"):
                yield Static(_create_project_seven_logo(), id="elia-title")
            model_name_or_id = (
                self.elia.runtime_config.selected_model.id
                or self.elia.runtime_config.selected_model.name
            )
            model = get_model(model_name_or_id, self.elia.launch_config)
            yield Label(self._get_selected_model_link_text(model), id="model-label")

    def _get_selected_model_link_text(self, model: EliaChatModel) -> str:
        return f"[@click=screen.options]{escape(model.display_name or model.name)}[/]"

    def _update_selected_model(self, model: EliaChatModel) -> None:
        print(self.elia.runtime_config)
        model_label = self.query_one("#model-label", Label)
        model_label.update(self._get_selected_model_link_text(model))
