@echo off
chcp 65001 > nul
title SIFMA - Instalador de Dependencias y Servidor Local

echo ========================================================
echo        SIFMA - SISTEMA DE FENOTIPADO Y TELEMETRÍA
echo           Instalador Automatizado para Campo
echo ========================================================
echo.

:: 1. Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH.
    echo Por favor instala Python 3.10+ desde https://www.python.org/downloads/
    echo Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación.
    echo.
    pause
    exit /b 1
)

echo [1/4] Verificando entorno virtual Python (.venv)...
if not exist "%~dp0..\.venv" (
    echo Creando entorno virtual en "%~dp0..\.venv"...
    python -m venv "%~dp0..\.venv"
)

echo [2/4] Activando entorno virtual...
call "%~dp0..\.venv\Scripts\activate.bat"

echo [3/4] Actualizando pip e instalando requerimientos...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

if %errorlevel% neq 0 (
    echo.
    echo [AVISO] Ocurrió un inconveniente con algunas librerías. Reintentando instalación individual...
    python "%~dp0core\dependencies.py"
)

echo.
echo [4/4] Limpiando archivos temporales y cachés...
for /d /r "%~dp0" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

echo.
echo ========================================================
echo   ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!
echo ========================================================
echo.
echo Para iniciar el servidor ejecuta: Iniciar_Servidor.bat
echo o bien: python "%~dp0app.py"
echo.
pause
