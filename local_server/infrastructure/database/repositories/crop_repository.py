from typing import List, Optional
from domain.models import CropProfile
from infrastructure.database.connection import db

class CropProfileRepository:
    """Implementación SQLAlchemy para perfiles de cultivo y calibración morfométrica."""
    
    def get_by_type(self, crop_type: str) -> Optional[CropProfile]:
        if not crop_type:
            return None
        return CropProfile.query.filter_by(crop_type=crop_type).first()

    def get_all(self) -> List[CropProfile]:
        return CropProfile.query.all()

    def save_or_update(self, profile: CropProfile) -> CropProfile:
        existing = self.get_by_type(profile.crop_type)
        if not existing:
            db.session.add(profile)
        else:
            existing.display_name = profile.display_name
            existing.h_min = profile.h_min
            existing.h_max = profile.h_max
            existing.s_min = profile.s_min
            existing.s_max = profile.s_max
            existing.v_min = profile.v_min
            existing.v_max = profile.v_max
            existing.l_min = profile.l_min
            existing.l_max = profile.l_max
            existing.a_min = profile.a_min
            existing.a_max = profile.a_max
            existing.b_min = profile.b_min
            existing.b_max = profile.b_max
            existing.pixel_to_cm_ratio = profile.pixel_to_cm_ratio
            existing.has_stem = profile.has_stem
        db.session.commit()
        return profile
