from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import os

from fastapi import BackgroundTasks, FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn

from .adk_app import build_runner, generate_answer
from .rag import ingest_directory, search
from .settings import settings


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None
    user_id: str = "user"
    session_id: Optional[str] = None


class IngestRequest(BaseModel):
    reset: bool = False
    chunk_size: int = settings.chunk_size
    overlap: int = settings.chunk_overlap
    source_dir: Path = settings.data_dir


# Carrega variáveis do .env (inclui OPENAI_API_KEY)
load_dotenv()

key = os.getenv("OPENAI_API_KEY", "")
print(f"[server] OPENAI_API_KEY set: {'yes' if key else 'no'}")
if key:
    print(f"[server] OPENAI_API_KEY prefix: {key[:8]}...")

runner = build_runner()
app = FastAPI(title="Local RAG + ADK", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query")
async def query(body: QueryRequest):
    top_k = body.top_k or settings.top_k
    session_id = body.session_id or body.user_id  # garante contexto por usuário
    # Ajusta top_k dinamicamente no system prompt via tool arg
    async def answer():
        return await generate_answer(
            body.question,
            user_id=body.user_id,
            session_id=session_id,
            runner=runner,
        )

    # Nota: top_k é consumido no tool local_rag (default via settings)
    return {"answer": await answer()}


@app.post("/ingest")
async def ingest(body: IngestRequest, background_tasks: BackgroundTasks):
    def _job():
        ingest_directory(
            source_dir=body.source_dir,
            chunk_size=body.chunk_size,
            overlap=body.overlap,
            reset=body.reset,
        )

    background_tasks.add_task(_job)
    return {"status": "ingest scheduled"}


@app.post("/debug/search")
async def debug_search(body: QueryRequest):
    matches = search(body.question, top_k=body.top_k or settings.top_k)
    return {"matches": matches}


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
