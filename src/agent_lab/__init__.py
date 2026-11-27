def main() -> None:
    import uvicorn

    uvicorn.run("agent_lab.app:app", host="127.0.0.1", port=8000, reload=False)


__all__ = ["main"]
