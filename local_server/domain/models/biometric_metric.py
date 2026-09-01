from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db

class BiometricMetric(db.Model):
    """Entidad que registra los parámetros biométricos y rutas de imagen procesadas."""
    __tablename__ = 'biometric_metric'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('capture_session.id'), nullable=False, index=True)
    session = relationship("CaptureSession", back_populates="metrics")
    
    photo_index = Column(Integer, default=0) # 0 = Promedio del período, 1..5 = Toma individual
    is_average = Column(Boolean, default=False) # True si representa el consolidado del lote
    capture_exact_time = Column(DateTime, nullable=True)
    
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
