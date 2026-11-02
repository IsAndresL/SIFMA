# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

"""
Fachada de enrutamiento web para compatibilidad modular.
Delegación al controlador dashboard_routes de la capa presentation.web.
"""
from presentation.web.dashboard_routes import dashboard_bp, get_active_plant_id

__all__ = ["dashboard_bp", "get_active_plant_id"]
