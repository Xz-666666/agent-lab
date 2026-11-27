from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .llm import LLM, SYSTEM_PROMPT, LLMResponse
from .tools import TOOLS, execute_tool

MAX_TOOL_ROUNDS = 4


class Agent:
    """A minimal tool-calling agent with a bounded loop."""

    def __init__(self, llm: LLM, max_tool_rounds: int = MAX_TOOL_ROUNDS) -> None:
        self._llm = llm
        self._max_tool_rounds = max_tool_rounds

    def reply(self, message: str) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        tools = [tool.schema() for tool in TOOLS.values()]

        for _ in range(self._max_tool_rounds):
            response = self._llm.complete(messages, tools)
            if not response.tool_calls:
                return response.content or ""

            messages.append(self._assistant_message(response))
            for call in response.tool_calls:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": execute_tool(call.name, call.arguments),
                    }
                )

        return "工具调用次数超过上限，已停止。"

    def stream_reply(self, message: str) -> Iterator[str]:
        """Stream a reply. Tool-triggering messages fall back to a buffered reply."""
        if "/calc" in message:
            text = self.reply(message)
            for index in range(0, len(text), 2):
                yield text[index : index + 2]
            return

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
        yield from self._llm.stream(messages)

    @staticmethod
    def _assistant_message(response: LLMResponse) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": call.arguments,
                    },
                }
                for call in response.tool_calls
            ],
        }
