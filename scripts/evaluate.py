"""Evaluate retrieval, and compare Standard RAG with Agentic RAG.

python scripts/evaluate.py --retrieval-only   (no API key needed)
python scripts/evaluate.py                    (full run, writes eval/results.md)

Answers are scored by checking that every expected value appears in the text.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rag.agent import AgenticRAG, StandardRAG
from rag.llm import GroqLLM, LLMError
from rag.retrieval import MODES, KnowledgeBase


def load(kb) -> list[dict]:
    """Expected values that depend on the data are computed here, not typed by hand."""
    gulf = kb.sql("SELECT year, SUM(revenue_egp) r FROM sales_data WHERE region='Gulf Export' GROUP BY year ORDER BY year").r
    units = kb.sql("SELECT SUM(units_sold) u FROM sales_data WHERE region='Gulf Export' AND year=2025 "
                   "GROUP BY product ORDER BY u DESC").u[0]
    salary = kb.sql("SELECT AVG(monthly_salary_egp) a FROM employees WHERE department='Engineering'").a[0]
    growth = (gulf[1] / gulf[0] - 1) * 100
    # The report tables are rounded, so growth computed from them may differ in the first decimal.
    values = {"{gulf_growth}": rf"{int(growth)}(\.\d+)?|{round(growth)}", "{gulf_top_units}": f"{units:,}|{units}",
              "{eng_salary}": f"{int(salary):,}|{int(salary)}|{round(salary):,}|{round(salary)}"}
    questions = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    for q in questions:
        q["expect"] = [values.get(e, e) for e in q["expect"]]
    return questions


def correct(answer: str, expect: list[str]) -> bool:
    # Models use narrow spaces and typographic hyphens in numbers such as "1 992" or "12-month".
    text = re.sub(r"(?<=\d)[   ](?=\d{3})", ",", answer)
    text = re.sub(r"[   ]", " ", text).replace("‑", "-").replace("’", "'")
    return all(re.search(rf"(?<![\d.])(?:{e})(?!\d)" if e[0].isdigit() else e, text, re.I) for e in expect)


def retrieval(kb, questions) -> list[str]:
    rows = ["| Mode | Recall of needed documents, top 4 |", "|---|---|"]
    for mode in MODES:
        hits = total = 0
        for q in questions:
            found = {c.doc for c in kb.search(q["question"], mode, 4)}
            hits += len(found & set(q["docs"]))
            total += len(q["docs"])
        rows.append(f"| {mode} | {hits}/{total} ({hits / total:.0%}) |")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval-only", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    kb = KnowledgeBase()
    kb.refresh(lambda _: None)
    questions = load(kb)
    lines = ["# Evaluation", "", "## Retrieval (one raw query, no agent)", "", *retrieval(kb, questions), ""]
    if args.retrieval_only:
        print("\n".join(lines))
        return
    try:
        llm = GroqLLM()
    except LLMError as e:
        sys.exit(str(e))
    systems = {"Standard": StandardRAG(kb, llm), "Agentic": AgenticRAG(kb, llm)}
    score = {name: [0, 0, 0.0] for name in systems}  # correct, tokens, seconds
    table, details, done = ["| Question | Type | Standard | Agentic | Tool calls |", "|---|---|---|---|---|"], [], 0
    for q in questions:
        marks, calls = {}, 0
        for name, system in systems.items():
            try:
                r = system.ask(q["question"])
            except LLMError as e:
                print(f"Stopped at {q['id']}: {e}")
                break
            marks[name] = correct(r.answer, q["expect"])
            calls = r.tool_calls
            details.append(f"### {q['id']} - {name} ({'correct' if marks[name] else 'wrong'})\n\n**Q:** {q['question']}\n\n"
                           f"{r.answer}\n\nSources: {'; '.join(s.label for s in r.sources) or 'none'}\n")
            score[name][1] += r.tokens
            score[name][2] += r.seconds
            time.sleep(3)  # stay inside the free per-minute limit
        if len(marks) < 2:
            break
        done += 1
        for name in systems:
            score[name][0] += marks[name]
        table.append(f"| {q['id']} | {q['type']} | {'yes' if marks['Standard'] else 'no'} | "
                     f"{'yes' if marks['Agentic'] else 'no'} | {calls} |")
        print(table[-1], flush=True)
    if not done:
        sys.exit(1)
    lines += ["## Answers", "", "| System | Correct | Average tokens | Average seconds |", "|---|---|---|---|"]
    lines += [f"| {n} | {s[0]}/{done} | {s[1] // done:,} | {s[2] / done:.1f} |" for n, s in score.items()]
    lines += ["", *table, "", "## All answers", "", *details]
    (ROOT / "eval" / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("Wrote eval/results.md")


if __name__ == "__main__":
    main()
