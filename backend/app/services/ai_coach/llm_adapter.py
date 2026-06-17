"""
LLM Adapter — OpenRouter integration with rules-based fallback.

Uses OpenRouter API when OPENROUTER_API_KEY is set, otherwise falls back
to the deterministic placeholder.
"""

from __future__ import annotations

import json
import os
from typing import Any

from app.config import settings


class LLMAdapter:
    """Interface for generating narrative coaching text via an LLM.

    When OPENROUTER_API_KEY is set, calls OpenRouter (OpenAI-compatible).
    Otherwise falls back to a deterministic placeholder.
    """

    TIMEOUT = 30
    _OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def _build_prompt(self, stats: dict, leaks: list[str]) -> list[dict[str, str]]:
        """Build the chat messages for the LLM."""
        stats_summary = json.dumps(stats, indent=2)
        leaks_summary = "\n".join(f"- {l}" for l in leaks) if leaks else "No significant leaks detected."

        system = (
            "You are an expert poker coach. Given a player's statistics and detected leaks, "
            "generate a concise, actionable coaching report (2-3 paragraphs). "
            "Focus on the most impactful improvements. Be specific and encouraging."
        )

        user = (
            f"Player stats:\n{stats_summary}\n\n"
            f"Detected leaks:\n{leaks_summary}\n\n"
            "Please provide a personalized coaching report."
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _call_openrouter(self, messages: list[dict[str, str]]) -> str | None:
        """Call OpenRouter API. Returns response text or None on failure."""
        try:
            import httpx
        except ImportError:
            return None

        api_key = settings.OPENROUTER_API_KEY
        if not api_key:
            return None

        model = settings.OPENROUTER_MODEL
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if os.environ.get("OPENROUTER_HTTP_REFERER"):
            headers["HTTP-Referer"] = os.environ["OPENROUTER_HTTP_REFERER"]
        if os.environ.get("OPENROUTER_X_TITLE"):
            headers["X-Title"] = os.environ["OPENROUTER_X_TITLE"]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
        }

        try:
            with httpx.Client(timeout=self.TIMEOUT) as client:
                resp = client.post(self._OPENROUTER_URL, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def generate_report(self, stats: dict, leaks: list[str]) -> str:
        """Return a personalised narrative report.

        Tries OpenRouter first; falls back to placeholder on failure.
        """
        if self.is_available():
            messages = self._build_prompt(stats, leaks)
            result = self._call_openrouter(messages)
            if result:
                return result

        return "LLM integration coming soon — using rules-based engine for now."

    def is_available(self) -> bool:
        """Return True when the backing LLM service is configured."""
        return bool(settings.OPENROUTER_API_KEY)
