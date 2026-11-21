"""Autoprueba del ejecutable: comprueba que las piezas críticas se cargan.

Uso (también dentro del .exe): LocWeave.exe --selftest ruta_del_informe.txt
Devuelve 0 si todo cargó bien. El informe es un archivo porque el .exe no tiene consola.
"""
import os
import tempfile
import traceback


def run_selftest(report_path=None) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["LOCWEAVE_HOME"] = tempfile.mkdtemp(prefix="locweave-selftest-")
    lines, failed = [], False

    def check(label, action):
        nonlocal failed
        try:
            action()
            lines.append(f"OK    {label}")
        except Exception:  # noqa: BLE001 - se informa en el archivo
            failed = True
            lines.append(f"FALLO {label}\n{traceback.format_exc()}")

    def qt_window():
        from PySide6.QtWidgets import QApplication

        from app.database import Database
        from app.gui.main_window import MainWindow
        from app.gui.theme import theme
        from app.services.project_service import LocWeaveService
        from PySide6.QtCore import QSettings

        app = QApplication.instance() or QApplication([])
        theme.set("dark")
        settings = QSettings(os.path.join(os.environ["LOCWEAVE_HOME"], "s.ini"), QSettings.IniFormat)
        window = MainWindow(LocWeaveService(Database(os.path.join(os.environ["LOCWEAVE_HOME"], "t.db"))), settings)
        window.show()
        if window.grab().isNull():
            raise RuntimeError("La ventana no se pudo dibujar")
        window.close()
        app.processEvents()

    def pipeline():
        from app.database import Database
        from app.services.project_service import LocWeaveService

        folder = os.environ["LOCWEAVE_HOME"]
        source = os.path.join(folder, "demo.json")
        with open(source, "w", encoding="utf-8") as fh:
            fh.write('{"a": "Hello {name}"}')
        service = LocWeaveService(Database(os.path.join(folder, "p.db")))
        project = service.import_file(source, "demo", "en", "es")
        service.translate(project.id, "mock")
        service.export(project.id, os.path.join(folder, "out.json"))

    def argos():
        import argostranslate.package  # noqa: F401
        import argostranslate.translate  # noqa: F401

    check("interfaz Qt (ventana, tema, dibujo)", qt_window)
    check("pipeline completo con motor de demostración", pipeline)
    check("motor Argos Translate (importación)", argos)

    text = "\n".join(lines) + ("\n\nRESULTADO: FALLÓ\n" if failed else "\n\nRESULTADO: OK\n")
    if report_path:
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 1 if failed else 0
