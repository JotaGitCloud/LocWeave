"""Elementos decorativos: fondos con brillo, logo con halo, título con degradado, tarjetas y etiquetas."""
from typing import List

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen,
                           QRadialGradient)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .icons import icon, logo_svg
from .theme import mix, qcolor, theme

VIOLET = "#9B6BFF"   # segundo color del degradado de marca


def brand_gradient(x1: float, y1: float, x2: float, y2: float) -> QLinearGradient:
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0.0, QColor(theme.p["accent_hover"]))
    g.setColorAt(1.0, QColor(mix(theme.p["accent"], VIOLET, 0.6)))
    return g


def _glow(painter: QPainter, center: QPointF, radius: float, color: str, alpha: float) -> None:
    grad = QRadialGradient(center, radius)
    grad.setColorAt(0.0, qcolor(color, alpha))
    grad.setColorAt(1.0, qcolor(color, 0.0))
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(grad))
    painter.drawRect(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))


class AuroraBackground(QWidget):
    """Fondo de la pantalla de inicio: brillos suaves de color y una cuadrícula de puntos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        dark = p["name"] == "dark"
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(p["bg"]))
        w, h = self.width(), self.height()
        _glow(painter, QPointF(w * 0.5, h * 0.18), max(w, h) * 0.55, p["accent"], 0.20 if dark else 0.14)
        _glow(painter, QPointF(w * 0.92, h * 0.88), max(w, h) * 0.45, VIOLET, 0.13 if dark else 0.10)
        _glow(painter, QPointF(w * 0.05, h * 0.75), max(w, h) * 0.30, p["accent"], 0.08 if dark else 0.06)
        painter.setPen(Qt.NoPen)
        painter.setBrush(qcolor(p["text"], 0.055 if dark else 0.07))
        step = 28
        for x in range(step // 2, w, step):
            for y in range(step // 2, h, step):
                painter.drawEllipse(QPointF(x, y), 1.1, 1.1)


class SidebarFrame(QFrame):
    """Barra lateral con un degradado sutil y un resplandor de marca arriba."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        dark = p["name"] == "dark"
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        base = QLinearGradient(0, 0, 0, self.height())
        base.setColorAt(0.0, QColor(mix(p["panel"], p["accent"], 0.06 if dark else 0.04)))
        base.setColorAt(1.0, QColor(p["panel"]))
        painter.fillRect(self.rect(), QBrush(base))
        _glow(painter, QPointF(self.width() * 0.3, 0), self.width() * 1.1, p["accent"], 0.20 if dark else 0.12)
        painter.setPen(QPen(qcolor(p["border"], 0.9), 1))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())


class HeroLogo(QWidget):
    """Logo grande dentro de una baldosa con halo de color."""

    def __init__(self, size: int = 112, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        s = self._size
        _glow(painter, QPointF(s / 2, s / 2), s * 0.62, p["accent"], 0.38)
        tile = QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64)
        path = QPainterPath()
        path.addRoundedRect(tile, s * 0.18, s * 0.18)
        painter.fillPath(path, QColor(mix(p["panel"], p["accent"], 0.10)))
        painter.setPen(QPen(qcolor(p["accent"], 0.55), 1.2))
        painter.drawPath(path)
        logo = QRectF(tile.x() + s * 0.1, tile.y() + s * 0.1, tile.width() - s * 0.2, tile.height() - s * 0.2)
        QSvgRenderer(logo_svg(p["accent_hover"], p["text"])).render(painter, logo)


class GradientTitle(QWidget):
    """Título grande con degradado de marca."""

    def __init__(self, text: str, point_size: float = 26, parent=None):
        super().__init__(parent)
        self._text = text
        self._font = QFont("Inter")
        self._font.setPointSizeF(point_size)
        self._font.setWeight(QFont.DemiBold)
        self._font.setStyleHint(QFont.SansSerif)
        metrics = QFontMetrics(self._font)
        self.setFixedSize(metrics.horizontalAdvance(text) + 12, metrics.height() + 8)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self._font)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor(theme.p["text"]))
        grad.setColorAt(1.0, QColor(mix(theme.p["accent_hover"], VIOLET, 0.55)))
        painter.setPen(QPen(QBrush(grad), 0))
        painter.drawText(self.rect(), Qt.AlignCenter, self._text)


