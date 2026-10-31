"""Klien LLM lokal lewat Ollama HTTP API. Tidak ada panggilan ke layanan AI publik."""

from typing import Protocol

import httpx

from pipeline.config import Settings


class LLMError(Exception):
    pass


class KlienLLM(Protocol):
    nama_model: str

    def chat_json(self, system: str, user: str, schema: dict, temperature: float) -> str:
        """Kirim prompt, kembalikan string JSON mentah dari model."""
        ...


class KlienOllama:
    def __init__(self, settings: Settings):
        self.host = settings.ollama_host.rstrip("/")
        self.nama_model = settings.ollama_model
        self.timeout = settings.ollama_timeout

    def chat_json(self, system: str, user: str, schema: dict, temperature: float) -> str:
        payload = {
            "model": self.nama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": schema,  # structured output: Ollama memaksa output mengikuti JSON Schema
            "stream": False,
            "think": False,  # model "thinking" dimatikan supaya cepat dan output langsung JSON
            "options": {"temperature": temperature},
        }
        try:
            r = httpx.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise LLMError(f"Tidak bisa menghubungi Ollama di {self.host}: {e}") from e
        if r.status_code == 400 and "think" in r.text:
            # model yang tidak mendukung opsi think: ulangi tanpa opsi itu
            payload.pop("think")
            r = httpx.post(f"{self.host}/api/chat", json=payload, timeout=self.timeout)
        if r.status_code != 200:
            raise LLMError(f"Ollama mengembalikan HTTP {r.status_code}: {r.text[:300]}")
        try:
            return r.json()["message"]["content"]
        except (ValueError, KeyError) as e:
            raise LLMError(f"Respons Ollama tidak terduga: {r.text[:300]}") from e
