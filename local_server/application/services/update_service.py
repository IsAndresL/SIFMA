# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
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

            # Buscar el archivo ejecutable (.exe) dentro de los assets del Release
            download_url = None
            asset_name = None
            asset_size_mb = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    asset_name = name
                    if asset.get("size"):
                        asset_size_mb = round(asset["size"] / (1024 * 1024), 2)
                    break

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
                    f"Nueva versión disponible ({latest_tag}). Tus datos en {config.USER_DATA_DIR} están protegidos."
                    if has_update
                    else f"SIFMA está actualizado en su última versión oficial (v{current_version})."
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

        # Crear script .bat que espera el cierre del proceso actual, reemplaza solo el .exe y relanza SIFMA
        updater_bat = os.path.join(temp_update_dir, "apply_sifma_update.bat")
        current_pid = os.getpid()
        bat_content = (
            "@echo off\r\n"
            "chcp 65001 >nul\r\n"
            f"timeout /t 2 /nobreak >nul\r\n"
            f"taskkill /PID {current_pid} /F >nul 2>&1\r\n"
            "timeout /t 1 /nobreak >nul\r\n"
            f'move /Y "{staged_exe}" "{current_exe}" >nul\r\n'
            f'start "" "{current_exe}"\r\n'
            'del "%~f0"\r\n'
        )
        with open(updater_bat, "w", encoding="utf-8") as bat_file:
            bat_file.write(bat_content)

        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=creation_flags)

        def _graceful_shutdown():
            time.sleep(1.2)
            os._exit(0)

        threading.Thread(target=_graceful_shutdown, daemon=True).start()

        return {
            "status": "success",
            "requires_manual_download": False,
            "message": (
                "Actualización descargada y verificada. SIFMA se reiniciará automáticamente en unos segundos "
                "conservando intactos todos tus datos e imágenes."
            ),
        }

