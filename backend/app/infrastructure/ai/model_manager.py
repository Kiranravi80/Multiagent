"""
PAIOS Model Manager.

Unified interface for local LLM inference via Ollama.
Supports structured JSON output, retries, and optional Groq fallback.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import AIModelError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Manages LLM inference through Ollama (local) with optional Groq fallback.

    Usage:
        manager = ModelManager()
        response = await manager.generate("Summarize this text...")
        structured = await manager.generate_json("Extract data...", schema={...})
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Create the HTTP client for Ollama API calls."""
        self._client = httpx.AsyncClient(
            base_url=self._settings.ollama_base_url,
            timeout=httpx.Timeout(self._settings.ollama_timeout_seconds),
        )
        logger.info(
            "model_manager_initialized",
            base_url=self._settings.ollama_base_url,
            default_model=self._settings.ollama_default_model,
        )

    async def shutdown(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str = "",
        temperature: float = 0.0,
        max_retries: int | None = None,
    ) -> str:
        """
        Generate a text response from the LLM.

        Tries Ollama first. Falls back to Groq if configured and Ollama fails.

        Args:
            prompt: The user prompt.
            model: Override model name. Defaults to Settings.ollama_default_model.
            system: Optional system message.
            temperature: Sampling temperature.
            max_retries: Override max retries.

        Returns:
            The generated text response.

        Raises:
            AIModelError: If all providers fail.
        """
        model = model or self._settings.ollama_default_model
        retries = max_retries if max_retries is not None else self._settings.ollama_max_retries

        # Attempt Ollama
        for attempt in range(retries):
            try:
                return await self._ollama_generate(prompt, model=model, system=system, temperature=temperature)
            except Exception as exc:
                logger.warning(
                    "ollama_attempt_failed",
                    attempt=attempt + 1,
                    model=model,
                    error=str(exc),
                )
                if attempt == retries - 1:
                    logger.error("ollama_all_attempts_failed", model=model)

        # Attempt Groq fallback
        if self._settings.use_groq_fallback and self._settings.groq_api_key:
            logger.info("falling_back_to_groq")
            try:
                return await self._groq_generate(prompt, system=system, temperature=temperature)
            except Exception as exc:
                logger.error("groq_fallback_failed", error=str(exc))

        raise AIModelError(
            f"All LLM providers failed after {retries} attempts",
            model=model,
        )

    async def generate_json(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str = "",
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response from the LLM.

        Automatically strips markdown code fences and parses JSON.

        Raises:
            AIModelError: If response is not valid JSON.
        """
        raw = await self.generate(
            prompt,
            model=model,
            system=system or "You are a structured data extraction assistant. Always respond with valid JSON only.",
            temperature=temperature,
        )

        # Clean markdown code fences
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                "json_parse_failed",
                raw_response=raw[:500],
                error=str(exc),
            )
            raise AIModelError(
                "LLM response is not valid JSON",
                details={"raw_response": raw[:500], "parse_error": str(exc)},
            )

    async def health_check(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            if self._client is None:
                return False
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available models from Ollama."""
        try:
            if self._client is None:
                return []
            response = await self._client.get("/api/tags")
            if response.status_code != 200:
                return []
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    # ── Private: Ollama API ────────────────────────────────────────────────

    async def _ollama_generate(
        self,
        prompt: str,
        *,
        model: str,
        system: str = "",
        temperature: float = 0.0,
    ) -> str:
        """Call Ollama /api/generate endpoint."""
        if self._client is None:
            raise AIModelError("ModelManager not initialized. Call initialize() first.")

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        response = await self._client.post("/api/generate", json=payload)

        if response.status_code != 200:
            raise AIModelError(
                f"Ollama returned status {response.status_code}",
                model=model,
                details={"response": response.text[:500]},
            )

        data = response.json()
        return data.get("response", "")

    # ── Private: Groq Fallback ─────────────────────────────────────────────

    async def _groq_generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.0,
    ) -> str:
        """Call Groq API as fallback (development only)."""
        async with httpx.AsyncClient(timeout=60) as client:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._settings.groq_model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )

            if response.status_code != 200:
                raise AIModelError(
                    f"Groq returned status {response.status_code}",
                    model=self._settings.groq_model,
                )

            data = response.json()
            return data["choices"][0]["message"]["content"]
