import cv2
import numpy as np

class ImageSegmenter:
    """
    Segmentador botánico avanzado basado en el Índice de Exceso de Verde (ExG),
    espacio de color HSV para clorofila, canal LAB y filtrado morfológico.
    Diseñado para aislar exclusivamente tejido vegetal en entornos reales (suelo, maceta, manos).
    """
    
    @staticmethod
    def create_foliage_mask(img, profile):
        """
        Crea una máscara binaria de alta precisión aislando el follaje y tallos verdes.
        Combina:
        1. Índice ExG (Excess Green Index: 2*G - R - B) para eliminar piel, tierra y plástico blanco.
        2. Umbralizado HSV calibrado para clorofila.
        3. Umbralizado LAB para confirmación cromática.
        """
        if img is None:
            return None
            
        # 1. Separación de canales BGR flotantes para calcular ExG
        b, g, r = cv2.split(img.astype(np.float32))
        exg = 2.0 * g - r - b
        
        # Umbral ExG: el tejido vegetal verde vivo tiene ExG marcadamente positivo (> 10)
        # La piel (R>G), tierra (R>G) y macetas blancas/grises (R~G~B) dan valores <= 0.
        exg_threshold = 10.0
        exg_mask = (exg > exg_threshold).astype(np.uint8) * 255
        
        # 2. Umbralizado en espacio HSV (Clorofila / Follaje)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_min = max(24, int(getattr(profile, 'h_min', 28)))
        h_max = min(96, int(getattr(profile, 'h_max', 90)))
        s_min = max(30, int(getattr(profile, 's_min', 35)))
        s_max = int(getattr(profile, 's_max', 255))
        v_min = max(25, int(getattr(profile, 'v_min', 30)))
        v_max = int(getattr(profile, 'v_max', 255))
        
        lower_hsv = np.array([h_min, s_min, v_min])
        upper_hsv = np.array([h_max, s_max, v_max])
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
        
        # 3. Umbralizado en espacio LAB (El canal A < 126 representa tonos verdes puros)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_min = int(getattr(profile, 'l_min', 20))
        l_max = int(getattr(profile, 'l_max', 255))
        a_max = min(126, int(getattr(profile, 'a_max', 124)))
        b_min = max(115, int(getattr(profile, 'b_min', 120)))
        
        lower_lab = np.array([l_min, 0, b_min])
        upper_lab = np.array([l_max, a_max, 255])
        mask_lab = cv2.inRange(lab, lower_lab, upper_lab)
        
        # 4. Fusión de máscaras (Intersección ExG + HSV + LAB)
        mask = cv2.bitwise_and(exg_mask, mask_hsv)
        mask = cv2.bitwise_and(mask, mask_lab)
        
        # Si la intersección con LAB elimina demasiados píxeles por iluminación, respaldar con ExG & HSV
        if cv2.countNonZero(mask) < 0.25 * cv2.countNonZero(cv2.bitwise_and(exg_mask, mask_hsv)):
            mask = cv2.bitwise_and(exg_mask, mask_hsv)
        
        # 5. Filtrado morfológico de ruido
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
        
        return mask

    @staticmethod
    def extract_valid_contours(mask, min_area=30):
        """
        Encuentra y filtra contornos por un área mínima en píxeles.
        Ajustado a 30px para capturar tallos finos y brotes como el cebollín.
        """
        if mask is None:
            return []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [c for c in contours if cv2.contourArea(c) >= min_area]

