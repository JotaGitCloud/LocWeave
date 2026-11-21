"""Configuración general y rutas de datos de LocWeave."""
import os
from pathlib import Path

APP_NAME = "LocWeave"
APP_VERSION = "0.1.0"


def data_dir() -> Path:
    """Carpeta donde se guarda la base de datos y los modelos de traducción."""
    custom = os.environ.get("LOCWEAVE_HOME")
    if custom:
        path = Path(custom)
    elif os.name == "nt":
        path = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    else:
        path = Path.home() / ".locweave"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "locweave.db"
