"""Autoprueba del ejecutable: comprueba que las piezas críticas se cargan.

Uso (también dentro del .exe): LocWeave.exe --selftest ruta_del_informe.txt [--real] [--screenshots carpeta]
Con --real descarga un modelo en→es (necesita internet) y traduce de verdad.
Devuelve 0 si todo cargó bien. El informe es un archivo porque el .exe no tiene consola.
"""
import os
import tempfile
import traceback


def run_selftest(report_path=None, real=False, screenshots=None) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["LOCWEAVE_HOME"] = tempfile.mkdtemp(prefix="locweave-selftest-")
    lines, failed = [], False

    def check(label, action):
        nonlocal failed
        try:
            detail = action()
            lines.append(f"OK    {label}" + (f"\n      {detail}" if detail else ""))
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

    def take_screenshots():
        """Guarda capturas de la ventana (inicio y proyecto, tema oscuro y claro) para revisar el diseño."""
        import json

        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QApplication

        from app.database import Database
        from app.gui.main_window import MainWindow, _load_fonts
        from app.gui.theme import theme
        from app.services.project_service import LocWeaveService

        def save_png(win, path):
            if not win.grab().save(path, "PNG"):
                raise RuntimeError(f"No se pudo guardar {path}")

        os.makedirs(screenshots, exist_ok=True)
        folder = os.environ["LOCWEAVE_HOME"]
        source = os.path.join(folder, "shots.json")
        demo = {
            "menu.start": "Nueva partida", "menu.load": "Cargar partida", "menu.quit": "Salir",
            "intro.1": "Bienvenido, {player}. Has despertado en la aldea de Hoshi.",
            "intro.2": "Tienes <b>3</b> misiones pendientes.\nHabla con el herrero.",
            "shop.buy": "Comprar por %d monedas", "shop.sold": "¡Vendido! Gracias por tu compra.",
            "quest.title": "La espada perdida", "ui.save": "Guardar", "ui.back": "Volver",
        }
        for n in range(1, 241):   # más textos para que el «tejido» se vea como en un juego real
            demo[f"npc.{n:03d}"] = f"Línea de diálogo número {n}, dicha por un aldeano."
        with open(source, "w", encoding="utf-8") as fh:
            json.dump(demo, fh, ensure_ascii=False)
        service = LocWeaveService(Database(os.path.join(folder, "shots.db")))
        project = service.import_file(source, "Aldea de Hoshi", "es", "en")
        service.translate(project.id, "mock")
        for k, seg in enumerate(service.segments(project.id)):   # variedad de estados para la captura
            if k % 7 == 3:
                service.save_translation(seg.id, "")
            elif k % 5 == 0:
                service.save_translation(seg.id, "Texto revisado a mano")
        service.import_file(source, "Tienda de Mei", "es", "en")   # segundo proyecto, sin traducir, para la barra lateral
        app = QApplication.instance() or QApplication([])
        _load_fonts(app)   # sin esto, la plataforma «offscreen» dibuja cuadros en lugar de texto
        settings = QSettings(os.path.join(folder, "shots.ini"), QSettings.IniFormat)
        window = MainWindow(service, settings)
        window.resize(1320, 820)
        window.show()
        for mode in ("dark", "light"):
            theme.set(mode)
            window.stack.setCurrentIndex(0)
            app.processEvents()
            save_png(window, os.path.join(screenshots, f"{mode}-inicio.png"))
            window._open_project(project.id)
            for _ in range(5):
                app.processEvents()
            window.table.selectRow(2)
            window.weave._anim.stop()   # sin esperar la animación de entrada
            window.weave._t = 1.0
            window.ring.settle()
            app.processEvents()
            app.processEvents()
            save_png(window, os.path.join(screenshots, f"{mode}-proyecto.png"))
            window.stack.setCurrentIndex(0)
        window.close()
        app.processEvents()
        names = sorted(os.listdir(screenshots))
        sizes = ", ".join(f"{n} ({os.path.getsize(os.path.join(screenshots, n))} B)" for n in names)
        if len(names) < 4:
            raise RuntimeError(f"Faltan capturas: {sizes or 'ninguna'}")
        return f"capturas guardadas en {screenshots}: {sizes}"

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
        from app.providers.stanza_stub import install_if_missing

        install_if_missing()
        import argostranslate.package  # noqa: F401
        import argostranslate.translate  # noqa: F401

    def real_translation():
        from app.providers import get_provider

        provider = get_provider("argos")
        provider.prepare("en", "es")
        source = "Hello, how are you today?"
        result = provider.translate_batch([source], "en", "es")[0]
        if not result.strip() or result.strip().lower() == source.lower():
            raise RuntimeError(f"La traducción no cambió el texto: {result!r}")
        return f"en→es: {source!r} → {result!r}"

    check("interfaz Qt (ventana, tema, dibujo)", qt_window)
    if screenshots:
        check("capturas de pantalla de la interfaz", take_screenshots)
    check("pipeline completo con motor de demostración", pipeline)
    check("motor Argos Translate (importación)", argos)
    if real:
        check("traducción real en→es (descarga un modelo)", real_translation)

    text = "\n".join(lines) + ("\n\nRESULTADO: FALLÓ\n" if failed else "\n\nRESULTADO: OK\n")
    if report_path:
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 1 if failed else 0
