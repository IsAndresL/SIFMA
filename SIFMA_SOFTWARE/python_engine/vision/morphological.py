# SIFMA — Filtrado Morfológico y Extracción de Contornos
import cv2
import numpy as np
from typing import List

class MorphologicalFilter:
    """Acondicionamiento morfológico y eliminación de ruido especular y motas."""

    @staticmethod
    def cleanup_mask(mask: np.ndarray, is_lateral: bool = False) -> np.ndarray:
        """Aplica apertura y cierre morfológico con elemento estructurante elíptico."""
        if mask is None:
            return mask
        k_size = (5, 5) if is_lateral else (3, 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, k_size)
        clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        clean = cv2.morphologyEx(clean, cv2.MORPH_OPEN, kernel)
        return clean

    @staticmethod
    def find_contours(mask: np.ndarray, min_area_px: int = 30) -> List[np.ndarray]:
        """Obtiene y filtra contornos externos de la máscara binaria."""
        if mask is None:
            return []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area_px]

