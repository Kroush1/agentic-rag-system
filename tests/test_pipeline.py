import shutil

from rag.ingest.chunk import split_text
from rag.ingest.clean import clean, clean_text
from rag.ingest.extract import Block
from rag.ingest.pipeline import ingest, process_file
from rag.ingest.store import VectorStore


def test_pdf_headers_removed_and_tables_kept(files):
    chunks = process_file(files["annual_report_2025.pdf"])
    text = "\n".join(c.text for c in chunks)
    assert "Internal use only" not in text and "Page 1" not in text
    assert "Gulf Export | 40.5" in text
    assert {c.section for c in chunks} >= {"Financial Highlights", "Outlook"}
    assert next(c for c in chunks if c.section == "Outlook").page == 3


def test_docx_tables_and_headings(files):
    chunks = process_file(files["travel_expense_policy.docx"])
    hotel = next(c for c in chunks if c.section.startswith("Hotel"))
    assert "Gulf countries | USD 180 | USD 60" in hotel.text


def test_clean_text():
    assert clean_text("infor-\nmation  and\nmore​") == "information and more"


def test_clean_keeps_text_repeated_on_one_page_only():
    blocks = [Block("same", page=1), Block("same", page=1), Block("other", page=2), Block("2", page=2)]
    assert [b.text for b in clean(blocks)] == ["same", "same", "other"]


def test_split_respects_size_and_overlaps():
    text = " ".join(f"Sentence number {i} has some words." for i in range(100))
    pieces = split_text(text, 300, 80)
    assert all(len(p) <= 300 for p in pieces)
    assert pieces[0].split("\n")[-1] in pieces[1]
    assert all(f"number {i} " in " ".join(pieces) for i in range(100))


def test_split_text_without_spaces_terminates():
    assert "".join(split_text("x" * 2500, 900, 150)) == "x" * 2500


def test_incremental_ingest(files, tmp_path):
    copy = tmp_path / "company_overview.md"
    shutil.copy(files["company_overview.md"], copy)
    store = VectorStore(tmp_path / "db")
    quiet = lambda _: None
    assert ingest(store, quiet, {copy.name: copy})["added"] == [copy.name]
    assert ingest(store, quiet, {copy.name: copy})["unchanged"] == [copy.name]
    copy.write_text("# New\n\nOnly this text remains.", encoding="utf-8")
    assert ingest(store, quiet, {copy.name: copy})["added"] == [copy.name]
    assert [c.text for c in store.all_chunks()] == ["Only this text remains."]
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    report = ingest(store, quiet, {bad.name: bad})
    assert "bad.pdf" in report["failed"] and report["removed"] == [copy.name]
