"""
SIFMA - Generador de Conjunto de Datos Fotográficos y Fenotipado de Cebollín (1 Semana)
Genera imágenes cenitales y laterales realistas para 7 días continuos (2026-09-01 al 2026-09-07),
3 períodos diarios (Mañana, Mediodía, Tarde) con 5 tomas individuales por sesión.
Ejecuta el pipeline de visión artificial agronómica y persiste las sesiones y métricas biométricas en SQLite.
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta
import cv2
import numpy as np

# Configurar entorno de importación
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from domain.models import CaptureSession, BiometricMetric, SensorReading, CropProfile
from infrastructure.database.connection import db
from infrastructure.vision import VisionPipelineManager
from core.config import config

def render_cenital_cebollin(day: int, period: str, shot_idx: int, width=640, height=480) -> np.ndarray:
    """
    Renderiza la vista cenital (superior del dosel) para cebollín en canastilla hidropónica.
    """
    period_offsets = {"Mañana": 0.0, "Mediodía": 0.33, "Tarde": 0.66}
    eff_time = (day - 1) + period_offsets.get(period, 0.0)
    
    # Semilla determinista con micro-variación por toma
    seed_val = int(day * 10000 + period_offsets.get(period, 0.0) * 1000 + shot_idx * 73)
    random.seed(seed_val)
    np.random.seed(seed_val % 2**32)
    
    # 1. Fondo de la torre hidropónica
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (30, 32, 35) # Gris oscuro neutro mate
    
    cx, cy = width // 2, height // 2
    # Jitter de cámara entre disparos
    cx += random.randint(-3, 3)
    cy += random.randint(-3, 3)
    
    # 2. Canastilla de cultivo (Net Cup) y collar de torre
    cv2.circle(img, (cx, cy), 205, (42, 45, 48), -1)
    cv2.circle(img, (cx, cy), 200, (26, 28, 30), -1)
    cv2.circle(img, (cx, cy), 180, (38, 40, 44), 3)
    
    # Rejillas plásticas de la canastilla
    for angle in range(0, 360, 24):
        rad = math.radians(angle + shot_idx * 2)
        x1 = int(cx + 125 * math.cos(rad))
        y1 = int(cy + 125 * math.sin(rad))
        x2 = int(cx + 175 * math.cos(rad))
        y2 = int(cy + 175 * math.sin(rad))
        cv2.line(img, (x1, y1), (x2, y2), (20, 22, 24), 3)
        
    # 3. Cubo de espuma fenólica / sustrato central (poliuretano agrícola)
    sponge_size = 90
    sx1, sy1 = cx - sponge_size // 2, cy - sponge_size // 2
    cv2.rectangle(img, (sx1, sy1), (sx1 + sponge_size, sy1 + sponge_size), (170, 175, 172), -1)
    cv2.rectangle(img, (sx1 + 4, sy1 + 4), (sx1 + sponge_size - 4, sy1 + sponge_size - 4), (190, 195, 192), -1)
    # Ranura central de inserción del plantín
    cv2.line(img, (cx - 18, cy), (cx + 18, cy), (115, 120, 118), 3)
    
    # 4. Dinámica botánica de crecimiento del Cebollín (Allium schoenoprasum)
    # Progresión de número de hojas tubulares: Día 1 = ~6 hojas, Día 7 = ~32 hojas
    num_blades = int(6 + eff_time * 4.2 + random.randint(-1, 1))
    
    # Longitud radial de las hojas tubulares (px)
    base_len = 42 + eff_time * 26.5 # Día 1: ~42px, Día 7: ~201px
    # Grosor de hoja tubular (px)
    base_width = 4.5 + eff_time * 1.6 # Día 1: ~4.5px, Día 7: ~14.1px
    
    # Distribución angular radial con rotación de toma
    rot_angle = (shot_idx - 1) * 3.5
    angles = np.linspace(0, 360, num_blades, endpoint=False) + rot_angle
    angles += np.random.uniform(-14, 14, num_blades)
    
    # Capa de Sombras arrojadas sobre la canastilla
    for angle in angles:
        blade_len = base_len * random.uniform(0.85, 1.15)
        rad = math.radians(angle)
        curve_offset = random.uniform(-0.35, 0.35)
        mid_x = cx + int((blade_len * 0.55) * math.cos(rad + curve_offset * 0.4))
        mid_y = cy + int((blade_len * 0.55) * math.sin(rad + curve_offset * 0.4))
        tip_x = cx + int(blade_len * math.cos(rad + curve_offset))
        tip_y = cy + int(blade_len * math.sin(rad + curve_offset))
        
        cv2.line(img, (cx + 5, cy + 5), (mid_x + 5, mid_y + 5), (18, 20, 22), int(base_width + 4))
        cv2.line(img, (mid_x + 5, mid_y + 5), (tip_x + 5, tip_y + 5), (18, 20, 22), int(base_width + 2))
        
    # Capa de Hojas Tubulares de Cebollín
    for angle in angles:
        blade_len = base_len * random.uniform(0.88, 1.12)
        w = max(3, int(base_width * random.uniform(0.9, 1.1)))
        rad = math.radians(angle)
        curve_offset = random.uniform(-0.32, 0.32)
        
        pts = []
        steps = 14
        for s in range(steps + 1):
            t = s / float(steps)
            cur_rad = rad + curve_offset * (t ** 1.4)
            r = blade_len * t
            px = int(cx + r * math.cos(cur_rad))
            py = int(cy + r * math.sin(cur_rad))
            pts.append([px, py])
        pts = np.array(pts, dtype=np.int32)
        
        # Borde cilíndrico verde bosque profundo
        cv2.polylines(img, [pts], False, (18, 110, 24), w + 2, lineType=cv2.LINE_AA)
        
        # Cuerpo cilíndrico verde clorofila vibrante
        g_val = random.randint(170, 210)
        r_val = random.randint(28, 48)
        b_val = random.randint(20, 38)
        cv2.polylines(img, [pts], False, (b_val, g_val, r_val), w, lineType=cv2.LINE_AA)
        
        # Espina central de brillo especular cilíndrico
        if w >= 4:
            cv2.polylines(img, [pts], False, (b_val + 24, min(255, g_val + 38), r_val + 26), max(1, w - 3), lineType=cv2.LINE_AA)
            
        # Ápice cónico cerrado
        tip_pt = tuple(pts[-1])
        cv2.circle(img, tip_pt, max(1, w // 2 - 1), (b_val, g_val, r_val), -1, lineType=cv2.LINE_AA)

    # 5. Corona basal de tallos en el centro
    crown_r = int(7 + eff_time * 2.8)
    cv2.circle(img, (cx, cy), crown_r, (40, 145, 48), -1)
    cv2.circle(img, (cx, cy), max(2, crown_r - 3), (85, 195, 92), -1)
    
    # Ruido gaussiano sutil de sensor digital
    noise = np.random.normal(0, 2.0, img.shape).astype(np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

def render_lateral_cebollin(day: int, period: str, shot_idx: int, width=640, height=480) -> np.ndarray:
    """
    Renderiza la vista lateral (perfil vertical y tallo) para cebollín en canastilla hidropónica.
    """
    period_offsets = {"Mañana": 0.0, "Mediodía": 0.33, "Tarde": 0.66}
    eff_time = (day - 1) + period_offsets.get(period, 0.0)
    
    seed_val = int(day * 20000 + period_offsets.get(period, 0.0) * 2000 + shot_idx * 97)
    random.seed(seed_val)
    np.random.seed(seed_val % 2**32)
    
    # 1. Fondo de estudio / cámara de fenotipado
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        grad = int(28 + 14 * (y / float(height)))
        img[y, :] = (grad, grad + 2, grad + 4)
        
    # Escala milimétrica de referencia en la pared de fondo
    cv2.line(img, (50, 30), (50, 440), (45, 48, 52), 1)
    for y_mark in range(40, 440, 35):
        cv2.line(img, (45, y_mark), (55, y_mark), (55, 58, 62), 1)
        
    base_x = width // 2 + random.randint(-3, 3)
    base_y = 425  # Línea de inserción en la canastilla
    
    # 2. Canastilla de cultivo (Net Cup blanca/gris en la base)
    cup_top_w = 150
    cup_bot_w = 105
    cup_h = 50
    cup_pts = np.array([
        [base_x - cup_top_w//2, base_y],
        [base_x + cup_top_w//2, base_y],
        [base_x + cup_bot_w//2, base_y + cup_h],
        [base_x - cup_bot_w//2, base_y + cup_h]
    ], dtype=np.int32)
    
    cv2.fillPoly(img, [cup_pts], (185, 190, 195))
    cv2.polylines(img, [cup_pts], True, (120, 125, 130), 2)
    # Reborde / pestaña de la canastilla
    cv2.rectangle(img, (base_x - cup_top_w//2 - 6, base_y - 6), 
                  (base_x + cup_top_w//2 + 6, base_y + 4), (205, 210, 215), -1)
    cv2.rectangle(img, (base_x - cup_top_w//2 - 6, base_y - 6), 
                  (base_x + cup_top_w//2 + 6, base_y + 4), (135, 140, 145), 1)

    # 3. Dinámica botánica de crecimiento en altura y grosor de tallo
    # Altura en píxeles: Día 1 = ~120 px (~5.4 cm), Día 7 = ~440 px (~21.0 cm)
    target_height_px = 115 + eff_time * 54.0 + random.uniform(-5.0, 5.0)
    target_height_px = min(height - 45, target_height_px)
    
    num_shoots = int(6 + eff_time * 3.8 + random.randint(-1, 1))
    
    # Grosor basal del cluster de tallos (px)
    # Día 1: ~4.5 px (~1.9 mm), Día 7: ~10.5 px (~4.2 mm)
    stem_cluster_w = 4.2 + eff_time * 1.05
    
    # Corona basal blanca/verde pálido saliendo del taco de esponja
    cv2.ellipse(img, (base_x, base_y - 2), (int(stem_cluster_w * 1.5), 6), 0, 0, 360, (200, 225, 205), -1)
    
    # 4. Generación de tallos y hojas tubulares verticales
    shoot_data = []
    for s in range(num_shoots):
        rel_pos = (s / max(1, num_shoots - 1)) - 0.5
        lean_angle = rel_pos * random.uniform(16, 32)
        h_factor = (1.0 - 0.22 * abs(rel_pos)) * random.uniform(0.90, 1.05)
        shoot_h = target_height_px * h_factor
        
        x_start = base_x + int(rel_pos * stem_cluster_w * 2.0)
        y_start = base_y - 2
        shoot_data.append((x_start, y_start, shoot_h, lean_angle, s))
        
    shoot_data.sort(key=lambda it: abs(it[0] - base_x), reverse=True)
    
    for x_start, y_start, shoot_h, lean_deg, s_idx in shoot_data:
        pts = []
        steps = 18
        rad = math.radians(lean_deg)
        curve_tip_bend = math.radians(lean_deg * 1.3 + random.uniform(-5, 5))
        
        for st in range(steps + 1):
            t = st / float(steps)
            cur_y = int(y_start - shoot_h * t)
            cur_x = int(x_start + (shoot_h * t * math.sin(rad)) + (shoot_h * (t**2) * 0.10 * math.sin(curve_tip_bend)))
            pts.append([cur_x, cur_y])
            
        pts = np.array(pts, dtype=np.int32)
        
        w_base = max(3, int(3.5 + eff_time * 0.85))
        
        # Borde verde oscuro
        cv2.polylines(img, [pts], False, (18, 105, 22), w_base + 2, lineType=cv2.LINE_AA)
        
        # Cuerpo verde clorofila
        g_col = random.randint(165, 205)
        r_col = random.randint(24, 44)
        b_col = random.randint(18, 36)
        cv2.polylines(img, [pts], False, (b_col, g_col, r_col), w_base, lineType=cv2.LINE_AA)
        
        # Brillo especular longitudinal
        if w_base >= 4:
            cv2.polylines(img, [pts], False, (b_col + 24, min(255, g_col + 38), r_col + 26), max(1, w_base - 3), lineType=cv2.LINE_AA)

    # 5. Base engrosada para medición exacta del diámetro de tallo basal
    for offset in range(2, 14):
        y_curr = base_y - offset
        bw = int(stem_cluster_w * (1.08 - offset * 0.025))
        cv2.line(img, (base_x - bw, y_curr), (base_x + bw, y_curr), (28, 160, 36), 2, lineType=cv2.LINE_AA)
        
    noise = np.random.normal(0, 2.0, img.shape).astype(np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

def generate_sensor_readings_for_week():
    """
    Genera y asegura lecturas de telemetría de sensores para los 7 días de la semana
    (2026-09-01 al 2026-09-07) de 06:00 a 20:00 cada 20 segundos.
    """
    start_date = datetime(2026, 9, 1).date()
    
    for day_offset in range(7):
        curr_date = start_date + timedelta(days=day_offset)
        date_str = curr_date.strftime("%Y-%m-%d")
        
        # Eliminar registros anteriores para asegurar campos completos de los 8 sensores
        SensorReading.query.filter(
            db.func.strftime('%Y-%m-%d', SensorReading.timestamp) == date_str
        ).delete(synchronize_session=False)
        db.session.commit()
            
        print(f"Generando telemetria de 8 sensores para {date_str}...")
        
        # Horario de riego para este día (11 riegos de 15 min cada ~75 min)
        irrigation_times = [
            (curr_date, 6, 30, 6, 45),
            (curr_date, 7, 45, 8, 0),
            (curr_date, 9, 0, 9, 15),
            (curr_date, 10, 15, 10, 30),
            (curr_date, 11, 30, 11, 45),
            (curr_date, 12, 45, 13, 0),
            (curr_date, 14, 0, 14, 15),
            (curr_date, 15, 15, 15, 30),
            (curr_date, 16, 30, 16, 45),
            (curr_date, 17, 45, 18, 0),
            (curr_date, 19, 0, 19, 15),
        ]
        
        irrigation_intervals = [
            (datetime(d.year, d.month, d.day, h1, m1), datetime(d.year, d.month, d.day, h2, m2))
            for d, h1, m1, h2, m2 in irrigation_times
        ]
        
        start_dt = datetime(curr_date.year, curr_date.month, curr_date.day, 6, 0, 0)
        end_dt = datetime(curr_date.year, curr_date.month, curr_date.day, 20, 0, 0)
        
        # Variación climática natural por día
        daily_temp_base = 25.0 + random.uniform(-0.6, 0.8)
        daily_temp_peak = 34.8 + random.uniform(-0.8, 1.2)
        daily_solar_peak = 102000.0 + random.uniform(-3000.0, 4500.0)
        
        readings_to_add = []
        curr_dt = start_dt
        while curr_dt <= end_dt:
            h_frac = curr_dt.hour + curr_dt.minute / 60.0 + curr_dt.second / 3600.0
            
            # 1. Bomba de Riego (A)
            is_pumping = False
            pump_elapsed = 0
            for p_s, p_e in irrigation_intervals:
                if p_s <= curr_dt <= p_e:
                    is_pumping = True
                    pump_elapsed = (curr_dt - p_s).total_seconds()
                    break
                    
            if is_pumping:
                if pump_elapsed <= 8:
                    curr_val = round(random.uniform(2.10, 2.38), 3)
                else:
                    curr_val = round(max(1.50, min(1.85, random.gauss(1.65, 0.04))), 3)
            else:
                curr_val = 0.0 if random.random() > 0.10 else round(random.uniform(0.000, 0.010), 3)
                
            # 2. Radiación Solar (lux)
            if 6.0 <= h_frac <= 18.5:
                t_norm = (h_frac - 6.0) / (18.5 - 6.0)
                solar_curve = math.sin(t_norm * math.pi)
                base_lux = (solar_curve ** 1.25) * daily_solar_peak
                cloud = 1.0 + 0.04 * math.sin(h_frac * 3.2) + random.uniform(-0.02, 0.03)
                lux_val = max(100.0, base_lux * cloud)
                if 12.1 <= h_frac <= 12.8:
                    lux_val = max(lux_val, 100000.0 + random.uniform(200.0, 3500.0))
            else:
                lux_val = 0.0
                
            # 3. Temperatura (°C)
            if h_frac <= 13.5:
                t_norm = (h_frac - 6.0) / (13.5 - 6.0)
                temp_val = daily_temp_base + (daily_temp_peak - daily_temp_base) * (1.0 - math.cos(t_norm * math.pi / 2))
            else:
                t_norm = (h_frac - 13.5) / (20.0 - 13.5)
                temp_val = daily_temp_peak - (daily_temp_peak - 27.2) * (t_norm ** 0.85)
            temp_val += random.gauss(0.0, 0.12)
            
            # 4. Humedad Relativa (% HR)
            if is_pumping:
                hum_target = 82.0 - (temp_val - 25.0) * 1.8 + 6.5
            else:
                hum_target = 88.0 - (temp_val - 25.0) * 2.85
            hum_val = max(52.0, min(95.0, hum_target + random.gauss(0.0, 0.6)))

            # 5. Conductividad Eléctrica (EC) (µS/cm)
            ec_diurnal = 1650.0 + 40.0 * math.sin(((h_frac - 6.0) / 14.0) * math.pi)
            if is_pumping:
                ec_diurnal += random.uniform(-3.0, 3.0)
            ec_val = max(1450.0, min(2100.0, ec_diurnal + random.gauss(0.0, 3.0)))

            # 6. pH de la Solución
            ph_diurnal = 6.18 + 0.15 * math.sin(((h_frac - 7.0) / 13.0) * math.pi)
            ph_val = max(5.6, min(6.7, ph_diurnal + random.gauss(0.0, 0.015)))

            # 7. Turbidez (NTU)
            if is_pumping:
                turb_base = 9.5 if pump_elapsed <= 180 else 7.0
            else:
                turb_base = 3.6
            turb_val = max(1.8, min(14.0, turb_base + random.gauss(0.0, 0.2)))

            # 8. Oxígeno Disuelto (DO) (mg/L)
            do_base = 7.6 - (temp_val - 25.0) * 0.05
            if is_pumping:
                do_base += 1.15
            do_val = max(5.8, min(9.4, do_base + random.gauss(0.0, 0.04)))
            
            readings_to_add.append(SensorReading(
                timestamp=curr_dt,
                temperature=round(temp_val, 2),
                humidity=round(hum_val, 1),
                uv_solar=round(lux_val, 1),
                motor_current=curr_val,
                ec_conductivity=round(ec_val, 1),
                water_ph=round(ph_val, 2),
                turbidity_ntu=round(turb_val, 2),
                dissolved_oxygen_mg_l=round(do_val, 2)
            ))
            curr_dt += timedelta(seconds=20)
            
        db.session.bulk_save_objects(readings_to_add)
        db.session.commit()
        print(f"Insertadas {len(readings_to_add)} lecturas de telemetria para {date_str}.")

def run_growth_dataset_generation():
    """
    Genera el conjunto completo de sesiones fotográficas y métricas para Cebollín (2026-09-01 al 2026-09-07).
    """
    app = create_app()
    with app.app_context():
        # 1. Asegurar calibración del perfil botánico de cebollín
        profile = CropProfile.query.filter_by(crop_type="cebollin").first()
        if not profile:
            profile = CropProfile(
                crop_type="cebollin",
                display_name="Cebollín (Allium schoenoprasum)",
                h_min=26, h_max=92, s_min=35, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=255, a_min=0, a_max=124, b_min=120, b_max=255,
                pixel_to_cm_ratio=0.038, has_stem=True,
                lat_h_min=30, lat_h_max=88, lat_s_min=40, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.045, lat_min_area=50, lat_filter_isolated=True
            )
            db.session.add(profile)
        else:
            profile.pixel_to_cm_ratio = 0.038
            profile.lat_pixel_to_cm_ratio = 0.045
            profile.has_stem = True
            profile.lat_filter_isolated = True
        db.session.commit()
        
        # 2. Asegurar lecturas de telemetría para toda la semana
        generate_sensor_readings_for_week()
        
        # 3. Eliminar sesiones previas de canastilla 1 en el rango de fechas para reescritura limpia
        start_date = datetime(2026, 9, 1).date()
        date_strs = [(start_date + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]
        
        for d_str in date_strs:
            existing_sessions = CaptureSession.query.filter(
                CaptureSession.plant_id == 1,
                db.func.strftime('%Y-%m-%d', CaptureSession.timestamp) == d_str
            ).all()
            for s in existing_sessions:
                db.session.delete(s)
        db.session.commit()
        print(f"Limpieza de sesiones previas completada para canastilla #1 ({len(date_strs)} dias).")
        
        pipeline = VisionPipelineManager()
        
        periods_schedule = [
            ("Mañana", 7, 45, 0),
            ("Mediodía", 12, 45, 0),
            ("Tarde", 17, 45, 0)
        ]
        
        total_sessions_created = 0
        total_photos_processed = 0
        
        for day_idx in range(1, 8):
            curr_date = start_date + timedelta(days=day_idx - 1)
            date_str = curr_date.strftime("%Y-%m-%d")
            
            for period_name, p_hour, p_min, p_sec in periods_schedule:
                session_dt = datetime(curr_date.year, curr_date.month, curr_date.day, p_hour, p_min, p_sec)
                batch_tag = f"batch_{session_dt.strftime('%Y%m%d_%H%M%S')}"
                
                upload_dir = os.path.join(config.UPLOAD_DIR, batch_tag)
                processed_dir = os.path.join(config.PROCESSED_DIR, batch_tag)
                os.makedirs(upload_dir, exist_ok=True)
                os.makedirs(processed_dir, exist_ok=True)
                
                # Buscar lectura de sensor más cercana para enlazar a la sesión
                closest_reading = SensorReading.query.order_by(
                    db.func.abs(db.func.strftime('%s', SensorReading.timestamp) - int(session_dt.timestamp()))
                ).first()
                sensor_id = closest_reading.id if closest_reading else None
                
                # Crear registro de CaptureSession
                session_record = CaptureSession(
                    period=period_name,
                    plant_id=1,
                    crop_type="cebollin",
                    timestamp=session_dt,
                    sensor_reading_id=sensor_id
                )
                db.session.add(session_record)
                db.session.flush() # Obtiene session_record.id
                
                cenital_results = []
                lateral_results = []
                cenital_paths = []
                lateral_paths = []
                
                # Generar y procesar 5 tomas individuales
                for shot in range(1, 6):
                    shot_dt = session_dt + timedelta(seconds=(shot - 1) * 12)
                    
                    # 1. Vista Cenital
                    cen_img = render_cenital_cebollin(day=day_idx, period=period_name, shot_idx=shot)
                    cen_orig_path = os.path.join(upload_dir, f"cenital_{shot}.png")
                    cen_proc_path = os.path.join(processed_dir, f"proc_cenital_{shot}.png")
                    cv2.imwrite(cen_orig_path, cen_img)
                    
                    m_cen = pipeline.process_cenital(cen_orig_path, cen_proc_path, profile)
                    if m_cen:
                        cenital_results.append(m_cen)
                        rel_cen_orig = os.path.relpath(cen_orig_path, config.DATA_DIR).replace("\\", "/")
                        rel_cen_proc = os.path.relpath(cen_proc_path, config.DATA_DIR).replace("\\", "/")
                        cenital_paths.append({
                            "orig": f"data/{rel_cen_orig}",
                            "proc": f"data/{rel_proc_cen}" if (rel_proc_cen := rel_cen_proc) else "",
                            "metrics": m_cen
                        })
                        
                    # 2. Vista Lateral
                    lat_img = render_lateral_cebollin(day=day_idx, period=period_name, shot_idx=shot)
                    lat_orig_path = os.path.join(upload_dir, f"lateral_{shot}.png")
                    lat_proc_path = os.path.join(processed_dir, f"proc_lateral_{shot}.png")
                    cv2.imwrite(lat_orig_path, lat_img)
                    
                    m_lat = pipeline.process_lateral(lat_orig_path, lat_proc_path, profile)
                    if m_lat:
                        lateral_results.append(m_lat)
                        rel_lat_orig = os.path.relpath(lat_orig_path, config.DATA_DIR).replace("\\", "/")
                        rel_lat_proc = os.path.relpath(lat_proc_path, config.DATA_DIR).replace("\\", "/")
                        lateral_paths.append({
                            "orig": f"data/{rel_lat_orig}",
                            "proc": f"data/{rel_proc_lat}" if (rel_proc_lat := rel_lat_proc) else "",
                            "metrics": m_lat
                        })
                        
                    # Guardar métrica individual para esta toma (photo_index = 1..5)
                    c_info = cenital_paths[-1] if cenital_paths else {}
                    l_info = lateral_paths[-1] if lateral_paths else {}
                    c_m = c_info.get("metrics", {})
                    l_m = l_info.get("metrics", {})
                    
                    ind_metric = BiometricMetric(
                        session_id=session_record.id,
                        photo_index=shot,
                        is_average=False,
                        capture_exact_time=shot_dt,
                        foliar_area_cm2=c_m.get("area_cm2", 0.0),
                        plant_height_cm=l_m.get("plant_height_cm", 0.0),
                        stem_diameter_mm=l_m.get("stem_diameter_mm", 0.0),
                        health_index=c_m.get("health_index", 100.0),
                        compacity_index=c_m.get("compacity_index", 0.0),
                        spots_count=0,
                        fruits_count=0,
                        image_path_cenital_orig=c_info.get("orig", ""),
                        image_path_cenital_proc=c_info.get("proc", ""),
                        image_path_lateral_orig=l_info.get("orig", ""),
                        image_path_lateral_proc=l_info.get("proc", "")
                    )
                    db.session.add(ind_metric)
                    total_photos_processed += 2
                    
                # Calcular promedio consolidado robusto
                final_avg = pipeline.filter_and_average(cenital_results, lateral_results)
                
                avg_metric = BiometricMetric(
                    session_id=session_record.id,
                    photo_index=0,
                    is_average=True,
                    capture_exact_time=session_dt,
                    foliar_area_cm2=final_avg.get("foliar_area_cm2", 0.0),
                    plant_height_cm=final_avg.get("plant_height_cm", 0.0),
                    stem_diameter_mm=final_avg.get("stem_diameter_mm", 0.0),
                    health_index=final_avg.get("health_index", 100.0),
                    compacity_index=final_avg.get("compacity_index", 0.0),
                    spots_count=0,
                    fruits_count=0,
                    image_path_cenital_orig=cenital_paths[0]["orig"] if cenital_paths else "",
                    image_path_cenital_proc=cenital_paths[0]["proc"] if cenital_paths else "",
                    image_path_lateral_orig=lateral_paths[0]["orig"] if lateral_paths else "",
                    image_path_lateral_proc=lateral_paths[0]["proc"] if lateral_paths else ""
                )
                db.session.add(avg_metric)
                db.session.commit()
                
                total_sessions_created += 1
                print(f"[Dia {day_idx} - {date_str}] {period_name:8s} -> "
                      f"Area: {final_avg['foliar_area_cm2']:6.2f} cm2 | "
                      f"Altura: {final_avg['plant_height_cm']:5.2f} cm | "
                      f"Tallo: {final_avg['stem_diameter_mm']:4.2f} mm | "
                      f"Salud: {final_avg['health_index']:5.1f}%")

        print("="*80)
        print(f"GENERACION COMPLETA:")
        print(f"Total Sesiones Creadas: {total_sessions_created} (7 dias x 3 periodos)")
        print(f"Total Imagenes Generadas y Procesadas: {total_photos_processed} fotos (Cenital + Lateral x 5 tomas)")
        print("="*80)

if __name__ == "__main__":
    run_growth_dataset_generation()
