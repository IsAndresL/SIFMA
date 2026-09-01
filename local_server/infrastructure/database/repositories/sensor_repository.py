from typing import List, Optional
from datetime import datetime
from domain.models import SensorReading
from infrastructure.database.connection import db

class SensorRepository:
    """Implementación SQLAlchemy para persistencia y consulta temporal de telemetría."""
    
    def add(self, reading: SensorReading) -> SensorReading:
        db.session.add(reading)
        db.session.commit()
        return reading

    def bulk_add(self, readings: List[SensorReading]) -> int:
        if not readings:
            return 0
        db.session.bulk_save_objects(readings)
        db.session.commit()
        return len(readings)

    def get_latest(self) -> Optional[SensorReading]:
        return SensorReading.query.order_by(SensorReading.timestamp.desc()).first()

    def get_recent(self, limit: int = 30) -> List[SensorReading]:
        readings = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(limit).all()
        readings.reverse()
        return readings

    def get_by_date(self, date_str: str) -> List[SensorReading]:
        if not date_str or date_str == "todos":
            return SensorReading.query.order_by(SensorReading.timestamp.asc()).all()
        return SensorReading.query.filter(
            db.func.strftime('%Y-%m-%d', SensorReading.timestamp) == date_str
        ).order_by(SensorReading.timestamp.asc()).all()

    def get_available_dates(self) -> List[str]:
        dates_query = db.session.query(
            db.func.strftime('%Y-%m-%d', SensorReading.timestamp)
        ).distinct().order_by(db.func.strftime('%Y-%m-%d', SensorReading.timestamp).desc()).all()
        return [d[0] for d in dates_query if d[0]]

    def find_nearest(self, target_timestamp: datetime) -> Optional[SensorReading]:
        if not target_timestamp:
            return None
        return SensorReading.query.order_by(
            db.func.abs(db.func.strftime('%s', SensorReading.timestamp) - db.func.strftime('%s', target_timestamp))
        ).first()

    def delete_by_date(self, date_str: str) -> int:
        if not date_str:
            return 0
        if date_str == "todos":
            count = SensorReading.query.delete()
        else:
            count = SensorReading.query.filter(
                db.func.strftime('%Y-%m-%d', SensorReading.timestamp) == date_str
            ).delete()
        db.session.commit()
        return count
