"""
Fachada de enrutamiento API para compatibilidad modular.
Delegación a los controladores de la capa presentation.api.
"""
from presentation.api import (
    api_blueprints,
    telemetry_api_bp,
    batch_api_bp,
    conclusion_api_bp,
    session_api_bp
)

# Exportar para compatibilidad
api_bp = batch_api_bp

__all__ = ["api_bp", "api_blueprints", "telemetry_api_bp", "batch_api_bp", "conclusion_api_bp", "session_api_bp"]
