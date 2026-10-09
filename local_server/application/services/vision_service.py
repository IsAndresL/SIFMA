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
    SensorRepository,
    ConfigRepository
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
        config_repo: Optional[ConfigRepository] = None,
        pipeline: Optional[VisionPipelineManager] = None
    ):
        self.session_repo = session_repo or CaptureSessionRepository()
        self.crop_repo = crop_repo or CropProfileRepository()
        self.sensor_repo = sensor_repo or SensorRepository()
        self.config_repo = config_repo or ConfigRepository()
        self.pipeline = pipeline or VisionPipelineManager()

    def detect_connected_usb_drives(self) -> List[Dict[str, Any]]:
        """
        Escanea unidades USB externas buscando exclusivamente la carpeta oficial 'SIFMA_CAPTURES'
        y agrupa los lotes de forma limpia por DÍA (YYYY-MM-DD) con sus respectivos turnos.
        Ignora cualquier otra carpeta del disco duro o de la memoria USB.
        """
        usb_days = []
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
            possible_roots = ["/media/nodo1", "/media/computo1", "/media/pi", "/media", "/mnt/usb", "/mnt"]
            
        for root in possible_roots:
            if not os.path.exists(root):
                continue
                
            # 1. Localizar la carpeta raíz SIFMA_CAPTURES
            target_sifma_dir = None
            if os.path.exists(os.path.join(root, "SIFMA_CAPTURES")):
                target_sifma_dir = os.path.join(root, "SIFMA_CAPTURES")
            else:
                # Buscar en subdirectorios directos (ej. /media/pi/USB_NAME/SIFMA_CAPTURES)
                try:
                    for d in os.listdir(root):
                        sub = os.path.join(root, d)
                        if os.path.isdir(sub):
                            cand = os.path.join(sub, "SIFMA_CAPTURES")
                            if os.path.exists(cand):
                                target_sifma_dir = cand
                                break
                except Exception:
                    pass

            # Si no hay carpeta SIFMA_CAPTURES en esta unidad, ignorar completamente esta USB
            if not target_sifma_dir or not os.path.exists(target_sifma_dir):
                continue

            # 2. Escanear exclusivamente las carpetas por fecha YYYY-MM-DD dentro de SIFMA_CAPTURES
            try:
                date_entries = sorted(os.listdir(target_sifma_dir))
                for entry in date_entries:
                    day_path = os.path.join(target_sifma_dir, entry)
                    if not os.path.isdir(day_path):
                        continue

                    # Validar si tiene formato de fecha YYYY-MM-DD
                    is_date = bool(re.match(r'^\d{4}[-_]\d{2}[-_]\d{2}$', entry) or re.match(r'^\d{2}[-_]\d{2}[-_]\d{4}$', entry))
                    date_label = entry.replace('_', '-') if is_date else entry

                    # Contar fotos y recopilar los turnos internos (mañana, mediodía, tarde)
                    turns_found = []
                    total_images = 0
                    
                    for sub_root, _, f_list in os.walk(day_path):
                        imgs = [f for f in f_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                        if imgs:
                            total_images += len(imgs)
                            folder_name = os.path.basename(sub_root).lower()
                            if 'manana' in folder_name or 'mañana' in folder_name:
                                turn_name = "Mañana"
                            elif 'medio_dia' in folder_name or 'mediodia' in folder_name or 'medio-dia' in folder_name:
                                turn_name = "Mediodía"
                            elif 'tarde' in folder_name:
                                turn_name = "Tarde"
                            else:
                                turn_name = folder_name.replace('_', ' ').title()
                            
                            turns_found.append({
                                "period": turn_name,
                                "path": sub_root,
                                "images_count": len(imgs)
                            })

                    if total_images > 0:
                        turns_labels = [t["period"] for t in turns_found]
                        summary_turns = ", ".join(turns_labels) if turns_labels else "Muestreos"
                        
                        usb_days.append({
                            "batch_name": f"{date_label} ({len(turns_found)} turnos - {total_images} fotos)",
                            "date_str": date_label,
                            "period_str": summary_turns,
                            "images_count": total_images,
                            "turns_count": len(turns_found),
                            "turns": turns_found,
                            "path": day_path,
                            "drive_root": root
                        })
            except Exception as e:
                pass

        usb_days.sort(key=lambda x: x.get("date_str", ""), reverse=True)
        return usb_days

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
        
        sys_config = self.config_repo.get()

        for i, src_img in enumerate(cenital_imgs):
            dst_orig = os.path.join(upload_dir, f"cenital_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_cenital_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = self.pipeline.process_cenital(dst_orig, dst_proc, profile, config=sys_config)
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
                
        for i, src_img in enumerate(lateral_imgs):
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
                motor_current=float(sensor_data.get("motor_current", 0.0)),
                motor_state=int(sensor_data.get("motor_state", 1 if float(sensor_data.get("motor_current", 0.0)) > 0 else 0)),
                water_ph=float(sensor_data.get("water_ph", 0.0)),
                ec_conductivity=float(sensor_data.get("ec_conductivity", 0.0)),
                turbidity_ntu=float(sensor_data.get("turbidity_ntu", 0.0)),
                dissolved_oxygen_mg_l=float(sensor_data.get("dissolved_oxygen_mg_l", 0.0)),
                water_temp=float(sensor_data.get("water_temp", 0.0))
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
