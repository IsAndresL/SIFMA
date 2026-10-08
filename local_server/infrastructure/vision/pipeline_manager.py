import os
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from domain.models import CropProfile
from domain.interfaces.vision import ISegmentationStrategy, IBiometricCalculator
from infrastructure.vision.strategies.exg_segmentation import ExgSegmentationStrategy
from infrastructure.vision.biometric_calculator import BiometricCalculator

class VisionPipelineManager:
    """
    Orquestador del pipeline de visión artificial agronómica SIFMA.
    - Corrige orientación física de las cámaras (Cenital 180° / Lateral 90° derecha).
    - Aplica ROI circular automático sobre la canastilla azul (anula personas, ropa y fondo).
    - Mide altura y tallo basal con precisión milimétrica desde la base del sustrato.
    """
    
    def __init__(
        self, 
        segmentation_strategy: Optional[ISegmentationStrategy] = None,
        biometric_calculator: Optional[IBiometricCalculator] = None
    ):
        self.segmenter = segmentation_strategy or ExgSegmentationStrategy()
        self.calculator = biometric_calculator or BiometricCalculator()

    @staticmethod
    def detect_blue_basket_roi(image: np.ndarray) -> tuple:
        """
        Detecta con precisión agrónoma la canastilla circular azul que contiene la planta,
        discriminando el tubo estructural superior y elementos del fondo.
        Retorna: (centro_x, centro_y, radio)
        """
        h_img, w_img = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 1. Segmentación previa de vegetación para priorizar la canastilla activa que contiene la planta
        lower_green = np.array([25, 30, 30])
        upper_green = np.array([88, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        b, g, r = cv2.split(image.astype(np.float32))
        exg = 2.0 * g - r - b
        exg_mask = np.uint8((exg > 15) & (g > r) & (g > b)) * 255
        plant_mask = cv2.bitwise_or(mask_green, exg_mask)
        
        # 2. Segmentación del color azul de la canastilla
        lower_blue = np.array([90, 45, 35])
        upper_blue = np.array([140, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask_blue_clean = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
        mask_blue_clean = cv2.morphologyEx(mask_blue_clean, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask_blue_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_radius = int(min(w_img, h_img) * 0.05)
        max_radius = int(min(w_img, h_img) * 0.45)
        candidates = []
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < 400:
                continue
                
            (cx, cy), radius = cv2.minEnclosingCircle(c)
            radius = int(radius)
            if radius < min_radius or radius > max_radius:
                continue
                
            peri = cv2.arcLength(c, True)
            circularity = (4 * np.pi * area) / (peri * peri) if peri > 0 else 0
            
            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = float(bw) / float(bh) if bh > 0 else 0
            
            # Conteo de píxeles de planta dentro del círculo candidato
            c_mask = np.zeros((h_img, w_img), dtype=np.uint8)
            cv2.circle(c_mask, (int(cx), int(cy)), radius, 255, -1)
            green_inside = cv2.countNonZero(cv2.bitwise_and(plant_mask, c_mask))
            
            # Puntuación agronómica:
            # - Máxima prioridad a la presencia de planta dentro del círculo
            # - Regularidad geométrica circular (aspect_ratio ~ 1.0 y circularidad alta)
            # - Penalización al tubo superior estructural (sin planta y pegado al borde superior)
            aspect_diff = abs(1.0 - aspect_ratio)
            score = (green_inside * 5.0) + (circularity * 300.0) - (aspect_diff * 150.0)
            
            if cy > h_img * 0.30:
                score += 200.0
            if by < h_img * 0.08:
                score -= 500.0
                
            candidates.append({
                'cx': int(cx), 'cy': int(cy), 'radius': radius,
                'green_inside': green_inside, 'score': score
            })
            
        if candidates:
            best = max(candidates, key=lambda k: k['score'])
            return best['cx'], best['cy'], int(best['radius'] * 1.03)
            
        # Fallback si no se detecta contorno: zona central
        return w_img // 2, int(h_img * 0.60), int(min(w_img, h_img) * 0.22)

    def process_cenital(self, image_path: str, output_path: str, profile: CropProfile) -> Optional[Dict[str, Any]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            return None

        # 1. Rotación de 180° para orientación superior en local_server
        img = cv2.rotate(img_raw, cv2.ROTATE_180)
        cv2.imwrite(image_path, img)

        h_img, w_img = img.shape[:2]

        # 2. Detección automática del ROI de la Canastilla Azul donde está la planta
        cx, cy, radius = self.detect_blue_basket_roi(img)
        
        roi_mask = np.zeros((h_img, w_img), dtype=np.uint8)
        cv2.circle(roi_mask, (cx, cy), radius, 255, -1)

        # 3. Segmentación foliar y aplicación estricta del ROI (anula personas, ropa y fondo exterior)
        raw_leaf_mask = self.segmenter.create_mask(img, profile)
        mask = cv2.bitwise_and(raw_leaf_mask, roi_mask)
        contours = self.segmenter.extract_contours(mask, min_area=25)
        
        # 4. Cálculo de Biometría Foliar
        metrics = self.calculator.calculate_cenital(img, mask, contours, profile)
        
        # 5. Generación de Overlay de visualización
        overlay = img.copy()
        
        # Dibujar círculo de delimitación de la Canastilla Azul (ROI)
        cv2.circle(overlay, (cx, cy), radius, (255, 180, 0), 2)  # Círculo azul claro/cian
        cv2.putText(overlay, "CANASTILLA AZUL (ROI)", (max(20, cx - 110), max(30, cy - radius - 10)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 180, 0), 2)

        if contours:
            # Dibujar contornos foliares en ROJO puro dentro de la canastilla
            cv2.drawContours(overlay, contours, -1, (0, 0, 255), 2)
            
            # Envoltura convexa de la canopia
            all_pts = np.vstack(contours)
            if len(all_pts) >= 3:
                hull = cv2.convexHull(all_pts)
                cv2.drawContours(overlay, [hull], -1, (0, 0, 255), 2)
            
        metrics["fruits_count"] = 0
        metrics["spots_count"] = 0
        
        # Superponer leyenda de métricas biométricas
        cv2.putText(overlay, f"Area Foliar: {metrics['area_cm2']:.1f} cm2", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(overlay, f"Salud Foliar: {metrics['health_index']:.1f}%", (20, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
        cv2.imwrite(output_path, overlay)
        return metrics

    def process_lateral(self, image_path: str, output_path: str, profile: CropProfile) -> Optional[Dict[str, Any]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            return None

        # 1. Rotación de 90 grados a la derecha (sentido horario) para orientación vertical correcta
        img = cv2.rotate(img_raw, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite(image_path, img)

        h, w = img.shape[:2]
            
        # 2. Segmentación botánica lateral de tallos y hojas
        mask = self.segmenter.create_mask(img, profile, is_lateral=True)
        min_area = int(getattr(profile, 'lat_min_area', 30))
        contours = self.segmenter.extract_contours(mask, min_area=min_area)
        
        # 3. Cálculo de altura vertical y diámetro basal de tallo
        metrics = self.calculator.calculate_lateral(img, mask, contours, profile)
        plant_contours = metrics.get("filtered_contours", contours)
        
        overlay = img.copy()
        if plant_contours:
            # Dibujar contornos en ROJO sobre tallos y hojas
            cv2.drawContours(overlay, plant_contours, -1, (0, 0, 255), 2)
            
            y_min = metrics.get("y_min")  # Ápice foliar superior
            y_max = metrics.get("y_max")  # Base del tallo en el sustrato
            x_points = metrics.get("x_points")
            
            if y_min is not None and y_max is not None and y_min < y_max and x_points is not None and len(x_points) > 0:
                x_center = int(np.mean(x_points))
                
                # Línea de medición vertical completa desde la base hasta la punta
                cv2.line(overlay, (x_center - 20, y_min), (x_center + 20, y_min), (0, 255, 255), 2)
                cv2.line(overlay, (x_center - 20, y_max), (x_center + 20, y_max), (0, 255, 255), 2)
                cv2.line(overlay, (x_center, y_min), (x_center, y_max), (0, 255, 255), 2)
                
                # Etiqueta de altura
                cv2.putText(overlay, f"H: {metrics['height_cm']:.1f} cm", (x_center + 15, int((y_min + y_max)/2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
                
            if metrics.get("stem_draw_y") is not None and metrics.get("stem_row_pixels") is not None:
                draw_y = metrics["stem_draw_y"]
                row_pixels = metrics["stem_row_pixels"]
                if len(row_pixels) > 0:
                    cv2.line(overlay, (np.min(row_pixels), draw_y), (np.max(row_pixels), draw_y), (0, 0, 255), 3)
                    cv2.circle(overlay, (np.min(row_pixels), draw_y), 4, (0, 0, 255), -1)
                    cv2.circle(overlay, (np.max(row_pixels), draw_y), 4, (0, 0, 255), -1)
                    cv2.putText(overlay, f"D: {metrics['stem_diameter_mm']:.1f} mm", (np.max(row_pixels) + 15, draw_y + 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
                                
        cv2.imwrite(output_path, overlay)
        return {
            "plant_height_cm": metrics.get("height_cm", 0.0),
            "stem_diameter_mm": metrics.get("stem_diameter_mm", 0.0)
        }

    @staticmethod
    def filter_and_average(cenital_results: List[Dict[str, Any]], lateral_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Elimina valores atípicos (+- 2 desviaciones estándar) y calcula medias robustas del lote."""
        final_metrics = {
            "foliar_area_cm2": 0.0,
            "health_index": 100.0,
            "compacity_index": 0.0,
            "spots_count": 0,
            "fruits_count": 0,
            "plant_height_cm": 0.0,
            "stem_diameter_mm": 0.0
        }
        
        def get_robust_mean(data_list):
            if not data_list: return 0.0
            if len(data_list) <= 2: return float(np.mean(data_list))
            mean = float(np.mean(data_list))
            std = float(np.std(data_list))
            if std == 0: return mean
            filtered = [x for x in data_list if abs(x - mean) <= 2 * std]
            return float(np.mean(filtered)) if filtered else mean

        if cenital_results:
            areas = [r.get("area_cm2", 0.0) for r in cenital_results]
            healths = [r.get("health_index", 100.0) for r in cenital_results]
            compacities = [r.get("compacity_index", 0.0) for r in cenital_results]
            
            final_metrics["foliar_area_cm2"] = round(get_robust_mean(areas), 2)
            final_metrics["health_index"] = round(get_robust_mean(healths), 2)
            final_metrics["compacity_index"] = round(get_robust_mean(compacities), 3)
            
        if lateral_results:
            heights = [r.get("plant_height_cm", 0.0) for r in lateral_results]
            diameters = [r.get("stem_diameter_mm", 0.0) for r in lateral_results]
            
            final_metrics["plant_height_cm"] = round(get_robust_mean(heights), 2)
            final_metrics["stem_diameter_mm"] = round(get_robust_mean(diameters), 2)
            
        return final_metrics
