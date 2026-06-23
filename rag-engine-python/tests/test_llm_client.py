from __future__ import annotations

import pytest

from app.llm_client import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_REASONING_EFFORT,
    LLMClientError,
    OpenAIJsonClient,
    openai_json_client_from_env,
)


class FakeOpenAIResponse:
    def __init__(self, output_text: object) -> None:
        self.output_text = output_text


class FakeResponsesResource:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> FakeOpenAIResponse:
        self.calls.append(kwargs)
        return FakeOpenAIResponse(self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text: str = '{"ok": true}') -> None:
        self.responses = FakeResponsesResource(output_text)


class FakeOpenAIJsonClient(OpenAIJsonClient):
    def __init__(self, fake_client: FakeOpenAIClient, model: str = "gpt-5-nano", api_key_env_var = "OPENAI_API_KEY") -> None:
        super().__init__(model = model, api_key_env_var=api_key_env_var)
        self.fake_client = fake_client

    def _build_client(self) -> FakeOpenAIClient:
        return self.fake_client


def test_complete_json_sends_prompt_to_responses_api() -> None:
    fake_client = FakeOpenAIClient(output_text='{"record_review_result": "no_discrepancy_found"}')
    client = FakeOpenAIJsonClient(fake_client=fake_client, model="gpt-5-nano")

    result = client.complete_json("Return JSON")

    assert result == '{"record_review_result": "no_discrepancy_found"}'
    assert fake_client.responses.calls == [
        {
            "model": "gpt-5-nano",
            "input": "Return JSON",
            "max_output_tokens": DEFAULT_MAX_OUTPUT_TOKENS,
            "reasoning": {"effort": DEFAULT_REASONING_EFFORT},
        }
    ]


def test_complete_json_omits_optional_params_when_unset() -> None:
    fake_client = FakeOpenAIClient()
    client = FakeOpenAIJsonClient(fake_client=fake_client)
    client.reasoning_effort = None
    client.max_output_tokens = None

    client.complete_json("Return JSON")

    assert fake_client.responses.calls == [
        {"model": "gpt-5-nano", "input": "Return JSON"}
    ]


def test_complete_json_rejects_empty_prompt() -> None:
    client = FakeOpenAIJsonClient(fake_client=FakeOpenAIClient())

    with pytest.raises(ValueError, match="prompt must not be empty"):
        client.complete_json("   ")


def test_extract_output_text_strips_response_text() -> None:
    client = FakeOpenAIJsonClient(fake_client=FakeOpenAIClient())

    result = client._extract_output_text(FakeOpenAIResponse('  {"ok": true}  '))

    assert result == '{"ok": true}'


@pytest.mark.parametrize("bad_output", [None, "", "   ", 123])
def test_extract_output_text_rejects_missing_or_non_string_output(bad_output: object) -> None:
    client = FakeOpenAIJsonClient(fake_client=FakeOpenAIClient())

    with pytest.raises(LLMClientError, match="did not contain output_text"):
        client._extract_output_text(FakeOpenAIResponse(bad_output))


def test_build_client_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = OpenAIJsonClient()

    with pytest.raises(LLMClientError, match="Missing required environment variable"):
        client._build_client()


def test_openai_json_client_from_env_uses_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    client = openai_json_client_from_env()

    assert client.model == DEFAULT_OPENAI_MODEL


def test_openai_json_client_from_env_allows_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")

    client = openai_json_client_from_env()

    assert client.model == "gpt-5-nano"
