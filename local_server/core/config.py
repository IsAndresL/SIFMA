# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import os
import sys
import secrets
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

# Detectar si el software corre empaquetado como ejecutable (.exe) con PyInstaller
IS_FROZEN: bool = getattr(sys, "frozen", False)
IS_DESKTOP_MODE: bool = IS_FROZEN or os.getenv("SIFMA_DESKTOP_MODE", "0") == "1"

# Directorio de recursos de solo lectura (plantillas HTML, CSS, JS, íconos)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE_DIR: str = getattr(sys, "_MEIPASS", BASE_DIR) if IS_FROZEN else BASE_DIR

# Directorio aislado de datos del usuario en el PC (%APPDATA%\SIFMA) para modo escritorio/ejecutable.
# Garantiza que ninguna actualización del ejecutable borre o reemplace la base de datos ni las fotos.
def _resolve_user_data_dir() -> str:
    custom_dir = os.getenv("SIFMA_USER_DATA_DIR")
    if custom_dir:
        os.makedirs(custom_dir, exist_ok=True)
        return os.path.abspath(custom_dir)
    if IS_DESKTOP_MODE:
        appdata_root = os.getenv("APPDATA") or os.path.expanduser("~")
        default_appdata = os.path.join(appdata_root, "SIFMA")
        os.makedirs(default_appdata, exist_ok=True)
        paths_cfg = os.path.join(default_appdata, "sifma_paths.json")
        if os.path.exists(paths_cfg):
            try:
                import json
                with open(paths_cfg, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                chosen_dir = saved.get("user_data_dir")
                if chosen_dir:
                    os.makedirs(chosen_dir, exist_ok=True)
                    return os.path.abspath(chosen_dir)
            except Exception:
                pass
        return default_appdata
    return BASE_DIR

USER_DATA_DIR: str = _resolve_user_data_dir()

def _initialize_secure_environment(user_dir: str, base_dir: str) -> str:
    """
    Carga las variables de entorno desde el directorio de datos del usuario (%APPDATA%\\SIFMA\\.env)
    o desde el entorno local de desarrollo. Si es la primera ejecución en un PC nuevo,
    genera automáticamente claves criptográficas únicas sin exponer credenciales en el código fuente.
    """
    user_env = os.path.join(user_dir, ".env")
    dev_env = os.path.join(base_dir, ".env")
    root_env = os.path.join(os.path.dirname(base_dir), ".env")

    # Si estamos en modo escritorio y aún no existe .env en %APPDATA%\SIFMA,
    # pero existe un .env junto al ejecutable o en el entorno local del equipo, importarlo sin empaquetarlo.
    if IS_DESKTOP_MODE and not os.path.exists(user_env):
        exe_dir_env = os.path.join(os.path.dirname(sys.executable), ".env") if IS_FROZEN else dev_env
        source_env = exe_dir_env if os.path.exists(exe_dir_env) else (dev_env if os.path.exists(dev_env) else None)
        if source_env and os.path.abspath(source_env) != os.path.abspath(user_env):
            try:
                with open(source_env, "r", encoding="utf-8") as src_f:
                    content = src_f.read()
                with open(user_env, "w", encoding="utf-8") as dst_f:
                    dst_f.write(content)
            except Exception:
                pass

    # Cargar en orden de prioridad: 1) %APPDATA%\SIFMA\.env, 2) local_server/.env, 3) raíz/.env
    if os.path.exists(user_env):
        load_dotenv(user_env)
    elif os.path.exists(dev_env):
        load_dotenv(dev_env)
    elif os.path.exists(root_env):
        load_dotenv(root_env)

    # Si tras cargar no existe archivo .env en user_dir, generar uno seguro y único para este PC
    if not os.path.exists(user_env):
        generated_secret = os.getenv("SIFMA_SECRET_KEY") or secrets.token_hex(32)
        generated_user = os.getenv("SIFMA_ADMIN_USER") or "SIFMA_ADMIN"
        generated_pass = os.getenv("SIFMA_ADMIN_PASSWORD") or f"Sifma#{secrets.token_hex(4)}"
        generated_name = os.getenv("SIFMA_ADMIN_FULLNAME") or "Administrador SIFMA"
        generated_mail = os.getenv("SIFMA_ADMIN_EMAIL") or "admin@sifma.local"
        try:
            os.makedirs(user_dir, exist_ok=True)
            with open(user_env, "w", encoding="utf-8") as f:
                f.write("# ========================================================\n")
                f.write("# SIFMA - CONFIGURACIÓN LOCAL SEGURA DEL EQUIPO (GENERADA AUTOMÁTICAMENTE)\n")
                f.write("# Este archivo es exclusivo de este PC y NO se sobrescribe al actualizar.\n")
                f.write("# ========================================================\n\n")
                f.write(f"SIFMA_SECRET_KEY={generated_secret}\n")
                f.write(f"SIFMA_ADMIN_USER={generated_user}\n")
                f.write(f"SIFMA_ADMIN_PASSWORD={generated_pass}\n")
                f.write(f"SIFMA_ADMIN_FULLNAME={generated_name}\n")
                f.write(f"SIFMA_ADMIN_EMAIL={generated_mail}\n")
            load_dotenv(user_env)
        except Exception:
            pass

    return user_env

ACTIVE_ENV_FILE: str = _initialize_secure_environment(USER_DATA_DIR, BASE_DIR)

@dataclass(frozen=True)
class AppConfig:
    """
    Configuración inmutable y centralizada del servidor y cliente de escritorio SIFMA.
    Separa estrictamente los recursos estáticos de la aplicación (RESOURCE_DIR)
    de la base de datos e imágenes operativas del usuario (USER_DATA_DIR).
    """
    APP_VERSION: str = "1.2.9"
    GITHUB_REPO: str = os.getenv("SIFMA_GITHUB_REPO", "IsAndresL/SIFMA")
    IS_FROZEN: bool = IS_FROZEN
    IS_DESKTOP_MODE: bool = IS_DESKTOP_MODE

    BASE_DIR: str = BASE_DIR
    RESOURCE_DIR: str = RESOURCE_DIR
    USER_DATA_DIR: str = USER_DATA_DIR
    ENV_FILE_PATH: str = ACTIVE_ENV_FILE

    DB_PATH: str = os.getenv("SIFMA_DB_PATH", os.path.join(USER_DATA_DIR, "sifma.db"))
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Secret Key criptográfica (generada dinámicamente por equipo si no está en .env)
    SECRET_KEY: str = os.getenv("SIFMA_SECRET_KEY") or secrets.token_hex(32)
    
    # Credenciales del Administrador Principal leídas exclusivamente desde el entorno local (.env)
    ADMIN_USERNAME: str = os.getenv("SIFMA_ADMIN_USER", "SIFMA_ADMIN")
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("SIFMA_ADMIN_PASSWORD", "")
    ADMIN_FULLNAME: str = os.getenv("SIFMA_ADMIN_FULLNAME", "Administrador SIFMA")
    ADMIN_EMAIL: str = os.getenv("SIFMA_ADMIN_EMAIL", "admin@sifma.local")

    # Directorios estáticos (solo lectura en bundle) y de datos operativos (persistentes en USER_DATA_DIR)
    STATIC_DIR: str = os.path.join(RESOURCE_DIR, "static")
    TEMPLATE_DIR: str = os.path.join(RESOURCE_DIR, "templates")
    DATA_DIR: str = (
        os.path.join(USER_DATA_DIR, "data")
        if IS_DESKTOP_MODE
        else os.path.join(STATIC_DIR, "data")
    )
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
    TELEMETRY_DIR: str = os.path.join(DATA_DIR, "telemetry")

    # Parámetros del fenotipado
    DEFAULT_PLANT_ID: int = 1
    MAX_PLANT_NODES: int = 4
    PHOTOS_PER_PERIOD: int = 5
    DEFAULT_PIXEL_TO_CM: float = 0.038

config = AppConfig()
