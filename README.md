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