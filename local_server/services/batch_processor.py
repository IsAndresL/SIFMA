"""
Fachada de compatibilidad para BatchProcessorService.
"""
from application.services import VisionApplicationService

_vision_app_service = VisionApplicationService()

class BatchProcessorService:
    @staticmethod
    def detect_connected_usb_drives():
        return _vision_app_service.detect_connected_usb_drives()

    @staticmethod
    def process_folder_batch(folder_path, crop_type=None, period="Día 1", sensor_data=None, plant_id=1):
        return _vision_app_service.process_folder_batch(
            folder_path=folder_path,
            crop_type=crop_type,
            period=period,
            sensor_data=sensor_data,
            plant_id=plant_id
        )
