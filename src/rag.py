from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from .chroma_setup import get_collection, reset_collection
from .chunker import Chunk, build_chunks, is_supported_file
from .settings import settings


def _upsert_chunks(chunks: Sequence[Chunk]) -> None:
    if not chunks:
        return

    collection = get_collection()
    collection.upsert(
        ids=[c.id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {"source": c.source, "page": c.page, "chunk": c.chunk_index}
            for c in chunks
        ],
    )


def ingest_directory(
    source_dir: Path | str = settings.data_dir,
    *,
    chunk_size: int = settings.chunk_size,
    overlap: int = settings.chunk_overlap,
    reset: bool = False,
) -> dict:
    """Indexa todos os PDFs/TXTs do diretório."""
    if reset:
        reset_collection()

    dir_path = Path(source_dir)
    files = [
        p for p in dir_path.rglob("*") if p.is_file() and is_supported_file(p)
    ]

    processed = 0
    total_chunks = 0
    for file_path in files:
        chunks = list(build_chunks(file_path, chunk_size=chunk_size, overlap=overlap))
        _upsert_chunks(chunks)
        processed += 1
        total_chunks += len(chunks)

    return {"files": processed, "chunks": total_chunks}


def ingest_paths(
    paths: Iterable[Path],
    *,
    chunk_size: int = settings.chunk_size,
    overlap: int = settings.chunk_overlap,
) -> dict:
    """Indexa apenas os caminhos informados."""
    path_list = list(paths)
    chunks_to_upsert: list[Chunk] = []
    for path in path_list:
        if not path.exists() or not is_supported_file(path):
            continue
        chunks_to_upsert.extend(
            build_chunks(path, chunk_size=chunk_size, overlap=overlap)
        )
    _upsert_chunks(chunks_to_upsert)
    return {
        "files": len(path_list),
        "chunks": len(chunks_to_upsert),
    }


def search(
    query: str,
    *,
    top_k: int = settings.top_k,
) -> list[dict]:
    """Consulta o ChromaDB e retorna trechos e metadados."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    matches: list[dict] = []
    for doc, meta, dist in zip(docs, metas, dists):
        matches.append(
            {
                "text": doc,
                "source": meta.get("source") if meta else None,
                "page": meta.get("page") if meta else None,
                "chunk": meta.get("chunk") if meta else None,
                "distance": dist,
            }
        )
    return matches
