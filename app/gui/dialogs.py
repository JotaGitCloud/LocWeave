"""Diálogos: nuevo proyecto y glosario."""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)

from ..languages import LANGUAGES
from ..parsers import SUPPORTED_EXTENSIONS
from ..services.project_service import LocWeaveService
from .widgets import IconButton, fade_in


def fill_languages(combo: QComboBox, with_auto: bool = False, current: str = "") -> None:
    combo.clear()
    if with_auto:
        combo.addItem("Detectar automáticamente", "auto")
    for code, name in LANGUAGES.items():
        combo.addItem(f"{name} ({code})", code)
    index = combo.findData(current or ("auto" if with_auto else "es"))
    combo.setCurrentIndex(max(index, 0))


class NewProjectDialog(QDialog):
    def __init__(self, parent=None, path: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        self.setMinimumWidth(540)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Nuevo proyecto")
        title.setProperty("role", "title")
        hint = QLabel("Elige el archivo con los textos de tu juego. LocWeave detecta el idioma por ti.")
        hint.setProperty("muted", True)
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)

        row = QHBoxLayout()
        self.path_edit = QLineEdit(path or "")
        self.path_edit.setPlaceholderText("Archivo del juego…")
        browse = IconButton("Examinar", "file")
        browse.clicked.connect(self._browse)
        row.addWidget(self.path_edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        formats = QLabel("Formatos: " + ", ".join(SUPPORTED_EXTENSIONS))
        formats.setProperty("role", "small")
        layout.addWidget(formats)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft)
        self.name_edit = QLineEdit(Path(path).stem if path else "")
        self.name_edit.setPlaceholderText("Nombre del proyecto")
        self.src_combo, self.tgt_combo = QComboBox(), QComboBox()
        fill_languages(self.src_combo, with_auto=True)
        fill_languages(self.tgt_combo, current="es")
        form.addRow("Nombre", self.name_edit)
        form.addRow("Idioma de origen", self.src_combo)
        form.addRow("Traducir a", self.tgt_combo)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = IconButton("Cancelar", None, "ghost")
        cancel.clicked.connect(self.reject)
        self.create_btn = IconButton("Crear proyecto", "plus", "primary")
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.create_btn)
        layout.addSpacing(6)
        layout.addLayout(buttons)

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self, 180, 0.0)

    def _browse(self) -> None:
        patterns = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(self, "Elegir archivo", "",
                                              f"Archivos de localización ({patterns});;Todos (*.*)")
        if path:
            self.path_edit.setText(path)
            if not self.name_edit.text():
                self.name_edit.setText(Path(path).stem)

    def _accept(self) -> None:
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "LocWeave", "Selecciona un archivo.")
            return
        self.accept()

    def values(self):
        return (self.path_edit.text().strip(), self.name_edit.text().strip(),
                self.src_combo.currentData(), self.tgt_combo.currentData())


class GlossaryDialog(QDialog):
    def __init__(self, service: LocWeaveService, project_id: int, parent=None):
        super().__init__(parent)
        self.service, self.project_id = service, project_id
        self.setWindowTitle("Glosario del proyecto")
        self.setMinimumSize(560, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        title = QLabel("Glosario")
        title.setProperty("role", "title")
        hint = QLabel("Estos términos se traducen siempre igual: nombres propios, objetos, lugares.")
        hint.setProperty("muted", True)
        hint.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Término original", "Traducción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        layout.addWidget(self.table, 1)

        form = QHBoxLayout()
        self.term, self.translation = QLineEdit(), QLineEdit()
        self.term.setPlaceholderText("Término")
        self.translation.setPlaceholderText("Traducción")
        add = IconButton("Añadir", "plus", "primary")
        add.clicked.connect(self._add)
        self.translation.returnPressed.connect(self._add)
        form.addWidget(self.term, 1)
        form.addWidget(self.translation, 1)
        form.addWidget(add)
        layout.addLayout(form)
        remove = IconButton("Eliminar seleccionado", "trash", "danger")
        remove.clicked.connect(self._remove)
        layout.addWidget(remove)
        self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self, 180, 0.0)

    def _refresh(self) -> None:
        terms = self.service.glossary(self.project_id)
        self.table.setRowCount(len(terms))
        for row, (term, translation) in enumerate(terms.items()):
            self.table.setItem(row, 0, QTableWidgetItem(term))
            self.table.setItem(row, 1, QTableWidgetItem(translation))

    def _add(self) -> None:
        self.service.add_term(self.project_id, self.term.text(), self.translation.text())
        self.term.clear()
        self.translation.clear()
        self.term.setFocus()
        self._refresh()

    def _remove(self) -> None:
        for index in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.service.remove_term(self.project_id, self.table.item(index, 0).text())
        self._refresh()
