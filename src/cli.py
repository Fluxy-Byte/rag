from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from .rag import ingest_directory, search
from .settings import settings
from .watcher import watch_folder


app = typer.Typer(help="Pipeline local de ingestão e teste de busca.")


@app.command()
def ingest(
    source_dir: Path = typer.Option(settings.data_dir, help="Pasta com PDFs/TXTs"),
    chunk_size: int = typer.Option(settings.chunk_size, min=200, max=2000),
    overlap: int = typer.Option(settings.chunk_overlap, min=0, max=1000),
    reset: bool = typer.Option(
        False, "--reset", help="Apaga a coleção antes de reindexar."
    ),
) -> None:
    result = ingest_directory(
        source_dir=source_dir, chunk_size=chunk_size, overlap=overlap, reset=reset
    )
    typer.echo(f"Ingestão concluída: {result}")


@app.command("search")
def search_cli(
    query: str = typer.Argument(..., help="Pergunta para teste manual."),
    top_k: int = typer.Option(settings.top_k, help="Número de trechos a retornar."),
) -> None:
    matches = search(query, top_k=top_k)
    if not matches:
        typer.echo("Nenhum resultado encontrado.")
        raise typer.Exit(code=1)

    for idx, match in enumerate(matches, start=1):
        src = match.get("source")
        page = match.get("page")
        chunk = match.get("chunk")
        score = match.get("distance")
        typer.echo(
            f"[{idx}] fonte={src} page={page} chunk={chunk} score={score:.4f}\n{match.get('text')}\n"
        )


@app.command()
def watch(
    folder: Path = typer.Option(settings.data_dir, help="Pasta a monitorar."),
    chunk_size: int = typer.Option(settings.chunk_size),
    overlap: int = typer.Option(settings.chunk_overlap),
) -> None:
    asyncio.run(
        watch_folder(folder=folder, chunk_size=chunk_size, overlap=overlap)
    )


if __name__ == "__main__":
    app()
