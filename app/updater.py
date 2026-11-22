"""Actualizaciones: consulta los Releases de GitHub, descarga el instalador y lo lanza.

Solo usa la biblioteca estándar. Solo se descarga desde releases/download del repositorio oficial y, si GitHub
informa el hash SHA-256 del archivo, se verifica antes de ejecutarlo.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .config import APP_VERSION

GITHUB_REPO = "JotaGitCloud/LocWeave"
USER_AGENT = "LocWeave-updater"
_PRE_RANK = {"dev": -1, "alpha": 0, "a": 0, "beta": 1, "b": 1, "rc": 2}
_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?([A-Za-z]+)\.?(\d*))?$")


class UpdateError(Exception):
    pass


@dataclass
class UpdateInfo:
    version: str
    tag: str
    notes: str
    asset_name: str
    asset_url: str
    size: int
    sha256: str
    page_url: str


def version_key(text: str) -> Tuple:
    """Clave ordenable: 0.1.0-beta1 < 0.1.0 < 0.1.1; las versiones «dev» van antes que todo."""
    m = _VERSION_RE.match((text or "").strip())
    if not m:
        return (0, 0, 0, -2, 0)
    major, minor, patch, pre, num = m.groups()
    if pre is None:
        return (int(major), int(minor), int(patch), 99, 0)
    return (int(major), int(minor), int(patch), _PRE_RANK.get(pre.lower(), 0), int(num or 0))


def is_dev(version: str) -> bool:
    return "dev" in (version or "").lower()


def current_variant() -> str:
    """«full» si esta compilación incluye PyTorch; «slim» en caso contrario."""
    return "full" if importlib.util.find_spec("torch") is not None else "slim"


def find_update(current: str, releases: List[dict], variant: str = "slim",
                include_prereleases: bool = True) -> Optional[UpdateInfo]:
    """Elige la versión más nueva que tenga el instalador de la variante y sea mayor que la actual."""
    wanted = f"LocWeave-Setup-{variant}.exe"
    best: Optional[UpdateInfo] = None
    for rel in releases:
        if rel.get("draft") or (rel.get("prerelease") and not include_prereleases):
            continue
        tag = rel.get("tag_name", "")
        asset = next((a for a in rel.get("assets", []) if a.get("name") == wanted), None)
        if not asset:
            continue
        info = UpdateInfo(version=tag.lstrip("vV"), tag=tag, notes=(rel.get("body") or "").strip(),
                          asset_name=wanted, asset_url=asset.get("browser_download_url", ""),
                          size=int(asset.get("size") or 0),
                          sha256=str(asset.get("digest") or "").replace("sha256:", ""),
                          page_url=rel.get("html_url", ""))
        if best is None or version_key(info.tag) > version_key(best.tag):
            best = info
    if best and version_key(best.tag) > version_key(current):
        return best
    return None


def fetch_releases(repo: str = GITHUB_REPO, timeout: float = 8.0) -> List[dict]:
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=20",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(f"No se pudo consultar GitHub: {exc}") from exc


def check_for_update(current: str = APP_VERSION, repo: str = GITHUB_REPO, variant: Optional[str] = None,
                     timeout: float = 8.0) -> Optional[UpdateInfo]:
    return find_update(current, fetch_releases(repo, timeout), variant or current_variant())


def download_installer(info: UpdateInfo, dest_dir: Path, progress: Callable[[str, int, int], None],
                       cancel: Optional[threading.Event] = None, repo: str = GITHUB_REPO) -> Path:
    if not info.asset_url.startswith(f"https://github.com/{repo}/releases/download/"):
        raise UpdateError("La dirección de descarga no pertenece al repositorio oficial de LocWeave.")
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / info.asset_name
    part = target.with_suffix(".part")
    req = urllib.request.Request(info.asset_url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    done = 0
    try:
        with urllib.request.urlopen(req, timeout=20) as resp, open(part, "wb") as fh:
            total = int(resp.headers.get("Content-Length") or info.size or 0)
            while True:
                if cancel is not None and cancel.is_set():
                    raise UpdateError("Descarga cancelada.")
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                progress(f"Descargando {info.asset_name}…", done, total)
    except UpdateError:
        part.unlink(missing_ok=True)
        raise
    except Exception as exc:  # noqa: BLE001
        part.unlink(missing_ok=True)
        raise UpdateError(f"No se pudo descargar la actualización: {exc}") from exc
    if info.size and done != info.size:
        part.unlink(missing_ok=True)
        raise UpdateError("La descarga quedó incompleta; inténtalo de nuevo.")
    if info.sha256 and digest.hexdigest().lower() != info.sha256.lower():
        part.unlink(missing_ok=True)
        raise UpdateError("El archivo descargado no coincide con el hash publicado; se descartó por seguridad.")
    os.replace(part, target)
    return target


def launch_installer(path: Path) -> None:
    """Ejecuta el instalador en silencio (cierra y reabre LocWeave) y deja que la aplicación termine."""
    flags = 0
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen([str(path), "/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"], creationflags=flags,
                     close_fds=True)
