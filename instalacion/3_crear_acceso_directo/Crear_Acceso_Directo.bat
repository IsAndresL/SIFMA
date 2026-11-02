@echo off
:: SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
:: Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
:: Año: 2026.

chcp 65001 > nul
title SIFMA - Paso 3: Crear Acceso Directo

echo Creando acceso directo oficial de SIFMA en el Escritorio...
powershell -ExecutionPolicy Bypass -File "%~dp0Crear_Acceso_Directo.ps1"

pause
