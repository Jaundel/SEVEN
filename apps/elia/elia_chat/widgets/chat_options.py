from __future__ import annotations
from typing import TYPE_CHECKING, cast

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, RadioSet, RadioButton, Static

from SEVEN.energy import list_cloud_profiles, list_local_profiles
from elia_chat.locations import config_file, theme_directory
from elia_chat.runtime_config import RuntimeConfig
from elia_chat.database.database import sqlite_file_name

if TYPE_CHECKING:
    from elia_chat.app import Elia


class ProfileRadioButton(RadioButton):
    """Radio button carrying an energy profile slug."""

    def __init__(
        self,
        slug: str,
        label: str,
        *,
        value: bool = False,
        button_first: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            label,
            value,
            button_first,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.slug = slug


class OptionsModal(ModalScreen[RuntimeConfig]):
    BINDINGS = [
        Binding("q", "app.quit", "Quit", show=False),
        Binding("escape", "app.pop_screen", "Close options", key_display="esc"),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.elia = cast("Elia", self.app)
        self.runtime_config = self.elia.runtime_config

    def compose(self) -> ComposeResult:
        local_profiles = list_local_profiles()
        cloud_profiles = list_cloud_profiles()
        with VerticalScroll(id="form-scrollable") as vs:
            vs.border_title = "Energy Profiles"
            vs.can_focus = False
            description = (
                "Choose the local hardware profile SEVEN should assume when "
                "tracking actual energy, along with the cloud baseline used to "
                "compute savings. Changes apply only to this session."
            )
            yield Static(description, id="profiles-description")
            with RadioSet(id="local-profiles") as local_rs:
                local_rs.border_title = "Local Hardware"
                for slug, label in local_profiles.items():
                    yield ProfileRadioButton(
                        slug=slug,
                        label=label,
                        value=slug == self.runtime_config.local_profile,
                    )
            with RadioSet(id="cloud-profiles") as cloud_rs:
                cloud_rs.border_title = "Cloud Baseline"
                for slug, label in cloud_profiles.items():
                    yield ProfileRadioButton(
                        slug=slug,
                        label=label,
                        value=slug == self.runtime_config.cloud_profile,
                    )
            with Vertical(id="xdg-info") as xdg_info:
                xdg_info.border_title = "Data & Themes"
                yield Static(f"{sqlite_file_name.absolute()}\n[dim]Database[/]\n")
                yield Static(f"{config_file()}\n[dim]Config[/]\n")
                yield Static(f"{theme_directory()}\n[dim]Themes directory[/]")
        yield Footer()

    def on_mount(self) -> None:
        self.apply_overridden_subtitles()

    @on(RadioSet.Changed, "#local-profiles")
    def _on_local_profile_changed(self, event: RadioSet.Changed) -> None:
        button = self._extract_pressed_button(event)
        if not button:
            return
        self._update_runtime_config(local_profile=button.slug)

    @on(RadioSet.Changed, "#cloud-profiles")
    def _on_cloud_profile_changed(self, event: RadioSet.Changed) -> None:
        button = self._extract_pressed_button(event)
        if not button:
            return
        self._update_runtime_config(cloud_profile=button.slug)

    def _update_runtime_config(self, **updates: str) -> None:
        self.elia.runtime_config = self.elia.runtime_config.model_copy(update=updates)
        self.apply_overridden_subtitles()
        self.refresh()

    def apply_overridden_subtitles(self) -> None:
        local_rs = self.query_one("#local-profiles", RadioSet)
        cloud_rs = self.query_one("#cloud-profiles", RadioSet)
        if self.elia.runtime_config.local_profile != self.elia.launch_config.default_local_profile:
            local_rs.border_subtitle = "overrides defaults"
        else:
            local_rs.border_subtitle = ""

        if self.elia.runtime_config.cloud_profile != self.elia.launch_config.default_cloud_profile:
            cloud_rs.border_subtitle = "overrides defaults"
        else:
            cloud_rs.border_subtitle = ""

    def _extract_pressed_button(
        self, event: RadioSet.Changed
    ) -> ProfileRadioButton | None:
        """Support Textual event API changes (pressed vs. pressed_button)."""

        button = getattr(event, "pressed", None)
        if button is None:
            button = getattr(event, "pressed_button", None)
        return cast(ProfileRadioButton | None, button)
