"""Diálogos: nuevo proyecto y glosario."""
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ..languages import LANGUAGES
from ..parsers import SUPPORTED_EXTENSIONS
from ..services.project_service import LocWeaveService
from .decor import DialogHeader, DropZone, FormatChip, GlowCard, StyledDialog
from .icons import icon
from .theme import theme
from .widgets import IconButton, fade_in


def fill_languages(combo: QComboBox, with_auto: bool = False, current: str = "") -> None:
    combo.clear()
    if with_auto:
        combo.addItem("Detectar automáticamente", "auto")
    for code, name in LANGUAGES.items():
        combo.addItem(f"{name} ({code})", code)
    index = combo.findData(current or ("auto" if with_auto else "es"))
    combo.setCurrentIndex(max(index, 0))


FORMAT_GROUPS = (("JSON", (".json",)), ("CSV", (".csv",)), ("PO / POT", (".po", ".pot")),
                 ("Properties", (".properties",)), ("Ren'Py", (".rpy",)))


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "section")
    return label


def _size_text(path: str) -> str:
    try:
        size = os.path.getsize(path)
    except OSError:
        return ""
    return f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"


class NewProjectDialog(StyledDialog):
    def __init__(self, parent=None, path: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        self.setMinimumWidth(620)
        self.setModal(True)
        self._path = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 26)
        layout.setSpacing(16)
        layout.addWidget(DialogHeader(
            "plus", "Nuevo proyecto",
            "Elige el archivo con los textos de tu juego. LocWeave detecta el idioma por ti."))

        self.drop = DropZone(SUPPORTED_EXTENSIONS)
        self.drop.browseRequested.connect(self._browse)
        self.drop.fileDropped.connect(self._set_path)
        layout.addWidget(self.drop)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        chips.addWidget(_field_label("Formatos"))
        chips.addSpacing(4)
        self.chips = []
        for label, exts in FORMAT_GROUPS:
            chip = FormatChip(label)
            self.chips.append((chip, exts))
            chips.addWidget(chip)
        chips.addStretch(1)
        layout.addLayout(chips)

        card = GlowCard(corner="tr", strength=0.6)
        grid = QVBoxLayout(card)
        grid.setContentsMargins(20, 16, 20, 18)
        grid.setSpacing(8)
        grid.addWidget(_field_label("Nombre del proyecto"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Por ejemplo: Aldea de Hoshi")
        grid.addWidget(self.name_edit)
        grid.addSpacing(6)
        langs = QHBoxLayout()
        langs.setSpacing(12)
        left, right = QVBoxLayout(), QVBoxLayout()
        left.setSpacing(6)
        right.setSpacing(6)
        self.src_combo, self.tgt_combo = QComboBox(), QComboBox()
        fill_languages(self.src_combo, with_auto=True)
        fill_languages(self.tgt_combo, current="es")
        left.addWidget(_field_label("Idioma de origen"))
        left.addWidget(self.src_combo)
        right.addWidget(_field_label("Traducir a"))
        right.addWidget(self.tgt_combo)
        self.arrow = QLabel()
        self.arrow.setFixedWidth(28)
        self.arrow.setAlignment(Qt.AlignCenter)
        langs.addLayout(left, 1)
        langs.addWidget(self.arrow, 0, Qt.AlignBottom)
        langs.addLayout(right, 1)
        grid.addLayout(langs)
        layout.addWidget(card)
        theme.changed.connect(self._restyle)
        self._restyle()

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = IconButton("Cancelar", None, "ghost")
        cancel.clicked.connect(self.reject)
        self.create_btn = IconButton("Crear proyecto", "plus", "primary")
        self.create_btn.setMinimumHeight(40)
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._accept)
        buttons.addWidget(cancel)
        buttons.addWidget(self.create_btn)
        layout.addSpacing(4)
        layout.addLayout(buttons)
        if path:
            self._set_path(path)
        self._sync_button()

    def _restyle(self) -> None:
        self.arrow.setPixmap(icon("arrow", theme.p["muted"], 18).pixmap(18, 18))

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self, 180, 0.0)

    def _browse(self) -> None:
        patterns = " ".join(f"*{e}" for e in SUPPORTED_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(self, "Elegir archivo", "",
                                              f"Archivos de localización ({patterns});;Todos (*.*)")
        if path:
            self._set_path(path)

    def _set_path(self, path: str) -> None:
        ext = Path(path).suffix.lower()
        known = ext in SUPPORTED_EXTENSIONS
        for chip, exts in self.chips:
            chip.set_active(known and ext in exts)
        if not known:
            self._path = ""
            self.drop.set_file("")
            self.drop.set_error(f"Formato no soportado ({ext or 'sin extensión'}). Prueba con uno de la lista.")
            self._sync_button()
            return
        self._path = path
        self.drop.set_file(path, f"{ext.lstrip('.').upper()} · {_size_text(path)} · clic para cambiar")
        if not self.name_edit.text().strip():
            self.name_edit.setText(Path(path).stem)
        self._sync_button()

    def _sync_button(self) -> None:
        self.create_btn.setEnabled(bool(self._path))

    def _accept(self) -> None:
        if self._path:
            self.accept()

    def values(self):
        return (self._path, self.name_edit.text().strip(), self.src_combo.currentData(), self.tgt_combo.currentData())


class GlossaryDialog(StyledDialog):
    def __init__(self, service: LocWeaveService, project_id: int, parent=None):
        super().__init__(parent)
        self.service, self.project_id = service, project_id
        self.setWindowTitle("Glosario del proyecto")
        self.setMinimumSize(620, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 26)
        layout.setSpacing(16)
        self.header = DialogHeader("book", "Glosario",
                                   "Estos términos se traducen siempre igual: nombres propios, objetos, lugares.")
        layout.addWidget(self.header)

        self.list_card = GlowCard(corner="tl", strength=0.5)
        lv = QVBoxLayout(self.list_card)
        lv.setContentsMargins(10, 8, 10, 10)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Término original", "Traducción"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.NoFrame)
        lv.addWidget(self.table)
        self.empty = QWidget()
        ev = QVBoxLayout(self.empty)
        ev.setAlignment(Qt.AlignCenter)
        ev.setSpacing(6)
        self.empty_icon = QLabel()
        self.empty_icon.setObjectName("IconTile")
        self.empty_icon.setFixedSize(52, 52)
        self.empty_icon.setAlignment(Qt.AlignCenter)
        empty_title = QLabel("Aún no hay términos")
        empty_title.setProperty("role", "cardtitle")
        empty_hint = QLabel("Añade el primero abajo: por ejemplo «Hoshi» → «Hoshi».")
        empty_hint.setProperty("role", "small")
        for w in (self.empty_icon, empty_title, empty_hint):
            ev.addWidget(w, 0, Qt.AlignHCenter)
        lv.addWidget(self.empty)
        layout.addWidget(self.list_card, 1)

        add_card = GlowCard(corner="br", strength=0.6)
        av = QVBoxLayout(add_card)
        av.setContentsMargins(20, 14, 20, 16)
        av.setSpacing(8)
        av.addWidget(_field_label("Añadir término"))
        form = QHBoxLayout()
        form.setSpacing(10)
        self.term, self.translation = QLineEdit(), QLineEdit()
        self.term.setPlaceholderText("Término original")
        self.translation.setPlaceholderText("Traducción")
        self.arrow = QLabel()
        self.arrow.setFixedWidth(22)
        self.arrow.setAlignment(Qt.AlignCenter)
        add = IconButton("Añadir", "plus", "primary")
        add.clicked.connect(self._add)
        self.translation.returnPressed.connect(self._add)
        form.addWidget(self.term, 1)
        form.addWidget(self.arrow)
        form.addWidget(self.translation, 1)
        form.addWidget(add)
        av.addLayout(form)
        layout.addWidget(add_card)

        footer = QHBoxLayout()
        self.remove_btn = IconButton("Eliminar seleccionado", "trash", "danger")
        self.remove_btn.clicked.connect(self._remove)
        close = IconButton("Cerrar", None, "ghost")
        close.clicked.connect(self.accept)
        footer.addWidget(self.remove_btn)
        footer.addStretch(1)
        footer.addWidget(close)
        layout.addLayout(footer)
        theme.changed.connect(self._restyle)
        self.table.itemSelectionChanged.connect(self._sync)
        self._restyle()
        self._refresh()

    def _restyle(self) -> None:
        self.arrow.setPixmap(icon("arrow", theme.p["muted"], 16).pixmap(16, 16))
        self.empty_icon.setPixmap(icon("book", theme.p["accent"], 24).pixmap(24, 24))

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self, 180, 0.0)

    def _sync(self) -> None:
        self.remove_btn.setEnabled(bool(self.table.selectedIndexes()))

    def _refresh(self) -> None:
        terms = self.service.glossary(self.project_id)
        self.table.setRowCount(len(terms))
        for row, (term, translation) in enumerate(terms.items()):
            self.table.setItem(row, 0, QTableWidgetItem(term))
            self.table.setItem(row, 1, QTableWidgetItem(translation))
        self.table.setVisible(bool(terms))
        self.empty.setVisible(not terms)
        n = len(terms)
        self.header.subtitle.setText(
            "Estos términos se traducen siempre igual: nombres propios, objetos, lugares."
            + (f"\n{n} {'término' if n == 1 else 'términos'} en este proyecto" if n else ""))
        self._sync()

    def _add(self) -> None:
        if not self.term.text().strip():
            self.term.setFocus()
            return
        self.service.add_term(self.project_id, self.term.text(), self.translation.text())
        self.term.clear()
        self.translation.clear()
        self.term.setFocus()
        self._refresh()

    def _remove(self) -> None:
        for index in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.service.remove_term(self.project_id, self.table.item(index, 0).text())
        self._refresh()
