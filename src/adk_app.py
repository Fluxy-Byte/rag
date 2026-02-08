from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Optional

from google.adk import Agent, Runner
from google.adk.apps.app import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from .rag import search
from .settings import settings
from dotenv import load_dotenv

# Garante que .env seja carregado em execuções fora do servidor (scripts/CLI)
load_dotenv()


def _format_hit(hit: dict) -> str:
    """Transforma um resultado em linha legível para o modelo."""
    citation_parts = []
    if src := hit.get("source"):
        citation_parts.append(Path(src).name)
    if chunk := hit.get("chunk"):
        citation_parts.append(f"chunk{chunk}")
    if page := hit.get("page"):
        citation_parts.append(f"p{page}")
    citation = "#".join(citation_parts) if citation_parts else "desconhecido"
    text = hit.get("text", "").replace("\n", " ").strip()
    return f"{text} [fonte: {citation}]"


def local_rag(query: str, top_k: int = settings.top_k) -> dict:
    """Busca vetorial local no ChromaDB usando embeddings SentenceTransformers.

    Retorna até `top_k` trechos relevantes com rótulos de fonte para citação.
    """
    hits = search(query, top_k=top_k)
    return {"hits": [_format_hit(h) for h in hits]}


def build_runner() -> Runner:
    """Monta Agent + Runner com memória em RAM (suficiente para VPN interna)."""
    agent = Agent(
        name="local_rag_agent",
        instruction=settings.system_prompt,
        model=settings.openai_model,
        tools=[local_rag],
    )
    app = App(name="local_rag_app", root_agent=agent)
    return Runner(
        app=app,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )


async def generate_answer(
    query: str,
    *,
    user_id: str = "user",
    session_id: str | None = None,
    runner: Optional[Runner] = None,
) -> str:
    """Executa o agente e retorna somente a resposta final."""
    runner = runner or build_runner()
    session_id = session_id or user_id
    new_message = types.Content(role="user", parts=[types.Part(text=query)])

    final_text: Optional[str] = None
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text or "" for part in event.content.parts if not part.thought
            )

    return final_text or ""


def generate_answer_sync(query: str, **kwargs) -> str:
    """Interface síncrona para uso em APIs."""
    return asyncio.run(generate_answer(query, **kwargs))


if __name__ == "__main__":
    print(generate_answer_sync("Quem é você?"))
