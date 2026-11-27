# agent-lab

用 FastAPI + OpenAI 从零搭建 LLM Agent 的实验场，包含流式对话、工具调用、测试与 CI。

## 功能

- `POST /chat`：普通对话，支持工具调用
- `POST /chat/stream`：SSE 流式返回
- `GET /health`：健康检查
- 内置 `calculator` 工具，使用 AST 解析，不调用 `eval`
- 没有 `OPENAI_API_KEY` 时自动进入离线演示模式

## 快速开始

```bash
uv sync
cp .env.example .env      # 可选：填入 OPENAI_API_KEY
uv run agent-lab
```

打开 http://127.0.0.1:8000/docs 查看接口文档。

### 试一下

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "/calc (12 + 8) * 3"}'
```

返回：

```json
{"reply":"计算结果是 60"}
```

流式接口：

```bash
curl -N -X POST http://127.0.0.1:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

## 设计说明

- `llm.py`：把模型调用抽象成 `LLM` 协议，`OpenAIClient` 走真实 API，`OfflineLLM` 用于离线演示和测试；
- `agent.py`：有上限的工具调用循环，最多 4 轮，避免模型无限调用；
- `tools.py`：工具注册表 + 安全计算器，只允许数字和 `+ - * / % **`，不使用 `eval`；
- `app.py`：FastAPI 路由，`/chat/stream` 用 SSE 分块返回。

## 项目结构

```text
src/agent_lab/
  app.py      FastAPI 路由
  agent.py    工具调用循环
  llm.py      模型客户端与离线实现
  tools.py    工具注册表与计算器
tests/        接口与工具测试
```

## 测试与 CI

```bash
uv run ruff check .
uv run pytest -q
```

CI 在每次 push / PR 时运行同样的命令。

## 当前进度

- [x] FastAPI 骨架与 `/chat`
- [x] SSE 流式返回
- [x] calculator 工具调用
- [x] 接口与工具测试
- [x] GitHub Actions CI
- [ ] 接入真实模型的多轮工具调用评测

## License

MIT
