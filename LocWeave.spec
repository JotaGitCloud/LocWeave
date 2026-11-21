# -*- mode: python ; coding: utf-8 -*-
# Empaquetado con PyInstaller (modo carpeta, sin consola): pyinstaller LocWeave.spec --noconfirm --clean
# Resultado: dist/LocWeave/LocWeave.exe
#
# Objetivo: que la descarga sea lo más liviana posible (pensado para equipos indie con pocos recursos).
import importlib.util

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_submodules

datas = [("app/gui/assets", "app/gui/assets")]
binaries, hiddenimports = [], []


def present(name):
    return importlib.util.find_spec(name) is not None


# Núcleo del motor de traducción: se incluye completo (datos, DLL y submódulos).
for package in ("argostranslate", "ctranslate2", "sentencepiece", "sacremoses", "minisbd", "spacy"):
    if present(package):
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h

# Dependencias muy pesadas que, según la versión de Argos, pueden estar presentes: solo lo imprescindible.
if present("stanza"):
    hiddenimports += collect_submodules("stanza")
if present("torch"):
    binaries += collect_dynamic_libs("torch")

# Módulos que LocWeave no usa (cada uno que sale reduce el tamaño final).
excludes = ["tkinter", "matplotlib", "IPython", "notebook", "pytest",
            "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
            "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtCharts", "PySide6.QtDataVisualization",
            "PySide6.QtBluetooth", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
            "PySide6.QtDesigner", "PySide6.QtHelp"]

# Archivos que no hacen falta para ejecutar: cabeceras, librerías de enlace, pruebas, traducciones de Qt, etc.
DROP_SUFFIXES = (".lib", ".pdb", ".h", ".hpp", ".cuh", ".cmake", ".pyi", ".c", ".cpp", ".pxd")
DROP_PARTS = ("/include/", "/tests/", "/test/", "pyside6/translations/", "pyside6/qml/", "caffe2/")
DROP_NAMES = ("opengl32sw", "qt6quick", "qt6qml", "qt6pdf", "qt6virtualkeyboard")


def keep(entry):
    dest = str(entry[0]).replace("\\", "/").lower()
    name = dest.rsplit("/", 1)[-1]
    return not (dest.endswith(DROP_SUFFIXES) or any(part in "/" + dest for part in DROP_PARTS)
                or name.startswith(DROP_NAMES))


a = Analysis(["main.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             excludes=excludes)
a.datas = [entry for entry in a.datas if keep(entry)]
a.binaries = [entry for entry in a.binaries if keep(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="LocWeave", console=False,
          icon="app/gui/assets/icon.ico")
coll = COLLECT(exe, a.binaries, a.datas, name="LocWeave")
