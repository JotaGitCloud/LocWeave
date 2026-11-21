"""Diagnóstico de DLL faltantes en el ejecutable congelado.

Uso: python tools/diag_dlls.py carpeta_internal paquete1 paquete2 ...
Recorre los .pyd/.dll de cada paquete, lee sus importaciones con pefile y muestra las DLL que no se
encuentran ni en el paquete, ni en la raíz de la app, ni en System32.
"""
import os
import sys

import pefile


def imports_of(path):
    pe = pefile.PE(path, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    names = [entry.dll.decode("ascii", "ignore") for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])]
    pe.close()
    return names


def main(argv):
    root = argv[1]
    system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    missing_total = 0
    for package in argv[2:]:
        folder = os.path.join(root, package)
        if not os.path.isdir(folder):
            print(f"[{package}] carpeta no encontrada en {root}")
            continue
        for current, _dirs, files in os.walk(folder):
            for name in files:
                if not name.lower().endswith((".pyd", ".dll")):
                    continue
                path = os.path.join(current, name)
                try:
                    wanted = imports_of(path)
                except Exception as exc:  # noqa: BLE001
                    print(f"[{package}] no se pudo leer {name}: {exc}")
                    continue
                for dll in wanted:
                    lower = dll.lower()
                    if lower.startswith("api-ms-win-") or lower.startswith("ext-ms-win-"):
                        continue
                    places = (current, root, system32)
                    if not any(os.path.exists(os.path.join(p, dll)) for p in places):
                        missing_total += 1
                        print(f"[{package}] {name} necesita {dll}  -> NO ENCONTRADA")
                    elif not any(os.path.exists(os.path.join(p, dll)) for p in (current, root)):
                        print(f"[{package}] {name} usa {dll} solo desde System32 (no va dentro de la app)")
    print(f"\nDLL faltantes: {missing_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
