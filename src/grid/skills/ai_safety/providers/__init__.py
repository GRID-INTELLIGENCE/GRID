"""AI Safety Provider Skills Module.

Provider-specific safety skills implementing various AI safety frameworks.
"""

from __future__ import annotations

from grid.skills.base import SimpleSkill

from .anthropic import provider_anthropic
from .google import provider_google
from .llama import provider_llama
from .mistral import provider_mistral
from .nvidia import provider_nvidia
from .openai import provider_openai
from .xai import provider_xai

# Provider skills registry
PROVIDER_SKILLS: dict[str, SimpleSkill] = {
    "openai": provider_openai,
    "anthropic": provider_anthropic,
    "google": provider_google,
    "xai": provider_xai,
    "mistral": provider_mistral,
    "nvidia": provider_nvidia,
    "llama": provider_llama,
}

__all__ = [
    # Provider skills
    "provider_openai",
    "provider_anthropic",
    "provider_google",
    "provider_xai",
    "provider_mistral",
    "provider_nvidia",
    "provider_llama",
    # Registry
    "PROVIDER_SKILLS",
    # Utilities
    "get_provider_skill",
    "list_available_providers",
]


def get_provider_skill(provider_name: str) -> SimpleSkill | None:
    """Get a provider skill by name.

    Args:
        provider_name: Name of the provider (openai, anthropic, etc.).

    Returns:
        Provider skill or None if not found.
    """
    return PROVIDER_SKILLS.get(provider_name.lower())


def list_available_providers() -> list[str]:
    """List all available provider names.

    Returns:
        List of provider names.
    """
    return list(PROVIDER_SKILLS.keys())
