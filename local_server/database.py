"""
Fachada de compatibilidad para el acceso a modelos y base de datos.
Re-exporta entidades desde domain.models e infrastructure.database.
"""
from infrastructure.database.connection import db
from infrastructure.database.seed import init_db_data
from domain.models import (
    Config,
    CropProfile,
    SensorReading,
    CaptureSession,
    BiometricMetric,
    AgronomicConclusion
)

__all__ = [
    "db",
    "init_db_data",
    "Config",
    "CropProfile",
    "SensorReading",
    "CaptureSession",
    "BiometricMetric",
    "AgronomicConclusion"
]
