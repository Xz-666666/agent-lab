from fastapi.testclient import TestClient

from agent_lab.agent import Agent
from agent_lab.app import create_app
from agent_lab.llm import OfflineLLM


def make_client() -> TestClient:
    return TestClient(create_app(Agent(OfflineLLM())))


def test_health() -> None:
    response = make_client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_rejects_empty_message() -> None:
    response = make_client().post("/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_rejects_blank_message() -> None:
    response = make_client().post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_offline_echo() -> None:
    response = make_client().post("/chat", json={"message": "你好"})
    assert response.status_code == 200
    assert "离线模式" in response.json()["reply"]


def test_chat_runs_calculator_tool() -> None:
    response = make_client().post("/chat", json={"message": "/calc (12 + 8) * 3"})
    assert response.status_code == 200
    assert "60" in response.json()["reply"]


def test_chat_stream_returns_sse() -> None:
    client = make_client()
    with client.stream("POST", "/chat/stream", json={"message": "你好"}) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert body.startswith("data: ")
    assert "[DONE]" in body
