import cv2
import numpy as np

class ImageSegmenter:
    """
    Clase encargada de la conversión de espacios de color,
    umbralaización HSV/LAB y filtrado morfológico de ruido.
    """
    
    @staticmethod
    def create_foliage_mask(img, profile):
        """
        Crea una máscara binaria aislando el follaje según el perfil de cultivo.
        Incluye mecanismo de fallback a HSV si el espacio LAB es demasiado restrictivo.
        """
        if img is None:
            return None
            
        # 1. Conversión de espacios de color
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        # 2. Umbralizado en espacio HSV (Follaje verde/clorofila)
        lower_hsv = np.array([int(profile.h_min), int(profile.s_min), int(profile.v_min)])
        upper_hsv = np.array([int(profile.h_max), int(profile.s_max), int(profile.v_max)])
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # 3. Umbralizado en espacio LAB (Aislamiento cromático suplementario)
        lower_lab = np.array([int(profile.l_min), int(profile.a_min), int(profile.b_min)])
        upper_lab = np.array([int(profile.l_max), int(profile.a_max), int(profile.b_max)])
        mask_lab = cv2.inRange(lab, lower_lab, upper_lab)
        
        # 4. Combinación de máscaras cromáticas
        mask = cv2.bitwise_and(mask_hsv, mask_lab)
        
        # Fallback robusto: si LAB resulta muy restrictivo (menos del 20% de píxeles HSV), usar mask_hsv
        hsv_count = cv2.countNonZero(mask_hsv)
        comb_count = cv2.countNonZero(mask)
        if hsv_count > 0 and (comb_count == 0 or comb_count < 0.2 * hsv_count):
            mask = mask_hsv
        
        # 5. Limpieza de ruido mediante operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask

    @staticmethod
    def extract_valid_contours(mask, min_area=30):
        """
        Encuentra y filtra contornos por un área mínima en píxeles.
        Ajustado a 30px para capturar tallos finos y alargados como el cebollín.
        """
        if mask is None:
            return []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area]
