from __future__ import annotations

import json
import logging
import threading
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional

import uvicorn
from ag_ui.core import (
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from ..ai.chat_provider import ChatMessage, ChatProvider, ToolCall
from ..ai.local_dev_provider import load_local_dev_provider
from ..ai.settings import load_ai_settings
from .tools import TOOL_DEFINITIONS, ViewerToolExecutor

logger = logging.getLogger(__name__)

app = FastAPI(title="enma-poc desktop viewer local API")

# A tool call is only useful once the 3D viewer exists, so MainWindow hands
# this in after constructing the UI; the FastAPI handler runs on its own
# background thread and has no other route to the viewer (importing
# MainWindow here would pull Qt widgets into the request path and create a
# circular import between app.py and this module).
_tool_executor: Optional[ViewerToolExecutor] = None

# Caps the number of model turns spent chasing tool calls in a single user
# request, so a model that never stops calling tools can't hang the request.
MAX_TOOL_TURNS = 5


def set_tool_executor(executor: ViewerToolExecutor) -> None:
    global _tool_executor
    _tool_executor = executor


def _build_provider() -> ChatProvider:
    local_provider = load_local_dev_provider()
    if local_provider is not None:
        return local_provider

    settings = load_ai_settings()
    if settings.provider == "anthropic":
        from ..ai.anthropic_adapter import AnthropicAdapter

        return AnthropicAdapter(api_key=settings.api_key, model=settings.model)

    from ..ai.openai_adapter import OpenAiAdapter

    return OpenAiAdapter(api_key=settings.api_key, model=settings.model)


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(part.text for part in content if getattr(part, "type", None) == "text")


def _to_chat_message(message) -> Optional[ChatMessage]:
    """Flatten one AG-UI transcript message onto our provider-agnostic shape.

    Tool calls/results from earlier turns are replayed as plain text so both
    adapters only need to understand a flat role/content transcript. The
    *current* turn's tool execution is handled live by the loop in
    ``_run_chat``, not by this history replay.
    """
    if message.role == "user":
        return ChatMessage(role="user", content=_content_to_text(message.content))
    if message.role == "assistant":
        return ChatMessage(role="assistant", content=message.content) if message.content else None
    if message.role == "tool":
        return ChatMessage(role="user", content=f"[tool result] {_content_to_text(message.content)}")
    if message.role in ("system", "developer"):
        return ChatMessage(role="system", content=_content_to_text(message.content))
    return None


async def _run_chat(run_input: RunAgentInput) -> AsyncIterator[str]:
    encoder = EventEncoder()
    thread_id = run_input.thread_id
    run_id = run_input.run_id

    def emit(event) -> str:
        return encoder.encode(event)

    yield emit(RunStartedEvent(thread_id=thread_id, run_id=run_id))

    try:
        provider = _build_provider()
    except RuntimeError as exc:
        yield emit(RunErrorEvent(message=str(exc)))
        return

    messages = [
        chat_message
        for chat_message in (_to_chat_message(message) for message in run_input.messages)
        if chat_message is not None
    ]

    try:
        for _ in range(MAX_TOOL_TURNS):
            message_id = str(uuid.uuid4())
            yield emit(TextMessageStartEvent(message_id=message_id, role="assistant"))

            text_parts: list[str] = []
            tool_call: Optional[ToolCall] = None

            async for chunk in provider.stream_chat(messages, TOOL_DEFINITIONS):
                if chunk.text:
                    text_parts.append(chunk.text)
                    yield emit(TextMessageContentEvent(message_id=message_id, delta=chunk.text))
                if chunk.tool_call is not None:
                    tool_call = chunk.tool_call

            yield emit(TextMessageEndEvent(message_id=message_id))
            messages.append(ChatMessage(role="assistant", content="".join(text_parts)))

            if tool_call is None:
                break

            tool_call_id = str(uuid.uuid4())
            yield emit(
                ToolCallStartEvent(
                    tool_call_id=tool_call_id,
                    tool_call_name=tool_call.name,
                    parent_message_id=message_id,
                )
            )
            yield emit(ToolCallArgsEvent(tool_call_id=tool_call_id, delta=json.dumps(tool_call.arguments)))
            yield emit(ToolCallEndEvent(tool_call_id=tool_call_id))

            result_json = json.dumps(_execute_tool(tool_call))
            yield emit(
                ToolCallResultEvent(
                    message_id=str(uuid.uuid4()),
                    tool_call_id=tool_call_id,
                    content=result_json,
                )
            )
            messages.append(ChatMessage(role="user", content=f"[tool result] {result_json}"))
        else:
            logger.warning("Run %s hit the %d-turn tool-call cap", run_id, MAX_TOOL_TURNS)

        yield emit(RunFinishedEvent(thread_id=thread_id, run_id=run_id))
    except Exception as exc:  # noqa: BLE001 - surfaced to the chat UI, not swallowed
        logger.exception("Chat run %s failed", run_id)
        yield emit(RunErrorEvent(message=str(exc)))


def _execute_tool(tool_call: ToolCall) -> dict:
    if _tool_executor is None:
        return {"status": "error", "detail": "Viewer is not ready yet"}
    try:
        return _tool_executor.execute(tool_call.name, tool_call.arguments)
    except Exception as exc:  # noqa: BLE001 - reported back to the model, not swallowed
        logger.exception("Tool execution failed: %s", tool_call.name)
        return {"status": "error", "detail": str(exc)}


@app.post("/chat")
async def chat(run_input: RunAgentInput) -> StreamingResponse:
    encoder = EventEncoder()
    return StreamingResponse(_run_chat(run_input), media_type=encoder.get_content_type())


# Mounted last and at "/" so it acts as a catch-all: Starlette matches routes
# in registration order, and the POST /chat route above must win before this
# falls through to serving the built frontend (see chat_ui/README.md).
_CHAT_UI_DIR = Path(__file__).resolve().parent.parent / "chat_ui"
if _CHAT_UI_DIR.is_dir():
    app.mount("/", StaticFiles(directory=_CHAT_UI_DIR, html=True), name="chat_ui")


def start_local_server(host: str = "127.0.0.1", port: int = 8756) -> threading.Thread:
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread
