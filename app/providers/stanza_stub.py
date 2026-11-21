"""Soporte de la variante liviana (sin PyTorch/stanza) para Argos Translate.

Argos importa `stanza` al cargarse y, según el paquete de idioma, lo usa para separar oraciones. LocWeave no incluye
`stanza` (pesa cientos de MB por PyTorch) y usa en su lugar el separador `minisbd` (ONNX, ya incluido).
Si `stanza` no está instalado, `install_if_missing()`:
  1. registra un módulo `stanza` vacío (cualquier uso real lanza AttributeError),
  2. hace que Argos use `MiniSBDSentencizer` donde pediría `StanzaSentencizer`.
"""
import importlib
import importlib.util
import sys
import types


def _prefer_minisbd() -> None:
    """Redirige el separador de oraciones de Argos a minisbd (mejor esfuerzo; no debe romper nada)."""
    try:
        settings = importlib.import_module("argostranslate.settings")
        chunk = getattr(settings, "ChunkType", None)
        if chunk is not None and hasattr(chunk, "MINISBD"):
            settings.chunk_type = chunk.MINISBD
        sbd = importlib.import_module("argostranslate.sbd")
        if hasattr(sbd, "MiniSBDSentencizer"):
            sbd.StanzaSentencizer = sbd.MiniSBDSentencizer
    except Exception:  # noqa: BLE001 - si algo falla, Argos mostrará su propio error al traducir
        pass


def install_if_missing() -> bool:
    """Registra el sustituto si `stanza` no existe. Devuelve True si lo registró."""
    if "stanza" in sys.modules or importlib.util.find_spec("stanza") is not None:
        return False
    stub = types.ModuleType("stanza")

    def _missing(name):
        # AttributeError (no ImportError): inspect/PySide consultan atributos como __wrapped__.
        raise AttributeError(f"'stanza.{name}' no está incluido en la versión liviana de LocWeave (sin PyTorch).")

    stub.__getattr__ = _missing  # type: ignore[attr-defined]
    sys.modules["stanza"] = stub
    _prefer_minisbd()
    return True
