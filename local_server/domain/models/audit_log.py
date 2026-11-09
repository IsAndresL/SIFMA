# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from datetime import datetime
from typing import Dict, Any, Optional
from infrastructure.database.connection import db

class AuditLog(db.Model):
    """
    Modelo de Registro de Auditoría y Trazabilidad de Acciones del Sistema (Audit Log).
    Exclusivo para el Super Usuario / Administrador Principal.
    """
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = db.Column(db.String(100), nullable=False, index=True)
    user_fullname = db.Column(db.String(150), nullable=True)
    user_role = db.Column(db.String(50), nullable=True)
    
    action = db.Column(db.String(80), nullable=False, index=True) # e.g. LOGIN, LOGOUT, CREATE_USER, DELETE_USER, etc.
    action_display = db.Column(db.String(120), nullable=True)     # e.g. "Creación de Usuario"
    module = db.Column(db.String(60), nullable=False, index=True) # e.g. USUARIOS, AUTENTICACION, CONFIGURACION, LOTES
    description = db.Column(db.Text, nullable=False)              # Descripción amigable y detallada de la acción
    details_json = db.Column(db.Text, nullable=True)              # Metadatos / JSON opcional
    ip_address = db.Column(db.String(60), nullable=True)          # Dirección IP del cliente
    level = db.Column(db.String(20), default='info', nullable=False) # 'info', 'success', 'warning', 'danger'

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'), foreign_keys=[user_id])

    def __init__(
        self,
        action: str,
        module: str,
        description: str,
        username: str = "sistema",
        user_id: Optional[int] = None,
        user_fullname: Optional[str] = None,
        user_role: Optional[str] = None,
        action_display: Optional[str] = None,
        level: str = "info",
        ip_address: Optional[str] = None,
        details_json: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.action = action
        self.action_display = action_display or action.replace('_', ' ').title()
        self.module = module
        self.description = description
        self.username = username
        self.user_id = user_id
        self.user_fullname = user_fullname or username
        self.user_role = user_role or "sistema"
        self.level = level if level in ['info', 'success', 'warning', 'danger'] else 'info'
        self.ip_address = ip_address
        self.details_json = details_json
        self.timestamp = timestamp or datetime.now()

    @property
    def level_badge_class(self) -> str:
        mapping = {
            'info': 'badge-info',
            'success': 'badge-success',
            'warning': 'badge-warning',
            'danger': 'badge-danger'
        }
        return mapping.get(self.level, 'badge-info')

    @property
    def action_icon(self) -> str:
        icon_map = {
            'LOGIN': 'login',
            'LOGOUT': 'logout',
            'LOGIN_FAILED': 'no_accounts',
            'CREATE_USER': 'person_add',
            'UPDATE_USER': 'manage_accounts',
            'DELETE_USER': 'person_remove',
            'TOGGLE_USER_STATUS': 'published_with_changes',
            'CHANGE_PASSWORD': 'password',
            'UPDATE_CONFIG': 'tune',
            'DELETE_BATCH': 'delete_sweep',
            'PROCESS_IMAGES': 'camera_enhance',
            'EXPORT_DATA': 'file_download',
            'UPLOAD_SESSION': 'cloud_upload',
            'CROP_PROFILE_UPDATE': 'psychology',
            'SYSTEM_EVENT': 'info'
        }
        return icon_map.get(self.action, 'receipt_long')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'date_formatted': self.timestamp.strftime('%d/%m/%Y'),
            'time_formatted': self.timestamp.strftime('%H:%M:%S'),
            'user_id': self.user_id,
            'username': self.username,
            'user_fullname': self.user_fullname or self.username,
            'user_role': self.user_role,
            'action': self.action,
            'action_display': self.action_display,
            'action_icon': self.action_icon,
            'module': self.module,
            'description': self.description,
            'details_json': self.details_json,
            'ip_address': self.ip_address or '127.0.0.1',
            'level': self.level,
            'level_badge_class': self.level_badge_class
        }
