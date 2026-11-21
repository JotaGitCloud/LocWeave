# LocWeave

Aplicación de escritorio para **localizar (traducir) videojuegos indie** sin gastar dinero: funciona con un
motor de traducción **local y gratuito** (sin cuentas ni claves de API). Está pensada para creadores con pocos
recursos y construida con una arquitectura **Pipeline** de seis etapas.

> Proyecto académico de la asignatura Arquitectura de Software.

## Qué hace

- Importa textos de juegos en **JSON, CSV, gettext (.po/.pot), .properties y Ren'Py (.rpy)**.
- Detecta el idioma de origen (o lo eliges): español, inglés, japonés, chino, coreano, francés, alemán,
  portugués, italiano y ruso. Pares como JP→EN o JP→ES funcionan usando el inglés como puente.
- Protege variables y etiquetas (`{player}`, `%d`, `<b>…</b>`, `[nombre]`, `\n`) para que no se rompan.
- **Glosario** por proyecto (nombres propios, objetos) y **memoria de traducción** que reutiliza tus
  traducciones revisadas.
- **Validación** automática: variables faltantes o sobrantes, saltos de línea, longitud, texto sin traducir.
- Edición manual segmento por segmento y **exportación al formato original**.

## Instalación

### Opción A: ejecutable de Windows (doble clic, sin terminal)
- **Instalador (recomendado):** baja `LocWeave-Setup-slim.exe` (unos 65 MB) desde la sección **Releases**,
  ejecútalo y sigue los pasos. No pide permisos de administrador.
- **Versión portátil:** baja `LocWeave-windows-slim.zip` (unos 100 MB), descomprímelo y abre `LocWeave.exe`.
- Existe también la variante `full` (con PyTorch, unos 240 MB): hace lo mismo y solo tiene sentido si necesitas
  los separadores de oraciones de `stanza`. Para el uso normal elige **slim**.
- Windows puede mostrar «Windows protegió su PC» porque el programa no tiene firma digital (cuesta dinero y este
  es un proyecto académico). Pulsa **Más información › Ejecutar de todas formas**.
- **Compilarlo tú mismo:** haz doble clic en `build_exe.bat` (la primera vez tarda varios minutos). Al terminar
  tendrás `dist\LocWeave\LocWeave.exe`; con clic derecho › *Enviar a* › *Escritorio* creas un acceso directo.
- `Abrir_LocWeave.bat` abre la app sin dejar una consola abierta (usa el `.exe` si existe, o el código fuente).

### Opción B: desde el código
Requiere **Python 3.11 o 3.12** (64 bits). Para abrirla después sin terminal, usa `Abrir_LocWeave.bat`.

