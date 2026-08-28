import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Config(db.Model):
    __tablename__ = 'config'
    id = Column(Integer, primary_key=True)
    server_url = Column(String(200), default="http://127.0.0.1:5000")
    plant_id = Column(Integer, default=1)
    photos_per_period = Column(Integer, default=5)
    capture_interval_sec = Column(Integer, default=2)
    scheduled_times_str = Column(String(100), default="07:05,12:05,17:05")
    safe_shutdown_enabled = Column(Boolean, default=False)
    selected_crop_type = Column(String(50), default="cebollin")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_json(self):
        return {
            "server_url": self.server_url,
            "plant_id": self.plant_id,
            "photos_per_period": self.photos_per_period,
            "capture_interval_sec": self.capture_interval_sec,
            "scheduled_times": [t.strip() for t in self.scheduled_times_str.split(",") if t.strip()],
            "safe_shutdown_enabled": self.safe_shutdown_enabled,
            "selected_crop_type": self.selected_crop_type
        }

class CropProfile(db.Model):
    __tablename__ = 'crop_profile'
    crop_type = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    
    # Rango HSV para segmentacion
    h_min = Column(Integer, default=30)
    h_max = Column(Integer, default=90)
    s_min = Column(Integer, default=40)
    s_max = Column(Integer, default=255)
    v_min = Column(Integer, default=40)
    v_max = Column(Integer, default=255)

    # Rango LAB para segmentacion
    l_min = Column(Integer, default=20)
    l_max = Column(Integer, default=255)
    a_min = Column(Integer, default=0)
    a_max = Column(Integer, default=125)
    b_min = Column(Integer, default=128)
    b_max = Column(Integer, default=255)

    # Parametros morfologicos
    pixel_to_cm_ratio = Column(Float, default=0.038)
    has_stem = Column(Boolean, default=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_json(self):
        return {
            "crop_type": self.crop_type,
            "display_name": self.display_name,
            "h_min": self.h_min,
            "h_max": self.h_max,
            "s_min": self.s_min,
            "s_max": self.s_max,
            "v_min": self.v_min,
            "v_max": self.v_max,
            "l_min": self.l_min,
            "l_max": self.l_max,
            "a_min": self.a_min,
            "a_max": self.a_max,
            "b_min": self.b_min,
            "b_max": self.b_max,
            "pixel_to_cm_ratio": self.pixel_to_cm_ratio,
            "has_stem": self.has_stem
        }

class SensorReading(db.Model):
    __tablename__ = 'sensor_reading'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    uv_solar = Column(Float, nullable=False)
    motor_current = Column(Float, nullable=False)

    sessions = relationship("CaptureSession", back_populates="sensor_reading")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class CaptureSession(db.Model):
    __tablename__ = 'capture_session'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    period = Column(String(50), nullable=False)
    plant_id = Column(Integer, default=1)
    crop_type = Column(String(50), nullable=False)
    
    sensor_reading_id = Column(Integer, ForeignKey('sensor_reading.id'), nullable=True)
    sensor_reading = relationship("SensorReading", back_populates="sessions")
    
    metrics = relationship("BiometricMetric", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class BiometricMetric(db.Model):
    __tablename__ = 'biometric_metric'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('capture_session.id'), nullable=False)
    session = relationship("CaptureSession", back_populates="metrics")
    
    photo_index = Column(Integer, default=0) # 0 = Promedio del periodo, 1..5 = Foto individual
    is_average = Column(Boolean, default=False) # True si representa el promedio estadistico del lote
    capture_exact_time = Column(DateTime, nullable=True) # Segundo exacto para sincronizacion con telemetria
    
    foliar_area_cm2 = Column(Float, default=0.0)
    plant_height_cm = Column(Float, default=0.0)
    stem_diameter_mm = Column(Float, default=0.0)
    health_index = Column(Float, default=100.0)
    compacity_index = Column(Float, default=0.0)
    spots_count = Column(Integer, default=0)
    fruits_count = Column(Integer, default=0)
    
    image_path_cenital_orig = Column(String(300), nullable=True)
    image_path_cenital_proc = Column(String(300), nullable=True)
    image_path_lateral_orig = Column(String(300), nullable=True)
    image_path_lateral_proc = Column(String(300), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "photo_index": self.photo_index,
            "is_average": self.is_average,
            "capture_exact_time": self.capture_exact_time.strftime("%H:%M:%S") if self.capture_exact_time else None,
            "foliar_area_cm2": round(self.foliar_area_cm2, 2),
            "plant_height_cm": round(self.plant_height_cm, 2),
            "stem_diameter_mm": round(self.stem_diameter_mm, 2),
            "health_index": round(self.health_index, 1),
            "compacity_index": round(self.compacity_index, 3),
            "image_path_cenital_orig": self.image_path_cenital_orig,
            "image_path_cenital_proc": self.image_path_cenital_proc,
            "image_path_lateral_orig": self.image_path_lateral_orig,
            "image_path_lateral_proc": self.image_path_lateral_proc
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AgronomicConclusion(db.Model):
    __tablename__ = 'agronomic_conclusion'
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, default=1)
    date_str = Column(String(20), nullable=False) # e.g. '2026-08-20' o '2026-08-24'
    period_type = Column(String(20), default='diario') # 'diario', 'semanal', 'mensual'
    growth_obs = Column(Text, nullable=True) # Observaciones sobre crecimiento foliar y vigor
    climate_obs = Column(Text, nullable=True) # Respuesta a temperatura, humedad y luz
    nutrition_obs = Column(Text, nullable=True) # Solucion nutritiva y bombeo
    general_conclusion = Column(Text, nullable=False) # Conclusion general
    author = Column(String(100), default='Investigador SIFMA')
    timestamp = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "date_str": self.date_str,
            "period_type": self.period_type,
            "growth_obs": self.growth_obs or "",
            "climate_obs": self.climate_obs or "",
            "nutrition_obs": self.nutrition_obs or "",
            "general_conclusion": self.general_conclusion or "",
            "author": self.author,
            "created_at": self.timestamp.strftime("%d/%m/%Y %H:%M")
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

def init_db_data(app):
    """Inicializa la base de datos con configuraciones por defecto si no existen."""
    with app.app_context():
        db.create_all()
        
        # Migracion automatica segura de columnas nuevas en SQLite
        with db.engine.connect() as conn:
            for col_sql in [
                "ALTER TABLE biometric_metric ADD COLUMN photo_index INTEGER DEFAULT 0",
                "ALTER TABLE biometric_metric ADD COLUMN is_average BOOLEAN DEFAULT 0",
                "ALTER TABLE biometric_metric ADD COLUMN capture_exact_time DATETIME"
            ]:
                try:
                    conn.execute(db.text(col_sql))
                    conn.commit()
                except Exception:
                    pass
        
        if not Config.query.first():
            default_config = Config(
                server_url="http://127.0.0.1:5000",
                plant_id=1,
                photos_per_period=5,
                capture_interval_sec=2,
                scheduled_times_str="07:05,12:05,17:05",
                safe_shutdown_enabled=False,
                selected_crop_type="cebollin"
            )
            db.session.add(default_config)

        # Perfiles de cultivo por defecto calibrados para entornos reales
        default_profiles = [
            CropProfile(
                crop_type="cebollin",
                display_name="Cebollín",
                h_min=26, h_max=92, s_min=35, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=255, a_min=0, a_max=124, b_min=120, b_max=255,
                pixel_to_cm_ratio=0.038, has_stem=True
            ),
            CropProfile(
                crop_type="lechuga",
                display_name="Lechuga",
                h_min=28, h_max=88, s_min=40, s_max=255, v_min=35, v_max=255,
                l_min=25, l_max=245, a_min=0, a_max=123, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False
            ),
            CropProfile(
                crop_type="fresa",
                display_name="Fresa",
                h_min=30, h_max=86, s_min=45, s_max=255, v_min=35, v_max=255,
                l_min=20, l_max=240, a_min=0, a_max=124, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False
            ),
            CropProfile(
                crop_type="albahaca",
                display_name="Albahaca",
                h_min=28, h_max=90, s_min=40, s_max=255, v_min=35, v_max=255,
                l_min=20, l_max=245, a_min=0, a_max=124, b_min=120, b_max=250,
                pixel_to_cm_ratio=0.038, has_stem=True
            ),
            CropProfile(
                crop_type="espinaca",
                display_name="Espinaca",
                h_min=26, h_max=88, s_min=45, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=240, a_min=0, a_max=122, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False
            ),
            CropProfile(
                crop_type="cilantro",
                display_name="Cilantro",
                h_min=26, h_max=90, s_min=35, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=245, a_min=0, a_max=124, b_min=120, b_max=250,
                pixel_to_cm_ratio=0.038, has_stem=True
            )
        ]

        for p in default_profiles:
            existing = CropProfile.query.filter_by(crop_type=p.crop_type).first()
            if not existing:
                db.session.add(p)
            else:
                existing.h_min = p.h_min
                existing.h_max = p.h_max
                existing.s_min = p.s_min
                existing.s_max = p.s_max
                existing.v_min = p.v_min
                existing.v_max = p.v_max
                existing.a_max = p.a_max
                existing.b_min = p.b_min

        db.session.commit()

