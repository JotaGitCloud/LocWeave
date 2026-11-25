"""Flujo de actualización dentro de la ventana: buscar, preguntar, descargar e instalar."""
import sys
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .. import updater
from ..config import APP_VERSION

LAST_CHECK_KEY = "update/last_check"
CHECK_EVERY_SECONDS = 12 * 3600


class UpdateController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.w = window
        self.pending = None
        self._silent = True

    def start_silent_check(self) -> None:
        """Al abrir la app (solo instalada, como mucho cada 12 h) busca en segundo plano sin molestar."""
        if not getattr(sys, "frozen", False):
            return
        try:
            last = float(self.w.settings.value(LAST_CHECK_KEY, 0) or 0)
        except (TypeError, ValueError):
            last = 0.0
        if time.time() - last < CHECK_EVERY_SECONDS:
            return
        QTimer.singleShot(4000, lambda: self.check(silent=True))

    def check(self, silent: bool = False) -> None:
        if self.w.worker is not None:
            if not silent:
                self.w.toast.show_message("Espera a que termine la tarea actual.", "error")
            return
        self._silent = silent
        self.w._run(lambda progress, cancel: updater.check_for_update(APP_VERSION),
                    self._checked, "Buscando actualizaciones…")
        # Los errores de red no deben mostrarse en la búsqueda silenciosa.
        if silent and self.w.worker is not None:
            self.w.worker.failed.disconnect(self.w._task_failed)
            self.w.worker.failed.connect(self._silent_failed)

    def _silent_failed(self, _error) -> None:
        self.w._task_cleanup()

    def _checked(self, info) -> None:
        self.w.settings.setValue(LAST_CHECK_KEY, time.time())
        if info is None:
            if not self._silent:
                self.w.toast.show_message(f"LocWeave {APP_VERSION} es la versión más reciente.")
            return
        self.pending = info
        box = QMessageBox(self.w)
        box.setWindowTitle("Actualización disponible")
        box.setIcon(QMessageBox.Information)
        box.setText(f"Hay una versión nueva de LocWeave: {info.version} (tienes la {APP_VERSION}).")
        mb = info.size / (1024 * 1024)
        detail = f"Se descargarán {mb:.0f} MB y la aplicación se reiniciará. Tus proyectos no se pierden."
        if info.notes:
            detail += "\n\nNovedades:\n" + info.notes[:1200]
        box.setInformativeText(detail)
        install = box.addButton("Actualizar ahora", QMessageBox.AcceptRole)
        box.addButton("Más tarde", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is install:
            self.download(info)

    def download(self, info) -> None:
        dest = Path(tempfile.gettempdir()) / "LocWeaveUpdate"
        self.w._run(lambda progress, cancel: updater.download_installer(info, dest, progress, cancel),
                    self._downloaded, "Descargando actualización…")

    def _downloaded(self, path) -> None:
        try:
            updater.launch_installer(Path(path))
        except OSError as exc:
            self.w.toast.show_message(f"No se pudo iniciar el instalador: {exc}", "error")
            return
        QApplication.quit()
