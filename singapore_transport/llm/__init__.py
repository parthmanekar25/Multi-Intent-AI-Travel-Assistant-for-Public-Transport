"""Groq LLM client with Gemini-compatible .generate_content helper."""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq

from singapore_transport.config import get_settings

logger = logging.getLogger(__name__)


class GroqModel:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self._client: Groq | None = None

    @property
    def client(self) -> Groq:
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def generate_content(self, prompt: str, *, json_mode: bool = False) -> Any:
        try:
            kwargs: dict[str, Any] = {
                "messages": [{"role": "user", "content": prompt}],
                "model": self.model,
                "temperature": 0,
            }
            if json_mode or "json" in prompt.lower():
                kwargs["response_format"] = {"type": "json_object"}

            completion = self.client.chat.completions.create(**kwargs)
            text = completion.choices[0].message.content or ""
            return type("obj", (), {"text": text})
        except Exception as exc:  # noqa: BLE001 — surface soft failure to caller
            logger.exception("Groq API error: %s", exc)
            return type("obj", (), {"text": "{}"})

    def generate_json(self, prompt: str) -> dict[str, Any]:
        response = self.generate_content(prompt, json_mode=True)
        text = (response.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            logger.warning("Failed to parse Groq JSON: %s", text[:200])
            return {}


_default_model: GroqModel | None = None


def get_llm() -> GroqModel:
    global _default_model
    if _default_model is None:
        _default_model = GroqModel()
    return _default_model
