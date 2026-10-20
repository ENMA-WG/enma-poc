from __future__ import annotations

import json
import os
from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from .chat_provider import ChatChunk, ChatMessage, ToolCall, ToolDefinition

DEFAULT_MODEL = "claude-sonnet-5"

# Anthropic has no "system" role message; it is a separate top-level param.
MAX_TOKENS = 4096


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
        system_prompt: Optional[str] = None
        anthropic_messages = []
        for message in messages:
            if message.role == "system":
                system_prompt = message.content
                continue
            role = "assistant" if message.role == "assistant" else "user"
            anthropic_messages.append({"role": role, "content": message.content})

        anthropic_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

        kwargs = dict(
            model=self._model,
            max_tokens=MAX_TOKENS,
            messages=anthropic_messages,
            tools=anthropic_tools,
        )
        if system_prompt:
            kwargs["system"] = system_prompt

        # Only one tool call per turn is supported, matching ChatChunk.tool_call
        # being a single Optional value.
        tool_call_name: Optional[str] = None
        tool_call_json = ""

        async with self._client.messages.stream(**kwargs) as stream:
            async for event in stream:
                if event.type == "content_block_start" and event.content_block.type == "tool_use":
                    tool_call_name = event.content_block.name
                    tool_call_json = ""
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield ChatChunk(text=event.delta.text)
                    elif event.delta.type == "input_json_delta":
                        tool_call_json += event.delta.partial_json

        if tool_call_name is not None:
            try:
                arguments = json.loads(tool_call_json) if tool_call_json else {}
            except json.JSONDecodeError:
                arguments = {}
            yield ChatChunk(tool_call=ToolCall(name=tool_call_name, arguments=arguments))

        yield ChatChunk(done=True)
