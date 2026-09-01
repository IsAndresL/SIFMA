"""
Fachada de enrutamiento web para compatibilidad modular.
Delegación al controlador dashboard_routes de la capa presentation.web.
"""
from presentation.web.dashboard_routes import dashboard_bp, get_active_plant_id

__all__ = ["dashboard_bp", "get_active_plant_id"]
