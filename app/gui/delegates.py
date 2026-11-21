"""Modelo de la tabla de segmentos y delegados de dibujo (pastillas de estado, variables resaltadas)."""
import html
from typing import Dict, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen, QTextDocument, QTextOption
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

from ..models import STATUS_LABELS, Segment
from ..services.placeholders import PLACEHOLDER_RE
from .theme import mix, status_style, theme

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
        r.adjust(-radius if first else 0, 1, radius if last else 0, -1)
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
                painter.translate(inner.left(), inner.top() + (inner.height() - doc.size().height()) / 2)
                doc.drawContents(painter)
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
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 70)

    def paint(self, painter: QPainter, option, index) -> None:
        p = theme.p
        info: dict = index.data(PROJECT_ROLE)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(option.rect).adjusted(4, 2, -4, -2)
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        if selected or hovered:
            painter.setBrush(QColor(p["sel_bg"] if selected else p["raised"]))
            painter.setPen(QPen(QColor(p["sel_border"]), 1) if selected else Qt.NoPen)
            painter.drawRoundedRect(rect, 10, 10)
        inner = rect.adjusted(14, 10, -14, -10)
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
        track = QRectF(inner.left(), inner.bottom() - 4, inner.width(), 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(p["track"]))
        painter.drawRoundedRect(track, 2, 2)
        fraction = info["progress"]
        if fraction > 0:
            done = QRectF(track.left(), track.top(), track.width() * fraction, 4)
            painter.setBrush(QColor(p["bar_ok"] if fraction >= 0.999 else p["accent"]))
            painter.drawRoundedRect(done, 2, 2)
        painter.restore()
