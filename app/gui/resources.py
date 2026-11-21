"""Rutas de recursos, válidas desde el código fuente y desde el ejecutable de PyInstaller."""
import sys
from pathlib import Path


def assets_dir() -> Path:
    frozen = getattr(sys, "_MEIPASS", None)
    if frozen:
        return Path(frozen) / "app" / "gui" / "assets"
    return Path(__file__).resolve().parent / "assets"
