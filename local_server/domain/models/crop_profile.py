from sqlalchemy import Column, Integer, String, Float, Boolean
from infrastructure.database.connection import db

class CropProfile(db.Model):
    """Entidad de perfil botánico y parámetros cromáticos/morfométricos por especie."""
    __tablename__ = 'crop_profile'
    
    crop_type = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    
    # Rango HSV para segmentación
    h_min = Column(Integer, default=26)
    h_max = Column(Integer, default=92)
    s_min = Column(Integer, default=35)
    s_max = Column(Integer, default=255)
    v_min = Column(Integer, default=30)
    v_max = Column(Integer, default=255)

    # Rango LAB para segmentación
    l_min = Column(Integer, default=20)
    l_max = Column(Integer, default=255)
    a_min = Column(Integer, default=0)
    a_max = Column(Integer, default=124)
    b_min = Column(Integer, default=120)
    b_max = Column(Integer, default=255)

    # Parámetros morfométricos
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
