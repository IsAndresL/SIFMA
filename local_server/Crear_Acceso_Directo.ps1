$desktop = [Environment]::GetFolderPath("Desktop")
$wscript = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path $desktop "SIFMA - Servidor Local.lnk"
$targetBat = "c:\Luna-Dev Compartido\Dev\Luna - Personal\SIFMA\local_server\Iniciar_SIFMA.bat"
$workDir = "c:\Luna-Dev Compartido\Dev\Luna - Personal\SIFMA\local_server"
$iconPath = "c:\Luna-Dev Compartido\Dev\Luna - Personal\SIFMA\local_server\static\img\sifma_icon.ico"

$shortcut = $wscript.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $workDir
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "Iniciar Sistema de Fenotipado y Telemetria SIFMA"
$shortcut.Save()

Write-Output "ACCESO DIRECTO CREADO EXITOSAMENTE EN EL ESCRITORIO"
