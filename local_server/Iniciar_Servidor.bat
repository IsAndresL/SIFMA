@echo off
chcp 65001 > nul
title SIFMA - Servidor Local

:: Abrir automáticamente la página en el navegador predeterminado después de 2.5 segundos
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

:: Si existe el entorno virtual, activarlo
if exist "%~dp0..\.venv\Scripts\activate.bat" (
    call "%~dp0..\.venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
)

echo ========================================================
echo        SIFMA - SERVIDOR LOCAL EN PRODUCCIÓN
echo ========================================================
echo.
echo Servidor activo en: http://127.0.0.1:5000
echo La ventana se mantendrá abierta para mantener el servidor.
echo Presiona Ctrl+C para detener el servidor.
echo.

python "%~dp0app.py"

pause
