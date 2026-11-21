"""Punto de entrada de LocWeave. Sin argumentos abre la interfaz gráfica; con argumentos, la CLI."""
import os
import sys

# En el ejecutable sin consola (modo ventana) stdout/stderr no existen: se redirigen para evitar errores.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


def run() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        from app.selftest import run_selftest
        report = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
        return run_selftest(report, real='--real' in sys.argv)
    if len(sys.argv) > 1:
        from app.cli import main as cli_main
        return cli_main()
    from app.gui.main_window import launch
    launch()
    return 0


if __name__ == "__main__":
    sys.exit(run())
