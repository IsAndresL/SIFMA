import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    """
    Configuración inmutable y centralizada del servidor SIFMA.
    Permite parametrización por variables de entorno y define valores predeterminados seguros.
    """
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH: str = os.getenv("SIFMA_DB_PATH", os.path.join(BASE_DIR, "sifma.db"))
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    
    # Secret Key segura (leída de entorno o fallback persistente)
    SECRET_KEY: str = os.getenv("SIFMA_SECRET_KEY", "sifma_secure_production_secret_key_2026")
    
    # Credenciales maestras (para autenticación)
    ADMIN_USERNAME: str = os.getenv("SIFMA_ADMIN_USER", "admin")
    ADMIN_DEFAULT_PASSWORD: str = "sifma2026"
    ADMIN_PASSWORD_HASH: str = os.getenv(
        "SIFMA_ADMIN_HASH", 
        "scrypt:32768:8:1$7CsmFqjZ8V8j09hM$353597d2e7d70cf2418e2be3568fa0511516e88ff2ec0882e3895e638b9daebc558c3db08cb70575d1d6199341496a77eb86f7b3a985f47fb07e606552a8eb54"
    )

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
