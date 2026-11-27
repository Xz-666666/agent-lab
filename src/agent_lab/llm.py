from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol

SYSTEM_PROMPT = (
    "你是一个简洁、准确的中文助手。遇到算术问题时调用 calculator 工具，不要心算。"
    "回答控制在三句话以内。"
)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLM(Protocol):
    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse: ...

    def stream(self, messages: list[dict[str, Any]]) -> Iterator[str]: ...


class OpenAIClient:
    """Thin wrapper around the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools or None,
        )
        message = response.choices[0].message
        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=call.function.arguments,
            )
            for call in (message.tool_calls or [])
        ]
        return LLMResponse(content=message.content, tool_calls=calls)

    def stream(self, messages: list[dict[str, Any]]) -> Iterator[str]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class OfflineLLM:
    """Deterministic demo model used when no API key is configured.

    It still exercises the tool-calling loop when the message contains /calc.
    """

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        last = messages[-1]
        if last.get("role") == "tool":
            return LLMResponse(content=f"计算结果是 {last.get('content')}")

        user_text = self._last_user_text(messages)
        if "/calc" in user_text:
            expression = user_text.split("/calc", 1)[1].strip()
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="offline-call-1",
                        name="calculator",
                        arguments=json.dumps(
                            {"expression": expression},
                            ensure_ascii=False,
                        ),
                    )
                ]
            )

        return LLMResponse(
            content=(
                f"离线模式：我收到了「{user_text}」。"
                "配置 OPENAI_API_KEY 后会调用真实模型。"
            )
        )

    def stream(self, messages: list[dict[str, Any]]) -> Iterator[str]:
        text = self.complete(messages, []).content or ""
        for index in range(0, len(text), 2):
            yield text[index : index + 2]

    @staticmethod
    def _last_user_text(messages: list[dict[str, Any]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return str(message.get("content", ""))
        return ""
