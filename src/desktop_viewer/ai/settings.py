from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import keyring

logger = logging.getLogger(__name__)

# A single OS-keychain "service" holds every stored value; each value is
# addressed by a distinct username. keyring maps this onto Windows Credential
# Locker / macOS Keychain / a Secret Service provider on Linux.
SERVICE_NAME = "enma-desktop-viewer"

PROVIDERS = ("openai", "anthropic")
DEFAULT_PROVIDER = "openai"

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-5",
}

ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


@dataclass
class AiSettings:
    provider: str
    model: str
    api_key: Optional[str]


def _get_password(username: str) -> Optional[str]:
    try:
        return keyring.get_password(SERVICE_NAME, username)
    except keyring.errors.KeyringError:
        # No usable backend (e.g. a headless CI box) - fall back to env vars
        # rather than crashing app startup over BYOK convenience storage.
        logger.warning("OS keychain unavailable; falling back to env vars", exc_info=True)
        return None


def load_ai_settings() -> AiSettings:
    provider = _get_password("provider") or DEFAULT_PROVIDER
    if provider not in PROVIDERS:
        provider = DEFAULT_PROVIDER

    model = _get_password(f"{provider}_model") or DEFAULT_MODELS[provider]

    api_key = _get_password(f"{provider}_api_key")
    if not api_key:
        api_key = os.environ.get(ENV_VARS[provider])

    return AiSettings(provider=provider, model=model, api_key=api_key)


def save_ai_settings(settings: AiSettings) -> None:
    if settings.provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {settings.provider!r}; expected one of {PROVIDERS}")

    keyring.set_password(SERVICE_NAME, "provider", settings.provider)
    keyring.set_password(SERVICE_NAME, f"{settings.provider}_model", settings.model)
    if settings.api_key:
        keyring.set_password(SERVICE_NAME, f"{settings.provider}_api_key", settings.api_key)
