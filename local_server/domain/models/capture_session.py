from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db

class CaptureSession(db.Model):
    """Entidad que agrupa un período de muestreo fotográfico para una canastilla de cultivo."""
    __tablename__ = 'capture_session'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    period = Column(String(50), nullable=False)
    plant_id = Column(Integer, default=1, index=True)
    crop_type = Column(String(50), nullable=False)
    
    sensor_reading_id = Column(Integer, ForeignKey('sensor_reading.id'), nullable=True)
    sensor_reading = relationship("SensorReading", back_populates="sessions")
    
    metrics = relationship("BiometricMetric", back_populates="session", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_average_metric(self):
        """Retorna la métrica promedio consolidada del lote si existe."""
        if not self.metrics:
            return None
        return next((m for m in self.metrics if m.is_average or m.photo_index == 0), self.metrics[0])

    def get_individual_photos(self):
        """Retorna las fotos y métricas individuales ordenadas por índice."""
        photos = [m for m in self.metrics if not m.is_average and m.photo_index > 0]
        photos.sort(key=lambda m: m.photo_index)
        return photos
