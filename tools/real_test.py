"""Prueba real de extremo a extremo: importa un .po/.pot de un juego, traduce con Argos, valida y exporta.

Uso: python tools/real_test.py archivo.pot [--lang es] [--out salida.po]
"""
import argparse
import collections
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Database  # noqa: E402
from app.parsers import get_handler  # noqa: E402
from app.services.project_service import LocWeaveService  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--lang", default="es")
    ap.add_argument("--out", default="resultado.po")
    args = ap.parse_args()

    service = LocWeaveService(Database(str(Path(tempfile.mkdtemp()) / "real.db")))
    t0 = time.time()
    project = service.import_file(args.source, "Prueba real", "en", args.lang)
    segments = service.segments(project.id)
    print(f"Importados: {len(segments)} textos en {time.time() - t0:.1f} s")

    service.prepare_languages("argos", "en", args.lang, lambda *a: None)
    t1 = time.time()
    last = [0.0]

    def progress(msg, done, total):
        if time.time() - last[0] > 20:
            last[0] = time.time()
            print(f"  … {done}/{total}", flush=True)

    report = service.translate(project.id, "argos", progress=progress)
    dt = time.time() - t1
    segs = service.segments(project.id)
    stats = service.stats(project.id)
    print(f"Traducción: {dt:.0f} s ({len(segs) / max(dt, 0.1):.1f} textos/s). Informe: {report}")
    print(f"Estados: {stats}")
    issues = collections.Counter()
    for s in segs:
        for i in (s.issues or []):
            issues[getattr(i, "code", str(i))] += 1
    print(f"Avisos de validación: {dict(issues)}")
    print("--- muestra ---")
    step = max(len(segs) // 14, 1)
    for s in segs[::step][:14]:
        print(f"[{s.status}] {s.source_text[:70]!r} -> {s.target_text[:70]!r}")

    out = Path(args.out)
    service.export(project.id, out)
    print(f"Exportado: {out} ({out.stat().st_size} bytes)")
    ok = True
    parsed = get_handler(str(out)).parse(out)
    print(f"Re-lectura del exportado: {len(parsed)} entradas")
    try:
        msgfmt = subprocess.run(["msgfmt", "-c", "-o", "/dev/null", str(out)], capture_output=True, text=True)
    except FileNotFoundError:
        print("msgfmt no disponible; se omite la validación con gettext.")
        return 0 if stats.get("total", 0) > 0 else 1
    if msgfmt.returncode == 0:
        print("msgfmt -c: el archivo exportado es válido para gettext.")
    else:
        ok = False
        print("msgfmt -c REPORTÓ PROBLEMAS:\n" + (msgfmt.stderr or "")[:2000])
    return 0 if ok and stats.get("total", 0) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
