from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db

class SensorReading(db.Model):
    """Entidad que almacena una muestra temporal de telemetría ambiental."""
    __tablename__ = 'sensor_reading'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    uv_solar = Column(Float, nullable=False)
    motor_current = Column(Float, nullable=False)

    sessions = relationship("CaptureSession", back_populates="sensor_reading")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 1),
            "uv_solar": round(self.uv_solar, 1),
            "motor_current": round(self.motor_current, 3)
        }
