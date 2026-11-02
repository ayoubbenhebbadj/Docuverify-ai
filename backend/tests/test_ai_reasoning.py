from types import SimpleNamespace

import pytest

from app import ai_extractor


def _response(finish="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content="{}"))],
        usage=SimpleNamespace(completion_tokens=10, completion_tokens_details=SimpleNamespace(reasoning_tokens=0)),
    )


def test_reasoning_off_by_default_for_openrouter(monkeypatch):
    monkeypatch.delenv("AI_REASONING", raising=False)
    assert ai_extractor.reasoning_extra_body() == {"reasoning": {"enabled": False}}


@pytest.mark.parametrize("mode,expected", [
    ("low", {"reasoning": {"effort": "low"}}),
    ("default", {}),
    ("off", {"reasoning": {"enabled": False}}),
])
def test_reasoning_modes(monkeypatch, mode, expected):
    monkeypatch.setenv("AI_REASONING", mode)
    assert ai_extractor.reasoning_extra_body() == expected


def test_other_providers_get_no_reasoning_option(monkeypatch):
    monkeypatch.setattr(ai_extractor, "AI_PROVIDER", "groq")
    assert ai_extractor.reasoning_extra_body() == {}


def test_reasoning_option_is_sent_and_dropped_if_provider_rejects(monkeypatch):
    calls = []

    def fake_create(**kwargs):
        calls.append(dict(kwargs))
        if "extra_body" in kwargs:
            raise RuntimeError("Unsupported parameter: reasoning")
        return _response()

    monkeypatch.setattr(ai_extractor.client.chat.completions, "create", fake_create)
    ai_extractor.create_with_retry(model="m", messages=[], max_tokens=100)
    assert "extra_body" in calls[0] and "extra_body" not in calls[1]
    assert len(calls) == 2


def test_caller_supplied_extra_body_is_respected(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        ai_extractor.client.chat.completions, "create",
        lambda **kw: seen.update(kw) or _response(),
    )
    ai_extractor.create_with_retry(model="m", messages=[], max_tokens=10, extra_body={"x": 1})
    assert seen["extra_body"] == {"x": 1}


def test_truncated_answers_retry_with_double_budget(monkeypatch):
    budgets = []

    def fake_create(**kw):
        budgets.append(kw["max_tokens"])
        return _response("length" if len(budgets) == 1 else "stop")

    monkeypatch.setattr(ai_extractor.client.chat.completions, "create", fake_create)
    ai_extractor.create_with_retry(model="m", messages=[], max_tokens=100)
    assert budgets == [100, 200]
