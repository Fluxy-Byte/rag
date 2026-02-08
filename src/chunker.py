from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    page: int | None
    chunk_index: int


def load_sections(file_path: Path) -> List[Tuple[str, int | None]]:
    """Lê PDF/TXT e retorna lista de pares (texto, página)."""
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return [(text, None)]

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return [
            (page.extract_text() or "", page_number)
            for page_number, page in enumerate(reader.pages, start=1)
        ]

    raise ValueError(f"Extensão não suportada: {suffix}")


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Quebra texto em blocos com sobreposição."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size deve ser maior que overlap.")

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


def build_chunks(file_path: Path, *, chunk_size: int, overlap: int) -> Iterable[Chunk]:
    """Gera chunks para um arquivo."""
    base = _make_base_id(file_path)
    section_index = 0
    for section_text, page in load_sections(file_path):
        section_text = _sanitize(section_text)
        for local_idx, text in enumerate(chunk_text(section_text, chunk_size, overlap)):
            chunk_id = f"{base}-{section_index}"
            section_index += 1
            yield Chunk(
                id=chunk_id,
                text=text,
                source=str(file_path),
                page=page,
                chunk_index=local_idx,
            )


def is_supported_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def _make_base_id(path: Path) -> str:
    digest = hashlib.md5(str(path).encode("utf-8")).hexdigest()[:8]
    return f"{path.stem}-{digest}"


def _sanitize(text: str) -> str:
    """Remove caracteres inválidos/surrogates para o tokenizer HF."""
    return (
        text.replace("\x00", " ")
        .encode("utf-8", errors="ignore")
        .decode("utf-8", errors="ignore")
    )
