from sqlalchemy import Column, Integer, String, Boolean
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
            "selected_crop_type": self.selected_crop_type
        }
