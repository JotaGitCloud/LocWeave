"""Sustituto mínimo de `stanza` para la variante liviana (sin PyTorch).

Argos Translate importa `stanza` al cargarse, pero solo lo usa en un separador de oraciones alternativo que
LocWeave no necesita (usa el de `minisbd`, basado en ONNX). Si `stanza` no está instalado, se registra un módulo
vacío para que Argos pueda importarse; cualquier uso real de `stanza` da un error claro.
"""
import importlib.util
import sys
import types


def install_if_missing() -> bool:
    """Registra el sustituto si `stanza` no existe. Devuelve True si lo registró."""
    if "stanza" in sys.modules or importlib.util.find_spec("stanza") is not None:
        return False
    stub = types.ModuleType("stanza")

    def _missing(name):
        raise ImportError(f"'stanza.{name}' no está incluido en la versión liviana de LocWeave (sin PyTorch).")

    stub.__getattr__ = _missing  # type: ignore[attr-defined]
    sys.modules["stanza"] = stub
    return True
