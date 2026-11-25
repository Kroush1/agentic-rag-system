"""extract -> clean -> chunk -> embed -> store, re-processing only files that changed."""
import hashlib
from pathlib import Path
from typing import Callable

from ..config import CHUNK_CHARS, CHUNK_OVERLAP, DOCUMENTS_DIR, EMBED_REPO, UPLOADS_DIR
from .chunk import Chunk, chunk
from .clean import clean
from .embed import embed_passages
from .extract import SUPPORTED, extract
from .store import VectorStore


def source_files(dirs=(DOCUMENTS_DIR, UPLOADS_DIR)) -> dict[str, Path]:
    """File name -> path. Built-in documents win over uploads with the same name."""
    files = {}
    for d in dirs:
        if d.exists():
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in SUPPORTED:
                    files.setdefault(p.name, p)
    return files


def file_hash(path: Path) -> str:
    # Settings are part of the hash so changing them re-indexes everything.
    settings = f"{EMBED_REPO}|{CHUNK_CHARS}|{CHUNK_OVERLAP}".encode()
    return hashlib.sha256(settings + path.read_bytes()).hexdigest()


def process_file(path: Path) -> list[Chunk]:
    return chunk(path.name, clean(extract(path)))


def ingest(store: VectorStore, log: Callable[[str], None] = print, files: dict[str, Path] | None = None) -> dict:
    files = source_files() if files is None else files
    known = store.hashes()
    report = {"added": [], "unchanged": [], "removed": [], "failed": {}}
    for doc in known.keys() - files.keys():
        store.delete(doc)
        report["removed"].append(doc)
    for doc, path in files.items():
        digest = file_hash(path)
        if known.get(doc) == digest:
            report["unchanged"].append(doc)
            continue
        try:
            chunks = process_file(path)
            if not chunks:
                raise ValueError("no text found (a scanned PDF needs OCR first)")
            vectors = embed_passages([c.search_text for c in chunks])
            store.delete(doc)
            store.add(chunks, vectors, digest)
            report["added"].append(doc)
            log(f"indexed {doc}: {len(chunks)} chunks")
        except Exception as e:  # one bad file must not stop the rest
            report["failed"][doc] = str(e)
            log(f"FAILED {doc}: {e}")
    return report
