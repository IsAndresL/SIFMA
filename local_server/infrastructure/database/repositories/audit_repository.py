# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from domain.models import AuditLog
from infrastructure.database.connection import db

class AuditRepository:
    """Implementación SQLAlchemy para persistencia y consulta de logs de auditoría."""

    def save(self, log_entry: AuditLog) -> AuditLog:
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        return AuditLog.query.get(log_id)

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
        query = AuditLog.query

        if module:
            query = query.filter(AuditLog.module == module.strip().upper())
        if action:
            query = query.filter(AuditLog.action == action.strip().upper())
        if level:
            query = query.filter(AuditLog.level == level.strip().lower())
        if username:
            query = query.filter(AuditLog.username.ilike(f"%{username.strip()}%"))
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                (AuditLog.description.ilike(s)) |
                (AuditLog.username.ilike(s)) |
                (AuditLog.user_fullname.ilike(s)) |
                (AuditLog.module.ilike(s)) |
                (AuditLog.action_display.ilike(s)) |
                (AuditLog.ip_address.ilike(s))
            )
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    def get_total_count(self) -> int:
        return AuditLog.query.count()

    def get_stats(self) -> Dict[str, Any]:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = AuditLog.query.filter(AuditLog.timestamp >= today_start).count()
        critical_count = AuditLog.query.filter(AuditLog.level.in_(['danger', 'warning'])).count()
        total_count = AuditLog.query.count()
        
        # Usuarios activos registrados en los logs hoy
        active_users_count = db.session.query(AuditLog.username).filter(AuditLog.timestamp >= today_start).distinct().count()

        return {
            'total_logs': total_count,
            'today_logs': today_count,
            'critical_logs': critical_count,
            'active_users_today': active_users_count
        }

    def delete_by_id(self, log_id: int) -> bool:
        log = AuditLog.query.get(log_id)
        if not log:
            return False
        db.session.delete(log)
        db.session.commit()
        return True

    def delete_all(self) -> int:
        deleted = AuditLog.query.delete()
        db.session.commit()
        return deleted

    def clear_old_logs(self, days: int = 180) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        deleted = AuditLog.query.filter(AuditLog.timestamp < cutoff).delete()
        db.session.commit()
        return deleted
