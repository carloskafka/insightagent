import importlib
import pathlib
import sys
import types

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def agent_module():
    original_agent = sys.modules.pop("app.agents.runtime", None)
    original_rag = sys.modules.get("app.integrations.rag_pipeline")
    original_config = sys.modules.get("app.core.config")

    fake_rag_pipeline = types.SimpleNamespace(search=lambda query, top_k=3: [])
    sys.modules["app.integrations.rag_pipeline"] = types.SimpleNamespace(rag_pipeline=fake_rag_pipeline)
    sys.modules["app.core.config"] = types.SimpleNamespace(
        OPENROUTER_API_KEY="",
        GOOGLE_SEARCH_API_KEY="",
        GOOGLE_CX="",
    )

    try:
        module = importlib.import_module("app.agents.runtime")
        yield module
    finally:
        sys.modules.pop("app.agents.runtime", None)
        if original_agent is not None:
            sys.modules["app.agents.runtime"] = original_agent
        if original_rag is not None:
            sys.modules["app.integrations.rag_pipeline"] = original_rag
        else:
            sys.modules.pop("app.integrations.rag_pipeline", None)
        if original_config is not None:
            sys.modules["app.core.config"] = original_config
        else:
            sys.modules.pop("app.core.config", None)


def test_agent_uses_safe_eval_for_math_queries(agent_module, monkeypatch):
    safe_eval_calls = []

    def fake_safe_eval(expr):
        safe_eval_calls.append(expr)
        return "4"

    def fail_llm(_messages):
        raise AssertionError("LLM should not be called for math queries")

    monkeypatch.setattr(agent_module, "_safe_eval", fake_safe_eval)
    monkeypatch.setattr(agent_module, "get_llm_response", fail_llm)

    response = agent_module.agent("2+2")

    assert response == "Result: 4"
    assert safe_eval_calls == ["2+2"]


def test_agent_uses_google_search_for_search_queries(agent_module, monkeypatch):
    search_calls = []

    def fake_google_search(query):
        search_calls.append(query)
        return [
            {"title": "Result 1", "link": "https://example.com/1"},
            {"title": "Result 2", "link": "https://example.com/2"},
        ]

    def fail_llm(_messages):
        raise AssertionError("LLM should not be called when search returns results")

    monkeypatch.setattr(agent_module, "google_search", fake_google_search)
    monkeypatch.setattr(agent_module, "get_llm_response", fail_llm)

    response = agent_module.agent("search python testing")

    assert search_calls == ["python testing"]
    assert response == (
        "Search results:\n"
        "- Result 1: https://example.com/1\n"
        "- Result 2: https://example.com/2"
    )


def test_agent_returns_api_instruction_for_api_queries(agent_module):
    response = agent_module.agent("call api https://example.com/users")

    assert response == "API calling requires structured input. Please use the /api/call endpoint directly."


def test_agent_uses_rag_context_when_available(agent_module, monkeypatch):
    llm_calls = []

    def fake_search(query, top_k=3):
        assert query == "What is in the docs?"
        assert top_k == 3
        return [
            {"text": "First context chunk"},
            {"text": "Second context chunk"},
        ]

    def fake_get_llm_response(messages):
        llm_calls.append(messages)
        return "Answer from RAG"

    monkeypatch.setattr(agent_module.rag_pipeline, "search", fake_search)
    monkeypatch.setattr(agent_module, "get_llm_response", fake_get_llm_response)

    response = agent_module.agent("What is in the docs?", use_rag=True, context="available")

    assert response == "Answer from RAG"
    assert llm_calls == [[
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use this context to answer:\n"
                "First context chunk\nSecond context chunk"
            ),
        },
        {"role": "user", "content": "What is in the docs?"},
    ]]


def test_agent_falls_back_to_llm_when_no_special_case_matches(agent_module, monkeypatch):
    llm_calls = []

    def fake_get_llm_response(messages):
        llm_calls.append(messages)
        return "Plain LLM answer"

    monkeypatch.setattr(agent_module, "get_llm_response", fake_get_llm_response)

    response = agent_module.agent("Tell me a joke", use_rag=False)

    assert response == "Plain LLM answer"
    assert llm_calls == [[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Tell me a joke"},
    ]]
