"""Componentes visuales propios de LocWeave."""
from typing import List, Optional

from PySide6.QtCore import (QEasingCurve, QEvent, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QWidget)

from .icons import icon, logo_svg
from .theme import theme


def fade_in(widget: QWidget, duration: int = 220, start: float = 0.0) -> QPropertyAnimation:
    """Desvanece una ventana (windowOpacity) al mostrarse."""
    widget.setWindowOpacity(start)
    anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    widget._fade_anim = anim  # evita que el recolector la destruya
    return anim


def pulse(widget: QWidget, duration: int = 180, start: float = 0.5) -> None:
    """Breve desvanecimiento de un panel interno (efecto de opacidad)."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    widget._pulse_anim = anim


class LogoWidget(QWidget):
    def __init__(self, size: int = 30, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        theme.changed.connect(self.update)

    def paintEvent(self, _event):
        p = theme.p
        renderer = QSvgRenderer(logo_svg(p["accent"], p["text"]))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter, QRectF(0, 0, self._size, self._size))


class IconButton(QPushButton):
    """Botón con icono que se recolorea al cambiar de tema."""

    def __init__(self, text: str = "", icon_name: Optional[str] = None, kind: str = "secondary",
                 icon_only: bool = False, parent=None):
        super().__init__(text, parent)
        self._icon_name = icon_name
        self.setProperty("kind", kind)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(16, 16))
        if icon_only:
            self.setFixedWidth(38)
            self.setProperty("iconOnly", True)
        if kind == "seg":
            self.toggled.connect(lambda _checked: self.refresh_icon())
        self.refresh_icon()
        theme.changed.connect(self.refresh_icon)

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self.refresh_icon()

    def refresh_icon(self) -> None:
        name = getattr(self, "_icon_name", None)
        if not name:
            return
        p = theme.p
        kind = self.property("kind")
        color = p["on_accent"] if kind == "primary" else p["text"]
        if kind == "seg" and not self.isChecked():
            color = p["muted"]
        if not self.isEnabled():
            color = p["muted"]
        self.setIcon(icon(name, color, 16))

    def changeEvent(self, event):  # recolorea el icono al habilitar/deshabilitar
        super().changeEvent(event)
        if event.type() == QEvent.EnabledChange:
            self.refresh_icon()


class ThemeToggle(QFrame):
    """Selector «Claro | Oscuro»."""
    toggled_to = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Group")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        self.buttons = {}
        for name, label in (("light", "Claro"), ("dark", "Oscuro")):
            btn = IconButton(label, "sun" if name == "light" else "moon", "seg")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda _=False, n=name: self.toggled_to.emit(n))
            layout.addWidget(btn)
            self.buttons[name] = btn
        theme.changed.connect(self.sync)
        self.sync()

    def sync(self) -> None:
        for name, btn in self.buttons.items():
            btn.setChecked(name == theme.name)
            btn.refresh_icon()


class SegmentedBar(QWidget):
    """Barra de progreso en segmentos: revisados, traducidos, por revisar, pendientes (animada)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(6)
        self._from: List[float] = [0, 0, 0, 1]
        self._to: List[float] = [0, 0, 0, 1]
        self._t = 1.0
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(450)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._tick)
        theme.changed.connect(self.update)

    def set_counts(self, reviewed: int, translated: int, needs_review: int, pending: int) -> None:
        total = max(reviewed + translated + needs_review + pending, 1)
        target = [reviewed / total, translated / total, needs_review / total, pending / total]
        self._from = self._current()
        self._to = target
        self._anim.stop()
        self._anim.start()

    def _current(self) -> List[float]:
        return [a + (b - a) * self._t for a, b in zip(self._from, self._to)]

    def _tick(self, value) -> None:
        self._t = float(value)
        self.update()

    def paintEvent(self, _event):
        p = theme.p
        colors = [p["bar_ok"], p["accent"], p["bar_rv"], p["track"]]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 3, 3)
        painter.setClipPath(clip)
        gap, x, w = 2.0, 0.0, float(self.width())
        for color, frac in zip(colors, self._current()):
            seg = frac * w
            if seg <= 0.5:
                continue
            painter.fillRect(QRectF(x, 0, max(seg - gap, 1), self.height()), QColor(color))
            x += seg


class ThreadLine(QWidget):
    """El «hilo» que une el texto original con su traducción."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(56)
        self.warning = False
        theme.changed.connect(self.update)

    def set_warning(self, warning: bool) -> None:
        self.warning = warning
        self.update()

    def paintEvent(self, _event):
        p = theme.p
        w, h = self.width(), self.height()
        start, end = QPointF(0, h * 0.2), QPointF(w, h * 0.5)
        path = QPainterPath(start)
        path.cubicTo(QPointF(w * 0.5, h * 0.2), QPointF(w * 0.5, h * 0.5), end)
        color = QColor(p["rv_base"] if self.warning else p["accent"])
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawPath(path)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(start, 3.5, 3.5)
        painter.drawEllipse(end, 3.5, 3.5)


class Toast(QFrame):
    """Aviso flotante dentro de la ventana: entra deslizándose y se desvanece solo."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 18, 12)
        layout.setSpacing(10)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.text_label = QLabel()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._timer = QTimer(self, singleShot=True, interval=3400)
        self._timer.timeout.connect(self._hide)
        self.hide()

    def show_message(self, text: str, kind: str = "ok") -> None:
        p = theme.p
        name, color = {"ok": ("check", p["bar_ok"]), "error": ("alert", p["rv_base"]),
                       "info": ("check", p["accent"])}[kind]
        self.icon_label.setPixmap(icon(name, color, 18).pixmap(18, 18))
        self.text_label.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 28
        self.raise_()
        self.show()
        self._effect.setOpacity(0.0)
        fade = QPropertyAnimation(self._effect, b"opacity", self)
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        slide = QPropertyAnimation(self, b"pos", self)
        slide.setDuration(260)
        slide.setStartValue(QPoint(x, y + 26))
        slide.setEndValue(QPoint(x, y))
        slide.setEasingCurve(QEasingCurve.OutCubic)
        fade.start()
        slide.start()
        self._anims = (fade, slide)
        self._timer.start()

    def _hide(self) -> None:
        fade = QPropertyAnimation(self._effect, b"opacity", self)
        fade.setDuration(260)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.finished.connect(self.hide)
        fade.start()
        self._anims = (fade,)
