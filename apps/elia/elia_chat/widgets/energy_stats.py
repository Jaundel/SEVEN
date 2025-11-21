from __future__ import annotations

from textual.widgets import Static

from elia_chat.chats_manager import ChatsManager
from elia_chat.widgets.chat_header import ChatHeader
from elia_chat.energy_equivalents import random_equivalent


class EnergyStats(Static):
    """Display total energy used/saved across all conversations."""

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__("", name=name, id=id, classes=classes, disabled=disabled)

    async def on_mount(self) -> None:
        await self.refresh_stats()

    async def refresh_stats(self) -> None:
        used, saved = await ChatsManager.energy_totals(chat_id=None)
        used_text = ChatHeader._format_energy_value(used)
        saved_text = ChatHeader._format_energy_value(saved)
        equivalent = random_equivalent(saved)
        self.update(f"⚡ {used_text} used · 🌱 {saved_text} saved · {equivalent}")
