from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centraliza configurações do projeto RAG local."""

    chroma_path: Path = Path("chroma")
    chroma_host: Optional[str] = None  # se definido, usa Chroma remoto via HTTP
    collection_name: str = "local_docs"
    data_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_model_path: Path = Path("models/all-MiniLM-L6-v2")
    chunk_size: int = 800
    chunk_overlap: int = 200
    top_k: int = 5
    openai_model: str = "openai/gpt-4o-mini"
    system_prompt: str = (
        "Você é um assistente RAG interno. Responda em português de forma direta. "
        "Use apenas os trechos retornados pela ferramenta local_rag. "
        "Sempre cite a fonte no formato [fonte: <arquivo>#<chunk>]. "
        "Se não houver evidência suficiente, diga que não encontrou."
    )

    model_config = SettingsConfigDict(env_prefix="ADK_", extra="ignore")


settings = Settings()
