"""
Fachada de compatibilidad para servicios de base de datos.
"""
from application.services import SystemService, VisionApplicationService
from infrastructure.database.repositories import (
    ConfigRepository, 
    CropProfileRepository, 
    SensorRepository, 
    CaptureSessionRepository
)

_system_service = SystemService()
_vision_service = VisionApplicationService()

class DatabaseService:
    @staticmethod
    def get_config():
        return _system_service.get_config()

    @staticmethod
    def get_crop_profile(crop_type=None):
        return _system_service.get_profile(crop_type)

    @staticmethod
    def save_capture_session_with_metrics(period, crop_type, sensor_data, final_metrics, individual_metrics=None, cenital_paths=None, lateral_paths=None, plant_id=1):
        session_id = _vision_service._save_capture_session_with_metrics(
            period=period,
            crop_type=crop_type,
            sensor_data=sensor_data,
            final_metrics=final_metrics,
            individual_metrics=individual_metrics,
            cenital_paths=cenital_paths,
            lateral_paths=lateral_paths,
            plant_id=plant_id
        )
        avg_record = _vision_service.session_repo.get_by_id(session_id).get_average_metric()
        return session_id, avg_record
