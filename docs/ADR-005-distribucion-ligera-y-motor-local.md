# ADR 005 — Distribución ligera y motor de traducción local

**Estado:** aceptada

## Contexto
LocWeave está pensado para creadores indie con pocos recursos: no debe costar dinero, no debe exigir cuentas y
debe poder descargarse e instalarse con un doble clic, sin instalar Python. El motor de traducción local elegido
(Argos Translate) arrastra dependencias muy pesadas (PyTorch y `stanza`, además de `spacy`), de modo que la primera
versión empaquetada ocupaba 689 MB instalada (instalador de 164 MB).

## Decisión
1. **Motor local y gratuito:** Argos Translate, con los modelos de idioma descargados una sola vez por par
   (no vienen dentro del instalador).
2. **Empaquetado con PyInstaller (carpeta) e instalador Inno Setup** por usuario, sin permisos de administrador.
3. **Dos variantes de compilación**, generadas en CI desde el mismo código (`LOCWEAVE_SLIM`):
   - `slim` (recomendada): sin PyTorch, `stanza` ni `spacy`. Usa el separador de oraciones `minisbd` (ONNX).
   - `full`: con PyTorch y `stanza`, por si algún paquete de idioma lo exigiera.
4. **Autoprueba del ejecutable** (`--selftest --real`) en CI: abre la ventana, ejecuta el Pipeline, importa Argos y
   traduce una frase real en→es dentro del `.exe` compilado. Si falla, la compilación falla.

## Resultados medidos (compilación en Windows)
| Variante | App instalada | Zip | Instalador |
|---|---|---|---|
| `full` | 689 MB | 237 MB | 164 MB |
| `slim` | 224 MB | 80 MB | **52 MB** |

## Alternativas consideradas
- **API en la nube (DeepL, Google):** mejor calidad, pero implica cuentas, claves y costos recurrentes; contradice la
  premisa del proyecto.
- **Motor en línea ligero opcional:** descartado por ahora; podría añadirse como proveedor adicional sin cambiar el
  núcleo, porque el proveedor es intercambiable.
- **Una sola variante con todo:** más simple de mantener, pero 3 veces más pesada para todos los usuarios.

## Consecuencias
- **Positivas:** instalador de ~52 MB, funcionamiento sin internet tras instalar los idiomas, sin costos.
- **Negativas:** la calidad depende de los modelos de Argos (traducción asistida, requiere revisión); la primera
  traducción de cada par de idiomas necesita internet para descargar el modelo; sin firma digital, Windows SmartScreen
  muestra un aviso en la primera ejecución.
- **Riesgo:** una actualización de Argos podría reintroducir dependencias pesadas; la autoprueba en CI lo detecta.
