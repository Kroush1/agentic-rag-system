"""Step 3 - section-aware chunking with overlap inside long sections."""
import re
from dataclasses import dataclass

from ..config import CHUNK_CHARS, CHUNK_OVERLAP
from .extract import Block


@dataclass
class Chunk:
    id: str
    doc: str
    title: str
    section: str
    page: int
    order: int
    text: str

    @property
    def search_text(self) -> str:
        """Text used for embedding and BM25: carries document and section context."""
        return f"{self.title} > {self.section}\n{self.text}"

    @property
    def label(self) -> str:
        page = f", p.{self.page}" if self.page else ""
        return f"{self.doc} - {self.section}{page}"


def chunk(doc: str, blocks: list[Block]) -> list[Chunk]:
    title = next((b.text for b in blocks if b.kind == "heading"), doc)
    chunks: list[Chunk] = []
    section, page, buffer = title, 0, []

    def flush():
        for piece in split_text("\n".join(buffer)):
            chunks.append(Chunk(f"{doc}::{len(chunks)}", doc, title, section, page, len(chunks), piece))
        buffer.clear()

    for b in blocks:
        if b.kind == "heading":
            flush()
            section, page = b.text, b.page
        else:
            if b.page != page:  # a new page starts a new chunk so page citations stay exact
                flush()
                page = b.page
            buffer.append(b.text)
    flush()
    return chunks


def split_text(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    units = []
    for unit in re.split(r"(?<=[.!?؟])\s+|\n+", text):  # sentences or lines
        units += [unit[i:i + size] for i in range(0, len(unit), size)]
    pieces, current = [], []
    for unit in units:
        if current and _length(current) + len(unit) > size:
            pieces.append("\n".join(current))
            tail = []
            while current and _length(tail) + len(current[-1]) <= overlap:
                tail.insert(0, current.pop())
            current = tail if _length(tail) + len(unit) <= size else []
        current.append(unit)
    if current:
        pieces.append("\n".join(current))
    return pieces


def _length(units: list[str]) -> int:
    return sum(len(u) + 1 for u in units)
