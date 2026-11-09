# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from infrastructure.database.connection import db

ALL_MODULE_PERMISSIONS = [
    ("dashboard", "Resumen Diario", "dashboard", "Visualización de KPIs del día y resumen agronómico"),
    ("calendar", "Calendario de Muestreos", "calendar_month", "Navegación histórica de jornadas y muestreos"),
    ("processing", "Procesamiento y Visión", "camera_enhance", "Ejecución del pipeline OpenCV y detección USB"),
    ("gallery", "Galería de Lotes", "photo_library", "Explorador fotográfico y visor de tomas"),
    ("timelapse", "Time-Lapse Evolutivo", "slow_motion_video", "Generación y reproducción de video temporal"),
    ("sensors", "Sensores Ambientales", "sensors", "Telemetría en tiempo real y curvas fisicoquímicas"),
    ("cross_analysis", "Cruce y Correlaciones", "sync_alt", "Matriz de correlación multivariable de Pearson"),
    ("reports", "Dossier y Reportes", "assessment", "Generador interactivo de informes y fichas técnicas en PDF"),
    ("config", "Parámetros de Cultivo", "tune", "Calibración HSV/LAB, escala px/cm y ROI"),
    ("export_data", "Exportación de Datos", "download", "Descarga de reportes diarios y datasets CSV")
]

class User(db.Model):
    """
    Entidad de usuario del sistema SIFMA con control de acceso granular y basado en roles (RBAC).
    Roles soportados:
    - 'admin': Super Usuario / Administrador Principal (control total de la plataforma y usuarios)
    - 'investigador': Investigador / Agrónomo
    - 'operador': Técnico de Campo
    - 'personalizado': Rol a medida con permisos específicos por función
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(60), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(30), default='investigador', nullable=False) # 'admin', 'investigador', 'operador', 'personalizado'
    avatar_path = Column(String(255), nullable=True, default=None) # Ruta a la foto de perfil / avatar subido
    permissions = Column(Text, nullable=True, default=None) # JSON String con permisos granulares
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_super_admin(self) -> bool:
        """Indica si el usuario es el Super Usuario / Administrador Principal."""
        return self.role == 'admin' or self.username.lower() == 'admin'

    @property
    def role_display(self) -> str:
        roles_map = {
            "admin": "Administrador",
            "investigador": "Investigador / Agrónomo",
            "operador": "Técnico de Campo",
            "personalizado": "Acceso Personalizado"
        }
        return roles_map.get(self.role, "Usuario")

    @property
    def avatar_url(self) -> Optional[str]:
        """Retorna la URL web del avatar si tiene foto subida."""
        if self.avatar_path:
            clean = self.avatar_path.replace('\\', '/')
            if not clean.startswith('/') and not clean.startswith('http'):
                clean = '/' + clean
            return clean
        return None

    @property
    def avatar_initials(self) -> str:
        """Genera las 2 iniciales a partir del nombre completo."""
        if not self.full_name:
            return self.username[:2].upper()
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return parts[0][:2].upper()

    def get_permissions_dict(self) -> Dict[str, bool]:
        """Retorna el mapa booleano de permisos del usuario para cada módulo."""
        if self.is_super_admin:
            return {k: True for k, _, _, _ in ALL_MODULE_PERMISSIONS}
        
        parsed = {}
        if self.permissions:
            try:
                parsed = json.loads(self.permissions)
            except Exception:
                parsed = {}

        # Fallback predeterminado según el rol si no tiene JSON explícito
        if not parsed:
            if self.role == "investigador":
                parsed = {
                    "dashboard": True,
                    "calendar": True,
                    "processing": False,
                    "gallery": True,
                    "timelapse": True,
                    "sensors": True,
                    "cross_analysis": True,
                    "reports": True,
                    "config": False,
                    "export_data": True
                }
            elif self.role == "operador":
                parsed = {
                    "dashboard": True,
                    "calendar": True,
                    "processing": True,
                    "gallery": True,
                    "timelapse": False,
                    "sensors": True,
                    "cross_analysis": False,
                    "config": False,
                    "export_data": False
                }
            else:
                parsed = {k: False for k, _, _, _ in ALL_MODULE_PERMISSIONS}

        # Asegurar que todas las llaves existan
        res = {}
        for k, _, _, _ in ALL_MODULE_PERMISSIONS:
            res[k] = bool(parsed.get(k, False))
        return res

    def has_permission(self, permission_key: str) -> bool:
        """Verifica si el usuario tiene habilitado un permiso o módulo específico."""
        if self.is_super_admin:
            return True
        return self.get_permissions_dict().get(permission_key, False)

    def set_permissions_dict(self, perms_dict: Dict[str, Any]):
        """Serializa y almacena los permisos granulares."""
        if self.is_super_admin:
            self.permissions = json.dumps({k: True for k, _, _, _ in ALL_MODULE_PERMISSIONS})
        else:
            clean = {k: bool(perms_dict.get(k, False)) for k, _, _, _ in ALL_MODULE_PERMISSIONS}
            self.permissions = json.dumps(clean)

    def to_dict(self):
        perms = self.get_permissions_dict()
        enabled_count = sum(1 for v in perms.values() if v)
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email or "",
            "role": self.role,
            "role_display": self.role_display,
            "is_super_admin": self.is_super_admin,
            "avatar_initials": self.avatar_initials,
            "avatar_path": self.avatar_path,
            "avatar_url": self.avatar_url,
            "permissions": perms,
            "permissions_count": enabled_count,
            "total_permissions": len(ALL_MODULE_PERMISSIONS),
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M") if self.last_login else "Nunca"
        }

