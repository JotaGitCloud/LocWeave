"""Interfaz común para los manejadores de formato (etapas de Ingesta y Exportación)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class ParsedEntry:
    key: str
    text: str
    context: str = ""
    existing: str = ""  # traducción ya presente en el archivo, si existe


class FormatError(Exception):
    pass


def read_text(path) -> str:
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeError:
            continue
    return raw.decode("latin-1")


def has_letters(text: str) -> bool:
    return any(c.isalpha() for c in text)


class FormatHandler(ABC):
    name = ""
    extensions: tuple = ()

    @abstractmethod
    def parse(self, path) -> List[ParsedEntry]:
        """Extrae los textos traducibles del archivo."""

    @abstractmethod
    def export(self, source_path, output_path, translations: Dict[str, str], target_lang: str) -> None:
        """Escribe una copia del archivo original con las traducciones aplicadas."""
