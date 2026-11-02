# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$rootDir = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "SIFMA - Servidor Local.lnk"

$targetBat = (Resolve-Path (Join-Path $rootDir "instalacion\2_iniciar_servidor\Iniciar_Servidor.bat")).Path
$workDir = (Resolve-Path (Join-Path $rootDir "local_server")).Path
$iconPath = (Resolve-Path (Join-Path $rootDir "local_server\static\img\sifma_icon.ico")).Path

$wscript = New-Object -ComObject WScript.Shell
$shortcut = $wscript.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $workDir
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Description = "Sistema Integral de Fenotipado y Monitoreo Agricola (SIFMA) - Servidor Local"
$shortcut.Save()

Write-Host "========================================================" -ForegroundColor Green
Write-Host "  ACCESO DIRECTO DE SIFMA CREADO EN EL ESCRITORIO" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Ruta del acceso directo: $shortcutPath"
Write-Host "Destino: $targetBat"
Write-Host "Directorio de trabajo: $workDir"
Write-Host "Icono asignado: $iconPath"
Write-Host ""
