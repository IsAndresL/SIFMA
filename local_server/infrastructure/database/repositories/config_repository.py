from typing import Optional
from domain.models import Config
from infrastructure.database.connection import db

class ConfigRepository:
    """Implementación SQLAlchemy para persistencia de la configuración del sistema."""
    
    def get(self) -> Config:
        config = Config.query.first()
        if not config:
            config = Config()
            db.session.add(config)
            db.session.commit()
        return config

    def update(self, **kwargs) -> Config:
        config = self.get()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        db.session.commit()
        return config
