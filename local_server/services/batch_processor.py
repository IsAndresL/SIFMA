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
        Escanea las unidades de almacenamiento USB conectadas en Windows y Linux/Raspberry Pi.
        Busca la carpeta SIFMA_CAPTURES y extrae los lotes clasificados por fecha y período.
        """
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
            sifma_dir = os.path.join(root, "SIFMA_CAPTURES")
            if os.path.exists(sifma_dir):
                for entry in os.listdir(sifma_dir):
                    date_folder_path = os.path.join(sifma_dir, entry)
                    if os.path.isdir(date_folder_path):
                        # 1. Verificar si contiene subcarpetas de período (manana, medio_dia, tarde)
                        period_found = False
                        for sub_entry in os.listdir(date_folder_path):
                            sub_path = os.path.join(date_folder_path, sub_entry)
                            if os.path.isdir(sub_path):
                                imgs = glob.glob(os.path.join(sub_path, "*.png")) + glob.glob(os.path.join(sub_path, "*.jpg"))
                                if imgs:
                                    period_found = True
                                    period_name = sub_entry.replace("_", " ").title()
                                    usb_batches.append({
                                        "batch_name": f"📅 {entry} ({period_name})",
                                        "date_str": entry,
                                        "period_str": period_name,
                                        "path": sub_path,
                                        "drive_root": root
                                    })
                        # 2. Si no tenía subcarpetas de período pero contiene imágenes directamente
                        if not period_found:
                            imgs = glob.glob(os.path.join(date_folder_path, "*.png")) + glob.glob(os.path.join(date_folder_path, "*.jpg"))
                            if imgs:
                                usb_batches.append({
                                    "batch_name": f"📅 Lote {entry}",
                                    "date_str": entry,
                                    "period_str": "Completo",
                                    "path": date_folder_path,
                                    "drive_root": root
                                })
            else:
                for root_dir, dirs, files in os.walk(root):
                    if any(f.endswith(('.png', '.jpg', '.jpeg')) for f in files):
                        if "data" not in root_dir and "uploads" not in root_dir:
                            usb_batches.append({
                                "batch_name": f"📂 {os.path.basename(root_dir) or 'Memoria_USB'}",
                                "date_str": "",
                                "period_str": "General",
                                "path": root_dir,
                                "drive_root": root
                            })
                        break
                        
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
                
        if not sensor_data:
            sensor_data = {
                "temperature": 23.5,
                "humidity": 65.0,
                "uv_solar": 350.0,
                "motor_current": 0.42
            }
            
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
        
        last_cenital_orig, last_cenital_proc = None, None
        last_lateral_orig, last_lateral_proc = None, None
        
        for i, src_img in enumerate(cenital_imgs[:5]):
            dst_orig = os.path.join(upload_dir, f"cenital_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_cenital_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = VisionPipelineManager.process_cenital_image(dst_orig, dst_proc, profile)
            if res:
                cenital_results.append(res)
                last_cenital_orig = os.path.relpath(dst_orig, static_dir).replace("\\", "/")
                last_cenital_proc = os.path.relpath(dst_proc, static_dir).replace("\\", "/")
                
        for i, src_img in enumerate(lateral_imgs[:5]):
            dst_orig = os.path.join(upload_dir, f"lateral_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_lateral_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = VisionPipelineManager.process_lateral_image(dst_orig, dst_proc, profile)
            if res:
                lateral_results.append(res)
                last_lateral_orig = os.path.relpath(dst_orig, static_dir).replace("\\", "/")
                last_lateral_proc = os.path.relpath(dst_proc, static_dir).replace("\\", "/")
                
        final_metrics = VisionPipelineManager.filter_and_average_metrics(cenital_results, lateral_results)
        
        session_id, metrics_rec = DatabaseService.save_capture_session_with_metrics(
            period=period,
            crop_type=profile.crop_type,
            sensor_data=sensor_data,
            final_metrics=final_metrics,
            cenital_paths={"orig": f"data/{last_cenital_orig}", "proc": f"data/{last_cenital_proc}"},
            lateral_paths={"orig": f"data/{last_lateral_orig}", "proc": f"data/{last_lateral_proc}"},
            plant_id=plant_id
        )
        
        return {
            "session_id": session_id,
            "period": period,
            "crop_type": profile.crop_type,
            "plant_id": plant_id,
            "metrics": final_metrics,
            "processed_count": len(cenital_results) + len(lateral_results)
        }
