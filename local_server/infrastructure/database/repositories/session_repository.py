from typing import List, Optional
from domain.models import CaptureSession
from infrastructure.database.connection import db

class CaptureSessionRepository:
    """Implementación SQLAlchemy para persistencia de sesiones de fenotipado y métricas."""
    
    def get_by_id(self, session_id: int) -> Optional[CaptureSession]:
        return CaptureSession.query.get(session_id)

    def get_by_period_and_plant(self, period: str, plant_id: int) -> Optional[CaptureSession]:
        return CaptureSession.query.filter_by(
            plant_id=int(plant_id),
            period=period
        ).first()

    def get_all_by_plant(self, plant_id: int, order_asc: bool = False) -> List[CaptureSession]:
        query = CaptureSession.query.filter_by(plant_id=int(plant_id))
        if order_asc:
            return query.order_by(CaptureSession.timestamp.asc()).all()
        return query.order_by(CaptureSession.timestamp.desc()).all()

    def get_available_dates(self, plant_id: int) -> List[str]:
        dates_query = db.session.query(
            db.func.strftime('%Y-%m-%d', CaptureSession.timestamp)
        ).filter_by(plant_id=int(plant_id)).distinct().order_by(db.func.strftime('%Y-%m-%d', CaptureSession.timestamp).desc()).all()
        return [d[0] for d in dates_query if d[0]]

    def save(self, session: CaptureSession) -> CaptureSession:
        db.session.add(session)
        db.session.commit()
        return session

    def delete(self, session: CaptureSession) -> None:
        db.session.delete(session)
        db.session.commit()

    def delete_by_date(self, date_str: str, plant_id: int) -> int:
        query = CaptureSession.query.filter_by(plant_id=int(plant_id))
        if date_str != 'todos':
            query = query.filter(db.func.strftime('%Y-%m-%d', CaptureSession.timestamp) == date_str)
        sessions_to_del = query.all()
        count = len(sessions_to_del)
        for s in sessions_to_del:
            db.session.delete(s)
        db.session.commit()
        return count
