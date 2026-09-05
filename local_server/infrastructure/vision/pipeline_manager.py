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
    Orquestador del pipeline de visión artificial agronómica.
    Utiliza Inyección de Dependencias para la estrategia de segmentación y calculadora biométrica.
    (SOLID: DIP, SRP, OCP)
    """
    
    def __init__(
        self, 
        segmentation_strategy: Optional[ISegmentationStrategy] = None,
        biometric_calculator: Optional[IBiometricCalculator] = None
    ):
        self.segmenter = segmentation_strategy or ExgSegmentationStrategy()
        self.calculator = biometric_calculator or BiometricCalculator()

    def process_cenital(self, image_path: str, output_path: str, profile: CropProfile) -> Optional[Dict[str, Any]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        mask = self.segmenter.create_mask(img, profile)
        contours = self.segmenter.extract_contours(mask, min_area=30)
        
        metrics = self.calculator.calculate_cenital(img, mask, contours, profile)
        
        overlay = img.copy()
        if contours:
            # Dibujar contornos foliares en ROJO puro
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
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        mask = self.segmenter.create_mask(img, profile, is_lateral=True)
        min_area = int(getattr(profile, 'lat_min_area', 60))
        contours = self.segmenter.extract_contours(mask, min_area=min_area)
        
        metrics = self.calculator.calculate_lateral(img, mask, contours, profile)
        plant_contours = metrics.get("filtered_contours", contours)
        
        overlay = img.copy()
        if plant_contours:
            # Dibujar perfil de la planta en ROJO únicamente sobre los contornos del cluster vegetal
            cv2.drawContours(overlay, plant_contours, -1, (0, 0, 255), 2)
            
            y_min = metrics.get("y_min")
            y_max = metrics.get("y_max")
            x_points = metrics.get("x_points")
            
            if y_min is not None and y_max is not None and y_min < y_max and x_points is not None and len(x_points) > 0:
                x_center = int(np.mean(x_points))
                cv2.line(overlay, (x_center - 15, y_min), (x_center + 15, y_min), (0, 255, 255), 2)
                cv2.line(overlay, (x_center - 15, y_max), (x_center + 15, y_max), (0, 255, 255), 2)
                cv2.line(overlay, (x_center, y_min), (x_center, y_max), (0, 255, 255), 2)
                
                cv2.putText(overlay, f"H: {metrics['height_cm']:.1f} cm", (x_center + 15, int((y_min + y_max)/2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
            if metrics.get("stem_draw_y") is not None and metrics.get("stem_row_pixels") is not None:
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
