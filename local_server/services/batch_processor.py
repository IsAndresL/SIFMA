import os
import glob
import json
import shutil
import platform
import zipfile
from datetime import datetime

from core.vision import VisionPipelineManager
from services.db_service import DatabaseService

class BatchProcessorService:
    """
    Servicio para procesar lotes de imágenes desde archivos subidos (Drag & Drop),
    archivos ZIP o carpetas estructuradas en unidades USB detectadas.
    Estructura USB esperada: SIFMA_CAPTURES/YYYY-MM-DD/[manana|medio_dia|tarde]/
    """
    
    @staticmethod
    def detect_connected_usb_drives():
        """
        Escanea exhaustivamente las unidades USB conectadas en Windows y Linux.
        Identifica todas las carpetas y subcarpetas que contienen imágenes fotográficas
        y extrae automáticamente su fecha y período de muestreo (Mañana, Mediodía, Tarde).
        """
        import re
        usb_batches = []
        system = platform.system()
        
        possible_roots = []
        if system == "Windows":
            import string
            for letter in string.ascii_uppercase:
                if letter not in ['C']:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        possible_roots.append(drive)
        else: # Linux / Raspberry Pi
            possible_roots = ["/media", "/mnt", "/media/pi"]
            
        for root in possible_roots:
            if not os.path.exists(root):
                continue
                
            for root_dir, dirs, files in os.walk(root):
                # Omitir carpetas del sistema y temporales
                dirs[:] = [d for d in dirs if not d.startswith('$') and d not in ['System Volume Information', 'Recovery', '__pycache__', 'AppData']]
                
                image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not image_files:
                    continue
                    
                normalized_path = os.path.normpath(root_dir)
                path_parts = normalized_path.split(os.sep)
                
                date_str = ""
                period_str = ""
                
                # Buscar formato de fecha YYYY-MM-DD o DD-MM-YYYY
                for part in path_parts:
                    if re.match(r'^\d{4}[-_]\d{2}[-_]\d{2}$', part) or re.match(r'^\d{2}[-_]\d{2}[-_]\d{4}$', part):
                        date_str = part.replace('_', '-')
                        break
                        
                # Determinar período según el nombre de la carpeta
                folder_name = os.path.basename(normalized_path).lower()
                if 'manana' in folder_name or 'mañana' in folder_name or 'morning' in folder_name or '07' in folder_name:
                    period_str = "Mañana"
                elif 'medio_dia' in folder_name or 'mediodia' in folder_name or 'medio-dia' in folder_name or 'noon' in folder_name or '12' in folder_name:
                    period_str = "Mediodía"
                elif 'tarde' in folder_name or 'afternoon' in folder_name or 'noche' in folder_name or '17' in folder_name:
                    period_str = "Tarde"
                else:
                    period_str = folder_name.replace('_', ' ').title()

                if date_str and period_str:
                    batch_name = f"{date_str} - {period_str} ({len(image_files)} fotos)"
                elif date_str:
                    batch_name = f"{date_str} ({len(image_files)} fotos)"
                else:
                    batch_name = f"{period_str} ({len(image_files)} fotos)"

                usb_batches.append({
                    "batch_name": batch_name,
                    "date_str": date_str,
                    "period_str": period_str,
                    "images_count": len(image_files),
                    "path": normalized_path,
                    "drive_root": root
                })

        # Ordenar por fecha y período
        usb_batches.sort(key=lambda x: (x.get("date_str", ""), x.get("period_str", "")))
        return usb_batches

    @staticmethod
    def process_folder_batch(folder_path, crop_type=None, period="Día 1", sensor_data=None, plant_id=1):
        """
        Procesa una carpeta local o extraída de USB conteniendo imágenes cenitales y laterales.
        Soporta subcarpetas o imágenes directas.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"La ruta {folder_path} no existe.")
            
        metadata_file = os.path.join(folder_path, "metadata.json")
        if os.path.exists(metadata_file) and not sensor_data:
            try:
                with open(metadata_file, "r") as f:
                    meta = json.load(f)
                    sensor_data = meta.get("sensor_data", sensor_data)
                    crop_type = meta.get("crop_type", crop_type)
            except Exception:
                pass
                
        profile = DatabaseService.get_crop_profile(crop_type)
        
        all_images = glob.glob(os.path.join(folder_path, "*.png")) + glob.glob(os.path.join(folder_path, "*.jpg"))
        if not all_images:
            # Buscar 1 nivel más profundo si es una carpeta raíz de fecha
            all_images = glob.glob(os.path.join(folder_path, "*", "*.png")) + glob.glob(os.path.join(folder_path, "*", "*.jpg"))
            
        cenital_imgs = [f for f in all_images if "cenital" in os.path.basename(f).lower()]
        lateral_imgs = [f for f in all_images if "lateral" in os.path.basename(f).lower()]
        
        if not cenital_imgs and not lateral_imgs and all_images:
            half = len(all_images) // 2
            cenital_imgs = all_images[:half]
            lateral_imgs = all_images[half:]
            
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "data"))
        upload_dir = os.path.join(static_dir, "uploads", f"batch_{timestamp_str}")
        processed_dir = os.path.join(static_dir, "processed", f"batch_{timestamp_str}")
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        
        cenital_results = []
        lateral_results = []
        cenital_paths_list = []
        lateral_paths_list = []
        
        for i, src_img in enumerate(cenital_imgs[:5]):
            dst_orig = os.path.join(upload_dir, f"cenital_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_cenital_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = VisionPipelineManager.process_cenital_image(dst_orig, dst_proc, profile)
            if res:
                cenital_results.append(res)
                rel_orig = os.path.relpath(dst_orig, static_dir).replace("\\", "/")
                rel_proc = os.path.relpath(dst_proc, static_dir).replace("\\", "/")
                cenital_paths_list.append({
                    "index": i + 1,
                    "orig": f"data/{rel_orig}",
                    "proc": f"data/{rel_proc}",
                    "metrics": res
                })
                
        for i, src_img in enumerate(lateral_imgs[:5]):
            dst_orig = os.path.join(upload_dir, f"lateral_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_lateral_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = VisionPipelineManager.process_lateral_image(dst_orig, dst_proc, profile)
            if res:
                lateral_results.append(res)
                rel_orig = os.path.relpath(dst_orig, static_dir).replace("\\", "/")
                rel_proc = os.path.relpath(dst_proc, static_dir).replace("\\", "/")
                lateral_paths_list.append({
                    "index": i + 1,
                    "orig": f"data/{rel_orig}",
                    "proc": f"data/{rel_proc}",
                    "metrics": res
                })
                
        # Construir lista de 5 métricas individuales
        max_photos = max(len(cenital_paths_list), len(lateral_paths_list), 1)
        individual_metrics = []
        for i in range(max_photos):
            c_data = cenital_paths_list[i] if i < len(cenital_paths_list) else None
            l_data = lateral_paths_list[i] if i < len(lateral_paths_list) else None
            
            c_metrics = c_data["metrics"] if c_data else {}
            l_metrics = l_data["metrics"] if l_data else {}
            
            individual_metrics.append({
                "photo_index": i + 1,
                "capture_time": datetime.now(),
                "foliar_area_cm2": c_metrics.get("area_cm2", 0.0),
                "health_index": c_metrics.get("health_index", 100.0),
                "compacity_index": c_metrics.get("compacity_index", 0.0),
                "fruits_count": c_metrics.get("fruits_count", 0),
                "spots_count": c_metrics.get("spots_count", 0),
                "plant_height_cm": l_metrics.get("plant_height_cm", 0.0),
                "stem_diameter_mm": l_metrics.get("stem_diameter_mm", 0.0),
                "cenital_orig": c_data["orig"] if c_data else (lateral_paths_list[0]["orig"] if lateral_paths_list else ""),
                "cenital_proc": c_data["proc"] if c_data else (lateral_paths_list[0]["proc"] if lateral_paths_list else ""),
                "lateral_orig": l_data["orig"] if l_data else (cenital_paths_list[0]["orig"] if cenital_paths_list else ""),
                "lateral_proc": l_data["proc"] if l_data else (cenital_paths_list[0]["proc"] if cenital_paths_list else "")
            })
            
        final_metrics = VisionPipelineManager.filter_and_average_metrics(cenital_results, lateral_results)
        
        # Rutas por defecto del promedio (usar la primera toma representativa)
        default_cen_orig = cenital_paths_list[0]["orig"] if cenital_paths_list else ""
        default_cen_proc = cenital_paths_list[0]["proc"] if cenital_paths_list else ""
        default_lat_orig = lateral_paths_list[0]["orig"] if lateral_paths_list else ""
        default_lat_proc = lateral_paths_list[0]["proc"] if lateral_paths_list else ""
        
        session_id, metrics_rec = DatabaseService.save_capture_session_with_metrics(
            period=period,
            crop_type=profile.crop_type,
            sensor_data=sensor_data,
            final_metrics=final_metrics,
            individual_metrics=individual_metrics,
            cenital_paths={"orig": default_cen_orig, "proc": default_cen_proc},
            lateral_paths={"orig": default_lat_orig, "proc": default_lat_proc},
            plant_id=plant_id
        )
        
        return {
            "session_id": session_id,
            "period": period,
            "crop_type": profile.crop_type,
            "plant_id": plant_id,
            "metrics": final_metrics,
            "individual_metrics": individual_metrics,
            "processed_count": len(cenital_results) + len(lateral_results)
        }
