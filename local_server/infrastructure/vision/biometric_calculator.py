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

    def calculate_lateral(self, image: np.ndarray, mask: np.ndarray, contours: List[np.ndarray], profile: CropProfile, config: Optional[Any] = None) -> Dict[str, Any]:
        h, w, _ = image.shape
        height_cm = 0.0
        stem_diameter_mm = 0.0
        stem_draw_y = None
        stem_row_pixels = None
        y_min = None
        y_max = None
        x_points = None
        filtered_contours = []
        
        # Obtener línea base calibrada si está configurada
        baseline_mode = getattr(config, 'lateral_baseline_mode', 'manual_baseline') if config else 'manual_baseline'
        calib_baseline_ratio = getattr(config, 'lateral_baseline_y', None) if config else None
        
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
            
            y_min = int(np.min(y_points)) # Punto más alto detectado por OpenCV
            
            # Determinar la base de la planta (y_max):
            if baseline_mode == 'manual_baseline' and calib_baseline_ratio is not None and 0.1 <= float(calib_baseline_ratio) <= 0.98:
                calib_baseline_px = int(h * float(calib_baseline_ratio))
                # La base es la línea calibrada
                y_max = calib_baseline_px
            else:
                y_max = int(np.max(y_points))
            
            # Usar la escala vertical específica si existe, de lo contrario pixel_to_cm_ratio
            lateral_ratio = getattr(profile, 'lat_pixel_to_cm_ratio', None)
            if lateral_ratio is None or lateral_ratio <= 0:
                lateral_ratio = profile.pixel_to_cm_ratio
                
            if y_min < y_max:
                height_pixels = y_max - y_min
                height_cm = height_pixels * lateral_ratio
                
        # 4. Medición Inteligente de Diámetro de Tallo en Zona/Cuadro ROI Basal
        has_stem = getattr(profile, 'has_stem', True)
        stem_mode = getattr(config, 'lateral_stem_mode', 'auto_edge') if config else 'auto_edge'
        stem_data = {
            "stem_diameter_mm": 0.0,
            "stem_box": None,
            "stem_x_left": None,
            "stem_x_right": None,
            "stem_y_mid": None
        }
        
        if has_stem and stem_mode != 'disabled':
            stem_data = self.measure_stem_in_roi(image, config=config, profile=profile)
            stem_diameter_mm = stem_data.get("stem_diameter_mm", 0.0)
                        
        return {
            "height_cm": round(height_cm, 2),
            "stem_diameter_mm": round(stem_diameter_mm, 2),
            "y_min": y_min,
            "y_max": y_max,
            "x_points": x_points,
            "stem_box": stem_data.get("stem_box"),
            "stem_x_left": stem_data.get("stem_x_left"),
            "stem_x_right": stem_data.get("stem_x_right"),
            "stem_y_mid": stem_data.get("stem_y_mid"),
            "filtered_contours": filtered_contours
        }

    def measure_stem_in_roi(self, image: np.ndarray, config: Optional[Any], profile: CropProfile) -> Dict[str, Any]:
        """
        Escanea la franja/cuadro interactivo de la base del tallo para medir su calibre
        utilizando análisis de gradiente horizontal (bordes del cilindro) e intensidad,
        independiente de si el tallo es verde, café, leñoso u oliva.
        """
        h, w = image.shape[:2]
        
        # Parámetros del ROI de tallo
        stem_roi_x = getattr(config, 'lateral_stem_roi_x', 0.5000) if config else 0.5000
        stem_roi_y = getattr(config, 'lateral_stem_roi_y', 0.6600) if config else 0.6600
        stem_roi_w = getattr(config, 'lateral_stem_roi_width', 0.2000) if config else 0.2000
        stem_roi_h = getattr(config, 'lateral_stem_roi_height', 0.0500) if config else 0.0500
        
        cx = int(w * float(stem_roi_x))
        cy = int(h * float(stem_roi_y))
        box_w = max(24, int(w * float(stem_roi_w)))
        box_h = max(10, int(h * float(stem_roi_h)))
        
        x1 = max(0, cx - box_w // 2)
        x2 = min(w, cx + box_w // 2)
        y1 = max(0, cy - box_h // 2)
        y2 = min(h, cy + box_h // 2)
        
        lateral_ratio = getattr(profile, 'lat_pixel_to_cm_ratio', None)
        if lateral_ratio is None or lateral_ratio <= 0:
            lateral_ratio = profile.pixel_to_cm_ratio
            
        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            return {
                "stem_diameter_mm": 0.0,
                "stem_box": (x1, y1, x2, y2),
                "stem_x_left": None,
                "stem_x_right": None,
                "stem_y_mid": cy
            }
            
        # 1. Convertir a escala de grises y suavizar para reducir ruido de impresión 3D
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 2. Gradiente Horizontal Sobel (resalta las dos paredes verticales del tallo cilíndrico)
        grad_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        abs_grad_x = np.abs(grad_x)
        
        detected_widths = []
        detected_lefts = []
        detected_rights = []
        detected_ys = []
        
        roi_mid = (x2 - x1) // 2
        
        for r in range(roi.shape[0]):
            actual_y = y1 + r
            row_profile = abs_grad_x[r, :]
            
            # Buscar el pico de gradiente más fuerte a la izquierda del centro
            left_half = row_profile[:roi_mid]
            right_half = row_profile[roi_mid:]
            
            if len(left_half) > 3 and len(right_half) > 3:
                left_idx = np.argmax(left_half)
                right_idx = roi_mid + np.argmax(right_half)
                
                width_px = right_idx - left_idx
                # Validar que el ancho detectado sea razonable para un tallo botánico (ej: 4 a 60 px)
                if 4 <= width_px <= int((x2 - x1) * 0.85):
                    if row_profile[left_idx] > 6 and row_profile[right_idx] > 6:
                        detected_widths.append(width_px)
                        detected_lefts.append(x1 + left_idx)
                        detected_rights.append(x1 + right_idx)
                        detected_ys.append(actual_y)
                        
        if detected_widths:
            median_width = float(np.median(detected_widths))
            stem_diameter_mm = median_width * lateral_ratio * 10.0 # Conversión de cm a mm
            stem_x_left = int(np.median(detected_lefts))
            stem_x_right = int(np.median(detected_rights))
            stem_y_mid = int(np.median(detected_ys))
        else:
            # Umbralización adaptativa como respaldo en caso de bajo contraste
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if cnts:
                best_c = max(cnts, key=cv2.contourArea)
                bx, by, bw, bh = cv2.boundingRect(best_c)
                if 4 <= bw <= int((x2 - x1) * 0.85):
                    median_width = float(bw)
                    stem_diameter_mm = median_width * lateral_ratio * 10.0
                    stem_x_left = x1 + bx
                    stem_x_right = x1 + bx + bw
                    stem_y_mid = y1 + by + bh // 2
                else:
                    stem_diameter_mm = 0.0
                    stem_x_left = None
                    stem_x_right = None
                    stem_y_mid = cy
            else:
                stem_diameter_mm = 0.0
                stem_x_left = None
                stem_x_right = None
                stem_y_mid = cy
                
        return {
            "stem_diameter_mm": round(stem_diameter_mm, 2),
            "stem_box": (x1, y1, x2, y2),
            "stem_x_left": stem_x_left,
            "stem_x_right": stem_x_right,
            "stem_y_mid": stem_y_mid
        }
