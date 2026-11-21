"""Ajustes específicos de Windows (barra de título oscura, identidad en la barra de tareas)."""
import sys


def set_app_id(app_id: str = "LocWeave.Desktop") -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:  # noqa: BLE001
        pass


def set_dark_titlebar(window, dark: bool) -> None:
    """Hace que la barra de título de Windows 10/11 siga el tema de la app."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (20; 19 en versiones antiguas)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value),
                                                          ctypes.sizeof(value)) == 0:
                break
    except Exception:  # noqa: BLE001
        pass
