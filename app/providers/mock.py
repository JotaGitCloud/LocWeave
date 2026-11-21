"""Proveedor de demostración: no traduce, solo marca el texto. Útil para pruebas y para probar el flujo."""
from typing import List, Tuple

from .base import TranslationProvider


class MockProvider(TranslationProvider):
    name = "mock"
    label = "Demostración (no traduce)"

    def is_available(self) -> Tuple[bool, str]:
        return True, ""

    def translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        return [f"({target_lang}) {t}" for t in texts]
