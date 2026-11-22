"""Elementos decorativos: fondos con brillo, logo con halo, título con degradado, tarjetas y etiquetas."""
from PySide6.QtCore import QPointF, QRectF, Qt
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
