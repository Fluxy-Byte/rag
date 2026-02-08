from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from .settings import settings


@lru_cache
def _embedding_function() -> embedding_functions.SentenceTransformerEmbeddingFunction:
    """Carrega uma única instância do encoder local."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=str(settings.embedding_model_path)
    )


@lru_cache
def _client():
    """
    Seleciona cliente local (persistente) ou remoto (HTTP) conforme settings.chroma_host.
    """
    if settings.chroma_host:
        return chromadb.HttpClient(host=settings.chroma_host)

    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_path))


def get_collection():
    """Retorna (ou cria) a coleção padrão com embedding local."""
    return _client().get_or_create_collection(
        name=settings.collection_name,
        embedding_function=_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection() -> None:
    """Apaga a coleção, útil para reindexar do zero."""
    try:
        _client().delete_collection(settings.collection_name)
    except Exception:
        # Coleção pode não existir ainda.
        pass


def persist_directory() -> str:
    """Caminho usado pelo Chroma (útil para logs e debug)."""
    return str(settings.chroma_path)
