"""
Secrets reference provider.

Secrets are passed as references (e.g., "env:PASSWORD"), not raw values.
This prevents accidental logging/bundling of sensitive data.

The reference format is: "<provider>:<key>"
- env:VAR_NAME - environment variable
- keyring:SERVICE/ACCOUNT - OS keychain (future)

In logs and artifacts, only the reference is stored, never the value.
"""

from __future__ import annotations

import os
from typing import Protocol


class SecretsProvider(Protocol):
    """Protocol for resolving secret references to values."""

    def get(self, ref: str) -> str | None:
        """
        Resolve a secret reference to its value.

        Args:
            ref: Secret reference (e.g., "env:PASSWORD")

        Returns:
            The secret value, or None if not found.
        """
        ...

    def supports(self, ref: str) -> bool:
        """
        Check if this provider can handle the given reference.

        Args:
            ref: Secret reference

        Returns:
            True if this provider can resolve the reference.
        """
        ...


class EnvSecretsProvider:
    """
    Resolve secrets from environment variables.

    Reference format: "env:VAR_NAME"
    Example: "env:NEO4J_PASSWORD" resolves to os.environ["NEO4J_PASSWORD"]
    """

    PREFIX = "env:"

    def supports(self, ref: str) -> bool:
        return ref.startswith(self.PREFIX)

    def get(self, ref: str) -> str | None:
        if not self.supports(ref):
            return None
        var_name = ref[len(self.PREFIX) :]
        return os.environ.get(var_name)


class CompositeSecretsProvider:
    """
    Combine multiple secrets providers.

    Tries each provider in order until one returns a value.
    """

    def __init__(self, providers: list[SecretsProvider] | None = None):
        self.providers = providers or [EnvSecretsProvider()]

    def supports(self, ref: str) -> bool:
        return any(p.supports(ref) for p in self.providers)

    def get(self, ref: str) -> str | None:
        for provider in self.providers:
            if provider.supports(ref):
                value = provider.get(ref)
                if value is not None:
                    return value
        return None


def resolve_secrets(
    refs: dict[str, str],
    provider: SecretsProvider | None = None,
) -> dict[str, str]:
    """
    Resolve a dict of secret references to values.

    Args:
        refs: Dict mapping names to references (e.g., {"password": "env:NEO4J_PASSWORD"})
        provider: Secrets provider (defaults to CompositeSecretsProvider)

    Returns:
        Dict mapping names to resolved values.
        Missing secrets are omitted from the result.
    """
    provider = provider or CompositeSecretsProvider()
    result: dict[str, str] = {}
    for name, ref in refs.items():
        value = provider.get(ref)
        if value is not None:
            result[name] = value
    return result