class Pill(QWidget):
    """Etiqueta redondeada, p. ej. «100 % local»."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        font = QFont(self.font())
        font.setPointSizeF(9.5)
        font.setWeight(QFont.Medium)
        self._font = font
        self.setFixedSize(QFontMetrics(font).horizontalAdvance(text) + 30, 26)
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setBrush(qcolor(p["accent"], 0.13))
        painter.setPen(QPen(qcolor(p["accent"], 0.32), 1))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        painter.setFont(self._font)
        painter.setPen(QColor(p["chip"]))
        painter.drawText(rect, Qt.AlignCenter, self._text)


class FeatureCard(QFrame):
    """Tarjeta con icono, título y texto; resalta al pasar el ratón (ver QSS de StepCard)."""

    def __init__(self, number: str, icon_name: str, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StepCard")
        self.setFixedSize(248, 150)
        self.setCursor(Qt.ArrowCursor)
        self._icon_name = icon_name
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 16)
        v.setSpacing(4)
        top = QHBoxLayout()
        self._tile = QLabel()
        self._tile.setObjectName("IconTile")
        self._tile.setFixedSize(38, 38)
        self._tile.setAlignment(Qt.AlignCenter)
        top.addWidget(self._tile)
        top.addStretch(1)
        num = QLabel(number)
        num.setProperty("role", "stepnum")
        top.addWidget(num)
        v.addLayout(top)
        v.addSpacing(6)
        head = QLabel(title)
        head.setProperty("role", "cardtitle")
        v.addWidget(head)
        body = QLabel(text)
        body.setProperty("role", "small")
        body.setWordWrap(True)
        v.addWidget(body)
        v.addStretch(1)
        self._refresh()
        theme.changed.connect(self._refresh)

    def _refresh(self) -> None:
        self._tile.setPixmap(icon(self._icon_name, theme.p["accent_hover"], 20).pixmap(20, 20))


class StatsLegend(QWidget):
    """Leyenda de estados con punto de color: «● 4 revisados  ● 10 traducidos …» (colores iguales a la barra)."""

    ITEMS = (("reviewed", "ok_base", "revisados"), ("translated", "tr_base", "traducidos"),
             ("needs_review", "rv_base", "por revisar"), ("pending", "pe_base", "pendientes"))

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._counts = {}
        self.setFixedHeight(22)
        theme.changed.connect(self.update)

    def set_counts(self, total: int, counts: dict) -> None:
        self._total, self._counts = total, counts
        self.update()

    def paintEvent(self, _event):
        p = theme.p
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont(self.font())
        font.setPointSizeF(9.5)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        x, mid = 0.0, self.height() / 2
        head = f"{self._total} textos"
        painter.setPen(QColor(p["text"]))
        painter.drawText(QRectF(x, 0, metrics.horizontalAdvance(head) + 4, self.height()),
                         Qt.AlignVCenter | Qt.AlignLeft, head)
        x += metrics.horizontalAdvance(head) + 22
        for key, color, label in self.ITEMS:
            count = self._counts.get(key, 0)
            text = f"{count} {label}"
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(p[color]) if count else qcolor(p[color], 0.35))
            painter.drawEllipse(QPointF(x + 4, mid), 4, 4)
            painter.setPen(QColor(p["muted"]) if count else qcolor(p["muted"], 0.6))
            painter.drawText(QRectF(x + 14, 0, metrics.horizontalAdvance(text) + 4, self.height()),
                             Qt.AlignVCenter | Qt.AlignLeft, text)
            x += 14 + metrics.horizontalAdvance(text) + 20


class WeaveMap(QWidget):
    """«Tejido» del proyecto: cada texto es un hilo de color según su estado. Clic para saltar a ese texto."""

    rowClicked = Signal(int)
    STATUS_COLOR = {"reviewed": "bar_ok", "translated": "accent", "needs_review": "bar_rv", "pending": "track"}
    STATUS_LABEL = {"reviewed": "Revisado", "translated": "Traducido", "needs_review": "Por revisar",
                    "pending": "Pendiente"}
    MAX_H = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status: List[str] = []
        self._tips: List[str] = []
        self._current = -1
        self._hover = -1
        self._t = 1.0
        self._geom = (8.0, 1, 1)   # tamaño de celda, columnas, filas
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(18)
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(900)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._tick)
        theme.changed.connect(self.update)

    def set_segments(self, statuses: List[str], tips: List[str], animate: bool = True) -> None:
        self._status, self._tips = list(statuses), list(tips)
        self._relayout()
        if animate and statuses:
            self._anim.stop()
            self._anim.start()
        else:
            self._t = 1.0
        self.update()

    def set_status(self, row: int, status: str, tip: str) -> None:
        if 0 <= row < len(self._status):
            self._status[row], self._tips[row] = status, tip
            self.update()

    def set_current(self, row: int) -> None:
        self._current = row
        self.update()

    def _tick(self, value) -> None:
        self._t = float(value)
        self.update()

    def _relayout(self) -> None:
        n, width = max(len(self._status), 1), max(self.width(), 1)
        size = 14.0
        while size > 4.0:
            cols = max(int(width // size), 1)
            rows = -(-n // cols)
            if rows * size <= self.MAX_H:
                break
            size -= 1.0
        cols = max(int(width // size), 1)
        rows = -(-n // cols)
        self._geom = (size, cols, rows)
        self.setFixedHeight(int(max(rows * size, 12)) + 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        old = self._geom
        self._relayout()
        if old != self._geom:
            self.update()

    def _cell_rect(self, i: int) -> QRectF:
        size, cols, _ = self._geom
        return QRectF((i % cols) * size, (i // cols) * size + 1, size, size)

    def _index_at(self, pos) -> int:
        size, cols, rows = self._geom
        col, row = int(pos.x() // size), int((pos.y() - 1) // size)
        i = row * cols + col
        return i if 0 <= col < cols and 0 <= row < rows and 0 <= i < len(self._status) else -1

    def mouseMoveEvent(self, event):
        i = self._index_at(event.position())
        if i != self._hover:
            self._hover = i
            self.update()
        if i >= 0:
            self.setToolTip(f"#{i + 1} · {self.STATUS_LABEL.get(self._status[i], '')}\n{self._tips[i]}")
        else:
            self.setToolTip("")
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        i = self._index_at(event.position())
        if i >= 0 and event.button() == Qt.LeftButton:
            self.rowClicked.emit(i)
        super().mousePressEvent(event)

    def paintEvent(self, _event):
        p = theme.p
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        n = len(self._status)
        size, cols, _ = self._geom
        gap = 1.0 if size < 8 else 1.6
        radius = max(size * 0.28, 1.2)
        painter.setPen(Qt.NoPen)
        if n == 0:
            painter.setBrush(QColor(p["track"]))
            painter.drawRoundedRect(QRectF(0, 1, self.width(), 10), 5, 5)
            return
        for i, status in enumerate(self._status):
            # barrido de aparición de izquierda a derecha, como un telar
            reveal = min(max(self._t * 1.6 - (i / n) * 0.6, 0.0), 1.0)
            if reveal <= 0:
                continue
            color = QColor(p[self.STATUS_COLOR.get(status, "track")])
            if status == "pending":
                color.setAlphaF(0.55)
            color.setAlphaF(color.alphaF() * reveal)
            rect = self._cell_rect(i).adjusted(gap / 2, gap / 2, -gap / 2, -gap / 2)
            painter.setBrush(color)
            painter.drawRoundedRect(rect, radius, radius)
        for i, width in ((self._hover, 1.2), (self._current, 2.0)):
            if 0 <= i < n:
                rect = self._cell_rect(i).adjusted(-1, -1, 1, 1)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(p["text"]), width))
                painter.drawRoundedRect(rect, radius + 1, radius + 1)
                painter.setPen(Qt.NoPen)


class GlowCard(QFrame):
    """Tarjeta con fondo de panel, borde fino y un brillo de color en una esquina."""

    def __init__(self, parent=None, corner: str = "tr", strength: float = 1.0):
        super().__init__(parent)
        self.setObjectName("GlowCard")
        self._corner, self._strength = corner, strength
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        dark = p["name"] == "dark"
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        painter.fillPath(path, QColor(p["panel"]))
        painter.save()
        painter.setClipPath(path)
        x = rect.right() if "r" in self._corner else rect.left()
        y = rect.top() if "t" in self._corner else rect.bottom()
        _glow(painter, QPointF(x, y), max(rect.width() * 0.45, 220), p["accent"],
              (0.16 if dark else 0.10) * self._strength)
        _glow(painter, QPointF(rect.width() - x, rect.height() - y), 180, VIOLET,
              (0.07 if dark else 0.05) * self._strength)
        painter.restore()
        edge = QLinearGradient(rect.topLeft(), rect.bottomRight())
        edge.setColorAt(0.0, qcolor(p["accent"], 0.38 if dark else 0.30))
        edge.setColorAt(0.5, qcolor(p["border"], 0.9))
        edge.setColorAt(1.0, qcolor(VIOLET, 0.28 if dark else 0.22))
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QBrush(edge), 1.0))
        painter.drawPath(path)


class ProgressRing(QWidget):
    """Anillo de avance con degradado de marca y porcentaje al centro."""

    def __init__(self, size: int = 92, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._value = 0.0
        self._from = 0.0
        self._to = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(700)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._tick)
        theme.changed.connect(self.update)

    def set_value(self, fraction: float) -> None:
        self._from, self._to = self._value, max(0.0, min(1.0, fraction))
        self._anim.stop()
        self._anim.start()

    def settle(self) -> None:
        """Termina la animación al instante (capturas y pruebas)."""
        self._anim.stop()
        self._value = self._to
        self.update()

    def _tick(self, t) -> None:
        self._value = self._from + (self._to - self._from) * float(t)
        self.update()

    def paintEvent(self, _event):
        p = theme.p
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        thick = 9.0
        rect = QRectF(self.rect()).adjusted(thick, thick, -thick, -thick)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(p["track"]), thick, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(rect)
        if self._value > 0.003:
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, QColor(p["accent_hover"]))
            grad.setColorAt(1.0, QColor(mix(p["accent"], VIOLET, 0.7)))
            painter.setPen(QPen(QBrush(grad), thick, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(rect, 90 * 16, int(-self._value * 360 * 16))
        font = QFont(self.font())
        font.setPointSizeF(15)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(p["text"]))
        painter.drawText(QRectF(self.rect()).adjusted(0, -7, 0, -7), Qt.AlignCenter, f"{round(self._value * 100)}%")
        font.setPointSizeF(8)
        font.setWeight(QFont.Normal)
        painter.setFont(font)
        painter.setPen(QColor(p["muted"]))
        painter.drawText(QRectF(self.rect()).adjusted(0, 22, 0, 22), Qt.AlignCenter, "avance")
