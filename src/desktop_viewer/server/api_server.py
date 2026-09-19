from __future__ import annotations

import threading

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="enma-poc desktop viewer local API")


@app.post("/chat")
async def chat(payload: dict):
    raise NotImplementedError("wire up ChatProvider streaming response")


def start_local_server(host: str = "127.0.0.1", port: int = 8756) -> threading.Thread:
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread
