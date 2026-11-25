import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.config import DOCUMENTS_DIR
from rag.ingest.pipeline import ingest, source_files
from rag.ingest.store import VectorStore
from rag.retrieval import KnowledgeBase


@pytest.fixture(scope="session")
def files():
    return source_files((DOCUMENTS_DIR,))


@pytest.fixture(scope="session")
def kb(files, tmp_path_factory):
    store = VectorStore(tmp_path_factory.mktemp("chroma"))
    report = ingest(store, lambda _: None, files)
    assert not report["failed"]
    return KnowledgeBase(store, files)
