import os
from typing import List, Dict, Any, Optional, Tuple
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
    def is_cenital_inverted(img: np.ndarray) -> bool:
        """
        Detecta si la foto cenital está de cabeza (al revés con la base del tubo abajo).
        Si la base azul está abajo, retorna True para requerir rotación de 180°.
        """
        h, w = img.shape[:2]
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_blue = cv2.inRange(hsv, np.array([95, 50, 40]), np.array([135, 255, 255]))
        col_w_start, col_w_end = int(w * 0.40), int(w * 0.60)
        top_blue = cv2.countNonZero(mask_blue[:int(h * 0.20), col_w_start:col_w_end])
        bottom_blue = cv2.countNonZero(mask_blue[int(h * 0.80):, col_w_start:col_w_end])
        return bottom_blue > top_blue

    @staticmethod
    def orient_lateral_upright(img: np.ndarray) -> np.ndarray:
        """
        Asegura que la foto lateral quede con orientación vertical perfecta:
        canastilla azul con arlita en la base inferior y planta creciendo erguida hacia arriba.
        """
        h, w = img.shape[:2]
        # 1. Si está en formato horizontal (sensor apaisado), rotar a vertical
        if w > h:
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            h, w = img.shape[:2]

        # 2. Verificar que la arlita (sustrato de cultivo) esté en la mitad inferior
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_arlita = cv2.inRange(hsv, np.array([5, 60, 40]), np.array([22, 255, 180]))
        pts = np.argwhere(mask_arlita > 0)

        if len(pts) > 500:
            mean_y = np.mean(pts[:, 0])
            # Si el sustrato está en la mitad superior (mean_y < h/2), la planta está de cabeza -> rotar 180°
            if mean_y < (h / 2.0):
                img = cv2.rotate(img, cv2.ROTATE_180)

        return img

    @staticmethod
    def detect_blue_basket_roi(image: np.ndarray) -> tuple:
        """
        Detecta con precisión sub-milimétrica la canastilla circular azul individual donde
        está plantado el cultivo activo, aislando arlita y follaje, anulando el fondo de laboratorio.
        Retorna: (centro_x, centro_y, radio)
        """
        h_img, w_img = image.shape[:2]
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 1. Segmentación de vegetación activa
        lower_green = np.array([25, 30, 30])
        upper_green = np.array([88, 255, 255])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        
        b, g, r = cv2.split(image.astype(np.float32))
        exg = 2.0 * g - r - b
        exg_mask = np.uint8((exg > 15) & (g > r) & (g > b)) * 255
        plant_mask = cv2.bitwise_or(mask_green, exg_mask)
        
        # 2. Segmentación estricta del plástico azul de la canastilla
        lower_blue = np.array([95, 50, 40])
        upper_blue = np.array([135, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Kernel elíptico moderado para mantener la individualidad del aro
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_blue_clean = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
        mask_blue_clean = cv2.morphologyEx(mask_blue_clean, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask_blue_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Rango exacto del radio de una canastilla azul individual (~10% a 14% de la altura)
        min_radius = int(min(w_img, h_img) * 0.08)
        max_radius = int(min(w_img, h_img) * 0.15)
        candidates = []
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < 3000 or area > 600000:
                continue
                
            (cx, cy), radius = cv2.minEnclosingCircle(c)
            radius = int(radius)
            if radius < min_radius or radius > max_radius:
                continue
                
            peri = cv2.arcLength(c, True)
            circularity = (4 * np.pi * area) / (peri * peri) if peri > 0 else 0
            
            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = float(bw) / float(bh) if bh > 0 else 0
            
            # Solo evaluar canastillas ubicadas en la columna central de la torre
            if not (w_img * 0.38 <= cx <= w_img * 0.62 and h_img * 0.30 <= cy <= h_img * 0.60):
                continue
                
            c_mask = np.zeros((h_img, w_img), dtype=np.uint8)
            cv2.circle(c_mask, (int(cx), int(cy)), radius, 255, -1)
            green_inside = cv2.countNonZero(cv2.bitwise_and(plant_mask, c_mask))
            
            # Puntuación agrónoma:
            # - Máxima presencia de planta
            # - Circularidad geométrica
            # - Relación de aspecto ~ 1.0 (aro circular)
            aspect_diff = abs(1.0 - aspect_ratio)
            score = (green_inside * 4.0) + (circularity * 3000.0) - (aspect_diff * 800.0)
            
            candidates.append({
                'cx': int(cx), 'cy': int(cy), 'radius': radius,
                'green_inside': green_inside, 'score': score
            })
            
        if candidates:
            best = max(candidates, key=lambda k: k['score'])
    def detect_blue_basket_roi(self, img: np.ndarray, config: Optional[Any] = None) -> Tuple[int, int, int]:
        """
        Calcula el ROI cenital. Si el usuario configuró coordenadas personalizadas en Config,
        las utiliza; de lo contrario busca el aro azul automáticamente con fallback agrónomo.
        """
        h_img, w_img = img.shape[:2]
        
        # 1. Si hay configuración explícita guardada por el usuario
        if config is not None:
            cx_ratio = getattr(config, 'cenital_roi_cx', None)
            cy_ratio = getattr(config, 'cenital_roi_cy', None)
            rad_ratio = getattr(config, 'cenital_roi_radius', None)
            if cx_ratio is not None and cy_ratio is not None and rad_ratio is not None:
                cx = int(w_img * float(cx_ratio))
                cy = int(h_img * float(cy_ratio))
                radius = int(min(w_img, h_img) * float(rad_ratio))
                return cx, cy, radius

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_blue = cv2.inRange(hsv, np.array([90, 45, 30]), np.array([140, 255, 255]))
        plant_mask = self.segmenter.create_mask(img, CropProfile(crop_type="detect", display_name="detect"))
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_blue_clean = cv2.morphologyEx(mask_blue, cv2.MORPH_OPEN, kernel)
        mask_blue_clean = cv2.morphologyEx(mask_blue_clean, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask_blue_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_radius = int(min(w_img, h_img) * 0.08)
        max_radius = int(min(w_img, h_img) * 0.18)
        candidates = []
        
        for c in contours:
            area = cv2.contourArea(c)
            if area < 3000 or area > 600000:
                continue
                
            (cx, cy), radius = cv2.minEnclosingCircle(c)
            radius = int(radius)
            if radius < min_radius or radius > max_radius:
                continue
                
            peri = cv2.arcLength(c, True)
            circularity = (4 * np.pi * area) / (peri * peri) if peri > 0 else 0
            
            bx, by, bw, bh = cv2.boundingRect(c)
            aspect_ratio = float(bw) / float(bh) if bh > 0 else 0
            
            if not (w_img * 0.35 <= cx <= w_img * 0.65 and h_img * 0.28 <= cy <= h_img * 0.62):
                continue
                
            c_mask = np.zeros((h_img, w_img), dtype=np.uint8)
            cv2.circle(c_mask, (int(cx), int(cy)), radius, 255, -1)
            green_inside = cv2.countNonZero(cv2.bitwise_and(plant_mask, c_mask))
            
            aspect_diff = abs(1.0 - aspect_ratio)
            score = (green_inside * 4.0) + (circularity * 3000.0) - (aspect_diff * 800.0)
            
            candidates.append({
                'cx': int(cx), 'cy': int(cy), 'radius': radius,
                'green_inside': green_inside, 'score': score
            })
            
        if candidates:
            best = max(candidates, key=lambda k: k['score'])
            return best['cx'], best['cy'], int(best['radius'] * 1.05)
            
        # Calibración agrónoma física central por defecto
        calib_cx = int(w_img * 0.4955)
        calib_cy = int(h_img * 0.4408)
        calib_radius = int(min(w_img, h_img) * 0.145)
        return calib_cx, calib_cy, calib_radius

    def process_cenital(self, image_path: str, output_path: str, profile: CropProfile, config: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            return None

        # 1. Rotación de 180° antes de procesar si está al revés
        if self.is_cenital_inverted(img_raw):
            img = cv2.rotate(img_raw, cv2.ROTATE_180)
            cv2.imwrite(image_path, img)
        else:
            img = img_raw

        h_img, w_img = img.shape[:2]

        # 2. Obtención de centro y radio del ROI (Manual o Automático)
        cx, cy, radius = self.detect_blue_basket_roi(img, config=config)
        roi_mode = getattr(config, 'cenital_roi_mode', 'dynamic_conn') if config else 'dynamic_conn'
        
        roi_mask = np.zeros((h_img, w_img), dtype=np.uint8)
        cv2.circle(roi_mask, (cx, cy), radius, 255, -1)

        # 3. Segmentación foliar
        raw_leaf_mask = self.segmenter.create_mask(img, profile)
        
        # Filtro Inteligente de Componentes Conectados (Filtro Anti-Plantas Vecinas)
        if roi_mode == 'dynamic_conn':
            # Aplicar ROI amplio y filtrar islas desconectadas que pertenezcan a otras canastillas
            bounded_leaf = cv2.bitwise_and(raw_leaf_mask, roi_mask)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bounded_leaf, connectivity=8)
            
            # Centroide de la canastilla
            target_mask = np.zeros_like(bounded_leaf)
            inner_core_radius = max(15, int(radius * 0.45))
            
            for label_idx in range(1, num_labels):
                area = stats[label_idx, cv2.CC_STAT_AREA]
                if area < 25:
                    continue
                comp_mask = (labels == label_idx).astype(np.uint8)
                
                # Verificar si el componente toca el núcleo central de la canastilla
                # o está lo suficientemente cerca del centro
                dist_to_center = np.sqrt((centroids[label_idx][0] - cx)**2 + (centroids[label_idx][1] - cy)**2)
                
                # Si está dentro del rango o toca la zona central
                comp_core_overlap = cv2.countNonZero(cv2.bitwise_and(comp_mask, cv2.circle(np.zeros_like(comp_mask), (cx, cy), inner_core_radius, 255, -1)))
                
                if comp_core_overlap > 0 or dist_to_center <= (radius * 0.85):
                    target_mask = cv2.bitwise_or(target_mask, comp_mask * 255)
                    
            mask = target_mask if cv2.countNonZero(target_mask) > 0 else bounded_leaf
        else:
            mask = cv2.bitwise_and(raw_leaf_mask, roi_mask)
            
        contours = self.segmenter.extract_contours(mask, min_area=25)
        
        # 4. Cálculo de Biometría Foliar
        metrics = self.calculator.calculate_cenital(img, mask, contours, profile)
        
        # 5. Generación de Overlay de visualización
        overlay = img.copy()
        
        # Dibujar círculo de delimitación del ROI
        cv2.circle(overlay, (cx, cy), radius, (255, 180, 0), 3)  # Círculo cian/azul claro
        # Cruz central de anclaje
        cross_len = 16
        cv2.line(overlay, (cx - cross_len, cy), (cx + cross_len, cy), (0, 255, 0), 2)
        cv2.line(overlay, (cx, cy - cross_len), (cx, cy + cross_len), (0, 255, 0), 2)
        
        cv2.putText(overlay, "ROI", (max(20, cx - 100), max(30, cy - radius - 12)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 180, 0), 2)

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

    def process_lateral(self, image_path: str, output_path: str, profile: CropProfile, config: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img_raw = cv2.imread(image_path)
        if img_raw is None:
            return None

        # 1. Orientación vertical erguida antes de procesar
        img = self.orient_lateral_upright(img_raw)
        cv2.imwrite(image_path, img)

        h, w = img.shape[:2]
            
        # 2. Segmentación botánica lateral de tallos y hojas
        mask = self.segmenter.create_mask(img, profile, is_lateral=True)
        min_area = int(getattr(profile, 'lat_min_area', 30))
        contours = self.segmenter.extract_contours(mask, min_area=min_area)
        
        # 3. Cálculo de altura vertical y diámetro basal de tallo
        metrics = self.calculator.calculate_lateral(img, mask, contours, profile, config=config)
        plant_contours = metrics.get("filtered_contours", contours)
        
        overlay = img.copy()
        
        # Dibujar la línea base horizontal calibrada de la maceta (en rojo/cian neón)
        baseline_ratio = getattr(config, 'lateral_baseline_y', 0.72) if config else 0.72
        baseline_px = int(h * float(baseline_ratio))
        cv2.line(overlay, (0, baseline_px), (w, baseline_px), (0, 0, 255), 2)
        cv2.putText(overlay, "LINEA BASE MACETA", (15, max(25, baseline_px - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        
        if plant_contours:
            draw_contours = getattr(profile, 'lat_draw_contours', False)
            if draw_contours:
                # Dibujar contornos en ROJO sobre tallos y hojas solo si está habilitado
                cv2.drawContours(overlay, plant_contours, -1, (0, 0, 255), 2)
            
            y_min = metrics.get("y_min")  # Ápice foliar superior (detectado por OpenCV)
            y_max = metrics.get("y_max", baseline_px)  # Base calibrada de la planta
            x_points = metrics.get("x_points")
            
            if y_min is not None and y_max is not None and y_min < y_max and x_points is not None and len(x_points) > 0:
                x_center = int(np.mean(x_points))
                
                # Línea de medición vertical completa desde la base hasta la punta más alta
                cv2.line(overlay, (x_center - 25, y_min), (x_center + 25, y_min), (0, 255, 255), 2)
                cv2.line(overlay, (x_center - 25, y_max), (x_center + 25, y_max), (0, 255, 255), 2)
                cv2.line(overlay, (x_center, y_min), (x_center, y_max), (0, 255, 255), 2)
                
                # Etiqueta de altura
                cv2.putText(overlay, f"H: {metrics['height_cm']:.1f} cm", (x_center + 15, int((y_min + y_max)/2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
                
            # 4. Dibujar Cuadro ROI de Tallo y Medición de Diámetro
            stem_box = metrics.get("stem_box")
            stem_x_left = metrics.get("stem_x_left")
            stem_x_right = metrics.get("stem_x_right")
            stem_y_mid = metrics.get("stem_y_mid")
            stem_d = metrics.get("stem_diameter_mm", 0.0)

            if stem_box:
                bx1, by1, bx2, by2 = stem_box
                # Dibujar recuadro de la zona de escaneo en naranja/ámbar
                cv2.rectangle(overlay, (bx1, by1), (bx2, by2), (255, 165, 0), 1)
                cv2.putText(overlay, "SCAN TALLO", (bx1, max(18, by1 - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 165, 0), 1)
                
            if stem_x_left is not None and stem_x_right is not None and stem_d > 0 and stem_y_mid is not None:
                # Línea de medición de calibre del tallo con topes verticales
                cv2.line(overlay, (stem_x_left, stem_y_mid), (stem_x_right, stem_y_mid), (0, 255, 255), 2)
                cv2.line(overlay, (stem_x_left, stem_y_mid - 4), (stem_x_left, stem_y_mid + 4), (0, 255, 255), 2)
                cv2.line(overlay, (stem_x_right, stem_y_mid - 4), (stem_x_right, stem_y_mid + 4), (0, 255, 255), 2)
                cv2.putText(overlay, f"D: {stem_d:.1f} mm", (bx2 + 8 if stem_box else stem_x_right + 12, stem_y_mid + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                                
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
