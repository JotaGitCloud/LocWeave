"""Ventana principal de LocWeave (PySide6)."""
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QModelIndex, QSettings, Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QKeySequence, QShortcut, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog, QFrame, QGridLayout,
                               QHBoxLayout, QHeaderView, QLabel, QListView, QMainWindow, QMessageBox,
                               QProgressBar, QSplitter, QStackedWidget, QTableView, QTextEdit, QVBoxLayout,
                               QWidget)

from ..config import APP_NAME, APP_VERSION, db_path
from ..database import Database
from ..languages import LANGUAGES
from ..parsers import SUPPORTED_EXTENSIONS
from ..providers import DEFAULT_PROVIDER, ProviderError, provider_labels
from ..parsers import FormatError
from ..services.pipeline import PipelineError
from ..services.placeholders import extract_placeholders
from ..services.project_service import LocWeaveService
from ..services.validation import has_errors, validate
from .delegates import PROJECT_ROLE, ProjectDelegate, SegmentDelegate, SegmentTableModel, rich_html
from .decor import AuroraBackground, FeatureCard, GradientTitle, HeroLogo, Pill, SidebarFrame, StatsLegend, WeaveMap
from .dialogs import GlossaryDialog, NewProjectDialog, fill_languages
from .platform_utils import set_app_id, set_dark_titlebar
from .resources import assets_dir, samples_dir
from .theme import theme
from .update_flow import UpdateController
from .widgets import IconButton, LogoWidget, SegmentedBar, ThemeToggle, ThreadLine, Toast, fade_in, pulse
from .workers import TaskWorker

EXPECTED_ERRORS = (PipelineError, ProviderError, FormatError)


