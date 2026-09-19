from __future__ import annotations

import json
import os
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from .chat_provider import ChatChunk, ChatMessage, ToolCall, ToolDefinition

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
        request_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            tools=request_tools or None,
            stream=True,
        )

        # The Chat Completions stream sends the tool's name once and its
        # JSON arguments in fragments across several chunks; only the last
        # chunk carries finish_reason. We only support one tool call per
        # turn, matching ChatChunk.tool_call being a single Optional value.
        tool_call_name: Optional[str] = None
        tool_call_arguments = ""

        async for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta

            if delta.content:
                yield ChatChunk(text=delta.content)

            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    function = tool_call_delta.function
                    if function is None:
                        continue
                    if function.name:
                        tool_call_name = function.name
                    if function.arguments:
                        tool_call_arguments += function.arguments

        if tool_call_name is not None:
            try:
                arguments = json.loads(tool_call_arguments) if tool_call_arguments else {}
            except json.JSONDecodeError:
                arguments = {}
            yield ChatChunk(tool_call=ToolCall(name=tool_call_name, arguments=arguments))

        yield ChatChunk(done=True)
