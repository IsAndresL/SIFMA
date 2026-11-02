# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

"""
Fachada de compatibilidad para TelemetryService.
"""
from application.services.telemetry_service import TelemetryApplicationService as TelemetryService

__all__ = ["TelemetryService"]
