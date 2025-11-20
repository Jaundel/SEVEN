from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from textual.widgets import Label

from textual import log, on, work, events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget

from elia_chat import constants
from elia_chat.chats_manager import ChatsManager
from elia_chat.models import ChatData, ChatMessage
from elia_chat.screens.chat_details import ChatDetails
from elia_chat.seven_adapter import call_seven_router
from elia_chat.widgets.agent_is_typing import ResponseStatus
from elia_chat.widgets.chat_header import ChatHeader, TitleStatic
from elia_chat.widgets.prompt_input import PromptInput
from elia_chat.widgets.chatbox import Chatbox


if TYPE_CHECKING:
    from elia_chat.app import Elia
    from litellm.types.completion import (
        ChatCompletionUserMessageParam,
        ChatCompletionAssistantMessageParam,
    )


class ChatPromptInput(PromptInput):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close chat", key_display="esc")]


class Chat(Widget):
    BINDINGS = [
        Binding("ctrl+r", "rename", "Rename", key_display="^r"),
        Binding("shift+down", "scroll_container_down", show=False),
        Binding("shift+up", "scroll_container_up", show=False),
        Binding(
            key="g",
            action="focus_first_message",
            description="First message",
            key_display="g",
            show=False,
        ),
        Binding(
            key="G",
            action="focus_latest_message",
            description="Latest message",
            show=False,
        ),
        Binding(key="f2", action="details", description="Chat info"),
    ]

    allow_input_submit = reactive(True)
    """Used to lock the chat input while the agent is responding."""

    def __init__(self, chat_data: ChatData) -> None:
        super().__init__()
        self.chat_data = chat_data
        self.elia = cast("Elia", self.app)
        self.model = chat_data.model

    @dataclass
    class AgentResponseStarted(Message):
        pass

    @dataclass
    class RoutingStatusUpdate(Message):
        """Sent when SEVEN routing status changes (e.g., local_starting, api_fetching)."""

        status: str

    @dataclass
    class AgentResponseComplete(Message):
        chat_id: int | None
        message: ChatMessage
        chatbox: Chatbox
        source_label: str | None = None

    @dataclass
    class AgentResponseFailed(Message):
        """Sent when the agent fails to respond e.g. cant connect.
        Can be used to reset UI state."""

        last_message: ChatMessage

    @dataclass
    class NewUserMessage(Message):
        content: str

    def compose(self) -> ComposeResult:
        yield ResponseStatus()
        yield ChatHeader(chat=self.chat_data, model=self.model)

        with VerticalScroll(id="chat-container") as vertical_scroll:
            vertical_scroll.can_focus = False

        yield ChatPromptInput(id="prompt")

    async def on_mount(self, _: events.Mount) -> None:
        """
        When the component is mounted, we need to check if there is a new chat to start
        """
        await self.load_chat(self.chat_data)

    @property
    def chat_container(self) -> VerticalScroll:
        return self.query_one("#chat-container", VerticalScroll)

    @property
    def is_empty(self) -> bool:
        """True if the conversation is empty, False otherwise."""
        return len(self.chat_data.messages) == 1  # Contains system message at first.

    def scroll_to_latest_message(self):
        container = self.chat_container
        container.refresh()
        container.scroll_end(animate=False, force=True)

    @on(AgentResponseFailed)
    def restore_state_on_agent_failure(self, event: Chat.AgentResponseFailed) -> None:
        original_prompt = event.last_message.message.get("content", "")
        if isinstance(original_prompt, str):
            self.query_one(ChatPromptInput).text = original_prompt

    async def new_user_message(self, content: str) -> None:
        log.debug(f"User message submitted in chat {self.chat_data.id!r}: {content!r}")

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        user_message: ChatCompletionUserMessageParam = {
            "content": content,
            "role": "user",
        }

        user_chat_message = ChatMessage(user_message, now_utc, self.chat_data.model)
        self.chat_data.messages.append(user_chat_message)
        user_message_chatbox = Chatbox(user_chat_message, self.chat_data.model)

        assert (
            self.chat_container is not None
        ), "Textual has mounted container at this point in the lifecycle."

        await self.chat_container.mount(user_message_chatbox)

        self.scroll_to_latest_message()
        self.post_message(self.NewUserMessage(content))

        await ChatsManager.add_message_to_chat(
            chat_id=self.chat_data.id, message=user_chat_message
        )

        prompt = self.query_one(ChatPromptInput)
        prompt.submit_ready = False
        self.stream_agent_response()

    @work(thread=True, group="agent_response")
    async def stream_agent_response(self) -> None:
        log.debug(
            "Routing chat %s through SEVEN backend (messages=%s)",
            self.chat_data.id,
            len(self.chat_data.messages),
        )

        self.post_message(self.AgentResponseStarted())
        try:
            # Create callback to post routing status updates to UI
            def on_routing_status_change(status: str) -> None:
                self.post_message(self.RoutingStatusUpdate(status=status))

            seven_result = call_seven_router(
                messages=self.chat_data.messages,
                runtime_config=self.elia.runtime_config,
                on_status_change=on_routing_status_change,
            )
        except Exception as exception:  # pylint: disable=broad-except
            log.exception("SEVEN routing failed: %s", exception)
            self.app.notify(
                f"SEVEN routing failed: {exception}",
                title="Routing error",
                severity="error",
                timeout=constants.ERROR_NOTIFY_TIMEOUT_SECS,
            )
            self.post_message(self.AgentResponseFailed(self.chat_data.messages[-1]))
            return

        ai_message: ChatCompletionAssistantMessageParam = {
            "content": seven_result.text,
            "role": "assistant",
        }
        metadata: dict[str, float | str] = {}
        if seven_result.energy_wh is not None:
            metadata["energy_wh"] = seven_result.energy_wh
        if seven_result.energy_savings_wh is not None:
            metadata["energy_saved_wh"] = seven_result.energy_savings_wh
        if seven_result.energy_profile_label:
            metadata["energy_profile"] = seven_result.energy_profile_label
        if seven_result.baseline_profile_label:
            metadata["energy_baseline_profile"] = seven_result.baseline_profile_label
        metadata = metadata or {}
        message = ChatMessage(
            message=ai_message,
            model=self.chat_data.model,
            timestamp=seven_result.timestamp,
            metadata=metadata or None,
        )
        response_chatbox = Chatbox(
            message=message,
            model=self.chat_data.model,
            classes="response-in-progress",
        )
        response_chatbox.border_title = seven_result.source_label

        self.app.call_from_thread(self.chat_container.mount, response_chatbox)
        self.app.call_from_thread(self.scroll_to_latest_message)

        self.post_message(
            self.AgentResponseComplete(
                chat_id=self.chat_data.id,
                message=message,
                chatbox=response_chatbox,
                source_label=seven_result.source_label,
            )
        )

    @on(AgentResponseFailed)
    @on(AgentResponseStarted)
    async def agent_started_responding(
        self, event: AgentResponseFailed | AgentResponseStarted
    ) -> None:
        try:
            awaiting_reply = self.chat_container.query_one("#awaiting-reply", Label)
        except NoMatches:
            pass
        else:
            if awaiting_reply:
                await awaiting_reply.remove()

    @on(AgentResponseComplete)
    async def agent_finished_responding(self, event: AgentResponseComplete) -> None:
        # Ensure the thread is updated with the message from the agent
        self.chat_data.messages.append(event.message)
        event.chatbox.border_title = event.source_label or "Agent"
        event.chatbox.remove_class("response-in-progress")
        prompt = self.query_one(ChatPromptInput)
        prompt.submit_ready = True

        header = self.query_one(ChatHeader)
        await header.refresh_energy_totals()

    @on(PromptInput.PromptSubmitted)
    async def user_chat_message_submitted(
        self, event: PromptInput.PromptSubmitted
    ) -> None:
        if self.allow_input_submit is True:
            user_message = event.text
            await self.new_user_message(user_message)

    @on(PromptInput.CursorEscapingTop)
    async def on_cursor_up_from_prompt(
        self, event: PromptInput.CursorEscapingTop
    ) -> None:
        self.focus_latest_message()

    @on(Chatbox.CursorEscapingBottom)
    def move_focus_to_prompt(self) -> None:
        self.query_one(ChatPromptInput).focus()

    @on(TitleStatic.ChatRenamed)
    async def handle_chat_rename(self, event: TitleStatic.ChatRenamed) -> None:
        if event.chat_id == self.chat_data.id and event.new_title:
            self.chat_data.title = event.new_title
            header = self.query_one(ChatHeader)
            header.update_header(self.chat_data, self.model)
            await ChatsManager.rename_chat(event.chat_id, event.new_title)

    def get_latest_chatbox(self) -> Chatbox:
        return self.query(Chatbox).last()

    def focus_latest_message(self) -> None:
        try:
            self.get_latest_chatbox().focus()
        except NoMatches:
            pass

    def action_rename(self) -> None:
        title_static = self.query_one(TitleStatic)
        title_static.begin_rename()

    def action_focus_latest_message(self) -> None:
        self.focus_latest_message()

    def action_focus_first_message(self) -> None:
        try:
            self.query(Chatbox).first().focus()
        except NoMatches:
            pass

    def action_scroll_container_up(self) -> None:
        if self.chat_container:
            self.chat_container.scroll_up()

    def action_scroll_container_down(self) -> None:
        if self.chat_container:
            self.chat_container.scroll_down()

    async def action_details(self) -> None:
        await self.app.push_screen(ChatDetails(self.chat_data))

    async def load_chat(self, chat_data: ChatData) -> None:
        chatboxes = [
            Chatbox(chat_message, chat_data.model)
            for chat_message in chat_data.non_system_messages
        ]
        await self.chat_container.mount_all(chatboxes)
        self.chat_container.scroll_end(animate=False, force=True)
        chat_header = self.query_one(ChatHeader)
        chat_header.update_header(
            chat=chat_data,
            model=chat_data.model,
        )

        # If the last message didn't receive a response, try again.
        messages = chat_data.messages
        if messages and messages[-1].message["role"] == "user":
            prompt = self.query_one(ChatPromptInput)
            prompt.submit_ready = False
            self.stream_agent_response()

    def action_close(self) -> None:
        self.app.clear_notifications()
        self.app.pop_screen()
