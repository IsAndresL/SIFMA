import cv2
import numpy as np

class FruitDetector:
    """
    Detector de frutos (ej. Tomate Cherry) basado en tonalidades rojo/naranja y circularidad.
    """
    
    @staticmethod
    def detect_fruits(img, overlay):
        """
        Detecta y contabiliza frutos circulares rojos/anaranjados.
        Retorna la cantidad detectada y dibuja marcadores sobre la imagen overlay.
        """
        if img is None:
            return 0
            
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Rangos HSV para tonalidades rojas (wraparound de 0° y 180°)
        lower_red1 = np.array([0, 50, 45])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 50, 45])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red = cv2.bitwise_or(
            cv2.inRange(hsv, lower_red1, upper_red1),
            cv2.inRange(hsv, lower_red2, upper_red2)
        )
        
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel_close)
        mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel_open)
        
        fruit_contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fruits_count = 0
        
        for c in fruit_contours:
            c_area = cv2.contourArea(c)
            if c_area > 40: # Área mínima para tomate individual
                c_perimeter = cv2.arcLength(c, True)
                if c_perimeter > 0:
                    circularity = (4 * np.pi * c_area) / (c_perimeter ** 2)
                    if circularity > 0.55: # Alta circularidad
                        fruits_count += 1
                        (x_f, y_f), r_f = cv2.minEnclosingCircle(c)
                        cv2.circle(overlay, (int(x_f), int(y_f)), int(r_f), (0, 255, 255), 2)
                        
        return fruits_count
