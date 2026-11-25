"""Step 2 - cleaning: unicode, headers/footers, page numbers, hyphenation, spacing."""
import re
import unicodedata
from collections import defaultdict

from .extract import Block

PAGE_NO = re.compile(r"^\W*(page\s*)?\d+(\s*(of|/)\s*\d+)?\W*$", re.I)


def clean_text(text: str, keep_lines: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)  # in-\nformation -> information
    if not keep_lines:
        text = re.sub(r"\n(?!\s*[-*•]|\s*\d+[.)])", " ", text)  # unwrap lines, keep list items
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r" *\n *", "\n", text).strip()


def clean(blocks: list[Block]) -> list[Block]:
    pages_with = defaultdict(set)
    for b in blocks:
        if b.page:
            pages_with[_key(b.text)].add(b.page)
    n_pages = max((b.page for b in blocks), default=0)
    out = []
    for b in blocks:
        seen = len(pages_with[_key(b.text)]) if b.page else 0
        repeated = seen >= 2 and seen >= 0.6 * n_pages  # running header or footer
        if b.kind != "table" and b.page and (PAGE_NO.match(b.text) or repeated):
            continue
        text = clean_text(b.text, keep_lines=b.kind == "table")
        if text:
            out.append(Block(text, b.kind, b.level, b.page))
    return out


def _key(text: str) -> str:
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", text)).strip().lower()
