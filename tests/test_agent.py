"""Agent loop tests with a scripted LLM, so they need no API key."""
import json

import groq
import httpx
import pytest

from rag import llm as llm_module
from rag.agent import AgenticRAG, StandardRAG, approx_tokens, finalize_citations, fit, language
from rag.llm import GroqLLM, LLMError, Reply, ToolCall
from rag.tools import SourceRegistry

PLAN = Reply(json.dumps({"strategy": "multi_step", "reason": "r", "sub_questions": ["a"], "steps": ["b"]}))
OK = Reply('{"grounded": true, "complete": true, "issues": [], "suggested_query": ""}')
BAD = Reply('{"grounded": false, "complete": true, "issues": ["number unsupported"], "suggested_query": "q"}')


def call(name, n="1", **args):
    return Reply("", [ToolCall(n, name, json.dumps(args))])


class ScriptedLLM:
    def __init__(self, *replies):
        self.replies, self.requests = list(replies), []

    def chat(self, messages, tools=None, role="agent", **_):
        self.requests.append((messages, tools))
        return self.replies.pop(0)


def test_plan_tools_verify_answer(kb):
    llm = ScriptedLLM(PLAN, call("search_knowledge_base", query="annual leave"), call("calculate", expression="21+7"),
                      Reply("You get 21 days【1】 and [99]."), OK)
    events = list(AgenticRAG(kb, llm).run("How many leave days?"))
    assert [e.type for e in events] == ["plan", "tool", "tool", "verify", "answer"]
    result = events[-1].data["result"]
    assert "[1]" in result.answer and "99" not in result.answer
    assert [s.number for s in result.sources] == [1] and result.tool_calls == 2


def test_revision_after_failed_verification(kb):
    llm = ScriptedLLM(PLAN, call("search_knowledge_base", query="sick leave"), Reply("99 days [1]"), BAD,
                      call("search_knowledge_base", query="sick leave full pay"), Reply("15 days [1]"), OK)
    events = list(AgenticRAG(kb, llm).run("Sick leave?"))
    assert "revise" in [e.type for e in events]
    assert events[-1].data["result"].answer == "15 days [1]"


def test_revises_only_once(kb):
    llm = ScriptedLLM(PLAN, call("search_knowledge_base", query="sick leave"), Reply("x [1]"), BAD, Reply("y [1]"), BAD)
    result = AgenticRAG(kb, llm).ask("Sick leave?")
    assert result.answer == "y [1]" and result.verification["ok"] is False


def test_nudged_when_answering_without_retrieval(kb):
    llm = ScriptedLLM(PLAN, Reply("From memory."), call("search_knowledge_base", query="ceo"), Reply("Mariam [1]"), OK)
    assert AgenticRAG(kb, llm).ask("Who is the CEO?").answer == "Mariam [1]"


def test_direct_question_skips_retrieval_and_verification(kb):
    llm = ScriptedLLM(Reply('{"strategy": "direct"}'), Reply("Hello!"))
    result = AgenticRAG(kb, llm).ask("hi")
    assert result.answer == "Hello!" and result.tool_calls == 0 and result.verification == {}


def test_step_limit_forces_final_answer(kb):
    loops = [call("calculate", str(i), expression="1+1") for i in range(7)]
    llm = ScriptedLLM(PLAN, *loops, Reply("Done."), OK)
    assert AgenticRAG(kb, llm).ask("loop").answer == "Done."
    assert llm.requests[8][1] is None  # no tools offered on the forced final turn


def test_bad_planner_json_falls_back(kb):
    llm = ScriptedLLM(Reply("not json"), call("search_knowledge_base", query="x"), Reply("a [1]"), Reply("garbage"))
    result = AgenticRAG(kb, llm).ask("q")
    assert result.plan["strategy"] == "multi_step" and result.verification["checked"] is False


def test_standard_rag(kb):
    result = StandardRAG(kb, ScriptedLLM(Reply("21 days [1]"))).ask("annual leave days")
    assert result.sources[0].number == 1


def test_citation_styles():
    reg = SourceRegistry()
    for i in range(5):
        reg.add(str(i), f"doc{i}", "t")
    text, used = finalize_citations("a 【2†L1】 b [1, 3] c [٤] d [4-5] e [17] f [2024]", reg)
    assert text == "a [2] b [1][3] c [4] d [4][5] e  f"
    assert [s.number for s in used] == [1, 2, 3, 4, 5]


def test_language_detection():
    assert language("ما هي سياسة الـ remote work؟").startswith("Arabic")
    assert not language("What is the policy?").startswith("Arabic")


def test_fit_shortens_oldest_tool_output_first():
    msgs = [{"role": "system", "content": "s"}, {"role": "tool", "content": "x" * 20000}, {"role": "tool", "content": "y" * 4000}]
    out = fit(msgs)
    assert approx_tokens(out) <= 5000 and len(out[2]["content"]) == 4000 and len(msgs[1]["content"]) == 20000


# --- Groq wrapper ------------------------------------------------------------
def _error(cls, status, headers=None):
    response = httpx.Response(status, headers=headers or {}, request=httpx.Request("POST", "https://x"))
    return cls("boom", response=response, body={"error": {"message": "boom"}})


class FakeCompletions:
    def __init__(self, script):
        self.script, self.models = script, []

    def create(self, **args):
        self.models.append(args["model"])
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _ok():
    from types import SimpleNamespace as N
    return N(choices=[N(message=N(content="hi", tool_calls=None))], usage=N(total_tokens=5))


def _wrapped(monkeypatch, *script):
    slept = []
    monkeypatch.setattr(llm_module.time, "sleep", slept.append)
    client = GroqLLM("test")
    fake = FakeCompletions(list(script))
    client.client = type("C", (), {"chat": type("D", (), {"completions": fake})})
    return client, fake, slept


def test_rate_limit_waits_then_retries(monkeypatch):
    client, fake, slept = _wrapped(monkeypatch, _error(groq.RateLimitError, 429, {"retry-after": "3"}), _ok())
    assert client.chat([]).text == "hi" and len(set(fake.models)) == 1 and slept == [3.3]


def test_long_rate_limit_falls_back_to_next_model(monkeypatch):
    client, fake, slept = _wrapped(monkeypatch, _error(groq.RateLimitError, 429, {"retry-after": "900"}), _ok())
    assert client.chat([]).model == llm_module.AGENT_MODELS[1] and slept == []


def test_all_models_busy_raises_clear_error(monkeypatch):
    errors = [_error(groq.RateLimitError, 429, {"retry-after": "900"}) for _ in llm_module.AGENT_MODELS]
    client, *_ = _wrapped(monkeypatch, *errors)
    with pytest.raises(LLMError, match="rate limited"):
        client.chat([])


def test_auth_error(monkeypatch):
    client, *_ = _wrapped(monkeypatch, _error(groq.AuthenticationError, 401))
    with pytest.raises(LLMError, match="API key"):
        client.chat([])


def test_missing_key(monkeypatch):
    monkeypatch.setattr(llm_module, "groq_api_key", lambda: "")
    with pytest.raises(LLMError, match="GROQ_API_KEY"):
        GroqLLM()
