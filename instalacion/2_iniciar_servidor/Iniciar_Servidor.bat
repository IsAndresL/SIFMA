@echo off
:: SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
:: Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
:: Año: 2026.

chcp 65001 > nul
title SIFMA - Servidor Local

set "ROOT_DIR=%~dp0..\.."
set "VENV_DIR=%ROOT_DIR%\.venv"
set "SERVER_DIR=%ROOT_DIR%\local_server"

:: Abrir automaticamente el navegador tras 2.5 segundos
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

:: Activar entorno virtual
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo [ADVERTENCIA] No se encontro entorno virtual en "%VENV_DIR%".
    echo Ejecutando con el Python del sistema...
)

echo ========================================================
echo        SIFMA - SERVIDOR LOCAL EN PRODUCCION
echo ========================================================
echo.
echo Servidor activo en: http://127.0.0.1:5000
echo La ventana se mantendra abierta para mantener el servicio activo.
echo Presione Ctrl+C para detener el servidor.
echo.

cd /d "%SERVER_DIR%"
python app.py

pause