```bash
git clone <URL-DEL-REPOSITORIO>
cd locweave
python -m venv .venv
.venv\Scripts\activate          # en Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Uso rápido

1. **Nuevo proyecto** → elige el archivo (hay ejemplos en `samples/`), el idioma de origen y el de destino.
2. **Preparar idiomas** (solo la primera vez por par de idiomas; necesita internet para descargar los modelos).
   Después todo funciona sin conexión.
3. **Traducir pendientes**. Los segmentos con problemas quedan en amarillo («Revisar»).
4. Corrige a mano en el panel inferior (`Ctrl+Enter` guarda). Lo que guardas sin errores pasa a la memoria de
   traducción.
5. **Exportar** genera el archivo traducido en el mismo formato.

Modo línea de comandos (útil para automatizar):

```bash
python main.py import samples/dialogos_ja.json --tgt es
python main.py translate 1 --provider argos      # o --provider mock para probar sin modelos
python main.py show 1
python main.py export 1 salida.es.json
```

## Arquitectura

Pipeline de seis etapas que comparten un contexto (`app/services/pipeline.py`). Cada etapa es una clase
independiente; el pipeline solo las ejecuta en orden.

| # | Etapa | Responsabilidad |
|---|-------|-----------------|
| 1 | Ingesta | Lee el archivo con el manejador de su formato (`app/parsers/`) |
| 2 | Segmentación | Detecta idioma, crea el proyecto y guarda los segmentos en SQLite |
| 3 | Preprocesamiento | Memoria de traducción, glosario y protección de variables |
| 4 | Traducción | Proveedor intercambiable (`app/providers/`): Argos local o demostración |
| 5 | Validación | Restaura variables, aplica QA y guarda el resultado |
| 6 | Exportación | Escribe el archivo traducido en el formato original |

```
main.py                 punto de entrada (GUI o CLI)
app/
  gui/                  interfaz Qt (PySide6): ventana, tema claro/oscuro, delegados, avisos, iconos
  cli.py                línea de comandos
  models.py             modelos de datos
  database.py           persistencia SQLite
  languages.py          idiomas y detección
  parsers/              un manejador por formato (JSON, CSV, PO, properties, Ren'Py)
  providers/            motores de traducción (Argos, demostración)
  services/             pipeline, validación, protección de variables, fachada
tests/                  pruebas unitarias (unittest)
.github/workflows/      CI y generación del ejecutable
```

La interfaz es una capa reemplazable que solo usa `LocWeaveService` (ver `docs/ADR-004-capa-de-presentacion-qt.md`).

Para agregar un formato: crea un `FormatHandler` en `app/parsers/` y regístralo en `__init__.py`.
Para agregar un motor: implementa `TranslationProvider` en `app/providers/`.

## Pruebas y ejecutable

```bash
python -m unittest discover -s tests -v          # pruebas del núcleo
pip install -r requirements-dev.txt
pyinstaller LocWeave.spec --noconfirm --clean    # genera dist/LocWeave/LocWeave.exe (o usa build_exe.bat)
```

Al subir una etiqueta `v*` (por ejemplo `git tag v0.1.0 && git push --tags`), GitHub Actions construye el
ejecutable de Windows y lo publica en Releases.

## Tamaño y filosofía de bajo recurso

LocWeave está pensado para equipos indie con pocos recursos: no cuesta nada, no pide cuentas y funciona sin
internet. Para que la descarga sea lo más liviana posible:

- Los modelos de idioma **no vienen incluidos**: se descargan una sola vez por par de idiomas, al pulsar
  «Preparar idiomas».
- La variante **slim** (la recomendada) no incluye PyTorch, `stanza` ni `spacy`: usa el separador de oraciones
  `minisbd` (ONNX). Resultado: instalador de ~65 MB frente a ~164 MB de la variante `full`, con la misma
  traducción (la compilación prueba una traducción real en→es dentro del `.exe` en ambas).
- El empaquetado excluye los módulos de Qt y archivos que no se usan (ver `LocWeave.spec`).
- Cada compilación en GitHub Actions publica un **informe de tamaños** en el resumen del trabajo
  (pestaña *Actions › Release (Windows)*), para seguir recortando con datos.

## Limitaciones conocidas

- La calidad depende de los modelos de Argos Translate; es una traducción asistida, revísala antes de publicar.
- El soporte de Ren'Py es básico (diálogos, menús, `_()`, `text`/`textbutton`); no interpreta bloques `python`.
- Los textos con plurales de `.po` se omiten por ahora.

---

# Notas del equipo y guía de la versión anterior

> Lo que sigue es el contenido original del README del equipo. La versión anterior de la aplicación (CustomTkinter + FastAPI + SQLAlchemy) se conserva en la carpeta `legacy/`; para ejecutarla, sitúate en `legacy/` e instala `legacy/requirements.txt`.

# LocWeave

Para LocWeave se eligió Trunk-Based Development por las siguientes razones:

Frecuencia de despliegue esperada: el sistema requiere integraciones y despliegues frecuentes (nuevos extractores, mejoras en validaciones, soporte de formatos y ajustes de workflow). Trunk-Based permite mantener la rama principal siempre en estado desplegable e integrar cambios de forma continua, evitando la acumulación de trabajo que generan estrategias con ramas de larga duración.

Tamaño del equipo: Tres integrantes

Esta combinación de alta frecuencia de cambios, equipo reducido de tres personas y necesidad de un proceso de release liviano hace que Trunk-Based Development sea la estrategia más adecuada para LocWeave frente a alternativas más pesadas como GitFlow.

//MENSAJE DE GRUPO: Deben crearse su entorno propio para la mayoria de librerias usadas en el código, aquí la guia:

# LocWeave — Guía de instalación y ejecución

## 1. Descripción

LocWeave es una aplicación de escritorio orientada a la localización y traducción de videojuegos indie. Este documento explica cómo configurar el entorno de desarrollo y ejecutar la aplicación desde Visual Studio Code.

## 2. Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- **Python 3.12:** puedes descargarlo desde [python.org](https://www.python.org/downloads/).
- **Visual Studio Code:** disponible en [code.visualstudio.com](https://code.visualstudio.com/).
- **Git:** disponible en [git-scm.com](https://git-scm.com/).

También se recomienda instalar la extensión oficial de Python para Visual Studio Code.

## 3. Descargar el repositorio

Abre una terminal y ejecuta el siguiente comando, reemplazando la URL por la dirección real del repositorio de LocWeave:


/// git clone URL_DEL_REPOSITORIO


Entra en la carpeta del proyecto:


/// cd NOMBRE_DEL_REPOSITORIO


También puedes descargar el repositorio directamente desde GitHub mediante **Code → Download ZIP** y extraer su contenido.

## 4. Abrir el proyecto en Visual Studio Code

Desde la terminal, ejecuta:


/// code .


También puedes abrir Visual Studio Code manualmente y seleccionar **File → Open Folder**, eligiendo la carpeta raíz de LocWeave.

## 5. Crear un entorno virtual

Se recomienda crear un entorno virtual para mantener aisladas las dependencias del proyecto.

En la terminal integrada de Visual Studio Code, ejecuta:


/// python -m venv .venv


Activa el entorno virtual en PowerShell:


/// .\.venv\Scripts\Activate.ps1


Si en vez de PowerShell utilizas el símbolo del sistema (CMD), ejecuta:


/// .venv\Scripts\activate.bat


Si PowerShell impide la activación por una restricción de ejecución, puedes continuar utilizando directamente el intérprete de `.venv` en los comandos siguientes.

## 6. Instalar las dependencias

Con el entorno virtual seleccionado, instala las dependencias declaradas en el archivo `requirements.txt`:


/// python -m pip install -r requirements.txt


Espera a que finalice la instalación antes de continuar.

Si ocurre un error durante la instalación, revisa el mensaje de la terminal y comprueba que estás utilizando una versión compatible de Python.

## 7. Configurar el intérprete de Python

En Visual Studio Code:

1. Abre la paleta de comandos con `Ctrl + Shift + P`.
2. Busca **Python: Select Interpreter**.
3. Selecciona el intérprete ubicado en `.venv\Scripts\python.exe`.

Esto permite que Visual Studio Code utilice las dependencias instaladas en el entorno virtual del proyecto.

## 8. Ejecutar LocWeave

Desde la carpeta raíz del proyecto, ejecuta el archivo de entrada de la aplicación.

Si `gui.py` se encuentra en la raíz:


/// python gui.py


Si `gui.py` se encuentra dentro de la carpeta `app`, utiliza el comando correspondiente a la estructura del proyecto. No ejecutes ambos comandos: utiliza únicamente la ruta correcta para el archivo de entrada.

Si la configuración es correcta, se abrirá la interfaz gráfica de LocWeave.

## 9. Base de datos

LocWeave utiliza SQLite mediante SQLAlchemy para gestionar los datos de la aplicación.

El proyecto incluye un archivo de base de datos llamado `locweave.db`. Conserva este archivo cuando sea necesario mantener los datos existentes. Si la aplicación se ejecuta en un entorno nuevo, comprueba que dispone de los permisos necesarios para acceder y escribir en la ubicación de la base de datos.

## 10. Solución de problemas

- **Python no se reconoce como comando:** comprueba la instalación de Python y prueba `py --version`.
- **No se encuentran módulos:** activa el entorno virtual correcto y vuelve a instalar las dependencias.
- **La aplicación no inicia:** revisa el error completo mostrado en la terminal y verifica la ruta del archivo de entrada.
- **Error relacionado con la base de datos:** comprueba la existencia de `locweave.db` y los permisos de escritura correspondientes.

## 11. Notas

Este procedimiento permite ejecutar el código fuente de LocWeave desde un entorno de desarrollo local. No requiere disponer de un ejecutable `.exe` previamente generado.

Aunque proximamente se agregará un ejecutable que se irá actualizando conforme el código y interfaz lo haga.

Para consultar el código fuente y las actualizaciones del proyecto, visita el repositorio oficial de LocWeave en GitHub.