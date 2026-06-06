"""
Multi-LLM Provider Registry
============================
Industry-standard provider abstraction that supports multiple LLM backends.
Validates API keys at startup and provides a unified interface for the
generator and router modules.

Supported providers:
  - Groq   (GROQ_API_KEY)
  - OpenAI (OPENAI_API_KEY)

To add a new provider, simply add an entry to PROVIDERS below.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Provider Registry
# ──────────────────────────────────────────────

PROVIDERS = {
    "Groq (LLaMA 3.1 8B)": {
        "backend": "groq",
        "model": "llama-3.1-8b-instant",
        "env_key": "GROQ_API_KEY",
    },
    "Groq (LLaMA 3.3 70B)": {
        "backend": "groq",
        "model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
    },
    "OpenAI (GPT-4o Mini)": {
        "backend": "openai",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "OpenAI (GPT-4o)": {
        "backend": "openai",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
}


def get_available_providers() -> list[str]:
    """Return only providers whose API key is present in the environment."""
    available = []
    for name, cfg in PROVIDERS.items():
        key = os.getenv(cfg["env_key"], "").strip()
        if key and key not in ("", "your_key_here", "sk-..."):
            available.append(name)
    return available


def get_all_provider_names() -> list[str]:
    """Return all registered provider names (regardless of key presence)."""
    return list(PROVIDERS.keys())


def validate_provider(provider_name: str) -> tuple[bool, str]:
    """
    Check whether a provider's API key is configured.

    Returns:
        (True,  "")            — key is valid
        (False, error_message) — key is missing or placeholder
    """
    if provider_name not in PROVIDERS:
        return False, f"Unknown provider: {provider_name}"

    cfg = PROVIDERS[provider_name]
    key = os.getenv(cfg["env_key"], "").strip()

    if not key or key in ("your_key_here", "sk-..."):
        return False, (
            f"🔑 API key not found for **{provider_name}**.\n\n"
            f"Please set `{cfg['env_key']}` in your `.env` file."
        )

    return True, ""


def get_provider_config(provider_name: str) -> dict:
    """
    Return the full config dict for a provider.
    Raises ValueError if provider is unknown or key is missing.
    """
    ok, err = validate_provider(provider_name)
    if not ok:
        raise ValueError(err)

    cfg = PROVIDERS[provider_name].copy()
    cfg["api_key"] = os.getenv(cfg["env_key"])
    return cfg


async def create_llm_client(provider_name: str):
    """
    Factory: return an async LLM client for the given provider.
    Supports Groq and OpenAI (both use the OpenAI-compatible interface).
    """
    cfg = get_provider_config(provider_name)

    if cfg["backend"] == "groq":
        from groq import AsyncGroq
        return AsyncGroq(api_key=cfg["api_key"]), cfg["model"]

    elif cfg["backend"] == "openai":
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=cfg["api_key"]), cfg["model"]

    else:
        raise ValueError(f"Unsupported backend: {cfg['backend']}")
