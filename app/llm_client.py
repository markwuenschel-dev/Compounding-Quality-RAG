from __future__ import annotations

import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Any


DEFAULT_OPENAI_MODEL = "gpt-5-nano"
DEFAULT_OPENAI_API_KEY_ENV_VAR = "OPENAI_API_KEY"
DEFAULT_OPENAI_MODEL_ENV_VAR = "OPENAI_MODEL"

load_dotenv("secrets.env")

class LLMClientError(RuntimeError):
    """Raised when the LLM provider cannot return usable output."""


@dataclass
class OpenAIJsonClient:
    model: str = DEFAULT_OPENAI_MODEL
    api_key_env_var: str = DEFAULT_OPENAI_API_KEY_ENV_VAR

    def complete_json(self, prompt: str) -> str:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("prompt must not be empty")

        client = self._build_client()

        try:
            response = client.responses.create(
                model=self.model,
                input=clean_prompt,
            )
        except Exception as exc:
            raise LLMClientError("OpenAI request failed.") from exc

        return self._extract_output_text(response)

    def _build_client(self) -> Any:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMClientError(
                f"Missing required environment variable: {self.api_key_env_var}"
            )

        from openai import OpenAI

        return OpenAI(api_key=api_key)

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)

        if not isinstance(output_text, str) or not output_text.strip():
            raise LLMClientError("OpenAI response did not contain output_text.")

        return output_text.strip()


def openai_json_client_from_env() -> OpenAIJsonClient:
    return OpenAIJsonClient(
        model=os.getenv(DEFAULT_OPENAI_MODEL_ENV_VAR, DEFAULT_OPENAI_MODEL)
    )