class HoverTable(QTableView):
    """Tabla que recuerda la fila bajo el cursor para resaltarla completa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_row = -1
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        row = self.rowAt(int(event.position().y()))
        if row != self.hover_row:
            self.hover_row = row
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover_row = -1
        self.viewport().update()
        super().leaveEvent(event)


def _label(text: str = "", role: Optional[str] = None, muted: bool = False) -> QLabel:
    label = QLabel(text)
    if role:
        label.setProperty("role", role)
    if muted:
        label.setProperty("muted", True)
    return label


class MainWindow(QMainWindow):
    def __init__(self, service: LocWeaveService, settings: QSettings):
        super().__init__()
        self.service, self.settings = service, settings
        self.project = None
        self.current = None
        self.worker: Optional[TaskWorker] = None
        self._on_success = None
        self._updating = False
        self._shown = False
        self._labels = provider_labels()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1320, 820)
        self.setMinimumSize(1180, 700)
        self.setAcceptDrops(True)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_empty_page())
        self.stack.addWidget(self._build_project_page())
        layout.addWidget(self.stack, 1)
        self.toast = Toast(root)

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._new_project)
        for seq in ("Ctrl+Return", "Ctrl+Enter"):
            sc = QShortcut(QKeySequence(seq), self.target_box, activated=self._save)
            sc.setContext(Qt.WidgetShortcut)

        theme.changed.connect(self._on_theme_changed)
        self._refresh_projects()
        self._set_project_actions(False)
        self.stack.setCurrentIndex(0)
        self.updates = UpdateController(self)
        self.updates.start_silent_check()

    # ================================================================ construcción
    def _build_sidebar(self) -> QFrame:
        side = SidebarFrame()
        side.setFixedWidth(268)
        v = QVBoxLayout(side)
        v.setContentsMargins(16, 24, 16, 18)
        v.setSpacing(0)
        head = QHBoxLayout()
        head.setContentsMargins(8, 0, 0, 0)
        head.setSpacing(10)
        head.addWidget(LogoWidget(30))
        titles = QVBoxLayout()
        titles.setSpacing(0)
        name = _label(APP_NAME)
        name.setStyleSheet("font-size: 19px; font-weight: 600;")
        titles.addWidget(name)
        titles.addWidget(_label("Localización para juegos indie", "small"))
        head.addLayout(titles)
        head.addStretch(1)
        v.addLayout(head)
        v.addSpacing(26)
        section = _label("Proyectos", "section")
        section.setContentsMargins(8, 0, 0, 6)
        v.addWidget(section)

        self.project_list = QListView()
        self.project_model = QStandardItemModel(self)
        self.project_list.setModel(self.project_model)
        self.project_list.setItemDelegate(ProjectDelegate(self.project_list))
        self.project_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.project_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.project_list.setMouseTracking(True)
        self.project_list.setFrameShape(QFrame.NoFrame)
        self.project_list.clicked.connect(lambda idx: self._open_project(idx.data(Qt.UserRole)))
        v.addWidget(self.project_list, 1)

        self.new_btn = IconButton("Nuevo proyecto", "plus", "primary")
        self.new_btn.setMinimumHeight(42)
        self.new_btn.clicked.connect(self._new_project)
        v.addSpacing(12)
        v.addWidget(self.new_btn)
        self.update_btn = IconButton("Buscar actualizaciones", "refresh", "ghost")
        self.update_btn.clicked.connect(lambda: self.updates.check(silent=False))
        v.addSpacing(6)
        v.addWidget(self.update_btn)
        return side

    def _build_empty_page(self) -> QWidget:
        page = AuroraBackground()
        outer = QVBoxLayout(page)
        outer.addStretch(1)
        col = QVBoxLayout()
        col.setAlignment(Qt.AlignHCenter)
        col.setSpacing(12)
        col.addWidget(HeroLogo(120), 0, Qt.AlignHCenter)
        col.addWidget(GradientTitle("Lleva tu juego a más idiomas", 27), 0, Qt.AlignHCenter)
        sub = _label("Importa los textos, tradúcelos con un motor local y gratuito, revisa y exporta\n"
                     "al formato original. Sin cuentas, sin costos.", muted=True)
        sub.setAlignment(Qt.AlignCenter)
        col.addWidget(sub)
        pills = QHBoxLayout()
        pills.setSpacing(8)
        pills.setAlignment(Qt.AlignHCenter)
        for text in ("100 % local", "Gratis", "Sin cuenta", "Funciona sin internet"):
            pills.addWidget(Pill(text))
        col.addSpacing(2)
        col.addLayout(pills)
        start = IconButton("Crear mi primer proyecto", "plus", "primary")
        start.setMinimumHeight(46)
        start.setMinimumWidth(260)
        start.clicked.connect(self._new_project)
        col.addSpacing(10)
        col.addWidget(start, 0, Qt.AlignHCenter)
        demo = IconButton("Probar con un ejemplo (japonés → español)", None, "ghost")
        demo.clicked.connect(self._open_sample)
        col.addWidget(demo, 0, Qt.AlignHCenter)
        col.addSpacing(14)

        steps = QHBoxLayout()
        steps.setSpacing(16)
        steps.setAlignment(Qt.AlignHCenter)
        for number, icon_name, title, text in (
                ("01", "upload", "Importa", "JSON, CSV, .po, .properties y scripts de Ren'Py"),
                ("02", "refresh", "Traduce", "Motor local, sin internet una vez instalados los idiomas"),
                ("03", "check", "Revisa y exporta", "Variables protegidas, glosario y memoria propios")):
            steps.addWidget(FeatureCard(number, icon_name, title, text))
        col.addLayout(steps)
        col.addSpacing(8)
        col.addWidget(_label("También puedes arrastrar un archivo a esta ventana.", "small"), 0, Qt.AlignHCenter)
        outer.addLayout(col)
        outer.addStretch(2)
        return page

    def _build_project_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(28, 22, 28, 14)
        v.setSpacing(12)

        # --- encabezado
        top = QHBoxLayout()
        top.setSpacing(14)
        self.title_label = _label("", "title")
        self.file_label = _label("", muted=True)
        top.addWidget(self.title_label)
        top.addWidget(self.file_label, 1)
        self.theme_toggle = ThemeToggle()
        self.theme_toggle.toggled_to.connect(self._set_theme)
        self.glossary_btn = IconButton("Glosario", "book")
        self.glossary_btn.clicked.connect(self._open_glossary)
        self.export_btn = IconButton("Exportar", "download")
        self.export_btn.clicked.connect(self._export)
        self.delete_btn = IconButton("", "trash", "ghost", icon_only=True)
        self.delete_btn.setToolTip("Eliminar proyecto")
        self.delete_btn.clicked.connect(self._delete_project)
        for w in (self.theme_toggle, self.glossary_btn, self.export_btn, self.delete_btn):
            top.addWidget(w)
        v.addLayout(top)

        self.bar = SegmentedBar()
        self.stats_label = StatsLegend()
        self.weave = WeaveMap()
        self.weave.setToolTip("Cada hilo es un texto. Haz clic para ir a él.")
        self.weave.rowClicked.connect(self._jump_to_row)
        v.addWidget(self.bar)
        v.addWidget(self.stats_label)
        v.addWidget(self.weave)

        # --- barra de herramientas
        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.src_combo, self.tgt_combo = QComboBox(), QComboBox()
        fill_languages(self.src_combo)
        fill_languages(self.tgt_combo)
        for combo in (self.src_combo, self.tgt_combo):
            combo.setMinimumWidth(150)
            combo.currentIndexChanged.connect(self._langs_changed)
        self.swap_btn = IconButton("", "swap", "ghost", icon_only=True)
        self.swap_btn.setToolTip("Intercambiar idiomas")
        self.swap_btn.clicked.connect(self._swap_langs)
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(230)
        for name, label in self._labels.items():
            self.provider_combo.addItem(label, name)
        saved = self.settings.value("provider", DEFAULT_PROVIDER)
        self.provider_combo.setCurrentIndex(max(self.provider_combo.findData(saved), 0))
        self.provider_combo.currentIndexChanged.connect(
            lambda: self.settings.setValue("provider", self.provider_combo.currentData()))
        self.prepare_btn = IconButton("", "cloud", "secondary", icon_only=True)
        self.prepare_btn.setToolTip("Preparar idiomas (descarga los modelos; requiere internet una sola vez)")
        self.prepare_btn.clicked.connect(self._prepare_languages)
        self.retranslate_btn = IconButton("", "refresh", "secondary", icon_only=True)
        self.retranslate_btn.setToolTip("Retraducir todo (excepto lo ya revisado)")
        self.retranslate_btn.clicked.connect(lambda: self._translate(False))
        self.translate_btn = IconButton("Traducir pendientes", "play", "primary")
        self.translate_btn.clicked.connect(lambda: self._translate(True))
        for w in (self.src_combo, self.swap_btn, self.tgt_combo):
            tools.addWidget(w)
        tools.addSpacing(10)
        tools.addWidget(self.provider_combo)
        tools.addWidget(self.prepare_btn)
        tools.addStretch(1)
        tools.addWidget(self.retranslate_btn)
        tools.addWidget(self.translate_btn)
        v.addLayout(tools)

        # --- tabla + editor
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        table_card = QFrame()
        table_card.setObjectName("Card")
        tv = QVBoxLayout(table_card)
        tv.setContentsMargins(8, 4, 8, 8)
        self.model = SegmentTableModel(self)
        self.table = HoverTable()
        self.table.setModel(self.model)
        self.table.setItemDelegate(SegmentDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 56)
        self.table.setColumnWidth(1, 170)
        self.table.setColumnWidth(4, 140)
        self.table.selectionModel().currentRowChanged.connect(self._on_row_changed)
        tv.addWidget(self.table)
        splitter.addWidget(table_card)

        self.editor_card = QFrame()
        self.editor_card.setObjectName("Card")
        grid = QGridLayout(self.editor_card)
        grid.setContentsMargins(18, 14, 18, 14)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(8)
        grid.addWidget(_label("Original", "section"), 0, 0)
        self.target_title = _label("Traducción", "section")
        grid.addWidget(self.target_title, 0, 2)
        self.source_box = QTextEdit()
        self.source_box.setReadOnly(True)
        self.source_box.setProperty("readonlyBox", True)
        self.target_box = QTextEdit()
        self.target_box.setAcceptRichText(False)
        self.target_box.setPlaceholderText("Escribe la traducción…")
        editor_font = QFont(self.font())
        editor_font.setPointSizeF(11.5)
        self.source_box.setFont(editor_font)
        self.target_box.setFont(editor_font)
        self.thread_line = ThreadLine()
        grid.addWidget(self.source_box, 1, 0)
        grid.addWidget(self.thread_line, 1, 1)
        grid.addWidget(self.target_box, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(1, 1)

        notes = QHBoxLayout()
        notes.setSpacing(10)
        self.issues_label = QLabel()
        self.issues_label.setTextFormat(Qt.RichText)
        self.issues_label.setWordWrap(True)
        self.insert_box = QHBoxLayout()
        self.insert_box.setSpacing(6)
        notes.addWidget(self.issues_label, 1)
        notes.addLayout(self.insert_box)
        hint = _label("Ctrl+Enter para guardar", "small")
        self.save_btn = IconButton("Guardar traducción", "check", "primary")
        self.save_btn.clicked.connect(self._save)
        notes.addWidget(hint)
        notes.addWidget(self.save_btn)
        grid.addLayout(notes, 2, 0, 1, 3)
        splitter.addWidget(self.editor_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        v.addWidget(splitter, 1)

        self._live_timer = QTimer(self, singleShot=True, interval=250)
        self._live_timer.timeout.connect(self._live_validate)
        self.target_box.textChanged.connect(self._live_timer.start)

        # --- pie con progreso de tareas
        self.footer = QWidget()
        fl = QHBoxLayout(self.footer)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(12)
        self.status_label = _label("", "small")
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(320)
        self.cancel_btn = IconButton("Cancelar", "x", "danger")
        self.cancel_btn.clicked.connect(self._cancel_task)
        fl.addWidget(self.status_label, 1)
        fl.addWidget(self.progress)
        fl.addWidget(self.cancel_btn)
        v.addWidget(self.footer)
        self.footer.hide()
        self._set_editor_enabled(False)
        return page

    # ================================================================ eventos de ventana
    def showEvent(self, event):
        super().showEvent(event)
        set_dark_titlebar(self, theme.name == "dark")
        if not self._shown:
            self._shown = True
            fade_in(self, 260, 0.0)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(3000)
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls and Path(urls[0].toLocalFile()).suffix.lower() in SUPPORTED_EXTENSIONS:
            event.acceptProposedAction()

    def dropEvent(self, event):
        self._new_project(event.mimeData().urls()[0].toLocalFile())

    def _on_theme_changed(self) -> None:
        set_dark_titlebar(self, theme.name == "dark")
        self.table.viewport().update()
        self.project_list.viewport().update()
        if self.current:
            self._show_source(self.current.source_text)
        self._live_validate()

    def _set_theme(self, name: str) -> None:
        theme.set(name)
        self.settings.setValue("theme", name)

    # ================================================================ tareas en segundo plano
    def _set_project_actions(self, enabled: bool) -> None:
        for w in (self.glossary_btn, self.export_btn, self.delete_btn, self.translate_btn, self.retranslate_btn,
                  self.prepare_btn, self.src_combo, self.tgt_combo, self.swap_btn, self.provider_combo):
            w.setEnabled(enabled and self.worker is None)

    def _run(self, fn, on_success, message: str) -> None:
        if self.worker is not None:
            return
        self._on_success = on_success
        self.worker = TaskWorker(fn, self)
        # Se conectan métodos de la ventana (no lambdas) para que Qt los ejecute en el hilo de la interfaz.
        self.worker.progress.connect(self._on_progress)
        self.worker.succeeded.connect(self._task_succeeded)
        self.worker.failed.connect(self._task_failed)
        self.worker.cancelled.connect(self._task_cancelled)
        self.status_label.setText(message)
        self.progress.setRange(0, 0)
        self.footer.show()
        self.new_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self._set_project_actions(False)
        self.worker.start()

    def _on_progress(self, message: str, done: int, total: int) -> None:
        self.status_label.setText(message)
        if total:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(done * 100 / total))
        else:
            self.progress.setRange(0, 0)

    def _task_cleanup(self, toast: Optional[str] = None, kind: str = "ok") -> None:
        worker, self.worker = self.worker, None
        if worker:
            worker.wait()
            worker.deleteLater()
        self.footer.hide()
        self.new_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self._set_project_actions(self.project is not None)
        if toast:
            self.toast.show_message(toast, kind)

    def _task_succeeded(self, result) -> None:
        callback = self._on_success
        self._task_cleanup()
        callback(result)

    def _task_cancelled(self) -> None:
        self._task_cleanup("Operación cancelada", "info")

    def _task_failed(self, exc: Exception) -> None:
        self._task_cleanup()
        text = str(exc) if isinstance(exc, EXPECTED_ERRORS) else f"Error inesperado ({type(exc).__name__}): {exc}"
        QMessageBox.critical(self, APP_NAME, text)

    def _cancel_task(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.status_label.setText("Cancelando…")

    # ================================================================ proyectos
    def _refresh_projects(self) -> None:
        self.project_model.clear()
        selected_row = -1
        for row, project in enumerate(self.service.list_projects()):
            stats = self.service.stats(project.id)
            total = stats.get("total", 0) or 1
            done = stats.get("translated", 0) + stats.get("reviewed", 0)
            src, tgt = LANGUAGES.get(project.source_lang, project.source_lang), \
                LANGUAGES.get(project.target_lang, project.target_lang)
            item = QStandardItem(project.name)
            item.setData(project.id, Qt.UserRole)
            item.setData({"name": project.name, "subtitle": f"{src} → {tgt} · {stats.get('total', 0)} textos",
                          "progress": done / total}, PROJECT_ROLE)
            item.setEditable(False)
            self.project_model.appendRow(item)
            if self.project and project.id == self.project.id:
                selected_row = row
        if selected_row >= 0:
            self.project_list.setCurrentIndex(self.project_model.index(selected_row, 0))

    def _new_project(self, path=None) -> None:
        if self.worker is not None:
            return
        dialog = NewProjectDialog(self, path if isinstance(path, str) else None)
        if dialog.exec():
            file, name, src, tgt = dialog.values()
            self._run(lambda progress, cancel: self.service.import_file(file, name, src, tgt, progress),
                      lambda project: self._open_project(project.id), "Importando archivo…")

    def _open_sample(self) -> None:
        """Crea un proyecto de ejemplo con el archivo incluido en la aplicación, para probarla en un clic."""
        sample = samples_dir() / "dialogos_ja.json"
        if self.worker is not None or not sample.exists():
            self.toast.show_message("No se encontró el archivo de ejemplo.", "error")
            return
        self._run(lambda progress, cancel: self.service.import_file(
            str(sample), "Ejemplo · diálogos (JP → ES)", "ja", "es", progress),
            lambda project: self._open_project(project.id), "Creando proyecto de ejemplo…")

    def _open_project(self, project_id: int) -> None:
        if self.worker is not None:
            return
        self.project = self.service.get_project(project_id)
        self._updating = True
        self.src_combo.setCurrentIndex(max(self.src_combo.findData(self.project.source_lang), 0))
        self.tgt_combo.setCurrentIndex(max(self.tgt_combo.findData(self.project.target_lang), 0))
        self._updating = False
        self.title_label.setText(self.project.name)
        self.file_label.setText(f"{Path(self.project.source_path).name} · {self.project.file_format}")
        self._reload_segments()
        self._set_project_actions(True)
        self.stack.setCurrentIndex(1)
        self._refresh_projects()

    def _delete_project(self) -> None:
        if not self.project:
            return
        answer = QMessageBox.question(self, APP_NAME, f"¿Eliminar el proyecto «{self.project.name}»?\n"
                                                      "El archivo original no se borra.")
        if answer == QMessageBox.Yes:
            self.service.delete_project(self.project.id)
            self.project, self.current = None, None
            self.model.set_segments([])
            self._set_project_actions(False)
            self.stack.setCurrentIndex(0)
            self._refresh_projects()

    def _langs_changed(self) -> None:
        if self._updating or not self.project:
            return
        try:
            self.service.set_languages(self.project.id, self.src_combo.currentData(), self.tgt_combo.currentData())
        except EXPECTED_ERRORS as exc:
            self.toast.show_message(str(exc), "error")
        self.project = self.service.get_project(self.project.id)
        self._updating = True
        self.src_combo.setCurrentIndex(max(self.src_combo.findData(self.project.source_lang), 0))
        self.tgt_combo.setCurrentIndex(max(self.tgt_combo.findData(self.project.target_lang), 0))
        self._updating = False
        self._refresh_projects()

    def _swap_langs(self) -> None:
        src, tgt = self.src_combo.currentData(), self.tgt_combo.currentData()
        self._updating = True
        self.src_combo.setCurrentIndex(self.src_combo.findData(tgt))
        self.tgt_combo.setCurrentIndex(self.tgt_combo.findData(src))
        self._updating = False
        self._langs_changed()

    # ================================================================ tabla y editor
    def _reload_segments(self) -> None:
        keep = self.current.id if self.current else None
        segments = self.service.segments(self.project.id)
        self.model.set_segments(segments)
        self._refresh_weave(segments, animate=keep is None)
        self._update_stats()
        row = self.model.row_of(keep) if keep is not None else None
        if row is not None:
            self.table.selectRow(row)
        else:
            self.current = None
            self._set_editor_enabled(False)
            self._clear_editor()

    def _refresh_weave(self, segments, animate: bool) -> None:
        self.weave.set_segments([sg.status for sg in segments], [self._tip(sg) for sg in segments], animate)
        row = self.model.row_of(self.current.id) if self.current else None
        self.weave.set_current(row if row is not None else -1)

    @staticmethod
    def _tip(seg) -> str:
        text = (seg.target_text or seg.source_text or "").replace("\n", " ")
        return text[:90] + ("…" if len(text) > 90 else "")

    def _jump_to_row(self, row: int) -> None:
        self.table.selectRow(row)
        self.table.scrollTo(self.model.index(row, 0), QAbstractItemView.PositionAtCenter)

    def _update_stats(self) -> None:
        s = self.service.stats(self.project.id)
        reviewed, translated = s.get("reviewed", 0), s.get("translated", 0)
        review, pending = s.get("needs_review", 0), s.get("pending", 0)
        self.bar.set_counts(reviewed, translated, review, pending)
        self.stats_label.set_counts(s["total"], {"reviewed": reviewed, "translated": translated,
                                                 "needs_review": review, "pending": pending})

    def _set_editor_enabled(self, enabled: bool) -> None:
        for w in (self.source_box, self.target_box, self.save_btn):
            w.setEnabled(enabled)

    def _clear_editor(self) -> None:
        self.source_box.clear()
        self.target_box.blockSignals(True)
        self.target_box.clear()
        self.target_box.blockSignals(False)
        self.issues_label.clear()
        self._clear_insert_buttons()
        self.thread_line.set_warning(False)

    def _show_source(self, text: str) -> None:
        body = rich_html(text, theme.p["input_bg"], one_line=False)
        self.source_box.setHtml(f'<p style="line-height:140%; margin:0;">{body}</p>')

    def _on_row_changed(self, current: QModelIndex, _previous) -> None:
        seg = self.model.segment_at(current.row()) if current.isValid() else None
        if seg is None:
            return
        self.current = seg
        self.weave.set_current(current.row())
        self._set_editor_enabled(True)
        self._show_source(seg.source_text)
        self.target_box.blockSignals(True)
        self.target_box.setPlainText(seg.target_text)
        self.target_box.blockSignals(False)
        self._live_validate()
        pulse(self.editor_card, 170, 0.6)

    def _clear_insert_buttons(self) -> None:
        while self.insert_box.count():
            item = self.insert_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _live_validate(self) -> None:
        self._clear_insert_buttons()
        if not self.current:
            return
        text = self.target_box.toPlainText()
        issues = validate(self.current.source_text, text) if text.strip() else []
        p = theme.p
        lines = []
        for issue in issues:
            color = p["rv"] if issue.severity == "error" else p["muted"]
            lines.append(f'<span style="color:{color};">{"●" if issue.severity == "error" else "○"}&nbsp; '
                         f'{issue.message}</span>')
        self.issues_label.setText("<br>".join(lines))
        self.thread_line.set_warning(has_errors(issues))
        missing = extract_placeholders(self.current.source_text) - extract_placeholders(text)
        for token in [t for t in missing if t != "\n"][:4]:
            btn = IconButton(f"Insertar {token}", None, "secondary")
            btn.clicked.connect(lambda _=False, t=token: self._insert_token(t))
            self.insert_box.addWidget(btn)

    def _insert_token(self, token: str) -> None:
        self.target_box.insertPlainText(token)
        self.target_box.setFocus()

    def _save(self) -> None:
        if not self.current:
            return
        try:
            seg, issues = self.service.save_translation(self.current.id, self.target_box.toPlainText())
        except EXPECTED_ERRORS as exc:
            self.toast.show_message(str(exc), "error")
            return
        self.current = seg
        self.model.update_segment(seg)
        row = self.model.row_of(seg.id)
        if row is not None:
            self.weave.set_status(row, seg.status, self._tip(seg))
        self._update_stats()
        self._refresh_projects()
        if has_errors(issues):
            self.toast.show_message("Guardado, pero revisa las variables", "error")
            return
        self.toast.show_message("Traducción guardada")
        row = self.model.row_of(seg.id)
        if row is not None and row + 1 < self.model.rowCount():
            self.table.selectRow(row + 1)
            self.table.scrollTo(self.model.index(row + 1, 0))

    # ================================================================ acciones
    def _prepare_languages(self) -> None:
        provider, src, tgt = self.provider_combo.currentData(), self.project.source_lang, self.project.target_lang
        self._run(lambda progress, cancel: self.service.prepare_languages(provider, src, tgt, progress),
                  lambda _: self.toast.show_message(f"Idiomas {src} → {tgt} listos para traducir sin internet"),
                  "Preparando idiomas (requiere internet la primera vez)…")

    def _translate(self, only_pending: bool) -> None:
        provider, pid = self.provider_combo.currentData(), self.project.id
        self._run(lambda progress, cancel: self.service.translate(pid, provider, only_pending, progress, cancel),
                  self._translation_done, "Traduciendo…")

    def _translation_done(self, report) -> None:
        self._reload_segments()
        self._refresh_projects()
        done, review, tm = report.get("translated", 0), report.get("needs_review", 0), report.get("tm_hits", 0)
        extra = f" · {review} por revisar" if review else ""
        extra += f" · {tm} desde la memoria" if tm else ""
        self.toast.show_message(f"{done} textos traducidos{extra}", "error" if review else "ok")

    def _open_glossary(self) -> None:
        GlossaryDialog(self.service, self.project.id, self).exec()

    def _export(self) -> None:
        source = Path(self.project.source_path)
        suggested = source.with_name(f"{source.stem}.{self.project.target_lang}{source.suffix}")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar traducción", str(suggested),
            f"{self.project.file_format} (*{source.suffix});;Todos (*.*)")
        if not path:
            return
        pid = self.project.id
        self._run(lambda progress, cancel: self.service.export(pid, path),
                  lambda report: self.toast.show_message(f"{report.get('exported', 0)} textos exportados"),
                  "Exportando…")


# ====================================================================== arranque
def _load_fonts(app: QApplication) -> None:
    for font_file in sorted((assets_dir() / "fonts").glob("*.[ot]tf")):
        QFontDatabase.addApplicationFont(str(font_file))
    font = QFont("Inter")
    font.setPointSizeF(10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)


def launch() -> None:
    set_app_id()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    icon_file = assets_dir() / "icon.png"
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))
    _load_fonts(app)
    settings = QSettings()
    theme.set(str(settings.value("theme", "dark")))
    window = MainWindow(LocWeaveService(Database(db_path())), settings)
    window.show()
    sys.exit(app.exec())
