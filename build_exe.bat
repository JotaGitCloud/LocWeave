@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo   LocWeave - creando el ejecutable (.exe)
echo ============================================
where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)

if not exist .venv (
    echo [1/4] Creando entorno virtual...
    %PY% -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat || goto :error

echo [2/4] Instalando dependencias (la primera vez tarda varios minutos)...
python -m pip install --upgrade pip || goto :error
pip install -r requirements-dev.txt || goto :error

echo [3/4] Ejecutando pruebas...
python -m unittest discover -s tests || echo ADVERTENCIA: alguna prueba fallo; se continua con la compilacion.

echo [4/4] Generando el ejecutable...
pyinstaller LocWeave.spec --noconfirm --clean || goto :error

echo.
echo Listo. Tu aplicacion esta en: dist\LocWeave\LocWeave.exe
echo Haz doble clic en LocWeave.exe para abrirla. Clic derecho - Enviar a - Escritorio crea un acceso directo.
explorer dist\LocWeave
pause
exit /b 0

:error
echo.
echo Ocurrio un error. Copia el mensaje de arriba y compartelo para resolverlo.
pause
exit /b 1
