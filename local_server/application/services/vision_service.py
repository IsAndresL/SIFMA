# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

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
    _progress = {
        "is_processing": False,
        "percent": 0,
        "message": "Inactivo",
        "current_item": 0,
        "total_items": 0,
        "current_turn": "",
        "detail": ""
    }

    @classmethod
    def get_progress(cls) -> Dict[str, Any]:
        return cls._progress

    @classmethod
    def set_progress(cls, percent: int, message: str, is_processing: bool = True, **kwargs):
        cls._progress["is_processing"] = is_processing
        cls._progress["percent"] = max(0, min(100, percent))
        cls._progress["message"] = message
        for k, v in kwargs.items():
            cls._progress[k] = v

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
        plant_id: int = 1,
        global_offset: int = 0,
        total_global_photos: int = 0,
        turn_label: str = ""
    ) -> Dict[str, Any]:
        """Procesa una carpeta de imágenes, calcula métricas biométricas individuales y promedio."""
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"La ruta {folder_path} no existe.")
            
        metadata_file = os.path.join(folder_path, "metadata.json")
        photos_meta_map = {}
        session_timestamp = datetime.now()
        
        # Obtener el cultivo asignado en el sistema para esta canastilla
        sys_config = self.config_repo.get()
        assigned_crop = getattr(sys_config, f"plant_{plant_id}_crop", None) or sys_config.selected_crop_type
        
        meta_crop = None
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    meta = json.load(f)
                    meta_crop = meta.get("crop_type")
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
                
        # Jerarquía: crop_type explícito > cultivo asignado a la Canastilla > metadata.json > fallback cebollín
        effective_crop = crop_type or assigned_crop or meta_crop or "cebollin"
        profile = self.crop_repo.get_by_type(effective_crop) or self.crop_repo.get_by_type(meta_crop) or self.crop_repo.get_by_type("cebollin") or self.crop_repo.get_all()[0]
        
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

        total_folder_photos = len(cenital_imgs) + len(lateral_imgs)
        actual_total = total_global_photos if total_global_photos > 0 else max(1, total_folder_photos)
        current_processed = global_offset
        turn_prefix = f"[{turn_label}] " if turn_label else ""

        for i, src_img in enumerate(cenital_imgs):
            current_processed += 1
            pct = int((current_processed / (actual_total + 1)) * 95)
            self.set_progress(
                percent=pct,
                message=f"{turn_prefix}Segmentando vista cenital {i+1}/{len(cenital_imgs)} (ExG + Otsu)...",
                is_processing=True,
                current_item=current_processed,
                total_items=actual_total,
                current_turn=turn_label
            )

            dst_orig = os.path.join(upload_dir, f"cenital_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_cenital_{i+1}.png")
            dst_spec = os.path.join(processed_dir, f"spectral_cenital_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = self.pipeline.process_cenital(dst_orig, dst_proc, profile, config=sys_config, spectral_output_path=dst_spec)
            if res:
                cenital_results.append(res)
                rel_orig = os.path.relpath(dst_orig, config.DATA_DIR).replace("\\", "/")
                rel_proc = os.path.relpath(dst_proc, config.DATA_DIR).replace("\\", "/")
                rel_spec = os.path.relpath(dst_spec, config.DATA_DIR).replace("\\", "/")
                cenital_paths_list.append({
                    "index": i + 1,
                    "orig": f"data/{rel_orig}",
                    "proc": f"data/{rel_proc}",
                    "spectral": f"data/{rel_spec}",
                    "metrics": res
                })
                
        for i, src_img in enumerate(lateral_imgs):
            current_processed += 1
            pct = int((current_processed / (actual_total + 1)) * 95)
            self.set_progress(
                percent=pct,
                message=f"{turn_prefix}Segmentando vista lateral {i+1}/{len(lateral_imgs)} (Tallo y Altura)...",
                is_processing=True,
                current_item=current_processed,
                total_items=actual_total,
                current_turn=turn_label
            )

            dst_orig = os.path.join(upload_dir, f"lateral_{i+1}.png")
            dst_proc = os.path.join(processed_dir, f"proc_lateral_{i+1}.png")
            shutil.copy(src_img, dst_orig)
            
            res = self.pipeline.process_lateral(dst_orig, dst_proc, profile, config=sys_config)
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
                "healthy_tissue_pct": c_metrics.get("healthy_tissue_pct", c_metrics.get("health_index", 100.0)),
                "chlorosis_pct": c_metrics.get("chlorosis_pct", 0.0),
                "necrosis_pct": c_metrics.get("necrosis_pct", 0.0),
                "gli_index": c_metrics.get("gli_index", 0.0),
                "vari_index": c_metrics.get("vari_index", 0.0),
                "exg_index": c_metrics.get("exg_index", 0.0),
                "apical_damage_ratio": c_metrics.get("apical_damage_ratio", 0.0),
                "interveinal_contrast": c_metrics.get("interveinal_contrast", 0.0),
                "plant_height_cm": l_metrics.get("plant_height_cm", 0.0),
                "stem_diameter_mm": l_metrics.get("stem_diameter_mm", 0.0),
                "cenital_orig": c_data["orig"] if c_data else (lateral_paths_list[0]["orig"] if lateral_paths_list else ""),
                "cenital_proc": c_data["proc"] if c_data else (lateral_paths_list[0]["proc"] if lateral_paths_list else ""),
                "spectral_map": c_data.get("spectral", "") if c_data else "",
                "lateral_orig": l_data["orig"] if l_data else (cenital_paths_list[0]["orig"] if cenital_paths_list else ""),
                "lateral_proc": l_data["proc"] if l_data else (cenital_paths_list[0]["proc"] if cenital_paths_list else "")
            })
            
        final_metrics = self.pipeline.filter_and_average(cenital_results, lateral_results)
        
        default_cen_orig = cenital_paths_list[0]["orig"] if cenital_paths_list else ""
        default_cen_proc = cenital_paths_list[0]["proc"] if cenital_paths_list else ""
        default_cen_spec = cenital_paths_list[0].get("spectral", "") if cenital_paths_list else ""
        default_lat_orig = lateral_paths_list[0]["orig"] if lateral_paths_list else ""
        default_lat_proc = lateral_paths_list[0]["proc"] if lateral_paths_list else ""
        
        session_id = self._save_capture_session_with_metrics(
            period=period,
            crop_type=profile.crop_type,
            sensor_data=sensor_data,
            final_metrics=final_metrics,
            individual_metrics=individual_metrics,
            cenital_paths={"orig": default_cen_orig, "proc": default_cen_proc, "spectral": default_cen_spec},
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
        active_sensor_dict = {}
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
            active_sensor_dict = sensor_record.to_dict() if hasattr(sensor_record, "to_dict") else dict(sensor_data)
        else:
            nearest = self.sensor_repo.find_nearest(session_timestamp)
            if nearest:
                sensor_id = nearest.id
                active_sensor_dict = {
                    "temperature": nearest.temperature,
                    "humidity": nearest.humidity,
                    "uv_solar": nearest.uv_solar,
                    "motor_current": nearest.motor_current,
                    "water_ph": nearest.water_ph,
                    "ec_conductivity": nearest.ec_conductivity,
                    "turbidity_ntu": nearest.turbidity_ntu,
                    "dissolved_oxygen_mg_l": nearest.dissolved_oxygen_mg_l,
                    "water_temp": getattr(nearest, "water_temp", 21.0)
                }

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

        # Inferencia neuronal ONNX (cv2.dnn) para el consolidado del lote
        ai_diag_avg = self.pipeline.ai_analyzer.infer_multimodal_diagnosis(
            spectral_metrics=final_metrics,
            sensor_data=active_sensor_dict
        )
        final_metrics["ai_diagnosis"] = ai_diag_avg

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
            spots_count=final_metrics.get("spots_count", 0),
            fruits_count=0,
            healthy_tissue_pct=final_metrics.get("healthy_tissue_pct", final_metrics.get("health_index", 100.0)),
            chlorosis_pct=final_metrics.get("chlorosis_pct", 0.0),
            necrosis_pct=final_metrics.get("necrosis_pct", 0.0),
            gli_index=final_metrics.get("gli_index", 0.0),
            vari_index=final_metrics.get("vari_index", 0.0),
            exg_index=final_metrics.get("exg_index", 0.0),
            ai_diagnosis_label=ai_diag_avg.get("diagnosis_label"),
            ai_confidence=ai_diag_avg.get("confidence_pct", 94.0),
            ai_diagnosis_json=json.dumps(ai_diag_avg, ensure_ascii=False),
            image_path_cenital_orig=cenital_paths.get("orig"),
            image_path_cenital_proc=cenital_paths.get("proc"),
            image_path_lateral_orig=lateral_paths.get("orig"),
            image_path_lateral_proc=lateral_paths.get("proc"),
            image_path_spectral_map=cenital_paths.get("spectral")
        )
        db.session.add(avg_record)

        # 2. Métricas individuales por cada una de las 5 tomas
        if individual_metrics:
            for item in individual_metrics:
                idx = item.get("photo_index", 1)
                t_exact = item.get("capture_time", session_timestamp)
                ai_diag_ind = self.pipeline.ai_analyzer.infer_multimodal_diagnosis(
                    spectral_metrics=item,
                    sensor_data=active_sensor_dict
                )
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
                    spots_count=item.get("spots_count", 0),
                    fruits_count=0,
                    healthy_tissue_pct=item.get("healthy_tissue_pct", item.get("health_index", 100.0)),
                    chlorosis_pct=item.get("chlorosis_pct", 0.0),
                    necrosis_pct=item.get("necrosis_pct", 0.0),
                    gli_index=item.get("gli_index", 0.0),
                    vari_index=item.get("vari_index", 0.0),
                    exg_index=item.get("exg_index", 0.0),
                    ai_diagnosis_label=ai_diag_ind.get("diagnosis_label"),
                    ai_confidence=ai_diag_ind.get("confidence_pct", 94.0),
                    ai_diagnosis_json=json.dumps(ai_diag_ind, ensure_ascii=False),
                    image_path_cenital_orig=item.get("cenital_orig"),
                    image_path_cenital_proc=item.get("proc") if "proc" in item else item.get("cenital_proc"),
                    image_path_lateral_orig=item.get("lateral_orig"),
                    image_path_lateral_proc=item.get("lateral_proc"),
                    image_path_spectral_map=item.get("spectral_map")
                )
                db.session.add(ind_record)

        db.session.commit()
        return session_record.id

    def ensure_metric_ai_analysis(
        self,
        metric: BiometricMetric,
        sensor_reading: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Garantiza que una métrica biométrica (incluso de sesiones históricas previas)
        cuente con su Mapa Térmico de Clorofila en disco y su diagnóstico neuronal ONNX.
        Si aún no se ha generado, lo calcula al vuelo y lo persiste de forma idempotente.
        """
        if metric is None:
            return {}

        sensor_dict = {}
        if sensor_reading is not None:
            sensor_dict = {
                "temperature": getattr(sensor_reading, "temperature", None),
                "humidity": getattr(sensor_reading, "humidity", None),
                "uv_solar": getattr(sensor_reading, "uv_solar", None),
                "motor_current": getattr(sensor_reading, "motor_current", None),
                "water_ph": getattr(sensor_reading, "water_ph", None),
                "ec_conductivity": getattr(sensor_reading, "ec_conductivity", None),
                "turbidity_ntu": getattr(sensor_reading, "turbidity_ntu", None),
                "dissolved_oxygen_mg_l": getattr(sensor_reading, "dissolved_oxygen_mg_l", None),
                "water_temp": getattr(sensor_reading, "water_temp", None),
            }

        needs_commit = False
        spectral_rel = getattr(metric, "image_path_spectral_map", None) or ""
        spectral_abs = os.path.join(
            config.DATA_DIR,
            spectral_rel.replace("data/", "", 1).lstrip("/")
        ) if spectral_rel else ""

        # Si existe la foto cenital original en disco pero aún no existe el mapa térmico espectral, generarlo al vuelo
        orig_rel = metric.image_path_cenital_orig or ""
        if orig_rel and (not spectral_rel or not os.path.isfile(spectral_abs)):
            orig_abs = os.path.join(
                config.DATA_DIR,
                orig_rel.replace("data/", "", 1).replace("static/data/", "", 1).lstrip("/")
            )
            if not os.path.isfile(orig_abs):
                orig_abs = os.path.join(config.STATIC_DIR, orig_rel.replace("static/", "", 1).lstrip("/"))

            if os.path.isfile(orig_abs):
                try:
                    proc_rel = metric.image_path_cenital_proc or orig_rel
                    proc_abs = os.path.join(
                        config.DATA_DIR,
                        proc_rel.replace("data/", "", 1).replace("static/data/", "", 1).lstrip("/")
                    )
                    spec_dir = os.path.dirname(proc_abs)
                    spec_name = f"spectral_{os.path.basename(proc_abs)}"
                    spec_abs_target = os.path.join(spec_dir, spec_name)

                    sys_cfg = self.config_repo.get()
                    crop_t = metric.session.crop_type if metric.session else "cebollin"
                    prof = self.crop_repo.get_by_type(crop_t) or self.crop_repo.get_by_type("cebollin")

                    import cv2
                    img_bgr = cv2.imread(orig_abs)
                    if img_bgr is not None and prof is not None:
                        cx, cy, rad = self.pipeline.detect_blue_basket_roi(img_bgr, config=sys_cfg)
                        roi_m = getattr(cv2, "circle")(
                            __import__("numpy").zeros(img_bgr.shape[:2], dtype="uint8"),
                            (cx, cy), rad, 255, -1
                        )
                        raw_m = self.pipeline.segmenter.create_mask(img_bgr, prof)
                        mask = cv2.bitwise_and(raw_m, roi_m)
                        spec_res = self.pipeline.ai_analyzer.analyze_canopy_spectrum_and_tissues(
                            image_bgr=img_bgr,
                            plant_mask=mask,
                            roi_circle=(cx, cy, rad),
                            spectral_output_path=spec_abs_target
                        )
                        rel_spec_out = "data/" + os.path.relpath(spec_abs_target, config.DATA_DIR).replace("\\", "/")
                        metric.image_path_spectral_map = rel_spec_out
                        metric.healthy_tissue_pct = spec_res["healthy_tissue_pct"]
                        metric.chlorosis_pct = spec_res["chlorosis_pct"]
                        metric.necrosis_pct = spec_res["necrosis_pct"]
                        metric.gli_index = spec_res["gli_index"]
                        metric.vari_index = spec_res["vari_index"]
                        metric.exg_index = spec_res["exg_index"]
                        needs_commit = True
                except Exception:
                    pass

        # Si aún no tiene diagnóstico JSON o índices espectrales inicializados, inferirlos
        diag_dict = metric.get_ai_diagnosis_dict()
        if not diag_dict or not metric.ai_diagnosis_label:
            h_pct = float(metric.healthy_tissue_pct if metric.healthy_tissue_pct is not None else (metric.health_index or 100.0))
            c_pct = float(metric.chlorosis_pct if metric.chlorosis_pct is not None else max(0.0, (100.0 - h_pct) * 0.72))
            n_pct = float(metric.necrosis_pct if metric.necrosis_pct is not None else max(0.0, 100.0 - h_pct - c_pct))
            gli_v = float(metric.gli_index if (metric.gli_index and metric.gli_index != 0.0) else round(0.04 + (h_pct / 100.0) * 0.24, 3))
            vari_v = float(metric.vari_index if (metric.vari_index and metric.vari_index != 0.0) else round(0.02 + (h_pct / 100.0) * 0.19, 3))
            exg_v = float(metric.exg_index if (metric.exg_index and metric.exg_index != 0.0) else round(0.08 + (h_pct / 100.0) * 0.28, 3))

            spec_input = {
                "healthy_tissue_pct": round(h_pct, 2),
                "chlorosis_pct": round(c_pct, 2),
                "necrosis_pct": round(n_pct, 2),
                "gli_index": gli_v,
                "vari_index": vari_v,
                "exg_index": exg_v,
            }
            diag_dict = self.pipeline.ai_analyzer.infer_multimodal_diagnosis(
                spectral_metrics=spec_input,
                sensor_data=sensor_dict
            )
            metric.healthy_tissue_pct = spec_input["healthy_tissue_pct"]
            metric.chlorosis_pct = spec_input["chlorosis_pct"]
            metric.necrosis_pct = spec_input["necrosis_pct"]
            metric.gli_index = spec_input["gli_index"]
            metric.vari_index = spec_input["vari_index"]
            metric.exg_index = spec_input["exg_index"]
            metric.ai_diagnosis_label = diag_dict.get("diagnosis_label")
            metric.ai_confidence = diag_dict.get("confidence_pct", 94.0)
            metric.ai_diagnosis_json = json.dumps(diag_dict, ensure_ascii=False)
            needs_commit = True

        if needs_commit:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        diag_dict["image_path_spectral_map"] = metric.image_path_spectral_map or ""
        return diag_dict
