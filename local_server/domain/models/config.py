from sqlalchemy import Column, Integer, String, Boolean, Float
from infrastructure.database.connection import db

class Config(db.Model):
    """Entidad de configuración de captura y parámetros del nodo central."""
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True)
    server_url = Column(String(200), default="http://127.0.0.1:5000")
    plant_id = Column(Integer, default=1)
    photos_per_period = Column(Integer, default=5)
    capture_interval_sec = Column(Integer, default=2)
    scheduled_times_str = Column(String(100), default="07:05,12:05,17:05")
    safe_shutdown_enabled = Column(Boolean, default=False)
    selected_crop_type = Column(String(50), default="cebollin")

    # Asignación de especie/perfil botánico independiente por cada Canastilla (1 a 4)
    plant_1_crop = Column(String(50), default="cebollin")
    plant_2_crop = Column(String(50), default="albahaca")
    plant_3_crop = Column(String(50), default="lechuga")
    plant_4_crop = Column(String(50), default="fresa")

    # Modo de Telemetría: Compartida por Torre (True) o Aislada por Canastilla (False)
    shared_telemetry = Column(Boolean, default=True)
    telemetry_mode = Column(String(50), default="shared_tower") # 'shared_tower' o 'isolated_node'

    # Ubicación Geográfica de la Torre (Santa Marta por defecto)
    latitude = Column(Float, default=11.2408)
    longitude = Column(Float, default=-74.1990)
    city_name = Column(String(100), default="Santa Marta, Magdalena")

    # Calibración de ROI Cenital Interactivo (Porcentajes normalizados 0.0 - 1.0)
    cenital_roi_cx = Column(Float, default=0.4955)
    cenital_roi_cy = Column(Float, default=0.4408)
    cenital_roi_radius = Column(Float, default=0.1450)
    cenital_roi_mode = Column(String(20), default="dynamic_conn") # 'dynamic_conn' o 'strict_circle'

    # Calibración de Línea Base Lateral Interactiva (Altura desde la maceta)
    lateral_baseline_y = Column(Float, default=0.7200) # Porcentaje de altura Y donde empieza el sustrato/borde de canastilla
    lateral_baseline_mode = Column(String(20), default="manual_baseline") # 'manual_baseline' o 'auto_bottom'

    # Calibración de Cuadro / Franja de Medición de Tallo (Scanline & Gradiente de Bordes)
    lateral_stem_roi_y = Column(Float, default=0.6600) # Centro Y del cuadro de tallo (normalizado 0.0 - 1.0)
    lateral_stem_roi_height = Column(Float, default=0.0500) # Altura del cuadro de tallo (normalizado 0.0 - 1.0)
    lateral_stem_roi_x = Column(Float, default=0.5000) # Centro X del cuadro de tallo (normalizado 0.0 - 1.0)
    lateral_stem_roi_width = Column(Float, default=0.2000) # Ancho del cuadro de tallo (normalizado 0.0 - 1.0)
    lateral_stem_mode = Column(String(20), default="auto_edge") # 'auto_edge' o 'disabled'

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
            "selected_crop_type": self.selected_crop_type,
            "plant_1_crop": self.plant_1_crop or "cebollin",
            "plant_2_crop": self.plant_2_crop or "albahaca",
            "plant_3_crop": self.plant_3_crop or "lechuga",
            "plant_4_crop": self.plant_4_crop or "fresa",
            "shared_telemetry": self.shared_telemetry if self.shared_telemetry is not None else True,
            "telemetry_mode": self.telemetry_mode or "shared_tower",
            "latitude": self.latitude if self.latitude is not None else 11.2408,
            "longitude": self.longitude if self.longitude is not None else -74.1990,
            "city_name": self.city_name or "Santa Marta, Magdalena",
            "cenital_roi_cx": self.cenital_roi_cx if self.cenital_roi_cx is not None else 0.4955,
            "cenital_roi_cy": self.cenital_roi_cy if self.cenital_roi_cy is not None else 0.4408,
            "cenital_roi_radius": self.cenital_roi_radius if self.cenital_roi_radius is not None else 0.1450,
            "cenital_roi_mode": self.cenital_roi_mode or "dynamic_conn",
            "lateral_baseline_y": self.lateral_baseline_y if self.lateral_baseline_y is not None else 0.7200,
            "lateral_baseline_mode": self.lateral_baseline_mode or "manual_baseline",
            "lateral_stem_roi_y": self.lateral_stem_roi_y if self.lateral_stem_roi_y is not None else 0.6600,
            "lateral_stem_roi_height": self.lateral_stem_roi_height if self.lateral_stem_roi_height is not None else 0.0500,
            "lateral_stem_roi_x": self.lateral_stem_roi_x if self.lateral_stem_roi_x is not None else 0.5000,
            "lateral_stem_roi_width": self.lateral_stem_roi_width if self.lateral_stem_roi_width is not None else 0.2000,
            "lateral_stem_mode": self.lateral_stem_mode or "auto_edge"
        }
