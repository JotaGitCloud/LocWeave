"""Prueba de humo de la interfaz Qt: se omite automáticamente si PySide6 no está instalado."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:  # pragma: no cover
    HAS_QT = False

from tests.helpers import TempCase  # noqa: E402


@unittest.skipUnless(HAS_QT, "PySide6 no está instalado")
class GuiSmokeTests(TempCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_opens_project_and_switches_theme(self):
        from app.gui.main_window import MainWindow
        from app.gui.theme import theme

        src = self.write("g.json", '{"a": "ゲームを始める", "b": "こんにちは、{player}さん！"}')
        project = self.service.import_file(src, "demo", "auto", "es")
        self.service.translate(project.id, "mock")

        settings = QSettings(str(self.dir / "settings.ini"), QSettings.IniFormat)
        window = MainWindow(self.service, settings)
        window.show()
        window._open_project(project.id)
        self.assertEqual(window.model.rowCount(), 2)
        window.table.selectRow(1)
        self.assertEqual(window.current.key, "/b")

        for name in ("light", "dark"):
            theme.set(name)
            self.assertFalse(window.grab().isNull())

        window.target_box.setPlainText("Hola")
        window._live_validate()
        self.assertIn("Faltan", window.issues_label.text())
        window.target_box.setPlainText("Hola, {player}")
        window._save()
        self.assertEqual(window.current.status, "reviewed")
        window.close()


if __name__ == "__main__":
    unittest.main()
