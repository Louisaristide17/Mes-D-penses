"""Appel au modèle de langage, par l'interface « chat completions » compatible OpenAI de Groq."""

import logging
from typing import Protocol

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

TIMEOUT = 45


class LLMUnavailable(Exception):
    """Le fournisseur n'a pas répondu, ou a refusé la requête."""


class LLMClient(Protocol):
    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        """Renvoie le message de l'assistant : son texte, ou les outils qu'il demande d'appeler."""


class GroqClient:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.url = f"{base_url.rstrip('/')}/chat/completions"

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            # Température basse : l'agent rapporte des chiffres, il n'a pas à être créatif.
            "temperature": 0.2,
        }
        try:
            response = httpx.post(
                self.url, json=payload, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=TIMEOUT
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]
        except httpx.HTTPStatusError as exc:
            # Le corps de l'erreur est journalisé côté serveur, jamais renvoyé au client.
            logger.error("Groq a répondu %s : %s", exc.response.status_code, exc.response.text[:500])
            raise LLMUnavailable from exc
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            logger.error("Appel à Groq impossible : %s", exc)
            raise LLMUnavailable from exc


def get_llm() -> LLMClient | None:
    """Client configuré, ou None si aucune clé n'est renseignée."""
    settings = get_settings()
    if not settings.groq_api_key:
        return None
    return GroqClient(settings.groq_api_key, settings.groq_model, settings.groq_base_url)
