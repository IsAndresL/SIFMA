import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
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
    selected_crop_type = Column(String(50), default="lechuga")

    @property
    def scheduled_times(self):
        return [t.strip() for t in self.scheduled_times_str.split(",") if t.strip()]

    @scheduled_times.setter
    def scheduled_times(self, value_list):
        self.scheduled_times_str = ",".join(value_list)

    def to_json(self):
        return {
            "server_url": self.server_url,
            "plant_id": self.plant_id,
            "photos_per_period": self.photos_per_period,
            "capture_interval_sec": self.capture_interval_sec,
            "scheduled_times": self.scheduled_times,
            "safe_shutdown_enabled": self.safe_shutdown_enabled,
            "selected_crop_type": self.selected_crop_type
        }

class CropProfile(db.Model):
    __tablename__ = 'crop_profile'
    crop_type = Column(String(50), primary_key=True) # e.g. "lechuga", "espinaca", "tomate_cherry"
    display_name = Column(String(100), nullable=False)
    
    # HSV Thresholds
    h_min = Column(Integer, default=30)
    h_max = Column(Integer, default=95)
    s_min = Column(Integer, default=35)
    s_max = Column(Integer, default=255)
    v_min = Column(Integer, default=35)
    v_max = Column(Integer, default=255)
    
    # LAB Thresholds (L = Lightness, A = Green-Red, B = Blue-Yellow)
    l_min = Column(Integer, default=0)
    l_max = Column(Integer, default=255)
    a_min = Column(Integer, default=0)
    a_max = Column(Integer, default=125) # Excluye tonos rojizos, favorece verdes en canal 'a'
    b_min = Column(Integer, default=125) # Favorece amarillentos/verdes en canal 'b'
    b_max = Column(Integer, default=200)
    
    # Physical Calibration (cm per pixel)
    pixel_to_cm_ratio = Column(Float, default=0.015) # Valor de escala por defecto
    
    # Rosette vs Stemmed crop switch
    has_stem = Column(Boolean, default=True)

    def to_json(self):
        return {
            "crop_type": self.crop_type,
            "display_name": self.display_name,
            "h_min": self.h_min, "h_max": self.h_max,
            "s_min": self.s_min, "s_max": self.s_max,
            "v_min": self.v_min, "v_max": self.v_max,
            "l_min": self.l_min, "l_max": self.l_max,
            "a_min": self.a_min, "a_max": self.a_max,
            "b_min": self.b_min, "b_max": self.b_max,
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

class CaptureSession(db.Model):
    __tablename__ = 'capture_session'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    period = Column(String(50), nullable=False) # "mañana", "mediodía", "tarde"
    plant_id = Column(Integer, default=1)
    crop_type = Column(String(50), nullable=False)
    
    sensor_reading_id = Column(Integer, ForeignKey('sensor_reading.id'), nullable=True)
    sensor_reading = relationship("SensorReading", back_populates="sessions")
    
    metrics = relationship("BiometricMetric", back_populates="session", cascade="all, delete-orphan")

class BiometricMetric(db.Model):
    __tablename__ = 'biometric_metric'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('capture_session.id'), nullable=False)
    session = relationship("CaptureSession", back_populates="metrics")
    
    # Biometric computed data
    foliar_area_cm2 = Column(Float, default=0.0)
    plant_height_cm = Column(Float, default=0.0)
    stem_diameter_mm = Column(Float, default=0.0)
    health_index = Column(Float, default=100.0) # 0 to 100 % greenness
    compacity_index = Column(Float, default=0.0)
    spots_count = Column(Integer, default=0)
    fruits_count = Column(Integer, default=0)
    
    # Storage relative paths
    image_path_cenital_orig = Column(String(300), nullable=True)
    image_path_cenital_proc = Column(String(300), nullable=True)
    image_path_lateral_orig = Column(String(300), nullable=True)
    image_path_lateral_proc = Column(String(300), nullable=True)

def init_db_data(app):
    """Inicializa la base de datos con configuraciones por defecto si no existen."""
    with app.app_context():
        db.create_all()
        
        # 1. Configuración por defecto
        if not Config.query.first():
            default_config = Config(
                server_url="http://127.0.0.1:5000",
                plant_id=1,
                photos_per_period=5,
                capture_interval_sec=2,
                scheduled_times_str="07:05,12:05,17:05",
                safe_shutdown_enabled=False,
                selected_crop_type="lechuga"
            )
            db.session.add(default_config)
            print("Base de datos sembrada: Configuración por defecto creada.")

        # 2. Perfiles de color por especie vegetal
        default_profiles = [
            CropProfile(
                crop_type="lechuga",
                display_name="Lechuga (Lactuca sativa)",
                h_min=20, h_max=100, s_min=25, s_max=255, v_min=5, v_max=255,
                l_min=0, l_max=255, a_min=0, a_max=132, b_min=120, b_max=215,
                pixel_to_cm_ratio=0.015, # 1px = ~0.15mm
                has_stem=False
            ),
            CropProfile(
                crop_type="espinaca",
                display_name="Espinaca (Spinacia oleracea)",
                h_min=35, h_max=90, s_min=50, s_max=255, v_min=35, v_max=240,
                l_min=10, l_max=220, a_min=0, a_max=118, b_min=132, b_max=195,
                pixel_to_cm_ratio=0.015,
                has_stem=False
            ),
            CropProfile(
                crop_type="tomate_cherry",
                display_name="Tomate Cherry (Solanum lycopersicum)",
                h_min=35, h_max=85, s_min=55, s_max=255, v_min=45, v_max=255,
                l_min=10, l_max=240, a_min=0, a_max=122, b_min=132, b_max=200,
                pixel_to_cm_ratio=0.012, # Escala diferente debido a altura
                has_stem=True
            ),
            CropProfile(
                crop_type="rabano",
                display_name="Rábano (Raphanus sativus)",
                h_min=28, h_max=92, s_min=35, s_max=255, v_min=40, v_max=255,
                l_min=10, l_max=230, a_min=0, a_max=125, b_min=130, b_max=200,
                pixel_to_cm_ratio=0.015,
                has_stem=True
            ),
            CropProfile(
                crop_type="cebollin",
                display_name="Cebollín (Allium schoenoprasum)",
                h_min=30, h_max=95, s_min=20, s_max=255, v_min=40, v_max=255,
                l_min=10, l_max=230, a_min=0, a_max=125, b_min=128, b_max=180,
                pixel_to_cm_ratio=0.018,
                has_stem=True
            ),
            CropProfile(
                crop_type="ornamentales",
                display_name="Flores Ornamentales (Color No Convencional)",
                h_min=5, h_max=170, s_min=30, s_max=255, v_min=40, v_max=255, # Umbral ampliado
                l_min=5, l_max=250, a_min=0, a_max=255, b_min=0, b_max=255,
                pixel_to_cm_ratio=0.015,
                has_stem=True
            )
        ]

        for profile in default_profiles:
            if not CropProfile.query.filter_by(crop_type=profile.crop_type).first():
                db.session.add(profile)
                print(f"Base de datos sembrada: Perfil de especie '{profile.display_name}' creado.")

        db.session.commit()
