"""Modelo de la tabla de segmentos y delegados de dibujo (pastillas de estado, variables resaltadas)."""
import html
from typing import Dict, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QTextDocument,
                           QTextOption)
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

from ..models import STATUS_LABELS, Segment
from ..services.placeholders import PLACEHOLDER_RE
from .theme import mix, qcolor, status_style, theme

COLUMNS = ("#", "Clave", "Original", "Traducción", "Estado")
SEGMENT_ROLE = Qt.UserRole + 1
PROJECT_ROLE = Qt.UserRole + 2


# ------------------------------------------------------------------ texto enriquecido
def rich_html(text: str, base_bg: str, one_line: bool = True) -> str:
    """HTML con las variables ({x}, %d, <b>, [x]…) resaltadas como etiquetas."""
    p = theme.p
    chip_bg, chip_fg = mix(base_bg, p["tr_base"], 0.20), p["chip"]
    out, last = [], 0
    for m in PLACEHOLDER_RE.finditer(text):
        out.append(_plain(text[last:m.start()], one_line))
        token = m.group(0)
        if token == "\n":
            out.append(" ⏎ " if one_line else "<br>")
        else:
            style = f"background-color:{chip_bg}; color:{chip_fg};"
            out.append(f'<span style="{style}">&nbsp;{html.escape(token)}&nbsp;</span>')
        last = m.end()
    out.append(_plain(text[last:], one_line))
    return f'<span style="color:{p["text"]};">{"".join(out)}</span>'


def _plain(chunk: str, one_line: bool) -> str:
    chunk = html.escape(chunk)
    return chunk.replace("\n", " ⏎ " if one_line else "<br>")


_DOC_CACHE: Dict[tuple, QTextDocument] = {}
theme.changed.connect(_DOC_CACHE.clear)


def _document(text: str, base_bg: str, font) -> QTextDocument:
    key = (text, base_bg, font.family(), font.pointSizeF())
    doc = _DOC_CACHE.get(key)
    if doc is None:
        if len(_DOC_CACHE) > 800:
            _DOC_CACHE.clear()
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(font)
        opt = QTextOption()
        opt.setWrapMode(QTextOption.NoWrap)
        doc.setDefaultTextOption(opt)
        doc.setHtml(rich_html(text, base_bg))
        _DOC_CACHE[key] = doc
    return doc


# ------------------------------------------------------------------ modelo
class SegmentTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: List[Segment] = []
        self._row_by_id: Dict[int, int] = {}

    def set_segments(self, segments: List[Segment]) -> None:
        self.beginResetModel()
        self._segments = list(segments)
        self._row_by_id = {s.id: i for i, s in enumerate(self._segments)}
        self.endResetModel()

    def update_segment(self, segment: Segment) -> None:
        row = self._row_by_id.get(segment.id)
        if row is None:
            return
        self._segments[row] = segment
        self.dataChanged.emit(self.index(row, 0), self.index(row, len(COLUMNS) - 1))

    def segment_at(self, row: int) -> Optional[Segment]:
        return self._segments[row] if 0 <= row < len(self._segments) else None

    def row_of(self, segment_id: int) -> Optional[int]:
        return self._row_by_id.get(segment_id)

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._segments)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        seg = self._segments[index.row()]
        if role == SEGMENT_ROLE:
            return seg
        if role == Qt.DisplayRole:
            return (str(index.row() + 1), seg.key, seg.source_text, seg.target_text,
                    STATUS_LABELS.get(seg.status, seg.status))[index.column()]
        return None


