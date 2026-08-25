import os
import cv2
import numpy as np

from .segmentation import ImageSegmenter
from .metrics import BiometricCalculator
from .fruit_detector import FruitDetector

class VisionPipelineManager:
    """
    Orquestador principal del pipeline de visión computacional.
    Procesa imágenes cenitales y laterales y dibuja la cobertura foliar en ROJO.
    """
    
    @staticmethod
    def process_cenital_image(image_path, output_path, profile):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        mask = ImageSegmenter.create_foliage_mask(img, profile)
        contours = ImageSegmenter.extract_valid_contours(mask, min_area=30)
        
        metrics = BiometricCalculator.calculate_cenital_metrics(img, mask, contours, profile)
        
        overlay = img.copy()
        if contours:
            # 1. Dibujar todos los contornos del área foliar en ROJO PURO (0, 0, 255 en BGR)
            cv2.drawContours(overlay, contours, -1, (0, 0, 255), 2)
            
            # 2. Dibujar el cerco exterior / Envoltura convexa de la canopia en ROJO DESTACADO
            all_pts = np.vstack(contours)
            if len(all_pts) >= 3:
                hull = cv2.convexHull(all_pts)
                cv2.drawContours(overlay, [hull], -1, (0, 0, 255), 2)
            
        fruits_count = FruitDetector.detect_fruits(img, overlay)
        metrics["fruits_count"] = fruits_count
        metrics["spots_count"] = 0
        
        # Superponer leyenda de métricas en color destacado (Rojo / Amarillo / Blanco)
        cv2.putText(overlay, f"Area Foliar: {metrics['area_cm2']:.1f} cm2", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(overlay, f"Salud Foliar: {metrics['health_index']:.1f}%", (20, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        if fruits_count > 0:
            cv2.putText(overlay, f"Frutos: {fruits_count}", (20, 110), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                        
        cv2.imwrite(output_path, overlay)
        return metrics

    @staticmethod
    def process_lateral_image(image_path, output_path, profile):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        mask = ImageSegmenter.create_foliage_mask(img, profile)
        contours = ImageSegmenter.extract_valid_contours(mask, min_area=30)
        
        metrics = BiometricCalculator.calculate_lateral_metrics(img, mask, contours, profile)
        
        overlay = img.copy()
        if contours:
            # Dibujar el perfil de la planta en ROJO (0, 0, 255)
            cv2.drawContours(overlay, contours, -1, (0, 0, 255), 2)
            
            y_min = metrics["y_min"]
            y_max = metrics["y_max"]
            x_points = metrics["x_points"]
            
            if y_min is not None and y_max is not None and y_min < y_max:
                x_center = int((np.min(x_points) + np.max(x_points)) / 2)
                cv2.line(overlay, (x_center - 15, y_min), (x_center + 15, y_min), (0, 255, 255), 2)
                cv2.line(overlay, (x_center - 15, y_max), (x_center + 15, y_max), (0, 255, 255), 2)
                cv2.line(overlay, (x_center, y_min), (x_center, y_max), (0, 255, 255), 2)
                
                cv2.putText(overlay, f"H: {metrics['height_cm']:.1f} cm", (x_center + 15, int((y_min + y_max)/2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
            if metrics["stem_draw_y"] is not None and metrics["stem_row_pixels"] is not None:
                draw_y = metrics["stem_draw_y"]
                row_pixels = metrics["stem_row_pixels"]
                if len(row_pixels) > 0:
                    cv2.line(overlay, (np.min(row_pixels), draw_y), (np.max(row_pixels), draw_y), (0, 0, 255), 3)
                    cv2.circle(overlay, (np.min(row_pixels), draw_y), 5, (0, 0, 255), -1)
                    cv2.circle(overlay, (np.max(row_pixels), draw_y), 5, (0, 0, 255), -1)
                    cv2.putText(overlay, f"D: {metrics['stem_diameter_mm']:.1f} mm", (np.max(row_pixels) + 15, draw_y + 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                
        cv2.imwrite(output_path, overlay)
        return {
            "plant_height_cm": metrics["height_cm"],
            "stem_diameter_mm": metrics["stem_diameter_mm"]
        }

    @staticmethod
    def filter_and_average_metrics(cenital_results, lateral_results):
        """
        Elimina valores atípicos (+- 2 desviaciones estándar) y calcula promedios del lote.
        """
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
            areas = [r["area_cm2"] for r in cenital_results]
            healths = [r["health_index"] for r in cenital_results]
            compacities = [r["compacity_index"] for r in cenital_results]
            fruits = [r["fruits_count"] for r in cenital_results]
            
            final_metrics["foliar_area_cm2"] = round(get_robust_mean(areas), 2)
            final_metrics["health_index"] = round(get_robust_mean(healths), 2)
            final_metrics["compacity_index"] = round(get_robust_mean(compacities), 3)
            final_metrics["fruits_count"] = int(np.round(np.median(fruits)))
            
        if lateral_results:
            heights = [r["plant_height_cm"] for r in lateral_results]
            diameters = [r["stem_diameter_mm"] for r in lateral_results]
            
            final_metrics["plant_height_cm"] = round(get_robust_mean(heights), 2)
            final_metrics["stem_diameter_mm"] = round(get_robust_mean(diameters), 2)
            
        return final_metrics
