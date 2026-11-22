"""Paletas (oscura y clara), hoja de estilos QSS y gestor de tema."""
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from ..config import data_dir
from .icons import svg_bytes

DARK = {
    "name": "dark", "bg": "#0E1424", "panel": "#151C30", "raised": "#1B2440", "raised_hover": "#222D50",
    "border": "#2A3658", "text": "#E8ECF5", "muted": "#9AA6C4", "accent": "#4C7DFF", "accent_hover": "#6B93FF",
    "accent_press": "#3A67E0", "on_accent": "#08101F", "sel_bg": "#1F2A4A", "sel_border": "#3A4F8C",
    "input_bg": "#0E1424", "track": "#26314F", "hover_row": "#19223C", "danger": "#7F1D1D",
    "ok": "#7FD6A4", "ok_base": "#5BC48A", "tr": "#9DB8FF", "tr_base": "#4C7DFF", "rv": "#F7C766",
    "rv_base": "#F2B84B", "pe": "#9AA6C4", "pe_base": "#9AA6C4", "chip": "#B4C8FF",
    "bar_ok": "#5BC48A", "bar_rv": "#F2B84B",
}
LIGHT = {
    "name": "light", "bg": "#F2F5FB", "panel": "#FFFFFF", "raised": "#EEF2FB", "raised_hover": "#E3E9F7",
    "border": "#D3DAEA", "text": "#14203A", "muted": "#5B6784", "accent": "#2F5FE0", "accent_hover": "#4A74EA",
    "accent_press": "#244FC4", "on_accent": "#FFFFFF", "sel_bg": "#E4EBFB", "sel_border": "#9DB2EA",
    "input_bg": "#F2F5FB", "track": "#DCE3F2", "hover_row": "#F3F6FD", "danger": "#B91C1C",
    "ok": "#1B7447", "ok_base": "#1F7A4D", "tr": "#2447B5", "tr_base": "#2F5FE0", "rv": "#8A5700",
    "rv_base": "#E09614", "pe": "#5B6784", "pe_base": "#5B6784", "chip": "#2447B5",
    "bar_ok": "#2E9E6A", "bar_rv": "#E0A12A",
}
PALETTES = {"dark": DARK, "light": LIGHT}
FONT_STACK = '"Inter", "Segoe UI", "Yu Gothic UI", "Meiryo UI", "Noto Sans JP", sans-serif'


def rgba(hex_color: str, alpha: float) -> str:
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{int(alpha * 255)})"


def qcolor(hex_color: str, alpha: float = 1.0) -> QColor:
    c = QColor(hex_color)
    c.setAlphaF(alpha)
    return c


def mix(a: str, b: str, t: float) -> str:
    """Mezcla opaca de dos colores (t=0 → a, t=1 → b)."""
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() + (cb.red() - ca.red()) * t), int(ca.green() + (cb.green() - ca.green()) * t),
                  int(ca.blue() + (cb.blue() - ca.blue()) * t)).name()


def status_style(status: str, p: dict):
    """(color de texto, color de fondo) de la pastilla de cada estado."""
    key = {"reviewed": "ok", "translated": "tr", "needs_review": "rv"}.get(status, "pe")
    alpha = 0.16 if p["name"] == "dark" else 0.14
    return QColor(p[key]), qcolor(p[key + "_base"], alpha)


def _chevron_file(p: dict) -> str:
    path: Path = data_dir() / f"chevron-{p['name']}.svg"
    path.write_bytes(svg_bytes("chevron", p["muted"]).data())
    return path.as_posix()


