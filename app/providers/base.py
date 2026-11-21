"""Interfaz de proveedores de traducción (intercambiables)."""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

ProgressFn = Callable[[str, int, int], None]


class ProviderError(Exception):
    pass


class TranslationProvider(ABC):
    name = ""
    label = ""

    @abstractmethod
    def is_available(self) -> Tuple[bool, str]:
        """(disponible, mensaje explicativo si no lo está)."""

    def prepare(self, source_lang: str, target_lang: str, progress: Optional[ProgressFn] = None) -> None:
        """Deja listo el par de idiomas (p. ej. descargar modelos). Por defecto no hace nada."""

    @abstractmethod
    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        ...
