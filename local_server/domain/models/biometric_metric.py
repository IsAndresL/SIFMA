# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db
import json

class BiometricMetric(db.Model):
    """Entidad que registra los parámetros biométricos, espectrales, diagnóstico IA y rutas de imagen procesadas."""
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
    
    # Índices espectrales RGB y segmentación de tejidos por Machine Learning (K-Means + CIELAB/HSV)
    healthy_tissue_pct = Column(Float, default=100.0)
    chlorosis_pct = Column(Float, default=0.0)
    necrosis_pct = Column(Float, default=0.0)
    gli_index = Column(Float, default=0.0)
    vari_index = Column(Float, default=0.0)
    exg_index = Column(Float, default=0.0)
    
    # Diagnóstico Fitopatológico y Nutricional por Red Neuronal ONNX (cv2.dnn)
    ai_diagnosis_label = Column(String(160), nullable=True)
    ai_confidence = Column(Float, default=0.0)
    ai_diagnosis_json = Column(Text, nullable=True)
    
    image_path_cenital_orig = Column(String(300), nullable=True)
    image_path_cenital_proc = Column(String(300), nullable=True)
    image_path_lateral_orig = Column(String(300), nullable=True)
    image_path_lateral_proc = Column(String(300), nullable=True)
    image_path_spectral_map = Column(String(300), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_ai_diagnosis_dict(self):
        if self.ai_diagnosis_json:
            try:
                return json.loads(self.ai_diagnosis_json)
            except Exception:
                pass
        return {}

    def to_dict(self):
        return {
            "id": self.id,
            "photo_index": self.photo_index,
            "is_average": self.is_average,
            "capture_exact_time": self.capture_exact_time.strftime("%H:%M:%S") if self.capture_exact_time else None,
            "foliar_area_cm2": round(self.foliar_area_cm2 or 0.0, 2),
            "plant_height_cm": round(self.plant_height_cm or 0.0, 2),
            "stem_diameter_mm": round(self.stem_diameter_mm or 0.0, 2),
            "health_index": round(self.health_index if self.health_index is not None else 100.0, 1),
            "compacity_index": round(self.compacity_index or 0.0, 3),
            "healthy_tissue_pct": round(self.healthy_tissue_pct if self.healthy_tissue_pct is not None else (self.health_index or 100.0), 1),
            "chlorosis_pct": round(self.chlorosis_pct or 0.0, 1),
            "necrosis_pct": round(self.necrosis_pct or 0.0, 1),
            "gli_index": round(self.gli_index or 0.0, 3),
            "vari_index": round(self.vari_index or 0.0, 3),
            "exg_index": round(self.exg_index or 0.0, 3),
            "ai_diagnosis_label": self.ai_diagnosis_label or "Estado Fitosanitario y Nutricional Óptimo",
            "ai_confidence": round(self.ai_confidence or 94.0, 1),
            "ai_diagnosis": self.get_ai_diagnosis_dict(),
            "image_path_cenital_orig": self.image_path_cenital_orig,
            "image_path_cenital_proc": self.image_path_cenital_proc,
            "image_path_lateral_orig": self.image_path_lateral_orig,
            "image_path_lateral_proc": self.image_path_lateral_proc,
            "image_path_spectral_map": self.image_path_spectral_map
        }
