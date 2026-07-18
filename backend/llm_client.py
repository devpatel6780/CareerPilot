"""Thin, swappable abstraction over the LLM provider.

Currently wraps NVIDIA NIM (via langchain-nvidia-ai-endpoints). Agent logic
should only ever call generate()/get_client() from this module, never touch
ChatNVIDIA directly, so a future provider swap doesn't ripple into agents.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"


class LLMClient:
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None,
                 max_retries: int = 3, backoff_seconds: float = 2.0):
        self.api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA_NIM_API_KEY is not set (check your .env file)")
        self.model = model
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._client = ChatNVIDIA(
            model=self.model,
            api_key=self.api_key,
            max_completion_tokens=2048,
            temperature=0,
            seed=0,
        )

    def generate(self, prompt: str, schema: dict | None = None):
        client = self._client.with_structured_output(schema) if schema else self._client

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = client.invoke(prompt)
                return result if schema else result.content
            except Exception as exc:  # NIM free tier can rate-limit; retry with backoff
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
        raise RuntimeError(f"NVIDIA NIM call failed after {self.max_retries} attempts") from last_error


_default_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


def generate(prompt: str, schema: dict | None = None):
    return get_client().generate(prompt, schema=schema)
