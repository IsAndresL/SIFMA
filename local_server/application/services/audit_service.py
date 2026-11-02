import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from flask import has_request_context, session, request
from domain.models import AuditLog
from infrastructure.database.repositories import AuditRepository

logger = logging.getLogger(__name__)

class AuditService:
    """
    Servicio de Auditoría y Trazabilidad de Acciones del Sistema SIFMA.
    Registra operaciones realizadas por los usuarios (Super Usuario, Investigadores, Técnicos).
    """
    _instance = None

    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        self.audit_repo = audit_repo or AuditRepository()

    @classmethod
    def get_instance(cls) -> "AuditService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log(
        self,
        action: str,
        module: str,
        description: str,
        level: str = "info",
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_fullname: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        action_display: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Registra una acción en la base de datos de auditoría.
        Si no se especifican los datos de usuario, intenta inferirlos del contexto de sesión Flask actual.
        """
        try:
            # Inferir contexto desde la petición Flask si está disponible
            if has_request_context():
                if user_id is None:
                    user_id = session.get('user_id')
                if username is None:
                    username = session.get('username')
                if user_fullname is None:
                    user_fullname = session.get('user_name')
                if user_role is None:
                    user_role = session.get('user_role')
                if ip_address is None:
                    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

            clean_username = (username or 'sistema').strip()
            details_str = json.dumps(details, ensure_ascii=False) if details else None

            log_entry = AuditLog(
                action=action.strip().upper(),
                action_display=action_display,
                module=module.strip().upper(),
                description=description.strip(),
                level=level,
                username=clean_username,
                user_id=user_id,
                user_fullname=user_fullname,
                user_role=user_role,
                ip_address=ip_address,
                details_json=details_str,
                timestamp=datetime.now()
            )

            saved = self.audit_repo.save(log_entry)
            logger.info(f"[AUDIT] [{module}] [{action}] {clean_username}: {description}")
            return saved
        except Exception as e:
            logger.error(f"Error al registrar log de auditoría: {e}", exc_info=True)
            return None

    def get_logs(
        self,
        limit: int = 250,
        offset: int = 0,
        module: Optional[str] = None,
        action: Optional[str] = None,
        level: Optional[str] = None,
        username: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        return self.audit_repo.get_logs(
            limit=limit,
            offset=offset,
            module=module,
            action=action,
            level=level,
            username=username,
            search=search,
            start_date=start_date,
            end_date=end_date
        )

    def get_stats(self) -> Dict[str, Any]:
        return self.audit_repo.get_stats()

    def delete_log(self, log_id: int) -> bool:
        """Elimina un registro individual de auditoría."""
        return self.audit_repo.delete_by_id(log_id)

    def clear_all_logs(self) -> int:
        """Elimina todos los registros de auditoría almacenados."""
        return self.audit_repo.delete_all()

    def generate_csv(self, logs: List[AuditLog]) -> str:
        """Genera el contenido CSV formateado del historial de logs."""
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            "ID", 
            "Fecha y Hora", 
            "Usuario", 
            "Nombre Completo", 
            "Rol", 
            "Módulo", 
            "Acción", 
            "Nivel", 
            "Descripción", 
            "Dirección IP"
        ])

        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.username,
                log.user_fullname or "",
                log.user_role or "",
                log.module,
                log.action_display or log.action,
                log.level.upper(),
                log.description,
                log.ip_address or "127.0.0.1"
            ])

        return output.getvalue()
