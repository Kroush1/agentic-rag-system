"""Step 5 - storage in a persistent Chroma vector database."""
import chromadb
from chromadb.config import Settings

from ..config import STORAGE_DIR
from .chunk import Chunk


class VectorStore:
    def __init__(self, path=STORAGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(str(path), Settings(anonymized_telemetry=False))
        self.col = self.client.get_or_create_collection("chunks", metadata={"hnsw:space": "cosine"},
                                                        embedding_function=None)

    def add(self, chunks: list[Chunk], vectors, file_hash: str) -> None:
        self.col.add(ids=[c.id for c in chunks], embeddings=vectors, documents=[c.text for c in chunks],
                     metadatas=[dict(doc=c.doc, title=c.title, section=c.section, page=c.page, order=c.order,
                                     hash=file_hash) for c in chunks])

    def delete(self, doc: str) -> None:
        self.col.delete(where={"doc": doc})

    def hashes(self) -> dict[str, str]:
        return {m["doc"]: m["hash"] for m in self.col.get(include=["metadatas"])["metadatas"]}

    def all_chunks(self) -> list[Chunk]:
        got = self.col.get(include=["documents", "metadatas"])
        chunks = [Chunk(i, m["doc"], m["title"], m["section"], m["page"], m["order"], t)
                  for i, t, m in zip(got["ids"], got["documents"], got["metadatas"])]
        return sorted(chunks, key=lambda c: (c.doc, c.order))

    def query(self, vector, k: int, docs: list[str] | None = None) -> list[tuple[str, float]]:
        """Return (chunk id, cosine similarity), best first."""
        n = min(k, self.col.count())
        if not n:
            return []
        got = self.col.query(query_embeddings=[list(vector)], n_results=n, include=["distances"],
                             where={"doc": {"$in": docs}} if docs else None)
        return [(i, 1 - d) for i, d in zip(got["ids"][0], got["distances"][0])]
