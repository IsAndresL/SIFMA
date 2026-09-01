from typing import List, Optional
from domain.models import AgronomicConclusion
from infrastructure.database.connection import db

class ConclusionRepository:
    """Implementación SQLAlchemy para la bitácora agronómica del investigador."""
    
    def get_by_id(self, conclusion_id: int) -> Optional[AgronomicConclusion]:
        return AgronomicConclusion.query.get(conclusion_id)

    def get_filtered(self, plant_id: int, date_str: Optional[str] = None, period_type: Optional[str] = None) -> List[AgronomicConclusion]:
        query = AgronomicConclusion.query.filter_by(plant_id=int(plant_id))
        if date_str and date_str != 'todos':
            query = query.filter_by(date_str=date_str)
        if period_type and period_type != 'todos':
            query = query.filter_by(period_type=period_type)
        return query.order_by(AgronomicConclusion.timestamp.desc()).all()

    def save(self, conclusion: AgronomicConclusion) -> AgronomicConclusion:
        db.session.add(conclusion)
        db.session.commit()
        return conclusion

    def delete(self, conclusion: AgronomicConclusion) -> None:
        db.session.delete(conclusion)
        db.session.commit()
