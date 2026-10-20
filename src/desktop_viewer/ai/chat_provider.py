from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional, Protocol


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatChunk:
    text: str = ""
    tool_call: Optional[ToolCall] = None
    done: bool = False


class ChatProvider(Protocol):
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> AsyncIterator[ChatChunk]:
        ...
