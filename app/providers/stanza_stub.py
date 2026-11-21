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


def _make_stub(name: str) -> types.ModuleType:
    stub = types.ModuleType(name)

    def _missing(attr):
        # AttributeError (no ImportError): inspect/PySide consultan atributos como __wrapped__.
        raise AttributeError(f"'{name}.{attr}' no está incluido en la versión liviana de LocWeave.")

    stub.__getattr__ = _missing  # type: ignore[attr-defined]
    return stub


def install_if_missing() -> bool:
    """Registra sustitutos de `stanza` (y `spacy`) si no existen. Devuelve True si registró alguno."""
    registered = False
    for name in ("stanza", "spacy"):
        if name in sys.modules or importlib.util.find_spec(name) is not None:
            continue
        sys.modules[name] = _make_stub(name)
        registered = True
    if registered:
        _prefer_minisbd()
    return registered
