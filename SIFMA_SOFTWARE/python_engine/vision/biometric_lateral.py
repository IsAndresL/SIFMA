# SIFMA — Calculador Biométrico de Vista Lateral
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

class LateralBiometrics:
    """Extrae altura de planta (cm) y diámetro basal de tallo (mm)."""

    @staticmethod
    def calculate(
        image_shape: tuple,
        contours: List[np.ndarray],
        pixel_to_cm_ratio: float = 0.05,
        baseline_ratio_y: float = 0.85
    ) -> Dict[str, Any]:
        h, w = image_shape[:2]
        height_cm = 0.0
        stem_diameter_mm = 0.0

        if not contours:
            return {
                "plant_height_cm": 0.0,
                "stem_diameter_mm": 0.0,
                "y_apex": None,
                "y_base": None
            }

        all_points = np.vstack(contours)
        y_points = all_points[:, 0, 1]
        x_points = all_points[:, 0, 0]

        y_apex = int(np.min(y_points))
        y_base = int(h * baseline_ratio_y)

        # Altura vertical en píxeles convertida a cm
        height_px = max(0, y_base - y_apex)
        height_cm = height_px * pixel_to_cm_ratio

        # Estimación de diámetro basal a 5% por encima de la base
        stem_y = int(y_base - (height_px * 0.05))
        stem_points_x = x_points[np.abs(y_points - stem_y) <= 3]

        if len(stem_points_x) >= 2:
            width_px = np.max(stem_points_x) - np.min(stem_points_x)
            stem_diameter_mm = (width_px * pixel_to_cm_ratio) * 10.0
        else:
            stem_diameter_mm = 4.5 # Fallback agronómico promedio

        return {
            "plant_height_cm": round(height_cm, 2),
            "stem_diameter_mm": round(stem_diameter_mm, 2),
            "y_apex": y_apex,
            "y_base": y_base
        }
