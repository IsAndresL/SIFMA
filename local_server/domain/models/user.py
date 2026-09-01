from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from infrastructure.database.connection import db

class User(db.Model):
    """
    Entidad de usuario del sistema SIFMA con control de acceso basado en roles (RBAC).
    Roles soportados:
    - 'admin': Administrador Principal (control total, gestion de usuarios y hardware)
    - 'investigador': Investigador / Agronomo (acceso a analitica, bitacora y graficas)
    - 'operador': Tecnico de Campo (procesamiento de lotes y monitoreo de sensores)
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(60), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(30), default='investigador', nullable=False) # 'admin', 'investigador', 'operador'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def role_display(self) -> str:
        roles_map = {
            "admin": "Administrador Principal",
            "investigador": "Investigador / Agrónomo",
            "operador": "Técnico de Campo"
        }
        return roles_map.get(self.role, "Usuario")

    @property
    def avatar_initials(self) -> str:
        """Genera las 2 iniciales a partir del nombre completo."""
        if not self.full_name:
            return self.username[:2].upper()
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return parts[0][:2].upper()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email or "",
            "role": self.role,
            "role_display": self.role_display,
            "avatar_initials": self.avatar_initials,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M") if self.last_login else "Nunca"
        }
