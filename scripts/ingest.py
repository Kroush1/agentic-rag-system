"""Build or refresh the knowledge base:  python scripts/ingest.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.ingest.pipeline import ingest
from rag.ingest.store import VectorStore

store = VectorStore()
report = ingest(store)
print({k: len(v) for k, v in report.items()}, "| total chunks:", store.col.count())
sys.exit(1 if report["failed"] else 0)
