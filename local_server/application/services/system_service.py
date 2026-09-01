from typing import List, Optional
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

    def update_profile(self, profile: CropProfile) -> CropProfile:
        return self.crop_repo.save_or_update(profile)
