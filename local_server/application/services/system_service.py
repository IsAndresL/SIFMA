from typing import List, Optional, Dict
from domain.models import Config, CropProfile
from infrastructure.database.repositories import ConfigRepository, CropProfileRepository

class SystemService:
    """Caso de uso: Gestión de configuración general del nodo y perfiles de cultivo."""
    
    def __init__(
        self, 
        config_repo: Optional[ConfigRepository] = None, 
        crop_repo: Optional[CropProfileRepository] = None
    ):
        self.config_repo = config_repo or ConfigRepository()
        self.crop_repo = crop_repo or CropProfileRepository()

    def get_config(self) -> Config:
        return self.config_repo.get()

    def update_config(self, **kwargs) -> Config:
        return self.config_repo.update(**kwargs)

    def get_all_profiles(self) -> List[CropProfile]:
        return self.crop_repo.get_all()

    def get_profile(self, crop_type: Optional[str] = None) -> CropProfile:
        if not crop_type:
            cfg = self.get_config()
            crop_type = cfg.selected_crop_type
        profile = self.crop_repo.get_by_type(crop_type)
        if not profile:
            profile = self.crop_repo.get_by_type("cebollin") or self.crop_repo.get_all()[0]
        return profile

    def get_crop_for_plant(self, plant_id: int) -> str:
        """Devuelve el tipo de cultivo asignado específicamente a la Canastilla (1 a 4)."""
        cfg = self.get_config()
        attr_name = f"plant_{plant_id}_crop"
        return getattr(cfg, attr_name, None) or cfg.selected_crop_type or "cebollin"

    def set_crop_for_plant(self, plant_id: int, crop_type: str) -> None:
        """Asigna un perfil botánico a una Canastilla específica."""
        attr_name = f"plant_{plant_id}_crop"
        self.update_config(**{attr_name: crop_type})

    def get_profile_for_plant(self, plant_id: int) -> CropProfile:
        """Obtiene la entidad CropProfile correspondiente a la Canastilla."""
        crop_type = self.get_crop_for_plant(plant_id)
        return self.get_profile(crop_type)

    def get_all_plant_profiles_map(self) -> Dict[int, Dict[str, str]]:
        """Devuelve el mapa completo de Canastillas (1..4) con sus especies y nombres."""
        res = {}
        for pid in range(1, 5):
            c_type = self.get_crop_for_plant(pid)
            prof = self.get_profile(c_type)
            res[pid] = {
                "plant_id": pid,
                "crop_type": c_type,
                "display_name": prof.display_name if prof else c_type.capitalize()
            }
        return res

    def update_profile(self, profile: CropProfile) -> CropProfile:
        return self.crop_repo.save_or_update(profile)
