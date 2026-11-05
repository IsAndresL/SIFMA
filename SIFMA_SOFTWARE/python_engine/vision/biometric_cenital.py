# SIFMA — Calculador Biométrico de Vista Cenital
import cv2
import numpy as np
from typing import List, Dict, Any

class CenitalBiometrics:
    """Extrae área foliar (cm²), índice de compacidad y salud fitosanitaria cromática."""

    @staticmethod
    def calculate(
        bgr_image: np.ndarray, 
        mask: np.ndarray, 
        contours: List[np.ndarray], 
        pixel_to_cm_ratio: float = 0.05
    ) -> Dict[str, Any]:
        plant_pixels = 0
        compacity = 0.0

        if contours:
            plant_pixels = int(sum(cv2.contourArea(c) for c in contours))
            largest = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest, True)
            largest_area = cv2.contourArea(largest)

            if perimeter > 0:
                compacity = (4.0 * np.pi * largest_area) / (perimeter ** 2)

        area_cm2 = plant_pixels * (pixel_to_cm_ratio ** 2)

        # Análisis cromático de clorofila activa en espacio HSV
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        healthy_mask = cv2.inRange(hsv, np.array([38, 45, 45]), np.array([82, 255, 255]))
        healthy_pixels = cv2.countNonZero(cv2.bitwise_and(mask, healthy_mask)) if mask is not None else 0

        health_pct = 100.0
        if plant_pixels > 0:
            health_pct = (healthy_pixels / plant_pixels) * 100.0
            health_pct = min(100.0, max(0.0, health_pct))

        return {
            "plant_pixels": plant_pixels,
            "foliar_area_cm2": round(area_cm2, 2),
            "health_index_pct": round(health_pct, 2),
            "compacity_index": round(compacity, 3)
        }
