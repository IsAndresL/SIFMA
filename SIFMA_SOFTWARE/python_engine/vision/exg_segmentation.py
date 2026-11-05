# SIFMA — Segmentador Botánico por Exceso de Verde (ExG)
import cv2
import numpy as np
from typing import Optional, Tuple

class ExgSegmenter:
    """
    Segmentación cromática multiespectral para aislamiento de tejido vegetal fotosintético.
    Implementa: ExG = 2*G - R - B, con refinamiento en espacios HSV y CIELAB.
    """
    def __init__(self, exg_thresh: float = 8.0):
        self.exg_thresh = exg_thresh

    def compute_exg_matrix(self, bgr_image: np.ndarray) -> np.ndarray:
        """Calcula matriz ExG en punto flotante a partir de una imagen BGR."""
        if bgr_image is None or bgr_image.size == 0:
            raise ValueError("Imagen BGR vacía o nula")
        b, g, r = cv2.split(bgr_image.astype(np.float32))
        return 2.0 * g - r - b

    def generate_binary_mask(self, bgr_image: np.ndarray, is_lateral: bool = False) -> np.ndarray:
        """
        Produce una máscara binaria (0 y 255) aislando el tejido foliar/tallo.
        """
        # 1. Filtro ExG
        exg = self.compute_exg_matrix(bgr_image)
        thresh = 5.0 if is_lateral else self.exg_thresh
        exg_mask = (exg > thresh).astype(np.uint8) * 255

        # 2. Rango HSV para clorofila vegetal
        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        lower_hsv = np.array([22, 25, 25])
        upper_hsv = np.array([92, 255, 255])
        hsv_mask = cv2.inRange(hsv, lower_hsv, upper_hsv)

        # 3. Rango LAB para discriminar fondos blancos y PVC
        lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
        lower_lab = np.array([15, 0, 118])
        upper_lab = np.array([255, 124, 255])
        lab_mask = cv2.inRange(lab, lower_lab, upper_lab)

        # 4. Fusión por intersección lógica
        combined = cv2.bitwise_and(exg_mask, hsv_mask)
        combined = cv2.bitwise_and(combined, lab_mask)

        # Si el filtrado LAB fue excesivo en cenital, relajar a ExG + HSV
        if not is_lateral:
            if cv2.countNonZero(combined) < 0.2 * cv2.countNonZero(exg_mask):
                combined = cv2.bitwise_and(exg_mask, hsv_mask)

        return combined
