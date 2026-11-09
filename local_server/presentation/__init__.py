# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from .api import api_bp
from .web import dashboard_bp

__all__ = ["api_bp", "dashboard_bp"]
