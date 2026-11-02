@echo off
:: SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
:: Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
:: Año: 2026.

chcp 65001 > nul
title SIFMA - Paso 1: Instalador de Dependencias

echo ========================================================
echo        SIFMA - SISTEMA DE FENOTIPADO Y TELEMETRIA
echo        Paso 1: Instalacion Automatizada de Dependencias
echo ========================================================
echo.

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en la variable PATH.
    echo.
    echo Por favor descargue e instale Python (version 3.10, 3.11, 3.12 o 3.13) desde:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANTE: Durante la instalacion, marque obligatoriamente la casilla:
    echo   "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/4] Verificando version de Python detectada:
python --version
echo.

set "ROOT_DIR=%~dp0..\.."
set "VENV_DIR=%ROOT_DIR%\.venv"
set "REQ_FILE=%ROOT_DIR%\local_server\requirements.txt"

echo [2/4] Verificando / creando entorno virtual (.venv)...
if not exist "%VENV_DIR%" (
    echo Creando entorno virtual en "%VENV_DIR%"...
    python -m venv "%VENV_DIR%"
) else (
    echo Entorno virtual detectado en "%VENV_DIR%".
)

echo.
echo [3/4] Activando entorno virtual y actualizando pip...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip

echo.
echo [4/4] Instalando dependencias verificadas desde requirements.txt...
python -m pip install -r "%REQ_FILE%"

echo.
echo ========================================================
echo   INSTALACION DE DEPENDENCIAS COMPLETADA EXITOSAMENTE
echo ========================================================
echo.
echo Siguiente paso:
echo   - Ejecutar: instalacion\2_iniciar_servidor\Iniciar_Servidor.bat
echo   - O (opcional): instalacion\3_crear_acceso_directo\Crear_Acceso_Directo.bat
echo.
pause
