import os
import glob
import json
import shutil
import re
import platform
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import config
from core.security import SecurityService
from domain.models import CaptureSession, BiometricMetric, SensorReading, CropProfile
from infrastructure.database.repositories import (
    CaptureSessionRepository, 
    CropProfileRepository, 
    SensorRepository
)
from infrastructure.vision import VisionPipelineManager
from infrastructure.database.connection import db

class VisionApplicationService:
    """
    Caso de uso: Procesamiento de lotes fotográficos, detección USB y persistencia de métricas individuales.
    (SOLID: SRP, DIP)
    """
    
    def __init__(
        self,
        session_repo: Optional[CaptureSessionRepository] = None,
        crop_repo: Optional[CropProfileRepository] = None,
        sensor_repo: Optional[SensorRepository] = None,
        pipeline: Optional[VisionPipelineManager] = None
    ):
        self.session_repo = session_repo or CaptureSessionRepository()
        self.crop_repo = crop_repo or CropProfileRepository()
        self.sensor_repo = sensor_repo or SensorRepository()
        self.pipeline = pipeline or VisionPipelineManager()

    def detect_connected_usb_drives(self) -> List[Dict[str, Any]]:
        """Escanea unidades USB y extrae carpetas con fotos clasificadas por fecha y período."""
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
        else:
            possible_roots = ["/media", "/mnt", "/media/pi"]
            
        for root in possible_roots:
            if not os.path.exists(root):
                continue
                
            for root_dir, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith('$') and d not in ['System Volume Information', 'Recovery', '__pycache__', 'AppData']]
                
                image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not image_files:
                    continue
                    
                normalized_path = os.path.normpath(root_dir)
                path_parts = normalized_path.split(os.sep)
                
                date_str = ""
                period_str = ""
                
                for part in path_parts:
                    if re.match(r'^\d{4}[-_]\d{2}[-_]\d{2}$', part) or re.match(r'^\d{2}[-_]\d{2}[-_]\d{4}$', part):
                        date_str = part.replace('_', '-')
                        break
                        
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

        usb_batches.sort(key=lambda x: (x.get("date_str", ""), x.get("period_str", "")))
        return usb_batches

    def process_folder_batch(
        self, 
        folder_path: str, 
        crop_type: Optional[str] = None, 
        period: str = "Día 1", 
        sensor_data: Optional[Dict[str, Any]] = None, 
        plant_id: int = 1
    ) -> Dict[str, Any]:
        """Procesa una carpeta de imágenes, calcula métricas biométricas individuales y promedio."""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"La ruta {folder_path} no existe.")
            
        metadata_file = os.path.join(folder_path, "metadata.json")
        photos_meta_map = {}
        session_timestamp = datetime.now()
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    meta = json.load(f)
                    crop_type = meta.get("crop_type", crop_type)
                    if "timestamp" in meta:
                        try:
                            session_timestamp = datetime.fromisoformat(meta["timestamp"])
                        except Exception:
                            try:
                                session_timestamp = datetime.strptime(meta["timestamp"], "%Y-%m-%d %H:%M:%S")
                            except Exception:
                                pass
                    for p_info in meta.get("photos", []):
                        p_idx = p_info.get("photo_index")
                        if p_idx is not None:
                            photos_meta_map[p_idx] = p_info
            except Exception:
                pass
                
        profile = self.crop_repo.get_by_type(crop_type) or self.crop_repo.get_by_type("cebollin") or self.crop_repo.get_all()[0]
        
        all_images = glob.glob(os.path.join(folder_path, "*.png")) + glob.glob(os.path.join(folder_path, "*.jpg"))
        if not all_images:
            all_images = glob.glob(os.path.join(folder_path, "*", "*.png")) + glob.glob(os.path.join(folder_path, "*", "*.jpg"))
            
        cenital_imgs = sorted([f for f in all_images if "cenital" in os.path.basename(f).lower()])
        lateral_imgs = sorted([f for f in all_images if "lateral" in os.path.basename(f).lower()])
        
        if not cenital_imgs and not lateral_imgs and all_images:
            half = len(all_images) // 2
            cenital_imgs = all_images[:half]
            lateral_imgs = all_images[half:]
            
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_dir = os.path.join(config.UPLOAD_DIR, f"batch_{timestamp_str}")
        processed_dir = os.path.join(config.PROCESSED_DIR, f"batch_{timestamp_str}")
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
            
            res = self.pipeline.process_cenital(dst_orig, dst_proc, profile)
            if res:
                cenital_results.append(res)
                rel_orig = os.path.relpath(dst_orig, config.DATA_DIR).replace("\\", "/")
                rel_proc = os.path.relpath(dst_proc, config.DATA_DIR).replace("\\", "/")
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
            
            res = self.pipeline.process_lateral(dst_orig, dst_proc, profile)
            if res:
                lateral_results.append(res)
                rel_orig = os.path.relpath(dst_orig, config.DATA_DIR).replace("\\", "/")
                rel_proc = os.path.relpath(dst_proc, config.DATA_DIR).replace("\\", "/")
                lateral_paths_list.append({
                    "index": i + 1,
                    "orig": f"data/{rel_orig}",
                    "proc": f"data/{rel_proc}",
                    "metrics": res
                })
                
        # Construir métricas individuales con timestamps específicos de cada toma
        max_photos = max(len(cenital_paths_list), len(lateral_paths_list), 1)
        individual_metrics = []
        
        for i in range(max_photos):
            photo_index = i + 1
            c_data = cenital_paths_list[i] if i < len(cenital_paths_list) else None
            l_data = lateral_paths_list[i] if i < len(lateral_paths_list) else None
            
            c_metrics = c_data["metrics"] if c_data else {}
            l_metrics = l_data["metrics"] if l_data else {}
            
            # Timestamp exacto de la toma individual
            p_meta = photos_meta_map.get(photo_index, {})
            p_time_str = p_meta.get("timestamp")
            if p_time_str:
                try:
                    exact_dt = datetime.strptime(p_time_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    exact_dt = session_timestamp
            else:
                exact_dt = session_timestamp
            
            individual_metrics.append({
                "photo_index": photo_index,
                "capture_time": exact_dt,
                "foliar_area_cm2": c_metrics.get("area_cm2", 0.0),
                "health_index": c_metrics.get("health_index", 100.0),
                "compacity_index": c_metrics.get("compacity_index", 0.0),
                "spots_count": c_metrics.get("spots_count", 0),
                "fruits_count": c_metrics.get("fruits_count", 0),
                "plant_height_cm": l_metrics.get("plant_height_cm", 0.0),
                "stem_diameter_mm": l_metrics.get("stem_diameter_mm", 0.0),
                "cenital_orig": c_data["orig"] if c_data else (lateral_paths_list[0]["orig"] if lateral_paths_list else ""),
                "cenital_proc": c_data["proc"] if c_data else (lateral_paths_list[0]["proc"] if lateral_paths_list else ""),
                "lateral_orig": l_data["orig"] if l_data else (cenital_paths_list[0]["orig"] if cenital_paths_list else ""),
                "lateral_proc": l_data["proc"] if l_data else (cenital_paths_list[0]["proc"] if cenital_paths_list else "")
            })
            
        final_metrics = self.pipeline.filter_and_average(cenital_results, lateral_results)
        
        default_cen_orig = cenital_paths_list[0]["orig"] if cenital_paths_list else ""
        default_cen_proc = cenital_paths_list[0]["proc"] if cenital_paths_list else ""
        default_lat_orig = lateral_paths_list[0]["orig"] if lateral_paths_list else ""
        default_lat_proc = lateral_paths_list[0]["proc"] if lateral_paths_list else ""
        
        # Persistencia en base de datos
        session_id = self._save_capture_session_with_metrics(
            period=period,
            crop_type=profile.crop_type,
            sensor_data=sensor_data,
            final_metrics=final_metrics,
            individual_metrics=individual_metrics,
            cenital_paths={"orig": default_cen_orig, "proc": default_cen_proc},
            lateral_paths={"orig": default_lat_orig, "proc": default_lat_proc},
            plant_id=plant_id,
            session_timestamp=session_timestamp
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

    def _save_capture_session_with_metrics(
        self, period, crop_type, sensor_data, final_metrics, 
        individual_metrics=None, cenital_paths=None, lateral_paths=None, plant_id=1,
        session_timestamp=None
    ) -> int:
        if not cenital_paths: cenital_paths = {}
        if not lateral_paths: lateral_paths = {}
        if not sensor_data: sensor_data = {}
        if not session_timestamp: session_timestamp = datetime.now()

        sensor_id = None
        if sensor_data and any(sensor_data.values()):
            sensor_record = SensorReading(
                timestamp=session_timestamp,
                temperature=float(sensor_data.get("temperature", 0.0)),
                humidity=float(sensor_data.get("humidity", 0.0)),
                uv_solar=float(sensor_data.get("uv_solar", 0.0)),
                motor_current=float(sensor_data.get("motor_current", 0.0))
            )
            self.sensor_repo.add(sensor_record)
            sensor_id = sensor_record.id
        else:
            nearest = self.sensor_repo.find_nearest(session_timestamp)
            sensor_id = nearest.id if nearest else None

        existing = self.session_repo.get_by_period_and_plant(period, int(plant_id))
        if existing:
            session_record = existing
            session_record.timestamp = session_timestamp
            session_record.crop_type = crop_type
            if sensor_id:
                session_record.sensor_reading_id = sensor_id

            for m in list(session_record.metrics):
                db.session.delete(m)
            db.session.flush()
        else:
            session_record = CaptureSession(
                period=period,
                plant_id=int(plant_id),
                crop_type=crop_type,
                sensor_reading_id=sensor_id,
                timestamp=session_timestamp
            )
            self.session_repo.save(session_record)

        # 1. Promedio consolidado
        avg_record = BiometricMetric(
            session_id=session_record.id,
            photo_index=0,
            is_average=True,
            capture_exact_time=session_timestamp,
            foliar_area_cm2=final_metrics.get("foliar_area_cm2", 0.0),
            plant_height_cm=final_metrics.get("plant_height_cm", 0.0),
            stem_diameter_mm=final_metrics.get("stem_diameter_mm", 0.0),
            health_index=final_metrics.get("health_index", 100.0),
            compacity_index=final_metrics.get("compacity_index", 0.0),
            spots_count=0,
            fruits_count=0,
            image_path_cenital_orig=cenital_paths.get("orig"),
            image_path_cenital_proc=cenital_paths.get("proc"),
            image_path_lateral_orig=lateral_paths.get("orig"),
            image_path_lateral_proc=lateral_paths.get("proc")
        )
        db.session.add(avg_record)

        # 2. Métricas individuales por cada una de las 5 tomas
        if individual_metrics:
            for item in individual_metrics:
                idx = item.get("photo_index", 1)
                t_exact = item.get("capture_time", session_timestamp)
                ind_record = BiometricMetric(
                    session_id=session_record.id,
                    photo_index=idx,
                    is_average=False,
                    capture_exact_time=t_exact,
                    foliar_area_cm2=item.get("foliar_area_cm2", 0.0),
                    plant_height_cm=item.get("plant_height_cm", 0.0),
                    stem_diameter_mm=item.get("stem_diameter_mm", 0.0),
                    health_index=item.get("health_index", 100.0),
                    compacity_index=item.get("compacity_index", 0.0),
                    spots_count=0,
                    fruits_count=0,
                    image_path_cenital_orig=item.get("cenital_orig"),
                    image_path_cenital_proc=item.get("proc") if "proc" in item else item.get("cenital_proc"),
                    image_path_lateral_orig=item.get("lateral_orig"),
                    image_path_lateral_proc=item.get("lateral_proc")
                )
                db.session.add(ind_record)

        db.session.commit()
        return session_record.id
