# agent-lab

用 FastAPI + OpenAI 从零搭建 LLM Agent 的实验场，记录从项目骨架、接口、工具调用到评测的完整过程。

## 快速开始

```bash
uv sync
cp .env.example .env      # 填入 OPENAI_API_KEY
uv run agent-lab
```

终端输出 `Hello from agent-lab!` 就说明环境正常。

## 当前进度

- [x] 项目骨架（uv + Python 3.12）
- [x] 依赖与密钥管理（`.env` 已忽略，提供 `.env.example`）
- [ ] 最小可用的 `/chat` 接口
- [ ] 工具调用
- [ ] 评测与回归用例

## 项目结构

```text
src/agent_lab/    核心代码
tests/            测试（待补）
pyproject.toml    依赖与项目元数据
```

## 设计说明

- 用 `uv` 管理依赖，`uv.lock` 入库，保证环境可复现；
- 模型调用与业务逻辑分离，后续替换模型不需要改业务代码；
- 密钥只从环境变量读取，不写入代码和仓库。

## License

MIT