# ------------------------------------------------------------------ delegado de la tabla
class SegmentDelegate(QStyledItemDelegate):
    PAD = 16

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 44)

    def _paint_row_background(self, painter: QPainter, option, index) -> None:
        p = theme.p
        selected = bool(option.state & QStyle.State_Selected)
        hovered = getattr(option.widget, "hover_row", -1) == index.row()
        if not (selected or hovered):
            return
        r = QRectF(option.rect)
        last = index.column() == index.model().columnCount() - 1
        first = index.column() == 0
        radius = 8.0
        # cada celda dibuja un trozo de la misma «píldora»: los extremos se prolongan fuera de la celda y se recortan
        r.adjust(0 if first else -radius, 1, 0 if last else radius, -1)
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)
        painter.setClipRect(option.rect)
        painter.fillPath(path, QColor(p["sel_bg"] if selected else p["hover_row"]))
        if selected:
            painter.setPen(QPen(QColor(p["accent"]), 1))
            painter.drawPath(path)

    def paint(self, painter: QPainter, option, index) -> None:
        p = theme.p
        seg: Segment = index.data(SEGMENT_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        self._paint_row_background(painter, option, index)
        rect: QRect = option.rect
        col = index.column()
        selected = bool(option.state & QStyle.State_Selected)
        base_bg = p["sel_bg"] if selected else p["panel"]
        inner = rect.adjusted(self.PAD, 0, -self.PAD, 0)
        painter.setClipRect(rect)

        if col in (0, 1):
            painter.setPen(QColor(p["muted"]))
            painter.setFont(option.font)
            text = index.data(Qt.DisplayRole)
            painter.drawText(inner, Qt.AlignVCenter | Qt.AlignLeft,
                             QFontMetrics(option.font).elidedText(text, Qt.ElideRight, inner.width()))
        elif col in (2, 3):
            text = seg.source_text if col == 2 else seg.target_text
            if col == 3 and not text.strip():
                painter.setPen(QColor(p["muted"]))
                painter.setFont(option.font)
                painter.drawText(inner, Qt.AlignVCenter | Qt.AlignLeft, "Sin traducir")
            else:
                doc = _document(text, base_bg, option.font)
                painter.setClipRect(inner)
                dy = inner.top() + (inner.height() - doc.size().height()) / 2
                painter.translate(inner.left(), dy)
                doc.drawContents(painter)
                painter.translate(-inner.left(), -dy)
                if doc.idealWidth() > inner.width():   # texto largo: se desvanece al borde en lugar de cortarse en seco
                    fade = QLinearGradient(inner.right() - 34, 0, inner.right(), 0)
                    fade.setColorAt(0.0, qcolor(base_bg, 0.0))
                    fade.setColorAt(1.0, qcolor(base_bg, 1.0))
                    painter.fillRect(QRect(inner.right() - 34, rect.top(), 35, rect.height()), QBrush(fade))
        else:
            self._paint_pill(painter, inner, seg, option.font)
        painter.restore()

    @staticmethod
    def _paint_pill(painter: QPainter, inner: QRect, seg: Segment, font) -> None:
        p = theme.p
        fg, bg = status_style(seg.status, p)
        label = STATUS_LABELS.get(seg.status, seg.status)
        metrics = QFontMetrics(font)
        w, h = metrics.horizontalAdvance(label) + 36, 24
        pill = QRectF(inner.left(), inner.top() + (inner.height() - h) / 2, w, h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(pill, h / 2, h / 2)
        painter.setBrush(fg)
        painter.drawEllipse(QPointF(pill.left() + 14, pill.center().y()), 3, 3)
        painter.setPen(fg)
        painter.drawText(QRectF(pill.left() + 24, pill.top(), w - 28, h), Qt.AlignVCenter | Qt.AlignLeft, label)


# ------------------------------------------------------------------ delegado de proyectos
class ProjectDelegate(QStyledItemDelegate):
    ACCENTS = ("accent", "#9B6BFF", "#2DB7A3", "#E6678F", "#F2B84B", "#5BC48A")
    STATUS_KEYS = (("reviewed", "bar_ok"), ("translated", "accent"), ("needs_review", "bar_rv"), ("pending", "track"))
    CELLS, ROWS = 26, 2

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 84)

    @classmethod
    def accent_for(cls, name: str, p: dict) -> str:
        pick = cls.ACCENTS[sum(ord(c) for c in name) % len(cls.ACCENTS)]
        return p.get(pick, pick)

    @classmethod
    def mini_weave(cls, counts: dict) -> list:
        """Reparte las celdas del mini tejido según las proporciones de cada estado (orden estable, aspecto tejido)."""
        n = cls.CELLS * cls.ROWS
        total = sum(counts.get(k, 0) for k, _ in cls.STATUS_KEYS) or 1
        cells, used = [], 0
        for key, _ in cls.STATUS_KEYS:
            c = round(counts.get(key, 0) / total * n)
            cells += [key] * min(c, n - used)
            used += c
        cells += ["pending"] * (n - len(cells))
        return [cells[(i * 11) % n] for i in range(n)]

    def paint(self, painter: QPainter, option, index) -> None:
        p = theme.p
        info: dict = index.data(PROJECT_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(option.rect).adjusted(4, 3, -4, -3)
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        painter.setBrush(QColor(p["sel_bg"] if selected else (p["raised"] if hovered else qcolor(p["raised"], 0.45))))
        painter.setPen(QPen(QColor(p["sel_border"]), 1) if selected else Qt.NoPen)
        painter.drawRoundedRect(rect, 11, 11)
        accent = QColor(self.accent_for(info["name"], p))
        painter.setPen(Qt.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(QRectF(rect.left() + 5, rect.top() + 13, 3.5, rect.height() - 26), 1.75, 1.75)
        inner = rect.adjusted(20, 9, -12, -9)
        font = option.font
        metrics = QFontMetrics(font)
        painter.setFont(font)
        painter.setPen(QColor(p["text"]))
        painter.drawText(QRectF(inner.left(), inner.top(), inner.width(), 18), Qt.AlignLeft | Qt.AlignVCenter,
                         metrics.elidedText(info["name"], Qt.ElideRight, int(inner.width())))
        small = painter.font()
        small.setPointSizeF(max(font.pointSizeF() - 1, 8))
        painter.setFont(small)
        painter.setPen(QColor(p["muted"]))
        painter.drawText(QRectF(inner.left(), inner.top() + 19, inner.width(), 16), Qt.AlignLeft | Qt.AlignVCenter,
                         QFontMetrics(small).elidedText(info["subtitle"], Qt.ElideRight, int(inner.width())))
        # mini tejido: dos filas de hilos con los colores de cada estado
        cells = self.mini_weave(info.get("counts", {}))
        colors = {key: p[col] for key, col in self.STATUS_KEYS}
        area_top, area_h = inner.bottom() - 15, 15.0
        step = inner.width() / self.CELLS
        size = min(step, area_h / self.ROWS)
        painter.setPen(Qt.NoPen)
        for i, status in enumerate(cells):
            col, row = i % self.CELLS, i // self.CELLS
            color = QColor(colors[status])
            if status == "pending":
                color.setAlphaF(0.55)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(inner.left() + col * step + 0.8, area_top + row * (size + 0.5), step - 1.6,
                                           size - 1.4), 1.6, 1.6)
        painter.restore()
