from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from domain.models import CropProfile

class BiometricCalculator:
    """
    Calculador de parámetros biométricos y morfométricos:
    Área Foliar (cm²), Índice de Salud (%), Altura de Planta (cm), Diámetro de Tallo (mm) e Índice de Compacidad.
    """
    
    def calculate_cenital(self, image: np.ndarray, mask: np.ndarray, contours: List[np.ndarray], profile: CropProfile) -> Dict[str, Any]:
        plant_pixels = 0
        compacity = 0.0
        
        if contours:
            plant_pixels = sum(cv2.contourArea(c) for c in contours)
            largest_contour = max(contours, key=cv2.contourArea)
            perimeter = cv2.arcLength(largest_contour, True)
            largest_area = cv2.contourArea(largest_contour)
            
            if perimeter > 0:
                compacity = (4 * np.pi * largest_area) / (perimeter ** 2)
                
        # Área física en cm²
        area_cm2 = plant_pixels * (profile.pixel_to_cm_ratio ** 2)
        
        # Índice de Salud Cromática (% de píxeles verde clorofila óptimo)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_green = np.array([38, 45, 45])
        upper_green = np.array([82, 255, 255])
        mask_healthy = cv2.inRange(hsv, lower_green, upper_green)
        
        healthy_plant_pixels = cv2.countNonZero(cv2.bitwise_and(mask, mask_healthy)) if mask is not None else 0
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

    def calculate_lateral(self, image: np.ndarray, mask: np.ndarray, contours: List[np.ndarray], profile: CropProfile) -> Dict[str, Any]:
        h, w, _ = image.shape
        height_cm = 0.0
        stem_diameter_mm = 0.0
        stem_draw_y = None
        stem_row_pixels = None
        y_min = None
        y_max = None
        x_points = None
        filtered_contours = []
        
        if contours:
            # 1. Filtro Espacial de Cluster Central (Descartar bordes y manchas aisladas)
            filter_isolated = getattr(profile, 'lat_filter_isolated', True)
            
            if filter_isolated and len(contours) > 1:
                # El contorno más grande representa el follaje/tallo principal
                largest_contour = max(contours, key=cv2.contourArea)
                lx, ly, lw, lh = cv2.boundingRect(largest_contour)
                lcx = lx + (lw / 2.0)
                
                # Tolerancia de proximidad al cluster vegetal principal
                max_horizontal_dist = max(75.0, min(140.0, lw * 1.0))
                
                for c in contours:
                    cx, cy, cw, ch = cv2.boundingRect(c)
                    center_x = cx + (cw / 2.0)
                    if abs(center_x - lcx) <= max_horizontal_dist:
                        filtered_contours.append(c)
                        
                if not filtered_contours:
                    filtered_contours = [largest_contour]
            else:
                filtered_contours = contours
                
            all_points = np.vstack([c for c in filtered_contours])
            y_points = all_points[:, 0, 1]
            x_points = all_points[:, 0, 0]
            
            y_min = int(np.min(y_points))
            y_max = int(np.max(y_points))
            
            # Usar la escala vertical específica si existe, de lo contrario pixel_to_cm_ratio
            lateral_ratio = getattr(profile, 'lat_pixel_to_cm_ratio', None)
            if lateral_ratio is None or lateral_ratio <= 0:
                lateral_ratio = profile.pixel_to_cm_ratio
                
            if y_min < y_max:
                height_pixels = y_max - y_min
                height_cm = height_pixels * lateral_ratio
                
                # Diámetro de tallo basal
                has_stem = getattr(profile, 'has_stem', True)
                if has_stem and height_cm >= 0.5:
                    widths = []
                    valid_y = []
                    for offset in range(2, 12):
                        test_y = y_max - offset
                        if 0 <= test_y < h and mask is not None:
                            row_pixels = np.where(mask[test_y, :] > 0)[0]
                            if len(row_pixels) > 0:
                                if x_points is not None and len(x_points) > 0:
                                    min_x, max_x = np.min(x_points), np.max(x_points)
                                    row_pixels = row_pixels[(row_pixels >= min_x - 5) & (row_pixels <= max_x + 5)]
                                if len(row_pixels) > 0:
                                    w_px = np.max(row_pixels) - np.min(row_pixels)
                                    if 1 <= w_px < 70:
                                        widths.append(w_px)
                                        valid_y.append(test_y)
                    
                    if widths:
                        stem_width_pixels = np.median(widths)
                        stem_diameter_mm = stem_width_pixels * lateral_ratio * 10
                        stem_draw_y = int(np.median(valid_y))
                        stem_row_pixels = np.where(mask[stem_draw_y, :] > 0)[0] if mask is not None else None
                        
        return {
            "height_cm": round(height_cm, 2),
            "stem_diameter_mm": round(stem_diameter_mm, 2),
            "y_min": y_min,
            "y_max": y_max,
            "x_points": x_points,
            "stem_draw_y": stem_draw_y,
            "stem_row_pixels": stem_row_pixels,
            "filtered_contours": filtered_contours
        }
