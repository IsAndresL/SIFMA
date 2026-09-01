"""
Fachada de compatibilidad para TelemetryService.
"""
from application.services.telemetry_service import TelemetryApplicationService as TelemetryService

__all__ = ["TelemetryService"]
