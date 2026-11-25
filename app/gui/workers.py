"""Ejecución de tareas largas en segundo plano para no congelar la interfaz."""
import threading

from PySide6.QtCore import QThread, Signal

from ..services.pipeline import Cancelled


class TaskWorker(QThread):
    progress = Signal(str, int, int)
    succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal()

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            result = self._fn(lambda msg, done, total: self.progress.emit(msg, done, total), self.cancel_event)
            self.succeeded.emit(result)
        except Cancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 - se informa a la interfaz
            self.failed.emit(exc)
