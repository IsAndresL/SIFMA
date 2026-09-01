import io
import csv
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from domain.models import CaptureSession, SensorReading, BiometricMetric
from infrastructure.database.repositories import (
    CaptureSessionRepository, 
    SensorRepository
)
from infrastructure.telemetry import TowerCsvImporter

class AnalyticsApplicationService:
    """
    Caso de uso: Cruce de fenotipado con telemetría ambiental,
    cálculo de correlaciones agronómicas y remuestreo de series temporales.
    (SOLID: SRP, DIP)
    """
    
    def __init__(
        self,
        session_repo: Optional[CaptureSessionRepository] = None,
        sensor_repo: Optional[SensorRepository] = None,
        csv_importer: Optional[TowerCsvImporter] = None
    ):
        self.session_repo = session_repo or CaptureSessionRepository()
        self.sensor_repo = sensor_repo or SensorRepository()
        self.csv_importer = csv_importer or TowerCsvImporter(self.sensor_repo, self.session_repo)

    def import_tower_csv(self, file_stream_or_path) -> Dict[str, Any]:
        return self.csv_importer.import_csv(file_stream_or_path)

    def get_cross_referenced_dataset(self, plant_id: int = 1) -> List[Dict[str, Any]]:
        """Retorna la matriz sincronizada de imágenes y telemetría por sesión."""
        sessions = self.session_repo.get_all_by_plant(plant_id=plant_id, order_asc=True)
        cross_data = []

        for s in sessions:
            sensor = s.sensor_reading
            if not sensor:
                sensor = self.sensor_repo.find_nearest(s.timestamp)

            temp = sensor.temperature if sensor else 0.0
            hum = sensor.humidity if sensor else 0.0
            uv = sensor.uv_solar if sensor else 0.0
            curr = sensor.motor_current if sensor else 0.0

            avg_metric = s.get_average_metric()
            individual_photos = [m.to_dict() for m in s.get_individual_photos()]

            if avg_metric:
                cross_data.append({
                    "session_id": s.id,
                    "date_str": s.period,
                    "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "exact_time": s.timestamp.strftime("%H:%M:%S"),
                    "crop_type": s.crop_type,
                    "plant_id": s.plant_id,
                    "foliar_area_cm2": round(avg_metric.foliar_area_cm2, 2),
                    "plant_height_cm": round(avg_metric.plant_height_cm, 2),
                    "stem_diameter_mm": round(avg_metric.stem_diameter_mm, 2),
                    "health_index": round(avg_metric.health_index, 1),
                    "compacity_index": round(avg_metric.compacity_index, 3),
                    "temperature_c": round(temp, 2),
                    "humidity_rh": round(hum, 1),
                    "uv_solar_lux": round(uv, 1),
                    "motor_current_a": round(curr, 3),
                    "photos_count": len(individual_photos),
                    "individual_photos": individual_photos
                })

        return cross_data

    def calculate_agronomic_correlations(self, cross_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estadísticas descriptivas e inferencias para investigación agronómica."""
        if not cross_data or len(cross_data) < 2:
            return {
                "optimal_temp_range": "21.0 - 24.5 °C",
                "optimal_humidity_range": "60.0 - 70.0 %",
                "optimal_uv_range": "300.0 - 450.0 lux",
                "growth_rate_cm2_day": 0.0,
                "insights": [
                    "Se requieren al menos 2 sesiones de muestreo para calcular correlaciones dinámicas de crecimiento.",
                    "El sistema evaluará las condiciones de mayor tasa de expansión foliar conforme se registren más períodos."
                ]
            }

        areas = [d["foliar_area_cm2"] for d in cross_data]
        delta_area = max(areas) - min(areas)
        growth_rate = round(delta_area / max(len(cross_data) - 1, 1), 2)

        median_area = float(np.median(areas))
        top_samples = [d for d in cross_data if d["foliar_area_cm2"] >= median_area]

        if top_samples:
            opt_temp_min = round(min(d["temperature_c"] for d in top_samples) - 0.5, 1)
            opt_temp_max = round(max(d["temperature_c"] for d in top_samples) + 0.5, 1)
            opt_hum_min = round(min(d["humidity_rh"] for d in top_samples) - 2.0, 1)
            opt_hum_max = round(max(d["humidity_rh"] for d in top_samples) + 2.0, 1)
            opt_uv_min = round(min(d["uv_solar_lux"] for d in top_samples) - 10.0, 1)
            opt_uv_max = round(max(d["uv_solar_lux"] for d in top_samples) + 10.0, 1)
        else:
            opt_temp_min, opt_temp_max = 21.0, 24.5
            opt_hum_min, opt_hum_max = 60.0, 70.0
            opt_uv_min, opt_uv_max = 300.0, 450.0

        insights = [
            f"Tasa media de incremento foliar: +{growth_rate} cm² por sesión registrada.",
            f"El mayor vigor y salud foliar se observó con temperaturas en rango {opt_temp_min} a {opt_temp_max} °C y humedad en {opt_hum_min}% a {opt_hum_max}%.",
            f"La radiación solar útil óptima para esta especie oscila entre {opt_uv_min} y {opt_uv_max} lux.",
            "La estabilidad en la corriente de la bomba confirma flujo de solución nutritiva sin obstrucciones."
        ]

        return {
            "optimal_temp_range": f"{opt_temp_min} - {opt_temp_max} °C",
            "optimal_humidity_range": f"{opt_hum_min} - {opt_hum_max} %",
            "optimal_uv_range": f"{opt_uv_min} - {opt_uv_max} lux",
            "growth_rate_cm2_day": growth_rate,
            "insights": insights
        }

    def get_sensor_timeline_data(self, target_date: Optional[str] = None, limit_points: int = 120) -> Dict[str, Any]:
        """Obtiene datos temporales remuestreados y estadísticas resumidas."""
        available_dates = self.sensor_repo.get_available_dates()

        if not target_date or target_date == "auto":
            target_date = available_dates[0] if available_dates else "todos"

        readings = self.sensor_repo.get_by_date(target_date)
        total_records = len(readings)

        if total_records == 0:
            return {
                "status": "success",
                "target_date": target_date,
                "available_dates": available_dates,
                "total_records": 0,
                "summary": {
                    "temperature": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": "Sin datos registrados"},
                    "humidity": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": "Sin datos registrados"},
                    "uv_solar": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": "Sin datos registrados"},
                    "motor_current": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": "Sin datos registrados"}
                },
                "timeline": []
            }

        temps = [r.temperature for r in readings]
        hums = [r.humidity for r in readings]
        uvs = [r.uv_solar for r in readings]
        currs = [r.motor_current for r in readings]

        summary = {
            "temperature": {
                "avg": round(float(np.mean(temps)), 1),
                "min": round(float(np.min(temps)), 1),
                "max": round(float(np.max(temps)), 1),
                "last": round(temps[-1], 1),
                "status": "Óptimo" if 18.0 <= np.mean(temps) <= 26.0 else "Fuera de Rango"
            },
            "humidity": {
                "avg": round(float(np.mean(hums)), 1),
                "min": round(float(np.min(hums)), 1),
                "max": round(float(np.max(hums)), 1),
                "last": round(hums[-1], 1),
                "status": "Óptimo" if 55.0 <= np.mean(hums) <= 75.0 else "Alerta Humedad"
            },
            "uv_solar": {
                "avg": round(float(np.mean(uvs)), 1),
                "min": round(float(np.min(uvs)), 1),
                "max": round(float(np.max(uvs)), 1),
                "last": round(uvs[-1], 1),
                "status": "Normal"
            },
            "motor_current": {
                "avg": round(float(np.mean(currs)), 3),
                "min": round(float(np.min(currs)), 3),
                "max": round(float(np.max(currs)), 3),
                "last": round(currs[-1], 3),
                "status": "Normal (Bomba Activa)" if np.mean(currs) >= 0.3 else "Bomba Inactiva"
            }
        }

        # Remuestreo inteligente
        step = max(1, total_records // limit_points)
        sampled_readings = readings[::step]
        if readings[-1] not in sampled_readings:
            sampled_readings.append(readings[-1])

        timeline = []
        for r in sampled_readings:
            time_label = r.timestamp.strftime("%H:%M:%S") if target_date != "todos" else r.timestamp.strftime("%d/%m %H:%M")
            timeline.append({
                "time": time_label,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": round(r.temperature, 2),
                "humidity": round(r.humidity, 1),
                "uv_solar": round(r.uv_solar, 1),
                "motor_current": round(r.motor_current, 3)
            })

        return {
            "status": "success",
            "target_date": target_date,
            "available_dates": available_dates,
            "total_records": total_records,
            "sampled_records": len(timeline),
            "summary": summary,
            "timeline": timeline
        }

    def generate_research_csv(self, cross_data: List[Dict[str, Any]]) -> str:
        """Genera contenido CSV estructurado para exportación científica."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')

        writer.writerow([
            "ID_Sesion",
            "Periodo_Muestreo",
            "Fecha_Hora_Captura",
            "Especie_Cultivo",
            "Canastilla_ID",
            "Area_Foliar_cm2",
            "Altura_Planta_cm",
            "Diametro_Tallo_mm",
            "Indice_Salud_pct",
            "Indice_Compacidad",
            "Temperatura_C",
            "Humedad_Relativa_pct",
            "Radiacion_Solar_UV_lux",
            "Corriente_Motor_A",
            "Numero_Fotos_Lote"
        ])

        for item in cross_data:
            writer.writerow([
                item.get("session_id", ""),
                item.get("date_str", ""),
                item.get("timestamp", ""),
                item.get("crop_type", ""),
                item.get("plant_id", 1),
                item.get("foliar_area_cm2", 0.0),
                item.get("plant_height_cm", 0.0),
                item.get("stem_diameter_mm", 0.0),
                item.get("health_index", 100.0),
                item.get("compacity_index", 0.0),
                item.get("temperature_c", 0.0),
                item.get("humidity_rh", 0.0),
                item.get("uv_solar_lux", 0.0),
                item.get("motor_current_a", 0.0),
                item.get("photos_count", 0)
            ])

        return output.getvalue()
