from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db

class SensorReading(db.Model):
    """Entidad que almacena una muestra temporal de telemetría ambiental y calidad de agua."""
    __tablename__ = 'sensor_reading'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Variables Ambientales
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    uv_solar = Column(Float, nullable=False)
    motor_current = Column(Float, nullable=False)
    
    # Variables Fisicoquímicas y de Calidad de Agua / Nutrientes
    ec_conductivity = Column(Float, nullable=True, default=1650.0) # µS/cm (Electroconductividad)
    water_ph = Column(Float, nullable=True, default=6.2) # pH (Potencial de Hidrógeno)
    turbidity_ntu = Column(Float, nullable=True, default=3.8) # NTU (Turbidez)
    dissolved_oxygen_mg_l = Column(Float, nullable=True, default=7.4) # mg/L (Oxígeno Disuelto)

    sessions = relationship("CaptureSession", back_populates="sensor_reading")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "temperature": round(self.temperature, 2) if self.temperature is not None else 0.0,
            "humidity": round(self.humidity, 1) if self.humidity is not None else 0.0,
            "uv_solar": round(self.uv_solar, 1) if self.uv_solar is not None else 0.0,
            "motor_current": round(self.motor_current, 3) if self.motor_current is not None else 0.0,
            "ec_conductivity": round(self.ec_conductivity, 1) if self.ec_conductivity is not None else 1650.0,
            "water_ph": round(self.water_ph, 2) if self.water_ph is not None else 6.2,
            "turbidity_ntu": round(self.turbidity_ntu, 2) if self.turbidity_ntu is not None else 3.8,
            "dissolved_oxygen_mg_l": round(self.dissolved_oxygen_mg_l, 2) if self.dissolved_oxygen_mg_l is not None else 7.4
        }

