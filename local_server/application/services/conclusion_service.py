from typing import List, Optional, Dict, Any
from domain.models import AgronomicConclusion
from infrastructure.database.repositories import ConclusionRepository

class ConclusionApplicationService:
    """Caso de uso: Gestión de notas y bitácora agronómica de investigación."""
    
    def __init__(self, conclusion_repo: Optional[ConclusionRepository] = None):
        self.conclusion_repo = conclusion_repo or ConclusionRepository()

    def get_conclusions(self, plant_id: int, date_str: Optional[str] = None, period_type: Optional[str] = None) -> List[AgronomicConclusion]:
        return self.conclusion_repo.get_filtered(plant_id, date_str, period_type)

    def create_conclusion(self, data: Dict[str, Any]) -> AgronomicConclusion:
        note = AgronomicConclusion(
            plant_id=int(data.get("plant_id", 1)),
            date_str=data.get("date_str"),
            period_type=data.get("period_type", "diario"),
            growth_obs=data.get("growth_obs", ""),
            climate_obs=data.get("climate_obs", ""),
            nutrition_obs=data.get("nutrition_obs", ""),
            general_conclusion=data.get("general_conclusion", ""),
            author=data.get("author", "Investigador SIFMA")
        )
        return self.conclusion_repo.save(note)

    def delete_conclusion(self, conclusion_id: int) -> bool:
        note = self.conclusion_repo.get_by_id(conclusion_id)
        if not note:
            return False
        self.conclusion_repo.delete(note)
        return True
