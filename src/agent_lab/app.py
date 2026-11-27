from __future__ import annotations

import json
import os
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from .agent import Agent
from .llm import LLM, OfflineLLM, OpenAIClient


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message 不能为空")
        return value


class ChatResponse(BaseModel):
    reply: str


def build_agent() -> Agent:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        llm: LLM = OpenAIClient(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        )
    else:
        llm = OfflineLLM()
    return Agent(llm)


def create_app(agent: Agent | None = None) -> FastAPI:
    app = FastAPI(title="agent-lab", version="0.2.0")
    current_agent = agent or build_agent()

    @app.get("/")
    def root() -> dict[str, str]:
        return {"name": "agent-lab", "docs": "/docs", "health": "/health"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        return ChatResponse(reply=current_agent.reply(request.message))

    @app.post("/chat/stream")
    def chat_stream(request: ChatRequest) -> StreamingResponse:
        def events() -> Iterator[str]:
            for delta in current_agent.stream_reply(request.message):
                payload = json.dumps({"delta": delta}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


app = create_app()
