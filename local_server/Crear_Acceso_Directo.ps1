# ========================================================
# SIFMA - Generador de Acceso Directo en el Escritorio
# Funciona en cualquier computador detectando la ruta actual
# ========================================================
$scriptDir = $PSScriptRoot
if (-not $scriptDir) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$desktop = [Environment]::GetFolderPath("Desktop")
$wscript = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path $desktop "SIFMA - Servidor Local.lnk"

$targetBat = Join-Path $scriptDir "Iniciar_Servidor.bat"
$workDir = $scriptDir
$iconPath = Join-Path $scriptDir "static\img\sifma_icon.ico"

$shortcut = $wscript.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $workDir
if (Test-Path $iconPath) {
    $shortcut.IconLocation = "$iconPath,0"
}
$shortcut.Description = "Iniciar Sistema Integral de Fenotipado y Monitoreo Agronómico (SIFMA)"
$shortcut.Save()

Write-Host "========================================================" -ForegroundColor Green
Write-Host "  ¡ACCESO DIRECTO DE SIFMA CREADO EN EL ESCRITORIO!" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Green
Write-Host "Ruta del acceso directo: $shortcutPath"
Write-Host "Destino: $targetBat"
Write-Host "Icono asignado: $iconPath"
Write-Host ""
