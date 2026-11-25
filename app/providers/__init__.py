"""Registro de proveedores de traducción."""
from .argos import ArgosProvider
from .base import ProviderError, TranslationProvider
from .mock import MockProvider

_PROVIDERS = {p.name: p for p in (ArgosProvider(), MockProvider())}
DEFAULT_PROVIDER = "argos"


def get_provider(name: str) -> TranslationProvider:
    try:
        return _PROVIDERS[name]
    except KeyError:
        raise ProviderError(f"Proveedor desconocido: {name}") from None


def provider_names():
    return list(_PROVIDERS)


def provider_labels():
    return {name: p.label for name, p in _PROVIDERS.items()}


__all__ = ["get_provider", "provider_names", "provider_labels", "ProviderError", "TranslationProvider",
           "DEFAULT_PROVIDER"]
