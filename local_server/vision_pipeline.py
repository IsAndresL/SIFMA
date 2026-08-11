import os
import cv2
import numpy as np

# Intentar importar plantcv para flujos avanzados si está disponible
HAS_PLANTCV = False
try:
    from plantcv import plantcv as pcv
    # Configurar pcv para que no muestre plots interactivos
    pcv.params.debug = None
    HAS_PLANTCV = True
except ImportError:
    pass



def ensure_dir(path):
    """Asegura que el directorio exista."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def process_cenital_image(image_path, output_path, profile):
    """
    Procesa una imagen cenital para calcular:
    - Área foliar (cm²)
    - Índice de salud cromática (%)
    - Índice de compacidad
    - Número de manchas (lesiones foliares)
    """
    ensure_dir(output_path)
    
    # 1. Leer imagen
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: No se pudo leer la imagen cenital {image_path}")
        return None
        
    h, w, _ = img.shape
    
    # 2. Conversión de espacios de color necesarios para salud y frutos
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    # Aplicar segmentación según Perfil de Color (HSV + LAB)
    # Rango HSV
    lower_hsv = np.array([profile.h_min, profile.s_min, profile.v_min])
    upper_hsv = np.array([profile.h_max, profile.s_max, profile.v_max])
    mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
    
    # Rango LAB
    lower_lab = np.array([profile.l_min, profile.a_min, profile.b_min])
    upper_lab = np.array([profile.l_max, profile.a_max, profile.b_max])
    mask_lab = cv2.inRange(lab, lower_lab, upper_lab)
    
    # Combinar máscaras
    mask = cv2.bitwise_and(mask_hsv, mask_lab)
    
    # Operaciones morfológicas para limpiar ruido (Opening/Closing)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 5. Detección de contornos de la planta
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    plant_pixels = 0
    compacity = 0.0
    perimeter = 0.0
    
    # Filtrar contornos muy pequeños (ruido < 150 px)
    valid_contours = [c for c in contours if cv2.contourArea(c) > 150]
    
    # Clon de imagen para dibujar el overlay
    overlay = img.copy()
    
    if valid_contours:
        # Sumar el área de todos los contornos válidos de la planta
        plant_pixels = sum(cv2.contourArea(c) for c in valid_contours)
        
        # Dibujar los contornos en verde vibrante
        cv2.drawContours(overlay, valid_contours, -1, (0, 255, 0), 2)
        
        # Obtener el contorno más grande para calcular compacidad
        largest_contour = max(valid_contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(largest_contour, True)
        largest_area = cv2.contourArea(largest_contour)
        
        if perimeter > 0:
            # Índice de compacidad: (4 * pi * Area) / (Perímetro^2)
            # Un círculo perfecto da 1.0, formas irregulares dan menor
            compacity = (4 * np.pi * largest_area) / (perimeter ** 2)
    
    # 6. Calcular área en cm² física basada en calibración
    # Area (cm2) = pixeles * (ratio_cm_por_pixel)^2
    area_cm2 = plant_pixels * (profile.pixel_to_cm_ratio ** 2)
    
    # 7. Calcular índice de salud cromática
    # Salud cromática = % de píxeles verde vibrante dentro del follaje segmentado
    # Definimos un rango estricto de "verde saludable" en HSV
    lower_green = np.array([38, 45, 45])
    upper_green = np.array([82, 255, 255])
    mask_healthy = cv2.inRange(hsv, lower_green, upper_green)
    
    # Intersectamos con la máscara del follaje para contar solo píxeles de planta
    healthy_plant_pixels = cv2.countNonZero(cv2.bitwise_and(mask, mask_healthy))
    
    health_index = 100.0
    if plant_pixels > 0:
        health_index = (healthy_plant_pixels / plant_pixels) * 100.0
        health_index = min(100.0, max(0.0, health_index))
        
    # 8. Estimación de manchas/necrosis foliar (Desactivado a solicitud del usuario)
    spots_count = 0
    
    # 9. Conteo estimado de frutos (para tomate cherry / objetos rojos/anaranjados circulares)
    # Umbralizado preciso para tonalidades rojas/anaranjadas del fruto, tolerando variaciones de luz y sombras
    lower_red1 = np.array([0, 50, 45])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([165, 50, 45])
    upper_red2 = np.array([180, 255, 255])
    
    mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), 
                              cv2.inRange(hsv, lower_red2, upper_red2))
    
    # Operaciones morfológicas de precisión: close de 5x5 para rellenar brillos sin fusionar tomates contiguos, y open de 3x3 para ruido
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_CLOSE, kernel_close)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel_open)
    
    # Buscar círculos en la máscara depurada de frutos
    fruit_contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fruits_count = 0
    for c in fruit_contours:
        c_area = cv2.contourArea(c)
        # Un tomate individual real tiene al menos 40 px de área (diámetro > 7px)
        if c_area > 40: 
            c_perimeter = cv2.arcLength(c, True)
            if c_perimeter > 0:
                circularity = (4 * np.pi * c_area) / (c_perimeter ** 2)
                # Al mantener los tomates separados, su circularidad individual es alta (> 0.55)
                if circularity > 0.55:
                    fruits_count += 1
                    # Dibujar círculos amarillos en la imagen procesada rodeando al fruto real en su tamaño correcto
                    (x_f, y_f), r_f = cv2.minEnclosingCircle(c)
                    cv2.circle(overlay, (int(x_f), int(y_f)), int(r_f), (0, 255, 255), 2)
    
    # 10. Guardar la imagen con las marcas y overlays
    # Superponer texto con métricas principales
    cv2.putText(overlay, f"Area: {area_cm2:.1f} cm2", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(overlay, f"Salud: {health_index:.1f}%", (20, 80), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    if spots_count > 0:
        cv2.putText(overlay, f"Manchas: {spots_count}", (20, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    if fruits_count > 0:
        cv2.putText(overlay, f"Frutos: {fruits_count}", (20, 160), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
                    
    cv2.imwrite(output_path, overlay)
    
    return {
        "foliar_area_cm2": round(area_cm2, 2),
        "health_index": round(health_index, 2),
        "compacity_index": round(compacity, 3),
        "spots_count": spots_count,
        "fruits_count": fruits_count
    }

def process_lateral_image(image_path, output_path, profile):
    """
    Procesa una imagen lateral para calcular:
    - Altura estimada de la planta (cm)
    - Diámetro del tallo (mm)
    """
    ensure_dir(output_path)
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: No se pudo leer la imagen lateral {image_path}")
        return None
        
    h, w, _ = img.shape
    
    # Segmentar planta del fondo usando HSV y LAB (similar a cenital)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    lower_hsv = np.array([profile.h_min, profile.s_min, profile.v_min])
    upper_hsv = np.array([profile.h_max, profile.s_max, profile.v_max])
    mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)
    
    lower_lab = np.array([profile.l_min, profile.a_min, profile.b_min])
    upper_lab = np.array([profile.l_max, profile.a_max, profile.b_max])
    mask_lab = cv2.inRange(lab, lower_lab, upper_lab)
    
    mask = cv2.bitwise_and(mask_hsv, mask_lab)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [c for c in contours if cv2.contourArea(c) > 150]
    
    height_cm = 0.0
    stem_diameter_mm = 0.0
    
    overlay = img.copy()
    
    if valid_contours:
        # Unión de todos los contornos para encontrar las dimensiones totales de la planta
        all_points = np.vstack([c for c in valid_contours])
        
        # Encontrar los extremos en el eje Y (vertical)
        # Nota: y=0 está en la parte superior, y=h en la inferior
        y_points = all_points[:, 0, 1]
        x_points = all_points[:, 0, 0]
        
        y_min = np.min(y_points) # Ápice foliar (punto más alto en la imagen)
        
        # Cargar interruptor de tallo
        has_stem = getattr(profile, 'has_stem', True)
        
        # La canastilla de plástico blanco termina físicamente en el ~73% de la altura de la imagen.
        # Por lo tanto, el nivel del suelo para medir la planta es siempre el borde superior de la canastilla.
        basket_rim_y = int(h * 0.73)
        
        if y_min >= basket_rim_y:
            # Si el ápice foliar está por debajo del borde superior (semilla o no ha emergido)
            y_max = basket_rim_y
            height_pixels = 0
            height_cm = 0.0
            stem_diameter_mm = 0.0
        else:
            y_max = basket_rim_y
            height_pixels = y_max - y_min
            height_cm = height_pixels * profile.pixel_to_cm_ratio
            
            # 3. Calcular Diámetro del Tallo (Solo si la especie tiene tallo y ya ha crecido lo suficiente)
            if has_stem and height_cm >= 2.0:
                # Medimos el grosor en la zona basal limpia (entre 3 y 8 píxeles por encima del rim de la canastilla)
                # Esta zona está completamente libre de hojas y ramas en plantas con tallo.
                widths = []
                valid_y = []
                for offset in range(3, 9):
                    test_y = y_max - offset
                    if 0 <= test_y < h:
                        row_pixels = np.where(mask[test_y, :] > 0)[0]
                        if len(row_pixels) > 0:
                            w_px = np.max(row_pixels) - np.min(row_pixels)
                            # Para evitar capturar hojas que empiecen inusualmente bajas, 
                            # filtramos anchos sospechosamente grandes para un tallo basal (ej. > 60px)
                            if w_px < 60: 
                                widths.append(w_px)
                                valid_y.append(test_y)
                
                if len(widths) > 0:
                    # Usamos la mediana robusta de los anchos basales medidos
                    stem_width_pixels = np.median(widths)
                    # Diámetro (mm) = pixeles * ratio * 10 (para convertir cm a mm)
                    stem_diameter_mm = stem_width_pixels * profile.pixel_to_cm_ratio * 10
                    
                    # Dibujamos el calibrador rojo en el Y central de nuestra zona de escaneo basal
                    draw_y = int(np.median(valid_y))
                    # Volvemos a leer los extremos en ese Y específico para dibujar la línea
                    row_pixels = np.where(mask[draw_y, :] > 0)[0]
                    if len(row_pixels) > 0:
                        cv2.line(overlay, (np.min(row_pixels), draw_y), (np.max(row_pixels), draw_y), (0, 0, 255), 3)
                        cv2.circle(overlay, (np.min(row_pixels), draw_y), 5, (0, 0, 255), -1)
                        cv2.circle(overlay, (np.max(row_pixels), draw_y), 5, (0, 0, 255), -1)
                        
                        # Dibujar indicador de diámetro
                        cv2.putText(overlay, f"D: {stem_diameter_mm:.1f} mm", (np.max(row_pixels) + 15, draw_y + 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    stem_diameter_mm = 0.0
            else:
                stem_diameter_mm = 0.0
        
        # Dibujar regla vertical de altura en Cyan
        x_center = int((np.min(x_points) + np.max(x_points)) / 2)
        cv2.line(overlay, (x_center - 15, y_min), (x_center + 15, y_min), (255, 255, 0), 2)
        cv2.line(overlay, (x_center - 15, y_max), (x_center + 15, y_max), (255, 255, 0), 2)
        cv2.line(overlay, (x_center, y_min), (x_center, y_max), (255, 255, 0), 2)
        
        # Dibujar los contornos en verde sutil
        cv2.drawContours(overlay, valid_contours, -1, (0, 200, 0), 1)
        
        # Dibujar texto de altura
        cv2.putText(overlay, f"H: {height_cm:.1f} cm", (x_center + 15, int((y_min + y_max)/2)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imwrite(output_path, overlay)
    
    return {
        "plant_height_cm": round(height_cm, 2),
        "stem_diameter_mm": round(stem_diameter_mm, 2)
    }

def filter_and_average_metrics(cenital_results, lateral_results):
    """
    Filtra los resultados de las 5 imágenes de cada cámara eliminando
    valores atípicos que superen las 2 desviaciones estándar de la media
    y promedia los valores válidos restantes.
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
    
    # 1. Promediar Métricas Cenitales
    if cenital_results:
        # Extraemos listas de cada parámetro
        areas = [r["foliar_area_cm2"] for r in cenital_results]
        healths = [r["health_index"] for r in cenital_results]
        compacities = [r["compacity_index"] for r in cenital_results]
        spots = [r["spots_count"] for r in cenital_results]
        fruits = [r["fruits_count"] for r in cenital_results]
        
        # Función auxiliar de promedio con filtro de desviación estándar
        def get_robust_mean(data_list):
            if not data_list: return 0.0
            if len(data_list) <= 2: return np.mean(data_list)
            
            mean = np.mean(data_list)
            std = np.std(data_list)
            
            if std == 0: return mean
            
            # Filtrar valores dentro de 2 desviaciones estándar
            filtered = [x for x in data_list if abs(x - mean) <= 2 * std]
            if not filtered: return mean
            
            return np.mean(filtered)
            
        final_metrics["foliar_area_cm2"] = round(get_robust_mean(areas), 2)
        final_metrics["health_index"] = round(get_robust_mean(healths), 2)
        final_metrics["compacity_index"] = round(get_robust_mean(compacities), 3)
        
        # Para conteos directos, usamos la mediana redondeada
        final_metrics["spots_count"] = int(np.round(np.median(spots)))
        final_metrics["fruits_count"] = int(np.round(np.median(fruits)))
        
    # 2. Promediar Métricas Laterales
    if lateral_results:
        heights = [r["plant_height_cm"] for r in lateral_results]
        diameters = [r["stem_diameter_mm"] for r in lateral_results]
        
        def get_robust_mean(data_list):
            if not data_list: return 0.0
            if len(data_list) <= 2: return np.mean(data_list)
            mean = np.mean(data_list)
            std = np.std(data_list)
            if std == 0: return mean
            filtered = [x for x in data_list if abs(x - mean) <= 2 * std]
            if not filtered: return mean
            return np.mean(filtered)
            
        final_metrics["plant_height_cm"] = round(get_robust_mean(heights), 2)
        final_metrics["stem_diameter_mm"] = round(get_robust_mean(diameters), 2)
        
    return final_metrics
