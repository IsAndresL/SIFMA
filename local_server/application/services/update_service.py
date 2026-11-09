# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple

from core.config import config
from core.logger import logger


class UpdateService:
    """
    Servicio de consulta y aplicación segura de actualizaciones para SIFMA Desktop.
    Garantiza que las actualizaciones reemplacen únicamente el binario ejecutable (.exe)
    sin tocar jamás la base de datos local (sifma.db) ni las carpetas de imágenes
    almacenadas en %APPDATA%\\SIFMA.
    """

    ALLOWED_DOWNLOAD_PREFIXES = (
        "https://github.com/IsAndresL/SIFMA/",
        "https://objects.githubusercontent.com/",
        "https://release-assets.githubusercontent.com/",
        "https://codeload.github.com/IsAndresL/SIFMA/",
    )

    @staticmethod
    def _parse_version(version_str: str) -> Tuple[int, ...]:
        """Convierte una cadena de versión (ej. 'v1.2.0' o '1.2') en una tupla numérica comparable."""
        if not version_str:
            return (0, 0, 0)
        cleaned = re.sub(r"^[^0-9]*", "", version_str.strip())
        parts = []
        for token in re.split(r"[.\-+_]", cleaned):
            if token.isdigit():
                parts.append(int(token))
            else:
                m = re.match(r"^(\d+)", token)
                if m:
                    parts.append(int(m.group(1)))
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:4])

    @staticmethod
    def get_protected_data_summary() -> Dict[str, Any]:
        """Calcula el estado de protección de la base de datos e imágenes locales del usuario."""
        db_exists = os.path.exists(config.DB_PATH)
        db_size_kb = round(os.path.getsize(config.DB_PATH) / 1024.0, 1) if db_exists else 0.0

        photos_count = 0
        for folder in (config.UPLOAD_DIR, config.PROCESSED_DIR):
            if os.path.exists(folder):
                for _, _, files in os.walk(folder):
                    photos_count += sum(
                        1 for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                    )

        return {
            "user_data_dir": config.USER_DATA_DIR,
            "db_path": config.DB_PATH,
            "db_exists": db_exists,
            "db_size_kb": db_size_kb,
            "protected_photos_count": photos_count,
            "is_desktop_mode": config.IS_DESKTOP_MODE,
            "is_frozen_exe": config.IS_FROZEN,
        }

    @classmethod
    def check_for_updates(cls) -> Dict[str, Any]:
        """
        Consulta la API pública de GitHub Releases del repositorio oficial para verificar
        si existe una versión superior a la instalada actualmente.
        """
        current_version = config.APP_VERSION
        repo = config.GITHUB_REPO
        protection_info = cls.get_protected_data_summary()

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": f"SIFMA-Desktop-Updater/{current_version}",
        }

        release_url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(release_url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest_tag = data.get("tag_name") or data.get("name") or current_version
            release_name = data.get("name") or f"SIFMA {latest_tag}"
            release_notes = data.get("body") or "Actualización oficial de estabilidad y mejoras de SIFMA."
            published_at = data.get("published_at") or ""
            html_url = data.get("html_url") or f"https://github.com/{repo}/releases"

            # Buscar el archivo ejecutable directo (priorizando SIFMA_Desktop.exe sobre el instalador)
            download_url = None
            asset_name = None
            asset_size_mb = None
            assets_list = data.get("assets", [])
            exe_assets = [a for a in assets_list if (a.get("name") or "").lower().endswith(".exe")]
            exe_assets.sort(key=lambda a: 0 if "desktop" in (a.get("name") or "").lower() else 1)
            if exe_assets:
                chosen = exe_assets[0]
                download_url = chosen.get("browser_download_url")
                asset_name = chosen.get("name")
                if chosen.get("size"):
                    asset_size_mb = round(chosen["size"] / (1024 * 1024), 2)

            has_update = cls._parse_version(latest_tag) > cls._parse_version(current_version)

            return {
                "status": "success",
                "current_version": current_version,
                "latest_version": latest_tag.lstrip("vV"),
                "latest_tag": latest_tag,
                "release_name": release_name,
                "release_notes": release_notes,
                "published_at": published_at,
                "html_url": html_url,
                "download_url": download_url,
                "asset_name": asset_name,
                "asset_size_mb": asset_size_mb,
                "update_available": has_update,
                "protection": protection_info,
                "message": (
                    f"Nueva versión disponible ({latest_tag})."
                    if has_update
                    else f"El sistema está actualizado (v{current_version})."
                ),
            }

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Aún no se ha publicado ningún Release en GitHub Releases (repositorio sin releases públicos)
                return {
                    "status": "success",
                    "current_version": current_version,
                    "latest_version": current_version,
                    "latest_tag": f"v{current_version}",
                    "release_name": f"SIFMA v{current_version}",
                    "release_notes": (
                        "Aún no se han publicado paquetes de actualización posteriores en GitHub Releases. "
                        "Tu instalación actual es la versión base oficial."
                    ),
                    "published_at": "",
                    "html_url": f"https://github.com/{repo}/releases",
                    "download_url": None,
                    "asset_name": None,
                    "asset_size_mb": None,
                    "update_available": False,
                    "protection": protection_info,
                    "message": f"SIFMA está al día (v{current_version}). No hay actualizaciones pendientes.",
                }
            logger.warning(f"Error HTTP consultando actualizaciones en GitHub: {e.code}")
            return {
                "status": "error",
                "current_version": current_version,
                "update_available": False,
                "protection": protection_info,
                "message": f"No fue posible consultar el servidor de versiones (HTTP {e.code}).",
            }
        except Exception as e:
            logger.warning(f"Excepción al consultar actualizaciones: {e}")
            return {
                "status": "error",
                "current_version": current_version,
                "update_available": False,
                "protection": protection_info,
                "message": "Sin conexión al servidor de actualizaciones de GitHub. Verifica tu acceso a Internet.",
            }

    @staticmethod
    def _get_clean_subprocess_env() -> Dict[str, str]:
        """
        Retorna un entorno limpio sin las variables internas del bootloader de PyInstaller (_MEI / _PYI),
        evitando que el nuevo ejecutable intente leer la carpeta temporal _MEI del proceso anterior.
        """
        env = os.environ.copy()
        for k in list(env.keys()):
            ku = k.upper()
            if ku.startswith("_PYI") or ku.startswith("_MEI") or ku in ("TCL_LIBRARY", "TK_LIBRARY"):
                env.pop(k, None)

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and "PATH" in env:
            norm_mei = os.path.normcase(os.path.normpath(meipass))
            clean_parts = [
                p for p in env["PATH"].split(os.pathsep)
                if p and os.path.normcase(os.path.normpath(p)) != norm_mei
            ]
            env["PATH"] = os.pathsep.join(clean_parts)

        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        return env

    @classmethod
    def download_and_apply_update(cls, download_url: str) -> Dict[str, Any]:
        """
        Descarga el nuevo ejecutable oficial desde GitHub Releases en una carpeta temporal
        y programa el reemplazo en caliente del archivo .exe sin tocar %APPDATA%\\SIFMA.
        """
        if not download_url or not any(download_url.startswith(p) for p in cls.ALLOWED_DOWNLOAD_PREFIXES):
            raise ValueError("URL de actualización no autorizada. Solo se permiten paquetes oficiales de GitHub Releases.")

        if not config.IS_FROZEN:
            return {
                "status": "info",
                "requires_manual_download": True,
                "download_url": download_url,
                "message": (
                    "Estás ejecutando SIFMA desde el código fuente de desarrollo (no desde el .exe compilado). "
                    "Se abrirá el enlace oficial para descargar el nuevo ejecutable."
                ),
            }

        current_exe = os.path.abspath(sys.executable)
        exe_dir = os.path.dirname(current_exe)
        exe_name = os.path.basename(current_exe)
        temp_update_dir = os.path.join(tempfile.gettempdir(), "sifma_updater")
        os.makedirs(temp_update_dir, exist_ok=True)
        staged_exe = os.path.join(temp_update_dir, "SIFMA_Desktop_Update.exe")

        headers = {"User-Agent": f"SIFMA-Desktop-Updater/{config.APP_VERSION}"}
        req = urllib.request.Request(download_url, headers=headers, method="GET")

        with urllib.request.urlopen(req, timeout=60) as resp, open(staged_exe, "wb") as out_file:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out_file.write(chunk)

        # Validar integridad básica del binario PE de Windows (encabezado 'MZ' y tamaño > 1 MB)
        if not os.path.exists(staged_exe) or os.path.getsize(staged_exe) < 1_000_000:
            raise ValueError("El paquete descargado está incompleto o no es un ejecutable válido.")

        with open(staged_exe, "rb") as f_check:
            magic = f_check.read(2)
        if magic != b"MZ":
            raise ValueError("El archivo descargado no corresponde a un ejecutable nativo de Windows (.exe).")

        # Crear script de actualización en PowerShell (.ps1) que espera el cierre del proceso actual,
        # reemplaza el binario .exe con reintentos y relanza SIFMA limpio sin heredar variables de PyInstaller.
        updater_ps1 = os.path.join(temp_update_dir, "apply_sifma_update.ps1")
        current_pid = os.getpid()

        ps1_content = f"""param(
    [string]$CurrentExe = "{current_exe}",
    [string]$StagedExe = "{staged_exe}",
    [string]$ExeDir = "{exe_dir}",
    [int]$TargetPid = {current_pid}
)

$ErrorActionPreference = "Continue"
$logFile = Join-Path (Split-Path -Parent $StagedExe) "sifma_update_runner.log"

function Log-Msg ($msg) {{
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$ts] $msg" | Out-File -FilePath $logFile -Append -Encoding UTF8
}}

Log-Msg "Iniciando reemplazo de binario para PID $TargetPid"
Log-Msg "Destino: $CurrentExe"
Log-Msg "Origen Staged: $StagedExe"

# 1. Esperar cierre del proceso anterior
Start-Sleep -Seconds 2
if ($TargetPid -gt 0) {{
    try {{
        $proc = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
        if ($proc) {{
            Log-Msg "Esperando salida de PID $TargetPid..."
            $proc.WaitForExit(6000)
        }}
    }} catch {{
        Log-Msg "Excepcion esperando PID: $_"
    }}
}}

# Cerrar cualquier instancia residual de SIFMA_Desktop
try {{
    Get-Process -Name "SIFMA_Desktop" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}} catch {{}}

Start-Sleep -Milliseconds 800

# 2. Reemplazar el archivo binario con reintentos
$replaced = $false
for ($i = 1; $i -le 25; $i++) {{
    try {{
        if (-not (Test-Path -LiteralPath $StagedExe)) {{
            Log-Msg "Staged exe ya fue movido exitosamente."
            $replaced = $true
            break
        }}
        Move-Item -LiteralPath $StagedExe -Destination $CurrentExe -Force -ErrorAction Stop
        Log-Msg "Ejecutable reemplazado correctamente en intento $i."
        $replaced = $true
        break
    }} catch {{
        Log-Msg "Intento $i fallido al mover binario: $_"
        Start-Sleep -Milliseconds 700
    }}
}}

if (-not $replaced) {{
    Log-Msg "ERROR CRITICO: No fue posible reemplazar $CurrentExe tras 25 intentos."
    exit 1
}}

# 3. Limpiar variables internas de PyInstaller (_MEI / _PYI) en la sesion actual
@('_PYI_APPLICATION_HOME_DIR', '_PYI_ARCHIVE_FILE', '_PYI_PARENT_PROCESS_LEVEL', '_PYI_SPLASH_IPC', '_MEIPASS', '_MEIPASS2', 'TCL_LIBRARY', 'TK_LIBRARY') | ForEach-Object {{
    [System.Environment]::SetEnvironmentVariable($_, $null, 'Process')
}}
[System.Environment]::SetEnvironmentVariable('PYINSTALLER_RESET_ENVIRONMENT', '1', 'Process')

# 4. Iniciar la nueva version de SIFMA Desktop via Shell.Application (para garantizar ventana visible SW_SHOWNORMAL)
if (Test-Path -LiteralPath $CurrentExe) {{
    Log-Msg "Iniciando nueva version en $CurrentExe via Shell.Application..."
    try {{
        $shell = New-Object -ComObject Shell.Application
        $shell.ShellExecute($CurrentExe, "", $ExeDir, "open", 1)
        Log-Msg "Nueva version iniciada exitosamente con ShellExecute."
    }} catch {{
        Log-Msg "Fallo ShellExecute: $_ - intentando Start-Process..."
        try {{
            Start-Process -FilePath $CurrentExe -WorkingDirectory $ExeDir
        }} catch {{
            Log-Msg "Fallo Start-Process: $_"
        }}
    }}
}} else {{
    Log-Msg "ERROR: No existe el binario en $CurrentExe tras el reemplazo."
}}

Start-Sleep -Seconds 2
try {{
    Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
}} catch {{}}
"""
        with open(updater_ps1, "w", encoding="utf-8", newline="\n") as ps_f:
            ps_f.write(ps1_content)

        clean_env = cls._get_clean_subprocess_env()
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
        )
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                updater_ps1,
            ],
            cwd=temp_update_dir,
            env=clean_env,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

        def _graceful_shutdown():
            time.sleep(1.2)
            try:
                import webview

                if webview.windows:
                    webview.windows[0].destroy()
            except Exception:
                pass
            time.sleep(0.8)
            os._exit(0)

        threading.Thread(target=_graceful_shutdown, daemon=True).start()

        return {
            "status": "success",
            "requires_manual_download": False,
            "message": "Actualizando y reiniciando SIFMA...",
        }

