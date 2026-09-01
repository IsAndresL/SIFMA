import io
import csv
import calendar
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from domain.models import CaptureSession, SensorReading, BiometricMetric
from infrastructure.database.connection import db
from infrastructure.database.repositories import (
    CaptureSessionRepository, 
    SensorRepository,
    ConfigRepository
)
from infrastructure.telemetry import TowerCsvImporter

class AnalyticsApplicationService:
    """
    Caso de uso: Cruce de fenotipado con telemetría ambiental,
    análisis por jornada diaria, cálculo de correlaciones agronómicas y remuestreo temporal.
    (SOLID: SRP, DIP)
    """
    
    def __init__(
        self,
        session_repo: Optional[CaptureSessionRepository] = None,
        sensor_repo: Optional[SensorRepository] = None,
        config_repo: Optional[ConfigRepository] = None,
        csv_importer: Optional[TowerCsvImporter] = None
    ):
        self.session_repo = session_repo or CaptureSessionRepository()
        self.sensor_repo = sensor_repo or SensorRepository()
        self.config_repo = config_repo or ConfigRepository()
        self.csv_importer = csv_importer or TowerCsvImporter(self.sensor_repo, self.session_repo)

    def import_tower_csv(self, file_stream_or_path) -> Dict[str, Any]:
        return self.csv_importer.import_csv(file_stream_or_path)

    def get_available_dates(self, plant_id: int = 1) -> List[str]:
        """Obtiene todas las fechas con datos registrados para la canastilla indicada."""
        session_dates = self.session_repo.get_available_dates(plant_id)
        if session_dates:
            return session_dates
        cfg = self.config_repo.get() if self.config_repo else None
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True
        if shared_telemetry:
            sensor_dates = self.sensor_repo.get_available_dates()
            if sensor_dates:
                return sensor_dates
        return [datetime.now().strftime("%Y-%m-%d")]

    def get_daily_summary_data(self, target_date: Optional[str] = None, plant_id: int = 1) -> Dict[str, Any]:
        """
        Retorna el análisis consolidado exacto para un día específico y canastilla específica.
        Si en la canastilla indicada no existen registros en la fecha o está en modo aislado,
        devuelve las métricas en 0 con bandera has_data=False y advertencia clara.
        """
        available_dates = self.get_available_dates(plant_id)
        
        # Si no se indica fecha, seleccionar la primera fecha disponible para esta canastilla
        if not target_date or target_date == "auto":
            target_date = available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d")

        cfg = self.config_repo.get() if self.config_repo else None
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True

        # 1. Obtener sesiones de fenotipado de la canastilla
        sessions = self.session_repo.get_by_date_and_plant(target_date, plant_id)
        has_plant_data = len(sessions) > 0

        # 2. Si la canastilla no tiene muestras fotográficas o si estamos en modo aislado sin muestras:
        if not has_plant_data:
            return {
                "target_date": target_date,
                "available_dates": available_dates,
                "has_data": False,
                "has_plant_data": False,
                "has_sensor_data": False,
                "kpis": {
                    "foliar_area_cm2": 0.0,
                    "foliar_area_diff": 0.0,
                    "temperature_c": 0.0,
                    "temperature_status": f"Sin datos en Canastilla #{plant_id}",
                    "humidity_rh": 0.0,
                    "humidity_status": f"Sin datos en Canastilla #{plant_id}",
                    "uv_solar_lux": 0.0,
                    "uv_solar_status": f"Sin datos en Canastilla #{plant_id}",
                    "health_index": 0.0,
                    "health_status": f"Sin fenotipado en Canastilla #{plant_id}",
                    "plant_height_cm": 0.0,
                    "stem_diameter_mm": 0.0,
                    "compacity_index": 0.0
                },
                "periods": {
                    "manana": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
                    "medio_dia": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
                    "tarde": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False}
                },
                "thermal_curve": {
                    "max_temp": 0.0,
                    "min_temp": 0.0,
                    "amplitude": 0.0,
                    "regime": "Sin registros",
                    "labels": ["07:00", "10:00", "13:00", "16:00", "19:00"],
                    "temps": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "min_band": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "max_band": [0.0, 0.0, 0.0, 0.0, 0.0]
                },
                "growth_chart": {
                    "labels": ["Mañana", "Mediodía", "Tarde"],
                    "areas": [0.0, 0.0, 0.0],
                    "best_period": "Sin registros",
                    "avg_height": 0.0,
                    "avg_diameter": 0.0
                },
                "pump_chart": {
                    "avg_current": 0.0,
                    "max_current": 0.0,
                    "status": "Inactiva",
                    "labels": ["07:00", "10:00", "13:00", "16:00", "19:00"],
                    "currents": [0.0, 0.0, 0.0, 0.0, 0.0]
                },
                "solar_chart": {
                    "avg_uv": 0.0,
                    "max_uv": 0.0,
                    "labels": ["07:00", "09:00", "11:00", "13:00", "15:00", "17:00", "19:00"],
                    "uv_values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                }
            }

        # Si hay muestras para esta canastilla:
        if not shared_telemetry:
            session_readings = [s.sensor_reading for s in sessions if s.sensor_reading]
            readings = session_readings
        else:
            readings = self.sensor_repo.get_by_date(target_date)

        has_sensor_data = len(readings) > 0

        # 2. Si no hay datos de fenotipado ni lecturas para este día
        if not has_plant_data and not has_sensor_data:
            return {
                "target_date": target_date,
                "available_dates": available_dates,
                "has_data": False,
                "has_plant_data": False,
                "has_sensor_data": False,
                "kpis": {
                    "foliar_area_cm2": 0.0,
                    "foliar_area_diff": 0.0,
                    "temperature_c": 0.0,
                    "temperature_status": f"Sin datos en Canastilla #{plant_id}",
                    "humidity_rh": 0.0,
                    "humidity_status": f"Sin datos en Canastilla #{plant_id}",
                    "uv_solar_lux": 0.0,
                    "uv_solar_status": f"Sin datos en Canastilla #{plant_id}",
                    "health_index": 0.0,
                    "health_status": f"Sin fenotipado en Canastilla #{plant_id}",
                    "plant_height_cm": 0.0,
                    "stem_diameter_mm": 0.0,
                    "compacity_index": 0.0
                },
                "periods": {
                    "manana": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
                    "medio_dia": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
                    "tarde": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False}
                },
                "thermal_curve": {
                    "max_temp": 0.0,
                    "min_temp": 0.0,
                    "amplitude": 0.0,
                    "regime": "Sin registros",
                    "labels": ["07:00", "10:00", "13:00", "16:00", "19:00"],
                    "temps": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "min_band": [0.0, 0.0, 0.0, 0.0, 0.0],
                    "max_band": [0.0, 0.0, 0.0, 0.0, 0.0]
                },
                "growth_chart": {
                    "labels": ["Mañana", "Mediodía", "Tarde"],
                    "areas": [0.0, 0.0, 0.0],
                    "best_period": "Sin registros",
                    "avg_height": 0.0,
                    "avg_diameter": 0.0
                },
                "pump_chart": {
                    "avg_current": 0.0,
                    "max_current": 0.0,
                    "status": "Inactiva",
                    "labels": ["07:00", "10:00", "13:00", "16:00", "19:00"],
                    "currents": [0.0, 0.0, 0.0, 0.0, 0.0]
                },
                "solar_chart": {
                    "avg_uv": 0.0,
                    "max_uv": 0.0,
                    "labels": ["07:00", "09:00", "11:00", "13:00", "15:00", "17:00", "19:00"],
                    "uv_values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                }
            }

        # 3. Procesar métricas biométricas de las sesiones del día para esta canastilla
        areas_list = []
        heights_list = []
        diameters_list = []
        healths_list = []
        compacity_list = []

        periods_data = {
            "manana": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
            "medio_dia": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False},
            "tarde": {"area": 0.0, "height": 0.0, "diameter": 0.0, "health": 0.0, "has_data": False}
        }

        for s in sessions:
            avg_m = s.get_average_metric()
            if avg_m:
                areas_list.append(avg_m.foliar_area_cm2)
                heights_list.append(avg_m.plant_height_cm)
                diameters_list.append(avg_m.stem_diameter_mm)
                healths_list.append(avg_m.health_index)
                compacity_list.append(avg_m.compacity_index)

                period_lower = s.period.lower().replace("ñ", "n").replace("í", "i").replace(" ", "_")
                for p_key in ["manana", "medio_dia", "tarde"]:
                    if p_key in period_lower or (p_key == "medio_dia" and "mediodia" in period_lower):
                        periods_data[p_key] = {
                            "area": round(avg_m.foliar_area_cm2, 2),
                            "height": round(avg_m.plant_height_cm, 2),
                            "diameter": round(avg_m.stem_diameter_mm, 2),
                            "health": round(avg_m.health_index, 1),
                            "has_data": True
                        }

        # 4. Procesar telemetría ambiental del día
        temps = [r.temperature for r in readings] if readings else [0.0]
        hums = [r.humidity for r in readings] if readings else [0.0]
        uvs = [r.uv_solar for r in readings] if readings else [0.0]
        currs = [r.motor_current for r in readings] if readings else [0.0]

        mean_area = round(float(np.mean(areas_list)), 2) if areas_list else 0.0
        mean_height = round(float(np.mean(heights_list)), 2) if heights_list else 0.0
        mean_diameter = round(float(np.mean(diameters_list)), 2) if diameters_list else 0.0
        mean_health = round(float(np.mean(healths_list)), 1) if healths_list else 0.0
        mean_compacity = round(float(np.mean(compacity_list)), 3) if compacity_list else 0.0

        mean_temp = round(float(np.mean(temps)), 1) if readings else 0.0
        min_temp = round(float(np.min(temps)), 1) if readings else 0.0
        max_temp = round(float(np.max(temps)), 1) if readings else 0.0
        amplitude = round(max_temp - min_temp, 1)

        mean_hum = round(float(np.mean(hums)), 1) if readings else 0.0
        mean_uv = round(float(np.mean(uvs)), 1) if readings else 0.0
        mean_curr = round(float(np.mean(currs)), 3) if readings else 0.0
        max_curr = round(float(np.max(currs)), 3) if readings else 0.0

        # Comparación con jornada anterior de esta misma canastilla
        area_diff = 0.0
        try:
            curr_idx = available_dates.index(target_date) if target_date in available_dates else -1
            if curr_idx != -1 and curr_idx + 1 < len(available_dates):
                prev_date = available_dates[curr_idx + 1]
                prev_sessions = self.session_repo.get_by_date_and_plant(prev_date, plant_id)
                prev_areas = [s.get_average_metric().foliar_area_cm2 for s in prev_sessions if s.get_average_metric()]
                if prev_areas and areas_list:
                    area_diff = round(mean_area - float(np.mean(prev_areas)), 2)
        except Exception:
            pass

        # 5. Generar series temporales para las gráficas del día
        thermal_labels = []
        thermal_temps = []
        thermal_min_band = []
        thermal_max_band = []
        pump_labels = []
        pump_currents = []
        solar_labels = []
        solar_uvs = []

        if readings:
            step = max(1, len(readings) // 20)
            sampled_readings = readings[::step]
            for r in sampled_readings:
                t_label = r.timestamp.strftime("%H:%M")
                thermal_labels.append(t_label)
                thermal_temps.append(round(r.temperature, 2))
                thermal_min_band.append(round(min_temp, 1))
                thermal_max_band.append(round(max_temp, 1))

                pump_labels.append(t_label)
                pump_currents.append(round(r.motor_current, 3))

                solar_labels.append(t_label)
                solar_uvs.append(round(r.uv_solar, 1))
        else:
            thermal_labels = ["07:00", "10:00", "13:00", "16:00", "19:00"]
            thermal_temps = [0.0] * 5
            thermal_min_band = [0.0] * 5
            thermal_max_band = [0.0] * 5
            pump_labels = thermal_labels
            pump_currents = [0.0] * 5
            solar_labels = thermal_labels
            solar_uvs = [0.0] * 5

        # Período de mayor vigor
        best_p = "Sin registros"
        if has_plant_data:
            if periods_data["medio_dia"]["area"] >= periods_data["manana"]["area"] and periods_data["medio_dia"]["area"] >= periods_data["tarde"]["area"]:
                best_p = "Mediodía"
            elif periods_data["tarde"]["area"] >= periods_data["manana"]["area"]:
                best_p = "Tarde"
            else:
                best_p = "Mañana"

        regime_str = "Óptimo" if 18.0 <= mean_temp <= 26.0 else "Estrés Térmico" if mean_temp > 26.0 else "Baja Temperatura"

        return {
            "target_date": target_date,
            "available_dates": available_dates,
            "has_data": has_plant_data,
            "has_plant_data": has_plant_data,
            "has_sensor_data": has_sensor_data,
            "kpis": {
                "foliar_area_cm2": mean_area,
                "foliar_area_diff": area_diff,
                "temperature_c": mean_temp,
                "temperature_status": "Régimen Óptimo" if (18.0 <= mean_temp <= 26.0 and has_sensor_data) else ("Alerta Térmica" if has_sensor_data else "Sin telemetría"),
                "humidity_rh": mean_hum,
                "humidity_status": "Rango Adecuado" if (55.0 <= mean_hum <= 75.0 and has_sensor_data) else ("Alerta Humedad" if has_sensor_data else "Sin telemetría"),
                "uv_solar_lux": mean_uv,
                "uv_solar_status": "Normal / Activa" if (mean_uv >= 200.0 and has_sensor_data) else ("Baja Irradiancia" if has_sensor_data else "Sin telemetría"),
                "health_index": mean_health,
                "health_status": ("Tejido Sano" if mean_health >= 85.0 else "Revisar Posible Clorosis") if has_plant_data else f"Sin fenotipado en Canastilla #{plant_id}",
                "plant_height_cm": mean_height,
                "stem_diameter_mm": mean_diameter,
                "compacity_index": mean_compacity
            },
            "periods": periods_data,
            "thermal_curve": {
                "max_temp": max_temp,
                "min_temp": min_temp,
                "amplitude": amplitude,
                "regime": regime_str if has_sensor_data else "Sin telemetría",
                "labels": thermal_labels,
                "temps": thermal_temps,
                "min_band": thermal_min_band,
                "max_band": thermal_max_band
            },
            "growth_chart": {
                "labels": ["Mañana", "Mediodía", "Tarde"],
                "areas": [periods_data["manana"]["area"], periods_data["medio_dia"]["area"], periods_data["tarde"]["area"]],
                "best_period": best_p,
                "avg_height": mean_height,
                "avg_diameter": mean_diameter
            },
            "pump_chart": {
                "avg_current": mean_curr,
                "max_current": max_curr,
                "status": ("Flujo Continuo" if mean_curr >= 0.3 else "Bomba en Espera") if has_sensor_data else "Inactiva",
                "labels": pump_labels,
                "currents": pump_currents
            },
            "solar_chart": {
                "avg_uv": mean_uv,
                "max_uv": round(float(np.max(uvs)), 1) if readings else 0.0,
                "labels": solar_labels,
                "uv_values": solar_uvs
            }
        }

    def get_cross_referenced_dataset(self, plant_id: int = 1) -> List[Dict[str, Any]]:
        """Retorna la matriz sincronizada de imágenes y telemetría por sesión y por foto."""
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
            avg_cenital = avg_metric.image_path_cenital_proc or "" if avg_metric else ""
            avg_lateral = avg_metric.image_path_lateral_proc or "" if avg_metric else ""
            session_cenital_url = "/static/" + avg_cenital.replace("static/", "").replace("local_server/static/", "").lstrip("/") if avg_cenital else ""
            session_lateral_url = "/static/" + avg_lateral.replace("static/", "").replace("local_server/static/", "").lstrip("/") if avg_lateral else ""

            raw_photos = s.get_individual_photos()
            individual_photos = []
            for idx, m in enumerate(raw_photos):
                m_dict = m.to_dict()
                m_dict["photo_num"] = idx + 1
                m_dict["temperature_c"] = round(temp, 2)
                m_dict["humidity_rh"] = round(hum, 1)
                m_dict["uv_solar_lux"] = round(uv, 1)
                m_dict["motor_current_a"] = round(curr, 3)
                m_dict["exact_time"] = s.timestamp.strftime("%H:%M:%S")

                c_proc = m.image_path_cenital_proc or ""
                l_proc = m.image_path_lateral_proc or ""
                m_dict["cenital_url"] = "/static/" + c_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/") if c_proc else ""
                m_dict["lateral_url"] = "/static/" + l_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/") if l_proc else ""
                m_dict["thumbnail_url"] = m_dict["cenital_url"] or m_dict["lateral_url"]

                individual_photos.append(m_dict)

            # Normalización del período y fecha
            raw_p = s.period or ""
            if " - " in raw_p:
                parts = raw_p.split(" - ")
                date_clean = parts[0].strip()
                period_clean = parts[1].strip()
            elif "_" in raw_p:
                parts = raw_p.split("_")
                date_clean = parts[0].strip()
                period_clean = parts[1].strip()
            else:
                date_clean = s.timestamp.strftime("%Y-%m-%d")
                period_clean = raw_p or "Muestreo"

            if avg_metric:
                cross_data.append({
                    "session_id": s.id,
                    "period": period_clean.capitalize(),
                    "period_name": period_clean.lower(),
                    "date_str": date_clean,
                    "full_period_label": f"{date_clean} - {period_clean.capitalize()}",
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
                    "cenital_url": session_cenital_url,
                    "lateral_url": session_lateral_url,
                    "photos_count": len(individual_photos),
                    "individual_photos": individual_photos
                })

        return cross_data

    def calculate_full_correlation_matrix(self, cross_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula la matriz de correlación de Pearson y regresión entre sensores y fenotipado."""
        sensor_keys = [
            ("temperature_c", "Temperatura Ambiente", "°C", "#2563eb"),
            ("humidity_rh", "Humedad Relativa", "%", "#0284c7"),
            ("uv_solar_lux", "Radiación Solar", "lux", "#d97706"),
            ("motor_current_a", "Corriente Bomba", "A", "#059669")
        ]
        pheno_keys = [
            ("foliar_area_cm2", "Área Foliar", "cm²", "#059669"),
            ("plant_height_cm", "Altura Planta", "cm", "#16a34a"),
            ("stem_diameter_mm", "Diámetro Tallo", "mm", "#84cc16"),
            ("health_index", "Índice de Salud", "%", "#10b981"),
            ("compacity_index", "Compacidad", "pts", "#047857")
        ]

        matrix_rows = []
        strongest_r = 0.0
        strongest_pair = "Sin datos suficientes"

        if not cross_data or len(cross_data) < 2:
            for s_key, s_label, s_unit, s_color in sensor_keys:
                cells = []
                for p_key, p_label, p_unit, p_color in pheno_keys:
                    cells.append({
                        "sensor_key": s_key,
                        "pheno_key": p_key,
                        "r": 0.0,
                        "r2": 0.0,
                        "interpretation": "Muestras insuficientes (mín. 2 períodos)",
                        "color_class": "neutral",
                        "bg_color": "rgba(241, 245, 249, 0.6)",
                        "text_color": "#64748b"
                    })
                matrix_rows.append({
                    "sensor_key": s_key,
                    "sensor_label": s_label,
                    "sensor_unit": s_unit,
                    "cells": cells
                })
            return {
                "sensors": [{"key": s[0], "label": s[1], "unit": s[2], "color": s[3]} for s in sensor_keys],
                "phenotypes": [{"key": p[0], "label": p[1], "unit": p[2], "color": p[3]} for p in pheno_keys],
                "matrix_rows": matrix_rows,
                "strongest_pair": strongest_pair
            }

        for s_key, s_label, s_unit, s_color in sensor_keys:
            s_vals = np.array([float(d.get(s_key, 0.0)) for d in cross_data], dtype=float)
            s_std = float(np.std(s_vals))
            cells = []

            for p_key, p_label, p_unit, p_color in pheno_keys:
                p_vals = np.array([float(d.get(p_key, 0.0)) for d in cross_data], dtype=float)
                p_std = float(np.std(p_vals))

                if s_std > 1e-6 and p_std > 1e-6:
                    r_val = float(np.corrcoef(s_vals, p_vals)[0, 1])
                    if np.isnan(r_val):
                        r_val = 0.0
                else:
                    r_val = 0.0

                r_val = round(r_val, 2)
                r2_val = round(r_val ** 2, 3)

                if r_val >= 0.65:
                    interp = "Correlación Directa Fuerte"
                    color_class = "pos-strong"
                    bg_color = "rgba(16, 185, 129, 0.28)"
                    text_color = "#065f46"
                elif r_val >= 0.25:
                    interp = "Correlación Directa Moderada"
                    color_class = "pos-mod"
                    bg_color = "rgba(52, 211, 153, 0.18)"
                    text_color = "#047857"
                elif r_val <= -0.65:
                    interp = "Correlación Inversa Fuerte"
                    color_class = "neg-strong"
                    bg_color = "rgba(239, 68, 68, 0.24)"
                    text_color = "#991b1b"
                elif r_val <= -0.25:
                    interp = "Correlación Inversa Moderada"
                    color_class = "neg-mod"
                    bg_color = "rgba(248, 113, 113, 0.16)"
                    text_color = "#b91c1c"
                else:
                    interp = "Relación Débil o Independiente"
                    color_class = "neutral"
                    bg_color = "rgba(241, 245, 249, 0.7)"
                    text_color = "#475569"

                if abs(r_val) > abs(strongest_r):
                    strongest_r = r_val
                    strongest_pair = f"{s_label} vs {p_label} (r = {r_val:+0.2f}, R² = {r2_val})"

                cells.append({
                    "sensor_key": s_key,
                    "pheno_key": p_key,
                    "r": r_val,
                    "r2": r2_val,
                    "interpretation": interp,
                    "color_class": color_class,
                    "bg_color": bg_color,
                    "text_color": text_color
                })

            matrix_rows.append({
                "sensor_key": s_key,
                "sensor_label": s_label,
                "sensor_unit": s_unit,
                "cells": cells
            })

        return {
            "sensors": [{"key": s[0], "label": s[1], "unit": s[2], "color": s[3]} for s in sensor_keys],
            "phenotypes": [{"key": p[0], "label": p[1], "unit": p[2], "color": p[3]} for p in pheno_keys],
            "matrix_rows": matrix_rows,
            "strongest_pair": strongest_pair
        }

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

    def get_sensor_timeline_data(self, target_date: Optional[str] = None, plant_id: int = 1, limit_points: int = 120) -> Dict[str, Any]:
        """Obtiene datos temporales remuestreados y estadísticas resumidas con soporte de aislamiento por canastilla."""
        cfg = self.config_repo.get() if self.config_repo else None
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True

        if not shared_telemetry and plant_id > 1:
            # Modo aislado: obtener exclusivamente las lecturas vinculadas a las sesiones de esta canastilla
            if not target_date or target_date == "auto":
                avail = self.session_repo.get_available_dates(plant_id)
                target_date = avail[0] if avail else datetime.now().strftime("%Y-%m-%d")
            
            if target_date == "todos":
                sessions = self.session_repo.get_all_by_plant(plant_id)
            else:
                sessions = self.session_repo.get_by_date_and_plant(target_date, plant_id)
            
            readings = [s.sensor_reading for s in sessions if s.sensor_reading]
            available_dates = self.session_repo.get_available_dates(plant_id)
        else:
            available_dates = self.sensor_repo.get_available_dates()
            if not target_date or target_date == "auto":
                target_date = available_dates[0] if available_dates else (datetime.now().strftime("%Y-%m-%d") if available_dates else "todos")
            readings = self.sensor_repo.get_by_date(target_date)

        total_records = len(readings)

        if total_records == 0:
            return {
                "status": "success",
                "target_date": target_date,
                "available_dates": available_dates,
                "total_records": 0,
                "records_count": 0,
                "summary": {
                    "temperature": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": f"Sin datos en Canastilla #{plant_id}"},
                    "humidity": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": f"Sin datos en Canastilla #{plant_id}"},
                    "uv_solar": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": f"Sin datos en Canastilla #{plant_id}"},
                    "motor_current": {"avg": 0.0, "min": 0.0, "max": 0.0, "last": 0.0, "status": "Inactiva"}
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
            "records_count": total_records,
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

    def sync_tower_telemetry_across_canastillas(self) -> Dict[str, Any]:
        """
        Sincroniza y vincula todas las sesiones de captura de todas las canastillas
        con la telemetría ambiental más cercana registrada en la torre.
        """
        all_sessions = self.session_repo.get_all()
        synced_count = 0
        for s in all_sessions:
            if not s.sensor_reading_id or not s.sensor_reading:
                nearest = self.sensor_repo.find_nearest(s.timestamp)
                if nearest:
                    s.sensor_reading_id = nearest.id
                    synced_count += 1
        db.session.commit()
        return {
            "status": "success",
            "message": f"Se sincronizaron {synced_count} sesiones fotográficas con las lecturas ambientales de la torre.",
            "synced_count": synced_count,
            "total_sessions": len(all_sessions)
        }

    def get_calendar_month_data(self, year: int, month: int, plant_id: int = 1) -> Dict[str, Any]:
        """
        Construye la matriz de días y semanas para la visualización del calendario interactivo,
        asociando a cada día sus indicadores de fenotipado (verde) y telemetría (azul).
        """
        cfg = self.config_repo.get() if self.config_repo else None
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True

        # Obtener todas las sesiones de este mes para la canastilla
        month_str = f"{year:04d}-{month:02d}"
        month_sessions = CaptureSession.query.filter(
            CaptureSession.plant_id == int(plant_id),
            db.func.strftime('%Y-%m', CaptureSession.timestamp) == month_str
        ).all()

        sessions_by_date = {}
        for s in month_sessions:
            d_str = s.timestamp.strftime("%Y-%m-%d")
            if d_str not in sessions_by_date:
                sessions_by_date[d_str] = []
            sessions_by_date[d_str].append(s)

        # Obtener lecturas de telemetría de este mes
        if shared_telemetry or int(plant_id) == 1:
            month_readings = SensorReading.query.filter(
                db.func.strftime('%Y-%m', SensorReading.timestamp) == month_str
            ).all()
        else:
            # En modo aislado, solo lecturas vinculadas a sesiones de esta canastilla
            reading_ids = [s.sensor_reading_id for s in month_sessions if s.sensor_reading_id]
            month_readings = SensorReading.query.filter(SensorReading.id.in_(reading_ids)).all() if reading_ids else []

        readings_by_date = {}
        for r in month_readings:
            d_str = r.timestamp.strftime("%Y-%m-%d")
            if d_str not in readings_by_date:
                readings_by_date[d_str] = []
            readings_by_date[d_str].append(r)

        # Construir cuadrícula de semanas (comenzando en Lunes: calendar.MONDAY)
        cal = calendar.Calendar(firstweekday=0)
        weeks_matrix = []
        month_days = cal.monthdatescalendar(year, month)

        SPANISH_MONTHS = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]

        total_photo_days = 0
        total_telemetry_days = 0
        total_combined_days = 0
        total_sessions = len(month_sessions)
        total_readings = len(month_readings)

        today_str = datetime.now().strftime("%Y-%m-%d")

        for week in month_days:
            week_days = []
            for d in week:
                d_str = d.strftime("%Y-%m-%d")
                is_current_month = (d.month == month)
                
                day_sessions = sessions_by_date.get(d_str, [])
                day_readings = readings_by_date.get(d_str, [])

                has_photos = len(day_sessions) > 0
                has_telemetry = len(day_readings) > 0

                if is_current_month:
                    if has_photos: total_photo_days += 1
                    if has_telemetry: total_telemetry_days += 1
                    if has_photos and has_telemetry: total_combined_days += 1

                periods = []
                avg_foliar_area = 0.0
                avg_health = 0.0
                if has_photos:
                    areas = []
                    healths = []
                    for s in day_sessions:
                        raw_p = s.period or "Muestreo"
                        if " - " in raw_p:
                            p_name = raw_p.split(" - ")[1].strip().capitalize()
                        elif "_" in raw_p:
                            p_name = raw_p.split("_")[1].strip().capitalize()
                        else:
                            p_name = raw_p.capitalize()
                        periods.append(p_name)
                        
                        m = s.get_average_metric()
                        if m:
                            areas.append(m.foliar_area_cm2 or 0.0)
                            healths.append(m.health_index or 100.0)
                    if areas:
                        avg_foliar_area = round(float(np.mean(areas)), 1)
                    if healths:
                        avg_health = round(float(np.mean(healths)), 1)

                avg_temp = 0.0
                avg_hum = 0.0
                avg_uv = 0.0
                if has_telemetry:
                    avg_temp = round(float(np.mean([r.temperature for r in day_readings])), 1)
                    avg_hum = round(float(np.mean([r.humidity for r in day_readings])), 1)
                    avg_uv = round(float(np.mean([r.uv_solar for r in day_readings])), 1)

                week_days.append({
                    "date_str": d_str,
                    "day_number": d.day,
                    "month": d.month,
                    "year": d.year,
                    "is_current_month": is_current_month,
                    "is_today": (d_str == today_str),
                    "has_photos": has_photos,
                    "photo_count": len(day_sessions),
                    "periods": sorted(list(set(periods))),
                    "avg_foliar_area": avg_foliar_area,
                    "avg_health": avg_health,
                    "has_telemetry": has_telemetry,
                    "telemetry_count": len(day_readings),
                    "avg_temp": avg_temp,
                    "avg_hum": avg_hum,
                    "avg_uv": avg_uv,
                    "is_complete": (has_photos and has_telemetry)
                })
            weeks_matrix.append(week_days)

        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1

        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        days_in_month_count = calendar.monthrange(year, month)[1]
        coverage_pct = round((total_photo_days / max(days_in_month_count, 1)) * 100, 1)

        return {
            "year": year,
            "month": month,
            "month_name": SPANISH_MONTHS[month],
            "plant_id": int(plant_id),
            "shared_telemetry": shared_telemetry,
            "weeks": weeks_matrix,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "summary": {
                "total_photo_days": total_photo_days,
                "total_telemetry_days": total_telemetry_days,
                "total_combined_days": total_combined_days,
                "total_sessions": total_sessions,
                "total_readings": total_readings,
                "days_in_month": days_in_month_count,
                "coverage_pct": coverage_pct
            }
        }

    def get_day_detail(self, date_str: str, plant_id: int = 1) -> Dict[str, Any]:
        """Retorna el desglose fotográfico y ambiental detallado para un día y canastilla."""
        sessions = self.session_repo.get_by_date_and_plant(date_str, plant_id)
        
        cfg = self.config_repo.get() if self.config_repo else None
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True

        if shared_telemetry or int(plant_id) == 1:
            readings = self.sensor_repo.get_by_date(date_str)
        else:
            readings = [s.sensor_reading for s in sessions if s.sensor_reading]

        session_list = []
        for s in sessions:
            avg_m = s.get_average_metric()
            cenital_url = ("/static/" + avg_m.image_path_cenital_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")) if (avg_m and avg_m.image_path_cenital_proc) else ""
            lateral_url = ("/static/" + avg_m.image_path_lateral_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")) if (avg_m and avg_m.image_path_lateral_proc) else ""
            
            raw_p = s.period or "Muestreo"
            p_clean = raw_p.split(" - ")[1].strip().capitalize() if " - " in raw_p else raw_p.capitalize()

            session_list.append({
                "id": s.id,
                "period": p_clean,
                "timestamp": s.timestamp.strftime("%H:%M:%S"),
                "foliar_area_cm2": avg_m.foliar_area_cm2 if avg_m else 0.0,
                "plant_height_cm": avg_m.plant_height_cm if avg_m else 0.0,
                "stem_diameter_mm": avg_m.stem_diameter_mm if avg_m else 0.0,
                "health_index": avg_m.health_index if avg_m else 100.0,
                "cenital_url": cenital_url,
                "lateral_url": lateral_url,
                "thumbnail_url": cenital_url or lateral_url
            })

        env_summary = {
            "has_readings": len(readings) > 0,
            "readings_count": len(readings),
            "avg_temp": round(float(np.mean([r.temperature for r in readings])), 1) if readings else 0.0,
            "min_temp": round(float(np.min([r.temperature for r in readings])), 1) if readings else 0.0,
            "max_temp": round(float(np.max([r.temperature for r in readings])), 1) if readings else 0.0,
            "avg_hum": round(float(np.mean([r.humidity for r in readings])), 1) if readings else 0.0,
            "min_hum": round(float(np.min([r.humidity for r in readings])), 1) if readings else 0.0,
            "max_hum": round(float(np.max([r.humidity for r in readings])), 1) if readings else 0.0,
            "avg_uv": round(float(np.mean([r.uv_solar for r in readings])), 1) if readings else 0.0,
            "avg_current": round(float(np.mean([r.motor_current for r in readings])), 3) if readings else 0.0
        }

        return {
            "status": "success",
            "date_str": date_str,
            "plant_id": plant_id,
            "has_photos": len(session_list) > 0,
            "photo_count": len(session_list),
            "sessions": session_list,
            "environment": env_summary
        }

    def get_inter_plant_benchmark_data(self) -> Dict[str, Any]:
        """
        Calcula la comparativa inter-canastillas de la torre hidropónica:
        - Curvas superpuestas de área foliar, altura, tallo y salud.
        - Análisis de gradiente vertical por nivel en la torre.
        - Tasa de Crecimiento Relativo (RGR) y Tasa de Crecimiento Absoluto (AGR).
        """
        from domain.models import CropProfile
        cfg = self.config_repo.get() if self.config_repo else None
        
        crop_names = {
            1: getattr(cfg, 'plant_1_crop', 'cebollin') if cfg else 'cebollin',
            2: getattr(cfg, 'plant_2_crop', 'albahaca') if cfg else 'albahaca',
            3: getattr(cfg, 'plant_3_crop', 'lechuga') if cfg else 'lechuga',
            4: getattr(cfg, 'plant_4_crop', 'fresa') if cfg else 'fresa'
        }

        LEVEL_NAMES = {
            1: "Nivel 1 - Base (Inferior)",
            2: "Nivel 2 - Medio-Bajo",
            3: "Nivel 3 - Medio-Alto",
            4: "Nivel 4 - Cúspide (Superior)"
        }

        all_dates_set = set()
        canastillas_data = {}

        CANASTILLA_COLORS = {
            1: {"border": "#10b981", "bg": "rgba(16, 185, 129, 0.15)", "name": "Verde Esmeralda"},
            2: {"border": "#0284c7", "bg": "rgba(2, 132, 199, 0.15)", "name": "Azul Océano"},
            3: {"border": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.15)", "name": "Púrpura"},
            4: {"border": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)", "name": "Ámbar"}
        }

        for pid in [1, 2, 3, 4]:
            crop_key = crop_names.get(pid, 'cebollin')
            profile = CropProfile.query.filter_by(crop_type=crop_key).first()
            display_name = profile.display_name if profile else crop_key.capitalize()
            scientific_name = ""

            sessions = self.session_repo.get_all_by_plant(plant_id=pid, order_asc=True)
            
            date_metrics = {}
            for s in sessions:
                d_str = s.timestamp.strftime("%Y-%m-%d")
                all_dates_set.add(d_str)
                m = s.get_average_metric()
                if d_str not in date_metrics:
                    date_metrics[d_str] = {"areas": [], "heights": [], "stems": [], "healths": []}
                if m:
                    if m.foliar_area_cm2: date_metrics[d_str]["areas"].append(m.foliar_area_cm2)
                    if m.plant_height_cm: date_metrics[d_str]["heights"].append(m.plant_height_cm)
                    if m.stem_diameter_mm: date_metrics[d_str]["stems"].append(m.stem_diameter_mm)
                    if m.health_index: date_metrics[d_str]["healths"].append(m.health_index)

            daily_series = []
            for d_str in sorted(list(date_metrics.keys())):
                dm = date_metrics[d_str]
                avg_area = round(float(np.mean(dm["areas"])), 2) if dm["areas"] else 0.0
                avg_height = round(float(np.mean(dm["heights"])), 2) if dm["heights"] else 0.0
                avg_stem = round(float(np.mean(dm["stems"])), 2) if dm["stems"] else 0.0
                avg_health = round(float(np.mean(dm["healths"])), 1) if dm["healths"] else 100.0
                daily_series.append({
                    "date": d_str,
                    "area_cm2": avg_area,
                    "height_cm": avg_height,
                    "stem_mm": avg_stem,
                    "health_index": avg_health,
                    "samples_count": len(dm["areas"])
                })

            initial_area = daily_series[0]["area_cm2"] if daily_series else 0.0
            latest_area = daily_series[-1]["area_cm2"] if daily_series else 0.0
            total_area_gain = round(latest_area - initial_area, 2)

            initial_height = daily_series[0]["height_cm"] if daily_series else 0.0
            latest_height = daily_series[-1]["height_cm"] if daily_series else 0.0
            total_height_gain = round(latest_height - initial_height, 2)

            days_count = len(daily_series)
            rgr_pct_day = 0.0
            agr_cm2_day = 0.0
            if days_count > 1 and initial_area > 0 and latest_area > 0:
                try:
                    rgr_pct_day = round(((np.log(latest_area) - np.log(initial_area)) / max(days_count - 1, 1)) * 100, 2)
                    agr_cm2_day = round((latest_area - initial_area) / max(days_count - 1, 1), 2)
                except Exception:
                    pass

            avg_health_overall = round(float(np.mean([d["health_index"] for d in daily_series])), 1) if daily_series else 0.0

            canastillas_data[pid] = {
                "plant_id": pid,
                "crop_key": crop_key,
                "display_name": display_name,
                "scientific_name": scientific_name,
                "level_name": LEVEL_NAMES[pid],
                "color": CANASTILLA_COLORS[pid],
                "has_data": len(daily_series) > 0,
                "sessions_count": len(sessions),
                "days_count": days_count,
                "initial_area": initial_area,
                "latest_area": latest_area,
                "total_area_gain": total_area_gain,
                "initial_height": initial_height,
                "latest_height": latest_height,
                "total_height_gain": total_height_gain,
                "rgr_pct_day": rgr_pct_day,
                "agr_cm2_day": agr_cm2_day,
                "avg_health_overall": avg_health_overall,
                "daily_series": daily_series
            }

        sorted_dates = sorted(list(all_dates_set))
        chart_labels = sorted_dates
        chart_datasets_area = []
        chart_datasets_height = []
        chart_datasets_health = []

        for pid in [1, 2, 3, 4]:
            c_info = canastillas_data[pid]
            series_map = {item["date"]: item for item in c_info["daily_series"]}
            
            area_data = [series_map.get(d, {}).get("area_cm2", None) for d in sorted_dates]
            height_data = [series_map.get(d, {}).get("height_cm", None) for d in sorted_dates]
            health_data = [series_map.get(d, {}).get("health_index", None) for d in sorted_dates]

            label_str = f"Canastilla #{pid}: {c_info['display_name']}"
            
            chart_datasets_area.append({
                "label": label_str,
                "data": area_data,
                "borderColor": c_info["color"]["border"],
                "backgroundColor": c_info["color"]["bg"],
                "borderWidth": 2.5,
                "fill": False,
                "tension": 0.3,
                "spanGaps": True
            })
            chart_datasets_height.append({
                "label": label_str,
                "data": height_data,
                "borderColor": c_info["color"]["border"],
                "backgroundColor": c_info["color"]["bg"],
                "borderWidth": 2.5,
                "fill": False,
                "tension": 0.3,
                "spanGaps": True
            })
            chart_datasets_health.append({
                "label": label_str,
                "data": health_data,
                "borderColor": c_info["color"]["border"],
                "backgroundColor": c_info["color"]["bg"],
                "borderWidth": 2.5,
                "fill": False,
                "tension": 0.3,
                "spanGaps": True
            })

        gradient_ranking = sorted(
            [c for c in canastillas_data.values() if c["has_data"]],
            key=lambda x: x["latest_area"],
            reverse=True
        )

        return {
            "canastillas": canastillas_data,
            "sorted_dates": sorted_dates,
            "chart_labels": chart_labels,
            "charts": {
                "area": chart_datasets_area,
                "height": chart_datasets_height,
                "health": chart_datasets_health
            },
            "gradient_ranking": gradient_ranking
        }

    def get_timelapse_data(self, plant_id: int = 1) -> Dict[str, Any]:
        """
        Prepara el dataset de fotogramas secuenciales para el Time-Lapse interactivo
        de evolución biológica de la canastilla seleccionada.
        """
        from domain.models import CropProfile
        cfg = self.config_repo.get() if self.config_repo else None
        
        crop_names = {
            1: getattr(cfg, 'plant_1_crop', 'cebollin') if cfg else 'cebollin',
            2: getattr(cfg, 'plant_2_crop', 'albahaca') if cfg else 'albahaca',
            3: getattr(cfg, 'plant_3_crop', 'lechuga') if cfg else 'lechuga',
            4: getattr(cfg, 'plant_4_crop', 'fresa') if cfg else 'fresa'
        }
        crop_key = crop_names.get(int(plant_id), 'cebollin')
        profile = CropProfile.query.filter_by(crop_type=crop_key).first()

        sessions = self.session_repo.get_all_by_plant(plant_id=int(plant_id), order_asc=True)

        frames = []
        for idx, s in enumerate(sessions):
            avg_m = s.get_average_metric()
            cenital_url = ("/static/" + avg_m.image_path_cenital_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")) if (avg_m and avg_m.image_path_cenital_proc) else ""
            lateral_url = ("/static/" + avg_m.image_path_lateral_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")) if (avg_m and avg_m.image_path_lateral_proc) else ""
            
            raw_p = s.period or f"Sesión {idx + 1}"
            p_clean = raw_p.split(" - ")[1].strip().capitalize() if " - " in raw_p else raw_p.capitalize()

            sensor = s.sensor_reading
            temp_val = sensor.temperature if sensor else 0.0
            hum_val = sensor.humidity if sensor else 0.0
            uv_val = sensor.uv_solar if sensor else 0.0
            curr_val = sensor.motor_current if sensor else 0.0

            frames.append({
                "frame_index": idx,
                "session_id": s.id,
                "date_str": s.timestamp.strftime("%Y-%m-%d"),
                "time_str": s.timestamp.strftime("%H:%M:%S"),
                "full_timestamp": s.timestamp.strftime("%d/%m/%Y %H:%M"),
                "period": p_clean,
                "cenital_url": cenital_url,
                "lateral_url": lateral_url,
                "foliar_area_cm2": avg_m.foliar_area_cm2 if avg_m else 0.0,
                "plant_height_cm": avg_m.plant_height_cm if avg_m else 0.0,
                "stem_diameter_mm": avg_m.stem_diameter_mm if avg_m else 0.0,
                "health_index": avg_m.health_index if avg_m else 100.0,
                "compacity_index": avg_m.compacity_index if avg_m else 0.0,
                "temperature": temp_val,
                "humidity": hum_val,
                "uv_solar": uv_val,
                "motor_current": curr_val
            })

        return {
            "status": "success",
            "plant_id": int(plant_id),
            "crop_key": crop_key,
            "crop_name": profile.display_name if profile else crop_key.capitalize(),
            "total_frames": len(frames),
            "has_frames": len(frames) > 0,
            "frames": frames
        }

    def get_scientific_dossier_data(self, target_date: Optional[str] = None, plant_id: int = 1) -> Dict[str, Any]:
        """
        Construye el dossier científico exhaustivo de la jornada para la generación del
        Reporte / Ficha Técnica de Investigación en PDF con rigor agronómico y estadístico.
        """
        from domain.models import CropProfile, AgronomicConclusion
        cfg = self.config_repo.get() if self.config_repo else None
        
        crop_names = {
            1: getattr(cfg, 'plant_1_crop', 'cebollin') if cfg else 'cebollin',
            2: getattr(cfg, 'plant_2_crop', 'albahaca') if cfg else 'albahaca',
            3: getattr(cfg, 'plant_3_crop', 'lechuga') if cfg else 'lechuga',
            4: getattr(cfg, 'plant_4_crop', 'fresa') if cfg else 'fresa'
        }
        crop_key = crop_names.get(int(plant_id), 'cebollin')
        profile = CropProfile.query.filter_by(crop_type=crop_key).first()
        display_name = profile.display_name if profile else crop_key.capitalize()

        LEVEL_NAMES = {
            1: "Nivel 1 - Base (Estrato Inferior)",
            2: "Nivel 2 - Medio-Bajo",
            3: "Nivel 3 - Medio-Alto",
            4: "Nivel 4 - Cúspide (Estrato Superior)"
        }

        available_dates = self.get_available_dates(plant_id)
        if not target_date or target_date == "auto":
            target_date = available_dates[0] if available_dates else datetime.now().strftime("%Y-%m-%d")

        sessions = self.session_repo.get_by_date_and_plant(target_date, int(plant_id))
        
        shared_telemetry = getattr(cfg, 'shared_telemetry', True) if cfg else True
        if shared_telemetry or int(plant_id) == 1:
            readings = self.sensor_repo.get_by_date(target_date)
        else:
            readings = [s.sensor_reading for s in sessions if s.sensor_reading]

        def compute_stats(values):
            if not values:
                return {
                    "count": 0, "mean": 0.0, "std": 0.0, "var": 0.0,
                    "min": 0.0, "max": 0.0, "median": 0.0, "iqr": 0.0,
                    "cv_pct": 0.0, "range": 0.0
                }
            arr = np.array(values, dtype=float)
            mean_val = float(np.mean(arr))
            std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
            var_val = float(np.var(arr, ddof=1)) if len(arr) > 1 else 0.0
            min_val = float(np.min(arr))
            max_val = float(np.max(arr))
            median_val = float(np.median(arr))
            q75, q25 = np.percentile(arr, [75, 25])
            iqr_val = float(q75 - q25)
            cv_val = float((std_val / mean_val) * 100) if mean_val != 0 else 0.0
            return {
                "count": len(arr),
                "mean": round(mean_val, 2),
                "std": round(std_val, 3),
                "var": round(var_val, 4),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "median": round(median_val, 2),
                "iqr": round(iqr_val, 2),
                "cv_pct": round(cv_val, 2),
                "range": round(max_val - min_val, 2)
            }

        temp_stats = compute_stats([r.temperature for r in readings if r.temperature is not None])
        hum_stats = compute_stats([r.humidity for r in readings if r.humidity is not None])
        uv_stats = compute_stats([r.uv_solar for r in readings if r.uv_solar is not None])
        curr_stats = compute_stats([r.motor_current for r in readings if r.motor_current is not None])

        sensor_stats_table = [
            {"param": "Temperatura Ambiental", "symbol": "T_amb", "unit": "°C", "stats": temp_stats, "optimal": "20.0 - 28.0 °C"},
            {"param": "Humedad Relativa", "symbol": "HR", "unit": "%", "stats": hum_stats, "optimal": "60.0 - 75.0 %"},
            {"param": "Radiación Solar / UV", "symbol": "Rad_UV", "unit": "lux", "stats": uv_stats, "optimal": "300 - 800 lux"},
            {"param": "Corriente de Bomba", "symbol": "I_pump", "unit": "A", "stats": curr_stats, "optimal": "0.35 - 0.60 A (Activa)"}
        ]

        areas = []
        heights = []
        stems = []
        healths = []
        compacities = []

        detailed_sessions_list = []
        photo_comparisons = []

        for s in sessions:
            avg_m = s.get_average_metric()
            if avg_m:
                if avg_m.foliar_area_cm2: areas.append(avg_m.foliar_area_cm2)
                if avg_m.plant_height_cm: heights.append(avg_m.plant_height_cm)
                if avg_m.stem_diameter_mm: stems.append(avg_m.stem_diameter_mm)
                if avg_m.health_index is not None: healths.append(avg_m.health_index)
                if avg_m.compacity_index: compacities.append(avg_m.compacity_index)

            cenital_orig = ""
            cenital_proc = ""
            lateral_orig = ""
            lateral_proc = ""

            if avg_m:
                if avg_m.image_path_cenital_orig:
                    cenital_orig = "/static/" + avg_m.image_path_cenital_orig.replace("static/", "").replace("local_server/static/", "").lstrip("/")
                if avg_m.image_path_cenital_proc:
                    cenital_proc = "/static/" + avg_m.image_path_cenital_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")
                if avg_m.image_path_lateral_orig:
                    lateral_orig = "/static/" + avg_m.image_path_lateral_orig.replace("static/", "").replace("local_server/static/", "").lstrip("/")
                if avg_m.image_path_lateral_proc:
                    lateral_proc = "/static/" + avg_m.image_path_lateral_proc.replace("static/", "").replace("local_server/static/", "").lstrip("/")

            raw_p = s.period or "Muestreo"
            p_clean = raw_p.split(" - ")[1].strip().capitalize() if " - " in raw_p else raw_p.capitalize()

            sensor_linked = s.sensor_reading
            t_val = sensor_linked.temperature if sensor_linked else 0.0
            h_val = sensor_linked.humidity if sensor_linked else 0.0
            u_val = sensor_linked.uv_solar if sensor_linked else 0.0
            c_val = sensor_linked.motor_current if sensor_linked else 0.0

            session_dict = {
                "id": s.id,
                "period": p_clean,
                "timestamp": s.timestamp.strftime("%H:%M:%S"),
                "foliar_area_cm2": round(avg_m.foliar_area_cm2, 2) if avg_m else 0.0,
                "plant_height_cm": round(avg_m.plant_height_cm, 2) if avg_m else 0.0,
                "stem_diameter_mm": round(avg_m.stem_diameter_mm, 2) if avg_m else 0.0,
                "health_index": round(avg_m.health_index, 1) if avg_m else 100.0,
                "compacity_index": round(avg_m.compacity_index, 3) if avg_m else 0.0,
                "temperature": t_val,
                "humidity": h_val,
                "uv_solar": u_val,
                "motor_current": c_val,
                "cenital_orig": cenital_orig,
                "cenital_proc": cenital_proc,
                "lateral_orig": lateral_orig,
                "lateral_proc": lateral_proc
            }
            detailed_sessions_list.append(session_dict)

            if cenital_proc or lateral_proc:
                photo_comparisons.append({
                    "period": p_clean,
                    "time": s.timestamp.strftime("%H:%M:%S"),
                    "cenital_orig": cenital_orig or cenital_proc,
                    "cenital_proc": cenital_proc or cenital_orig,
                    "lateral_orig": lateral_orig or lateral_proc,
                    "lateral_proc": lateral_proc or lateral_orig,
                    "area_cm2": round(avg_m.foliar_area_cm2, 2) if avg_m else 0.0,
                    "height_cm": round(avg_m.plant_height_cm, 2) if avg_m else 0.0,
                    "health_index": round(avg_m.health_index, 1) if avg_m else 100.0
                })

        biometric_stats_table = [
            {"param": "Área Foliar Cenital", "symbol": "AF", "unit": "cm²", "stats": compute_stats(areas)},
            {"param": "Altura de Planta", "symbol": "H_planta", "unit": "cm", "stats": compute_stats(heights)},
            {"param": "Diámetro de Tallo", "symbol": "D_tallo", "unit": "mm", "stats": compute_stats(stems)},
            {"param": "Índice de Salud Foliar", "symbol": "ISF", "unit": "%", "stats": compute_stats(healths)},
            {"param": "Índice de Compacidad", "symbol": "Comp", "unit": "adim.", "stats": compute_stats(compacities)}
        ]

        correlation_matrix = []
        if len(detailed_sessions_list) >= 2:
            x_temp = [s["temperature"] for s in detailed_sessions_list]
            x_hum = [s["humidity"] for s in detailed_sessions_list]
            x_uv = [s["uv_solar"] for s in detailed_sessions_list]
            y_area = [s["foliar_area_cm2"] for s in detailed_sessions_list]
            y_height = [s["plant_height_cm"] for s in detailed_sessions_list]
            y_health = [s["health_index"] for s in detailed_sessions_list]

            def calc_pearson(v1, v2):
                if len(v1) < 2 or np.std(v1) == 0 or np.std(v2) == 0:
                    return 0.0, "Sin variación suficiente"
                r = float(np.corrcoef(v1, v2)[0, 1])
                if np.isnan(r): return 0.0, "N/A"
                r_rounded = round(r, 3)
                if r_rounded >= 0.7: desc = "Correlación Fuerte Positiva (+)"
                elif r_rounded >= 0.3: desc = "Correlación Moderada Positiva (+)"
                elif r_rounded > -0.3: desc = "Sin Correlación Lineal Significativa"
                elif r_rounded > -0.7: desc = "Correlación Moderada Inversa (-)"
                else: desc = "Correlación Fuerte Inversa (-)"
                return r_rounded, desc

            r1, desc1 = calc_pearson(x_temp, y_area)
            correlation_matrix.append({"pair": "Temperatura (°C) vs Área Foliar (cm²)", "r": r1, "desc": desc1})

            r2, desc2 = calc_pearson(x_hum, y_area)
            correlation_matrix.append({"pair": "Humedad Relativa (%) vs Área Foliar (cm²)", "r": r2, "desc": desc2})

            r3, desc3 = calc_pearson(x_temp, y_health)
            correlation_matrix.append({"pair": "Temperatura (°C) vs Salud Foliar (%)", "r": r3, "desc": desc3})

            r4, desc4 = calc_pearson(x_uv, y_height)
            correlation_matrix.append({"pair": "Radiación Solar (lux) vs Altura (cm)", "r": r4, "desc": desc4})
        else:
            correlation_matrix = [
                {"pair": "Temperatura (°C) vs Área Foliar (cm²)", "r": 0.0, "desc": "Requiere al menos 2 muestreos"},
                {"pair": "Humedad Relativa (%) vs Área Foliar (cm²)", "r": 0.0, "desc": "Requiere al menos 2 muestreos"},
                {"pair": "Temperatura (°C) vs Salud Foliar (%)", "r": 0.0, "desc": "Requiere al menos 2 muestreos"}
            ]

        conclusions = AgronomicConclusion.query.filter_by(date_str=target_date, plant_id=int(plant_id)).order_by(AgronomicConclusion.timestamp.desc()).all()

        automated_insights = []
        if temp_stats["mean"] > 30.0:
            automated_insights.append({
                "type": "warning",
                "title": "Alerta de Estrés Térmico Registrado",
                "detail": f"La temperatura promedio de la jornada ({temp_stats['mean']} °C) superó el umbral de confort ({profile.h_max if profile else '28'} °C), lo cual puede acelerar la evapotranspiración foliar."
            })
        if hum_stats["mean"] < 50.0 and hum_stats["mean"] > 0:
            automated_insights.append({
                "type": "warning",
                "title": "Déficit de Humedad Relativa",
                "detail": f"La humedad media ({hum_stats['mean']} %) se situó por debajo del rango óptimo para sistemas aeropónicos, incrementando el riesgo de desecación foliar."
            })
        if len(areas) >= 2 and areas[-1] > areas[0]:
            gain = round(areas[-1] - areas[0], 2)
            automated_insights.append({
                "type": "positive",
                "title": "Expansión Foliar Diaria Positiva",
                "detail": f"Se cuantificó un incremento de área fotosintéticamente activa de +{gain} cm² a lo largo de las sesiones del día."
            })

        report_id = f"SIFMA-REP-{target_date.replace('-', '')}-CAN{plant_id}"

        return {
            "status": "success",
            "report_id": report_id,
            "target_date": target_date,
            "plant_id": int(plant_id),
            "display_name": display_name,
            "crop_key": crop_key,
            "level_name": LEVEL_NAMES.get(int(plant_id), f"Canastilla #{plant_id}"),
            "available_dates": available_dates,
            "sensor_stats_table": sensor_stats_table,
            "biometric_stats_table": biometric_stats_table,
            "correlation_matrix": correlation_matrix,
            "detailed_sessions": detailed_sessions_list,
            "photo_comparisons": photo_comparisons,
            "conclusions": [c.to_dict() for c in conclusions],
            "automated_insights": automated_insights,
            "has_data": (len(sessions) > 0 or len(readings) > 0),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
