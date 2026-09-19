from __future__ import annotations

import os
from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from .chat_provider import ChatChunk, ChatMessage, ToolDefinition

DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicAdapter:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> AsyncIterator[ChatChunk]:
        raise NotImplementedError(
            "wire up Anthropic Messages API streaming and tool calling"
        )
