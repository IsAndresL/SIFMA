from typing import List, Optional
import cv2
import numpy as np
from domain.models import CropProfile

class ExgSegmentationStrategy:
    """
    Estrategia de segmentación botánica avanzada basada en el Índice de Exceso de Verde (ExG),
    combinado con filtrado HSV de clorofila y canal LAB.
    (Pattern: Strategy)
    """
    
    def create_mask(self, image: np.ndarray, profile: CropProfile, is_lateral: bool = False) -> Optional[np.ndarray]:
        """
        Genera la máscara binaria aislando exclusivamente tejido vegetal.
        Descarta piel humana, tierra, sustratos y plástico blanco.
        Soporta calibración independiente para vista cenital y vista lateral.
        """
        if image is None:
            return None
            
        # 1. Índice de Exceso de Verde (ExG = 2*G - R - B)
        b, g, r = cv2.split(image.astype(np.float32))
        exg = 2.0 * g - r - b
        
        # En vista lateral se incrementa ligeramente la selectividad de ExG
        exg_thresh = 12.0 if is_lateral else 10.0
        exg_mask = (exg > exg_thresh).astype(np.uint8) * 255
        
        # 2. Umbralizado en espacio HSV para clorofila
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if is_lateral:
            h_min = max(28, int(getattr(profile, 'lat_h_min', 32)))
            h_max = min(92, int(getattr(profile, 'lat_h_max', 86)))
            s_min = max(35, int(getattr(profile, 'lat_s_min', 40)))
            s_max = int(getattr(profile, 'lat_s_max', 255))
            v_min = max(30, int(getattr(profile, 'lat_v_min', 35)))
            v_max = int(getattr(profile, 'lat_v_max', 255))
            
            l_min = max(15, int(getattr(profile, 'lat_l_min', 25)))
            l_max = int(getattr(profile, 'lat_l_max', 255))
            # Canal A < 119 discrimina con precisión el plástico blanco y la tierra
            a_max = min(119, int(getattr(profile, 'lat_a_max', 118)))
            b_min = max(120, int(getattr(profile, 'lat_b_min', 125)))
        else:
            h_min = max(24, int(getattr(profile, 'h_min', 28)))
            h_max = min(96, int(getattr(profile, 'h_max', 90)))
            s_min = max(30, int(getattr(profile, 's_min', 35)))
            s_max = int(getattr(profile, 's_max', 255))
            v_min = max(25, int(getattr(profile, 'v_min', 30)))
            v_max = int(getattr(profile, 'v_max', 255))
            
            l_min = int(getattr(profile, 'l_min', 20))
            l_max = int(getattr(profile, 'l_max', 255))
            a_max = min(126, int(getattr(profile, 'a_max', 124)))
            b_min = max(115, int(getattr(profile, 'b_min', 120)))
        
        lower_hsv = np.array([h_min, s_min, v_min])
        upper_hsv = np.array([h_max, s_max, v_max])
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # 3. Umbralizado en espacio LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        lower_lab = np.array([l_min, 0, b_min])
        upper_lab = np.array([l_max, a_max, 255])
        mask_lab = cv2.inRange(lab, lower_lab, upper_lab)
        
        # 4. Fusión de máscaras por intersección
        mask = cv2.bitwise_and(exg_mask, mask_hsv)
        mask = cv2.bitwise_and(mask, mask_lab)
        
        # Fallback de respaldo SOLO para vista cenital (en lateral LAB es fundamental para anular bordes)
        if not is_lateral:
            if cv2.countNonZero(mask) < 0.25 * cv2.countNonZero(cv2.bitwise_and(exg_mask, mask_hsv)):
                mask = cv2.bitwise_and(exg_mask, mask_hsv)
            
        # 5. Filtrado morfológico de ruido
        k_size = (5, 5) if is_lateral else (3, 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, k_size)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask

    def extract_contours(self, mask: np.ndarray, min_area: int = 30) -> List[np.ndarray]:
        """Extrae y filtra contornos por tamaño mínimo en píxeles."""
        if mask is None:
            return []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area]
