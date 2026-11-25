"""Iconos de línea (estilo Lucide, licencia ISC) dibujados desde SVG con el color del tema."""
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ATTRS = 'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'

PATHS = {
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "book": '<path d="M4 19.5V5a2 2 0 012-2h13v17H6.5A2.5 2.5 0 004 19.5z"/><path d="M4 19.5A2.5 2.5 0 016.5 22H19"/>',
    "download": '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
    "cloud": '<path d="M12 13v8M8 17l4 4 4-4"/><path d="M20 16.6A5 5 0 0018 7h-1.3A8 8 0 104 14.3"/>',
    "play": '<path d="M6 4l14 8-14 8z"/>',
    "refresh": '<path d="M21 12a9 9 0 11-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
    "swap": '<path d="M7 4L3 8l4 4M3 8h14M17 20l4-4-4-4M21 16H7"/>',
    "arrow": '<path d="M4 12h16M14 6l6 6-6 6"/>',
    "sun": ('<circle cx="12" cy="12" r="4"/>'
            '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2'
            'M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    "moon": '<path d="M20 14.5A8 8 0 119.5 4a6.5 6.5 0 0010.5 10.5z"/>',
    "trash": '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>',
    "file": '<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/>',
    "check": '<path d="M5 12l5 5L20 7"/>',
    "alert": ('<path d="M12 9v4M12 17h.01"/>'
              '<path d="M10.3 3.9L2.4 18a2 2 0 001.7 3h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/>'),
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "upload": '<path d="M12 16V5M7 9l5-5 5 5M5 20h14"/>',
}


def svg_bytes(name: str, color: str) -> QByteArray:
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {_ATTRS.format(c=color)}>{PATHS[name]}</svg>'
    return QByteArray(svg.encode("utf-8"))


def icon(name: str, color: str, size: int = 18) -> QIcon:
    renderer = QSvgRenderer(svg_bytes(name, color))
    scale = 2  # nitidez en pantallas de alta densidad
    pm = QPixmap(size * scale, size * scale)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size * scale, size * scale))
    painter.end()
    pm.setDevicePixelRatio(scale)
    return QIcon(pm)


def logo_svg(accent: str, text: str) -> QByteArray:
    """Logo provisional: lupa con un hilo ondulado dentro (reemplazable por el definitivo)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" fill="none">'
           f'<circle cx="13" cy="13" r="9" stroke="{accent}" stroke-width="2.4"/>'
           f'<path d="M20 20l7 7" stroke="{accent}" stroke-width="2.4" stroke-linecap="round"/>'
           f'<path d="M7.5 14c2-3 3.5 3 5.5 0s3.5 3 5.5 0" stroke="{text}" stroke-width="1.6" stroke-linecap="round"/>'
           f'</svg>')
    return QByteArray(svg.encode("utf-8"))
