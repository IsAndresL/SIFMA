import os
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Cargar .env desde local_server o desde la raiz del proyecto
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

@dataclass(frozen=True)
class AppConfig:
    """
    Configuración inmutable y centralizada del servidor SIFMA.
    Permite parametrización por variables de entorno y define valores predeterminados seguros.
    """
    BASE_DIR: str = BASE_DIR
    DB_PATH: str = os.getenv("SIFMA_DB_PATH", os.path.join(BASE_DIR, "sifma.db"))
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Secret Key segura (leída de entorno o fallback)
    SECRET_KEY: str = os.getenv("SIFMA_SECRET_KEY", "sifma_secure_production_secret_key_2026")
    
    # Credenciales del Administrador Principal desde .env
    ADMIN_USERNAME: str = os.getenv("SIFMA_ADMIN_USER", "SIFMA_ADMIN")
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("SIFMA_ADMIN_PASSWORD", "Sifma#Campo2026!")
    ADMIN_FULLNAME: str = os.getenv("SIFMA_ADMIN_FULLNAME", "Administrador SIFMA")
    ADMIN_EMAIL: str = os.getenv("SIFMA_ADMIN_EMAIL", "admin@sifma.local")

    # Directorios estáticos y de almacenamiento
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")
    DATA_DIR: str = os.path.join(STATIC_DIR, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
    TELEMETRY_DIR: str = os.path.join(DATA_DIR, "telemetry")

    # Parámetros del fenotipado
    DEFAULT_PLANT_ID: int = 1
    MAX_PLANT_NODES: int = 4
    PHOTOS_PER_PERIOD: int = 5
    DEFAULT_PIXEL_TO_CM: float = 0.038

config = AppConfig()