def build_qss(p: dict) -> str:
    chevron = _chevron_file(p)
    return f"""
QMainWindow, QDialog {{ background: {p['bg']}; }}
QFrame#Card {{ background: {p['panel']}; border-radius: 12px; border: none; }}
QFrame#Group {{ background: {p['raised']}; border: 1px solid {p['border']}; border-radius: 10px; }}
QFrame#Toast {{ background: {p['raised']}; border: 1px solid {p['sel_border']}; border-radius: 12px; }}
QFrame#StepCard {{ background: {rgba(p['panel'], 0.82)}; border: 1px solid {p['border']};
  border-radius: 16px; }}
QFrame#StepCard:hover {{ background: {p['raised']}; border: 1px solid {p['sel_border']}; }}
QLabel#IconTile {{ background: {rgba(p['accent'], 0.16)}; border-radius: 11px; }}
QLabel[role="stepnum"] {{ font-size: 12px; font-weight: 600; color: {p['muted']}; }}
QLabel[role="cardtitle"] {{ font-size: 15px; font-weight: 600; }}
QLabel {{ color: {p['text']}; background: transparent; }}
QLabel[muted="true"] {{ color: {p['muted']}; }}
QLabel[role="title"] {{ font-size: 24px; font-weight: 600; }}
QLabel[role="hero"] {{ font-size: 28px; font-weight: 600; }}
QLabel[role="small"] {{ font-size: 12px; color: {p['muted']}; }}
QLabel[role="step"] {{ font-size: 13px; font-weight: 600; color: {p['accent']}; }}
QLabel[role="section"] {{ font-size: 12px; font-weight: 500; color: {p['muted']}; }}
QToolTip {{ background: {p['raised']}; color: {p['text']}; border: 1px solid {p['border']}; padding: 6px 8px; }}

QPushButton {{ min-height: 36px; padding: 0 14px; border-radius: 8px; border: 1px solid {p['border']};
  background: {p['raised']}; color: {p['text']}; font-weight: 500; }}
QPushButton:hover {{ background: {p['raised_hover']}; }}
QPushButton:pressed {{ background: {p['border']}; }}
QPushButton:focus {{ border: 1px solid {p['accent']}; }}
QPushButton:disabled {{ color: {p['muted']}; background: {p['raised']}; border: 1px solid {p['border']}; }}
QPushButton[iconOnly="true"] {{ padding: 0; }}
QPushButton[kind="primary"] {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {p['accent']},
  stop:1 {mix(p['accent'], '#9B6BFF', 0.5)}); border: 1px solid {p['accent']}; color: {p['on_accent']};
  font-weight: 600; }}
QPushButton[kind="primary"]:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {p['accent_hover']},
  stop:1 {mix(p['accent_hover'], '#9B6BFF', 0.5)}); border-color: {p['accent_hover']}; }}
QPushButton[kind="primary"]:pressed {{ background: {p['accent_press']}; border-color: {p['accent_press']}; }}
QPushButton[kind="primary"]:disabled {{ background: {p['track']}; border-color: {p['track']}; color: {p['muted']}; }}
QPushButton[kind="ghost"] {{ background: transparent; border: 1px solid transparent; }}
QPushButton[kind="ghost"]:hover {{ background: {p['raised']}; }}
QPushButton[kind="danger"]:hover {{ background: {p['danger']}; border-color: {p['danger']}; color: #FFFFFF; }}
QPushButton[kind="seg"] {{ min-height: 30px; padding: 0 12px; border: none; background: transparent;
  color: {p['muted']}; }}
QPushButton[kind="seg"]:hover {{ color: {p['text']}; }}
QPushButton[kind="seg"]:checked {{ background: {p['sel_bg']}; color: {p['text']}; }}

QLineEdit, QTextEdit, QPlainTextEdit {{ background: {p['input_bg']}; color: {p['text']};
  border: 1px solid {p['border']}; border-radius: 10px; padding: 10px 14px;
  selection-background-color: {p['accent']}; selection-color: {p['on_accent']}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {p['accent']}; }}
QTextEdit[readonlyBox="true"] {{ border: 1px solid transparent; }}
QLineEdit {{ min-height: 20px; }}

QComboBox {{ background: {p['raised']}; color: {p['text']}; border: 1px solid {p['border']}; border-radius: 8px;
  min-height: 34px; padding: 0 12px; font-weight: 500; }}
QComboBox:hover {{ background: {p['raised_hover']}; }}
QComboBox:focus {{ border: 1px solid {p['accent']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({chevron}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{ background: {p['panel']}; color: {p['text']}; border: 1px solid {p['border']};
  selection-background-color: {p['sel_bg']}; selection-color: {p['text']}; outline: 0; padding: 4px; }}
QGroupBox {{ border: none; }}

QTableView, QListView, QTableWidget {{ background: transparent; border: none; outline: 0; color: {p['text']};
  selection-background-color: transparent; gridline-color: transparent; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: transparent; color: {p['muted']}; border: none; padding: 8px 16px;
  font-size: 12px; font-weight: 500; }}
QTableCornerButton::section {{ background: transparent; border: none; }}
QTableWidget::item {{ padding: 6px 10px; }}
QTableWidget::item:selected {{ background: {p['sel_bg']}; color: {p['text']}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p['border']}; border-radius: 4px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {p['sel_border']}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p['border']}; border-radius: 4px; min-width: 36px; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
  background: none; border: none; height: 0; width: 0; }}

QProgressBar {{ background: {p['track']}; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }}
QProgressBar::chunk {{ background: {p['accent']}; border-radius: 3px; }}
QMessageBox {{ background: {p['panel']}; }}
"""


class ThemeManager(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.name = "dark"
        self.p = DARK

    def set(self, name: str) -> None:
        name = name if name in PALETTES else "dark"
        self.name, self.p = name, PALETTES[name]
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_qss(self.p))
        self.changed.emit()


theme = ThemeManager()
