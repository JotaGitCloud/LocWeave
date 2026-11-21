# -*- mode: python ; coding: utf-8 -*-
# Empaquetado con PyInstaller (modo carpeta, sin consola): pyinstaller LocWeave.spec --noconfirm --clean
# Resultado: dist/LocWeave/LocWeave.exe
import importlib.util

from PyInstaller.utils.hooks import collect_all

datas = [("app/gui/assets", "app/gui/assets")]
binaries, hiddenimports = [], []

# Paquetes pesados del motor de traducción (solo se incluyen si están instalados).
for package in ("argostranslate", "ctranslate2", "sentencepiece", "stanza", "spacy", "sacremoses", "minisbd",
                "torch"):
    if importlib.util.find_spec(package):
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hiddenimports += h

# Módulos de Qt que LocWeave no usa (reducen el tamaño del ejecutable).
excludes = ["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
            "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.Qt3DCore", "PySide6.Qt3DRender",
            "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets", "PySide6.QtCharts", "PySide6.QtDataVisualization",
            "PySide6.QtBluetooth", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
            "PySide6.QtDesigner", "PySide6.QtHelp"]

a = Analysis(["main.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             excludes=excludes)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="LocWeave", console=False,
          icon="app/gui/assets/icon.ico")
coll = COLLECT(exe, a.binaries, a.datas, name="LocWeave")
