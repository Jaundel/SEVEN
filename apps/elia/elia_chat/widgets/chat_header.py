from __future__ import annotations
from dataclasses import dataclass

from rich.console import ConsoleRenderable, RichCast
from rich.markup import escape

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from elia_chat.chats_manager import ChatsManager
from elia_chat.config import EliaChatModel
from elia_chat.models import ChatData
from elia_chat.screens.rename_chat_screen import RenameChat


class TitleStatic(Static):
    @dataclass
    class ChatRenamed(Message):
        chat_id: int
        new_title: str

    def __init__(
        self,
        chat_id: int,
        renderable: ConsoleRenderable | RichCast | str = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.chat_id = chat_id

    def begin_rename(self) -> None:
        self.app.push_screen(RenameChat(), callback=self.request_chat_rename)

    def action_rename_chat(self) -> None:
        self.begin_rename()

    async def request_chat_rename(self, new_title: str) -> None:
        self.post_message(self.ChatRenamed(self.chat_id, new_title))


class ChatHeader(Widget):
    def __init__(
        self,
        chat: ChatData,
        model: EliaChatModel,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.chat = chat
        self.model = model
        self._energy_used_wh = 0.0
        self._energy_saved_wh = 0.0

    def update_header(self, chat: ChatData, model: EliaChatModel):
        self.chat = chat
        self.model = model

        model_static = self.query_one("#model-static", Static)
        title_static = self.query_one("#title-static", Static)
        energy_static = self.query_one("#energy-static", Static)

        model_static.update(self.model_static_content())
        title_static.update(self.title_static_content())
        energy_static.update(self.energy_static_content())

    def title_static_content(self) -> str:
        chat = self.chat
        content = escape(chat.title or chat.short_preview) if chat else "Empty chat"
        return f"[@click=rename_chat]{content}[/]"

    def model_static_content(self) -> str:
        model = self.model
        return escape(model.display_name or model.name) if model else "Unknown model"

    def compose(self) -> ComposeResult:
        yield TitleStatic(self.chat.id, self.title_static_content(), id="title-static")
        yield Static(self.model_static_content(), id="model-static")
        yield Static(self.energy_static_content(), id="energy-static")

    async def on_mount(self) -> None:
        await self.refresh_energy_totals()

    async def refresh_energy_totals(self) -> None:
        chat_id = self.chat.id
        used, saved = await ChatsManager.energy_totals(chat_id=chat_id)
        self._energy_used_wh = used
        self._energy_saved_wh = saved
        energy_static = self.query_one("#energy-static", Static)
        energy_static.update(self.energy_static_content())

    def energy_static_content(self) -> str:
        used = self._format_energy_value(self._energy_used_wh)
        saved = self._format_energy_value(self._energy_saved_wh)
        return f"{used} used · {saved} saved"

    @staticmethod
    def _format_energy_value(value_wh: float) -> str:
        if value_wh >= 1000.0:
            return f"{value_wh / 1000.0:.2f} kWh"
        return f"{value_wh:.2f} Wh"
