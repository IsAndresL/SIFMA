import cv2
import numpy as np

class BiometricCalculator:
    """
    Calculadora de parámetros biométricos (Área Foliar, Salud, Altura y Tallo).
    """
    
    @staticmethod
    def calculate_cenital_metrics(img, mask, contours, profile):
        """
        Calcula el área foliar (cm²), índice de salud (%) e índice de compacidad.
        """
        plant_pixels = 0
        compacity = 0.0
        
        if contours:
            plant_pixels = sum(cv2.contourArea(c) for c in contours)
            largest_contour = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest_contour, True)
            largest_area = cv2.contourArea(largest_contour)
            
            if perimeter > 0:
                compacity = (4 * np.pi * largest_area) / (perimeter ** 2)
                
        # 1. Área física en cm²
        area_cm2 = plant_pixels * (profile.pixel_to_cm_ratio ** 2)
        
        # 2. Índice de Salud Cromática (% de píxeles verde óptimo dentro de la planta)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_green = np.array([38, 45, 45])
        upper_green = np.array([82, 255, 255])
        mask_healthy = cv2.inRange(hsv, lower_green, upper_green)
        
        healthy_plant_pixels = cv2.countNonZero(cv2.bitwise_and(mask, mask_healthy))
        health_index = 100.0
        if plant_pixels > 0:
            health_index = (healthy_plant_pixels / plant_pixels) * 100.0
            health_index = min(100.0, max(0.0, health_index))
            
        return {
            "plant_pixels": plant_pixels,
            "area_cm2": round(area_cm2, 2),
            "health_index": round(health_index, 2),
            "compacity_index": round(compacity, 3)
        }

    @staticmethod
    def calculate_lateral_metrics(img, mask, contours, profile):
        """
        Calcula la altura estimada de la planta (cm) y el diámetro del tallo (mm).
        El nivel del suelo (borde de la canastilla) se sitúa al 73% de la altura de la imagen.
        """
        h, w, _ = img.shape
        height_cm = 0.0
        stem_diameter_mm = 0.0
        stem_draw_y = None
        stem_row_pixels = None
        
        if contours:
            all_points = np.vstack([c for c in contours])
            y_points = all_points[:, 0, 1]
            x_points = all_points[:, 0, 0]
            
            y_min = np.min(y_points) # Punto más alto de las hojas
            basket_rim_y = int(h * 0.73) # Suelo de referencia
            
            if y_min < basket_rim_y:
                y_max = basket_rim_y
                height_pixels = y_max - y_min
                height_cm = height_pixels * profile.pixel_to_cm_ratio
                
                # Cálculo de diámetro de tallo basal (si la especie tiene tallo)
                has_stem = getattr(profile, 'has_stem', True)
                if has_stem and height_cm >= 2.0:
                    widths = []
                    valid_y = []
                    for offset in range(3, 9):
                        test_y = y_max - offset
                        if 0 <= test_y < h:
                            row_pixels = np.where(mask[test_y, :] > 0)[0]
                            if len(row_pixels) > 0:
                                w_px = np.max(row_pixels) - np.min(row_pixels)
                                if w_px < 60: # Evitar hojas bajas
                                    widths.append(w_px)
                                    valid_y.append(test_y)
                    
                    if widths:
                        stem_width_pixels = np.median(widths)
                        stem_diameter_mm = stem_width_pixels * profile.pixel_to_cm_ratio * 10
                        stem_draw_y = int(np.median(valid_y))
                        stem_row_pixels = np.where(mask[stem_draw_y, :] > 0)[0]
                        
        return {
            "height_cm": round(height_cm, 2),
            "stem_diameter_mm": round(stem_diameter_mm, 2),
            "y_min": y_min if contours else None,
            "y_max": int(h * 0.73) if contours else None,
            "x_points": x_points if contours else None,
            "stem_draw_y": stem_draw_y,
            "stem_row_pixels": stem_row_pixels
        }
