from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv


DEFAULT_OPENAI_MODEL = "gpt-5-nano"
DEFAULT_OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"
DEFAULT_OPENAI_MODEL_ENV_VAR = "OPENAI_MODEL"

# Latency controls. gpt-5 models support a "minimal" reasoning effort that emits
# very few reasoning tokens for the fastest time-to-first-token; this structured
# extraction is rule-constrained and does not need deep reasoning. Capping output
# tokens removes the long generation tail. Both are overridable per environment.
DEFAULT_REASONING_EFFORT = "minimal"
DEFAULT_MAX_OUTPUT_TOKENS = 1024
REASONING_EFFORT_ENV_VAR = "OPENAI_REASONING_EFFORT"
MAX_OUTPUT_TOKENS_ENV_VAR = "OPENAI_MAX_OUTPUT_TOKENS"

load_dotenv("secrets.env")


class LLMClientError(RuntimeError):
    """Raised when the LLM provider cannot return usable output."""


@lru_cache(maxsize=4)
def _shared_openai_client(api_key: str) -> Any:
    """Reuse one OpenAI client per API key.

    The client owns an HTTP connection pool (keep-alive, TLS). Rebuilding it on
    every request re-pays connection setup, so cache it per key for the process.
    """
    from openai import OpenAI

    return OpenAI(api_key=api_key)


@dataclass
class OpenAIJsonClient:
    model: str = DEFAULT_OPENAI_MODEL
    api_key_env_var: str = DEFAULT_OPENAI_API_KEY_ENV_VAR
    reasoning_effort: str | None = DEFAULT_REASONING_EFFORT
    max_output_tokens: int | None = DEFAULT_MAX_OUTPUT_TOKENS

    def complete_json(self, prompt: str) -> str:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("System prompt must not be empty")

        client = self._build_client()

        request: dict[str, Any] = {
            "model": self.model,
            "input": clean_prompt,
        }
        if self.max_output_tokens is not None:
            request["max_output_tokens"] = self.max_output_tokens
        if self.reasoning_effort:
            request["reasoning"] = {"effort": self.reasoning_effort}

        try:
            response = client.responses.create(**request)
        except Exception as exc:
            raise LLMClientError("OpenAI request failed.") from exc

        return self._extract_output_text(response)

    def _build_client(self) -> Any:
        api_key = os.getenv(self.api_key_env_var)
        if not api_key:
            raise LLMClientError(
                f"Missing required environment variable: {self.api_key_env_var}"
            )

        return _shared_openai_client(api_key)

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)

        if not isinstance(output_text, str) or not output_text.strip():
            raise LLMClientError("OpenAI response did not contain output_text.")

        return output_text.strip()


def _int_env(name: str, default: int | None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def openai_json_client_from_env() -> OpenAIJsonClient:
    return OpenAIJsonClient(
        model=os.getenv(DEFAULT_OPENAI_MODEL_ENV_VAR, DEFAULT_OPENAI_MODEL),
        reasoning_effort=os.getenv(REASONING_EFFORT_ENV_VAR, DEFAULT_REASONING_EFFORT)
        or None,
        max_output_tokens=_int_env(
            MAX_OUTPUT_TOKENS_ENV_VAR, DEFAULT_MAX_OUTPUT_TOKENS
        ),
    )
