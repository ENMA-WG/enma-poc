from __future__ import annotations

import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .chat_provider import ChatChunk, ChatMessage, ToolDefinition

DEFAULT_MODEL = "gpt-4o"


class OpenAiAdapter:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
    ) -> AsyncIterator[ChatChunk]:
        raise NotImplementedError(
            "wire up openai Responses/Chat Completions streaming and tool calling"
        )
