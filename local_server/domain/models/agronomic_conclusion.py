from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from infrastructure.database.connection import db

class AgronomicConclusion(db.Model):
    """Entidad de la bitácora agronómica para anotaciones e inferencias del investigador."""
    __tablename__ = 'agronomic_conclusion'
    
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, default=1, index=True)
    date_str = Column(String(20), nullable=False, index=True) # e.g. '2026-08-24'
    period_type = Column(String(20), default='diario') # 'diario', 'semanal', 'mensual'
    growth_obs = Column(Text, nullable=True) # Observaciones sobre crecimiento foliar y vigor
    climate_obs = Column(Text, nullable=True) # Respuesta a temperatura, humedad y luz
    nutrition_obs = Column(Text, nullable=True) # Solución nutritiva y bombeo
    general_conclusion = Column(Text, nullable=False) # Conclusión general
    author = Column(String(100), default='Investigador SIFMA')
    timestamp = Column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
