"""Step 1 - text extraction. Every format becomes a list of Blocks."""
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import docx
import pandas as pd
import pymupdf

TEXT_TYPES = {".pdf", ".docx", ".md", ".txt"}
TABLE_TYPES = {".csv", ".xlsx"}
SUPPORTED = TEXT_TYPES | TABLE_TYPES


@dataclass
class Block:
    text: str
    kind: str = "para"  # heading | para | table
    level: int = 0
    page: int = 0


def extract(path: Path) -> list[Block]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf(path)
    if suffix == ".docx":
        return _docx(path)
    if suffix in {".md", ".txt"}:
        return _markdown(path.read_text(encoding="utf-8", errors="replace"))
    if suffix in TABLE_TYPES:
        return _table_card(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def load_tables(path: Path) -> dict[str, pd.DataFrame]:
    """Table name -> DataFrame for CSV/XLSX files."""
    if path.suffix.lower() == ".csv":
        return {table_name(path.stem): pd.read_csv(path)}
    sheets = pd.read_excel(path, sheet_name=None)
    if len(sheets) == 1:
        return {table_name(path.stem): next(iter(sheets.values()))}
    return {table_name(f"{path.stem}_{sheet}"): df for sheet, df in sheets.items()}


def table_name(text: str) -> str:
    name = re.sub(r"\W+", "_", text.lower()).strip("_") or "data"
    return f"t_{name}" if name[0].isdigit() else name


def describe_table(name: str, df: pd.DataFrame) -> str:
    """Compact schema used for search and in the agent prompt."""
    cols = []
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            cols.append(f"{col} (empty)")
        elif pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            cols.append(f"{col} (number {s.min():.15g} to {s.max():.15g})")
        elif s.nunique() <= 8:
            cols.append(f"{col} (one of: {', '.join(str(v)[:40] for v in s.unique())})")
        else:
            cols.append(f"{col} (text, e.g. {str(s.iloc[0])[:40]})")
    return f"Table {name}, {len(df)} rows. Columns: " + "; ".join(cols) + "."


def _table_card(path: Path) -> list[Block]:
    blocks = []
    for name, df in load_tables(path).items():
        blocks.append(Block(f"Data table {name}", "heading", 1))
        blocks.append(Block(describe_table(name, df)))
    return blocks


def _rows_to_text(rows) -> str:
    return "\n".join(" | ".join(re.sub(r"\s+", " ", str(c or "")).strip() for c in r) for r in rows)


def _pdf(path: Path) -> list[Block]:
    sizes, pages = Counter(), []
    with pymupdf.open(path) as doc:
        for page in doc:
            tables = page.find_tables().tables
            items = [(t.bbox[1], Block(_rows_to_text(t.extract()), "table", page=page.number + 1), 0) for t in tables]
            for b in page.get_text("dict")["blocks"]:
                if b["type"] != 0:
                    continue
                cx, cy = (b["bbox"][0] + b["bbox"][2]) / 2, (b["bbox"][1] + b["bbox"][3]) / 2
                if any(t.bbox[0] <= cx <= t.bbox[2] and t.bbox[1] <= cy <= t.bbox[3] for t in tables):
                    continue
                # One MuPDF block may hold a heading and its paragraph: split where the font size changes.
                for size, group in _by_size(b["lines"]):
                    text = "\n".join("".join(s["text"] for s in ln["spans"]) for ln in group).strip()
                    if text:
                        sizes[size] += len(text)
                        items.append((group[0]["bbox"][1], Block(text, page=page.number + 1), size))
            pages.append(sorted(items, key=lambda x: x[0]))
    body = sizes.most_common(1)[0][0] if sizes else 10
    big = sorted((s for s in sizes if s > body * 1.15), reverse=True)
    out = []
    for items in pages:
        for _, block, size in items:
            if size in big and len(block.text) < 120:
                block.kind, block.level = "heading", big.index(size) + 1
            out.append(block)
    return out


def _by_size(lines):
    groups = []
    for ln in lines:
        size = max((round(s["size"], 1) for s in ln["spans"]), default=0)
        if groups and groups[-1][0] == size:
            groups[-1][1].append(ln)
        else:
            groups.append((size, [ln]))
    return groups


def _docx(path: Path) -> list[Block]:
    out = []
    for item in docx.Document(str(path)).iter_inner_content():
        if isinstance(item, docx.table.Table):
            out.append(Block(_rows_to_text([[c.text for c in r.cells] for r in item.rows]), "table"))
        elif item.text.strip():
            style = item.style.name if item.style else ""
            if style == "Title":
                out.append(Block(item.text, "heading", 1))
            elif match := re.match(r"Heading (\d)", style):
                out.append(Block(item.text, "heading", int(match[1]) + 1))
            else:
                out.append(Block(item.text))
    return out


def _markdown(text: str) -> list[Block]:
    out = []
    for para in re.split(r"\n\s*\n|(?=^#{1,6} )", text, flags=re.M):
        para = para.strip()
        head, _, rest = para.partition("\n")
        if match := re.match(r"(#{1,6})\s+(.*)", head):
            out.append(Block(match[2], "heading", len(match[1])))
            para = rest.strip()
        if para:
            out.append(Block(para, "table" if para.startswith("|") else "para"))
    return out
