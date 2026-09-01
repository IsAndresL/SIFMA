"""
Fachada de compatibilidad para AnalyticsCrossService.
"""
from application.services import AnalyticsApplicationService

_analytics_app_service = AnalyticsApplicationService()

class AnalyticsCrossService:
    @staticmethod
    def parse_time_str(time_str):
        return _analytics_app_service.csv_importer.parse_time_str(time_str)

    @staticmethod
    def parse_date_str(date_str):
        return _analytics_app_service.csv_importer.parse_date_str(date_str)

    @staticmethod
    def import_tower_csv(file_stream_or_path, app=None):
        return _analytics_app_service.import_tower_csv(file_stream_or_path)

    @staticmethod
    def get_cross_referenced_dataset(plant_id=1):
        return _analytics_app_service.get_cross_referenced_dataset(plant_id)

    @staticmethod
    def calculate_agronomic_correlations(cross_data):
        return _analytics_app_service.calculate_agronomic_correlations(cross_data)

    @staticmethod
    def get_sensor_timeline_data(target_date=None, limit_points=120):
        return _analytics_app_service.get_sensor_timeline_data(target_date, limit_points)

    @staticmethod
    def generate_research_csv(cross_data):
        return _analytics_app_service.generate_research_csv(cross_data)
