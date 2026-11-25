"""Registro de manejadores de formato."""
from pathlib import Path

from .base import FormatError, FormatHandler, ParsedEntry
from .csv_handler import CsvHandler
from .json_handler import JsonHandler
from .po_handler import PoHandler
from .properties_handler import PropertiesHandler
from .renpy_handler import RenpyHandler

_HANDLERS = [JsonHandler(), CsvHandler(), PoHandler(), PropertiesHandler(), RenpyHandler()]
SUPPORTED_EXTENSIONS = tuple(ext for h in _HANDLERS for ext in h.extensions)


def get_handler(path) -> FormatHandler:
    ext = Path(path).suffix.lower()
    for handler in _HANDLERS:
        if ext in handler.extensions:
            return handler
    raise FormatError(
        f"Formato no soportado: '{ext}'. Formatos disponibles: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


__all__ = ["get_handler", "SUPPORTED_EXTENSIONS", "FormatError", "FormatHandler", "ParsedEntry"]
