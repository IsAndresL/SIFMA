from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database.connection import db

class SensorReading(db.Model):
    """Entidad que almacena una muestra temporal de telemetría ambiental y calidad de agua."""
    __tablename__ = 'sensor_reading'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
    # Variables Ambientales y Exterior
    temperature = Column(Float, nullable=False) # Temperatura exterior (°C)
    humidity = Column(Float, nullable=False) # Humedad relativa exterior (% HR)
    uv_solar = Column(Float, nullable=True, default=0.0)
    motor_current = Column(Float, nullable=True, default=0.0)
    motor_state = Column(Integer, nullable=True, default=0) # Estado Motor: 1 (Encendido) / 0 (Apagado)
    
    # Variables Fisicoquímicas y de Calidad de Agua / Nutrientes
    water_ph = Column(Float, nullable=True, default=6.2) # pH Solución (Potencial de Hidrógeno)
    ec_conductivity = Column(Float, nullable=True, default=1650.0) # µS/cm (Electroconductividad)
    turbidity_ntu = Column(Float, nullable=True, default=3.8) # NTU (Turbidez)
    dissolved_oxygen_mg_l = Column(Float, nullable=True, default=7.4) # mg/L (Oxígeno Disuelto)
    water_temp = Column(Float, nullable=True, default=20.0) # °C (Temperatura del agua)

    sessions = relationship("CaptureSession", back_populates="sensor_reading")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "water_ph": round(self.water_ph, 2) if self.water_ph is not None else 6.2,
            "ec_conductivity": round(self.ec_conductivity, 1) if self.ec_conductivity is not None else 1650.0,
            "turbidity_ntu": round(self.turbidity_ntu, 2) if self.turbidity_ntu is not None else 3.8,
            "dissolved_oxygen_mg_l": round(self.dissolved_oxygen_mg_l, 2) if self.dissolved_oxygen_mg_l is not None else 7.4,
            "water_temp": round(self.water_temp, 2) if self.water_temp is not None else 20.0,
            "temperature": round(self.temperature, 2) if self.temperature is not None else 0.0,
            "humidity": round(self.humidity, 1) if self.humidity is not None else 0.0,
            "motor_state": int(self.motor_state) if self.motor_state is not None else int(self.motor_current if self.motor_current is not None else 0),
            "motor_current": round(self.motor_current, 3) if self.motor_current is not None else 0.0,
            "uv_solar": round(self.uv_solar, 1) if self.uv_solar is not None else 0.0
        }

