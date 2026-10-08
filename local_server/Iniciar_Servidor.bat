@echo off
chcp 65001 > nul
title SIFMA - Servidor Local (Campo)

echo ========================================================
echo        SIFMA - SERVIDOR LOCAL EN PRODUCCIÓN
echo ========================================================
echo.

:: Si existe el entorno virtual, activarlo
if exist "%~dp0..\.venv\Scripts\activate.bat" (
    call "%~dp0..\.venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
)

echo Iniciando Servidor Local SIFMA en http://127.0.0.1:5000 ...
echo Presiona Ctrl+C para detener el servidor.
echo.

python "%~dp0app.py"

pause
