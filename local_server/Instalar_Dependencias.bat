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
    echo Por favor instala Python 3.10, 3.11, 3.12 o 3.13 desde https://www.python.org/downloads/
    echo Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación.
    echo.
    pause
    exit /b 1
)

echo [1/5] Verificando / creando entorno virtual (.venv)...
if not exist "%~dp0..\.venv" (
    if not exist "%~dp0.venv" (
        echo Creando entorno virtual en "%~dp0..\.venv"...
        python -m venv "%~dp0..\.venv"
    )
)

echo [2/5] Activando entorno virtual...
if exist "%~dp0..\.venv\Scripts\activate.bat" (
    call "%~dp0..\.venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
)

echo [3/5] Actualizando pip e instalando dependencias oficiales...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

echo.
echo [4/5] Creando acceso directo en el Escritorio...
powershell -ExecutionPolicy Bypass -File "%~dp0Crear_Acceso_Directo.ps1"

echo.
echo [5/5] Limpiando archivos temporales y cachés...
for /d /r "%~dp0" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

echo.
echo ========================================================
echo   ¡DESPLIEGUE E INSTALACIÓN COMPLETADA CON ÉXITO!
echo ========================================================
echo.
echo Para iniciar SIFMA en cualquier momento:
echo   - Haz doble clic en el icono "SIFMA - Servidor Local" en tu Escritorio
echo   - O ejecuta: Iniciar_Servidor.bat
echo.
pause
