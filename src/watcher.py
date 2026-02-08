from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable

from watchfiles import awatch

from .rag import ingest_paths
from .settings import settings


async def watch_folder(
    folder: Path | str = settings.data_dir,
    *,
    chunk_size: int = settings.chunk_size,
    overlap: int = settings.chunk_overlap,
) -> None:
    """Observa a pasta e reindexa quando novos arquivos chegam."""
    base = Path(folder)
    base.mkdir(parents=True, exist_ok=True)
    print(f"👀 Observando {base} por PDFs/TXTs novos...")

    async for changes in awatch(base):
        paths = {Path(path) for _, path in changes}
        result = ingest_paths(paths, chunk_size=chunk_size, overlap=overlap)
        print(f"Ingestão automática: {result}")


def run_watcher() -> None:
    asyncio.run(watch_folder())


if __name__ == "__main__":
    run_watcher()
