# ADR 002 (adenda) — Estructura interna del repositorio tras la migración a Qt

**Estado:** aceptada · **Reemplaza la sección «Decisión tomada» del ADR 002** (registrado en
`Registro_ADR_LocWeave_FINAL.docx`). El resto del ADR 002 (alternativas descartadas y buenas prácticas) sigue vigente.

## Contexto
El ADR 002 describía una estructura con un único `gui.py` (CustomTkinter), `models.py`, `database.py`, `schemas.py`
y `services/`. Al migrar la interfaz a Qt (ADR 004) y completar el núcleo, la estructura real cambió. La decisión de
fondo no cambia: **separar responsabilidades por carpetas** sin llegar a una arquitectura hexagonal completa.
El código anterior se conserva en `legacy/` por trazabilidad.

## Decisión
La estructura vigente es:

| Ruta | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada: abre la interfaz, ejecuta la CLI o la autoprueba (`--selftest`). |
| `app/models.py`, `app/languages.py`, `app/config.py` | Dominio y configuración (proyecto, segmento, idiomas, rutas). |
| `app/database.py` | Persistencia SQLite (biblioteca estándar; sin ORM). |
| `app/parsers/` | **Ingesta y exportación:** un manejador por formato (JSON, CSV, PO, `.properties`, Ren'Py). |
| `app/providers/` | **Traducción:** proveedor intercambiable (Argos local; demostración). |
| `app/services/` | **Pipeline:** protección de variables, validación y la fachada `LocWeaveService`. |
| `app/gui/` | **Presentación** (PySide6): ventana, tema, delegados, widgets, diálogos. |
| `app/cli.py` | Segunda interfaz sobre la misma fachada (prueba de que la presentación es reemplazable). |
| `tests/` | Pruebas unitarias y de integración (sin dependencia de la interfaz, salvo una prueba de humo). |
| `installer/`, `LocWeave.spec`, `tools/` | Empaquetado: PyInstaller, instalador de Windows y diagnósticos. |
| `.github/workflows/` | CI: pruebas, DevSecOps (gitleaks, flake8), compilación y publicación de versiones. |
| `docs/` | ADR adicionales (004 en adelante) y esta adenda. |

La regla de dependencias es unidireccional: `gui`/`cli` → `services` → `parsers`/`providers`/`database` → `models`.
Ninguna capa inferior importa de una superior.

## Consecuencias
- **Positivas:** cada etapa del Pipeline (ADR 001) tiene su carpeta; añadir un formato o un motor de traducción
  es crear un archivo en `parsers/` o `providers/` sin tocar lo demás; la CLI y la GUI comparten la fachada.
- **Negativas:** `LocWeaveService` concentra varias operaciones y puede crecer; aún no hay puertos formales (no es
  hexagonal), pero `parsers/` y `providers/` ya funcionan como adaptadores y la evolución es incremental.
- **Pendiente:** retirar `legacy/` cuando el equipo confirme que ya no se necesita.
