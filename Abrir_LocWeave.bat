@echo off
rem Abre LocWeave sin dejar una consola abierta: usa el .exe si existe; si no, el codigo con el entorno virtual.
cd /d "%~dp0"
if exist "dist\LocWeave\LocWeave.exe" (
    start "" "dist\LocWeave\LocWeave.exe"
) else if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    echo No se encontro el ejecutable ni el entorno virtual. Ejecuta primero build_exe.bat
    pause
)
