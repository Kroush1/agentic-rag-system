import pytest

from rag.tools import Toolbox, safe_eval


@pytest.mark.parametrize("query,doc,section", [
    ("How many days of annual leave do employees get?", "hr_handbook.pdf", "Annual Leave"),
    ("hotel limit in Europe", "travel_expense_policy.docx", "Hotel and Daily Allowance Limits"),
    ("SEV1 response time", "it_security_policy.docx", "Incident Response"),
    ("كم عدد أيام الإجازة المرضية؟", "hr_handbook.pdf", "Sick Leave"),
    ("من هو المدير المالي للشركة؟", "company_overview.md", "Leadership"),
])
def test_search_finds_section(kb, query, doc, section):
    assert (doc, section) in [(c.doc, c.section) for c in kb.search(query)]


def test_search_document_filter(kb):
    assert {c.doc for c in kb.search("remote days per week", docs=["remote_work_policy_2023.md"])} == {
        "remote_work_policy_2023.md"}


def test_resolve_doc(kb):
    assert kb.resolve_doc("HR handbook") == "hr_handbook.pdf"
    assert kb.resolve_doc("annual_report_2024") == "annual_report_2024.pdf"
    assert kb.resolve_doc("Annual Report") is None  # ambiguous
    assert kb.resolve_doc("nothing") is None


def test_sql_matches_annual_report(kb):
    total = kb.sql("SELECT SUM(revenue_egp) FROM sales_data WHERE year = 2025").iloc[0, 0]
    assert f"{total / 1e6:.1f}" == "207.2"


@pytest.mark.parametrize("query", ["DROP TABLE sales_data", "DELETE FROM employees", "PRAGMA table_info(employees)",
                                   "ATTACH 'x.db' AS x", "INSERT INTO employees DEFAULT VALUES",
                                   "SELECT 1; SELECT 2"])
def test_sql_is_read_only(kb, query):
    with pytest.raises(Exception):
        kb.sql(query)


def test_sql_runaway_query_is_stopped(kb):
    with pytest.raises(Exception, match="interrupted"):
        kb.sql("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT COUNT(*) FROM c")


def test_calculator():
    assert safe_eval("(207.2-172.4)/172.4*100") == pytest.approx(20.1856, abs=1e-3)
    assert safe_eval("round(sum([1, 2, 3]) / 4, 1)") == 1.5


@pytest.mark.parametrize("bad", ["__import__('os')", "a+1", "9**9**9", "(1).real", "'x'*9", "1,000 EGP", "[x for x in (1,)]"])
def test_calculator_rejects(bad):
    with pytest.raises(Exception):
        safe_eval(bad)


def test_toolbox_numbers_sources_once(kb):
    box = Toolbox(kb)
    first = box.run("search_knowledge_base", '{"query": "annual leave days"}')
    count = len(box.registry.sources)
    assert first.startswith("[1]") and count == 4
    assert "seen before" in box.run("search_knowledge_base", '{"query": "annual leave days"}')
    assert len(box.registry.sources) == count


def test_toolbox_errors_are_text(kb):
    box = Toolbox(kb)
    assert box.run("search_knowledge_base", "{bad").startswith("Error")
    assert box.run("_docs", "{}").startswith("Error: unknown tool")
    assert box.run("calculate", '{"wrong": 1}').startswith("Error: wrong arguments")
    assert "Available" in box.run("summarize_document", '{"document": "nope"}')
    assert box.run("analyze_data", '{"sql": "SELECT nope FROM employees"}').startswith("SQL error")


def test_compare_documents(kb):
    out = Toolbox(kb).run("compare_documents", '{"topic": "remote days per week", "documents": '
                                               '["remote_work_policy_2023.md", "remote_work_policy_2026.md"]}')
    assert "1 day per week" in out and "3 days per week" in out
