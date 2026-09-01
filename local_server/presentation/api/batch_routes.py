import os
import json
import shutil
import tempfile
import zipfile
import re
from flask import request, jsonify, session
from core.security import SecurityService
from application.services import VisionApplicationService, SystemService
from . import api_bp

vision_service = VisionApplicationService()
system_service = SystemService()

@api_bp.route('/api/config', methods=['GET'])
def get_config():
    config = system_service.get_config()
    return jsonify(config.to_json())

@api_bp.route('/api/scan_usb', methods=['GET'])
def scan_usb_drives():
    try:
        batches = vision_service.detect_connected_usb_drives()
        return jsonify({
            "status": "success",
            "count": len(batches),
            "batches": batches,
            "drives": batches
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al escanear unidades USB: {e}"}), 500

@api_bp.route('/api/process_usb_path', methods=['POST'])
def process_usb_path():
    data = request.json or {}
    folder_path = data.get("folder_path") or data.get("path") or data.get("mountpoint")
    crop_type = data.get("crop_type")
    period = data.get("period", "Día 1")
    plant_id = data.get("plant_id") or session.get("active_plant_id", 1)
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({"status": "error", "message": f"Ruta no válida o no encontrada: {folder_path}"}), 400
        
    try:
        res = vision_service.process_folder_batch(
            folder_path, 
            crop_type=crop_type, 
            period=period,
            plant_id=int(plant_id)
        )
        return jsonify({
            "status": "success",
            "message": f"Lote procesado con éxito para Canastilla #{plant_id} ({period})",
            "data": res
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al procesar lote USB: {e}"}), 500

@api_bp.route('/api/process_usb_mount', methods=['POST'])
def process_usb_mount():
    """Procesa recursivamente todas las carpetas del día o lote detectado."""
    data = request.json or {}
    mountpoint = data.get("mountpoint") or data.get("folder_path")
    target_date = data.get("target_date")
    plant_id = data.get("plant_id") or session.get("active_plant_id", 1)
    
    if not mountpoint or not os.path.exists(mountpoint):
        return jsonify({"status": "error", "message": f"Ruta de memoria USB no encontrada: {mountpoint}"}), 400

    batches = vision_service.detect_connected_usb_drives()
    target_batches = [b for b in batches if mountpoint in b["path"] or b["path"] in mountpoint or mountpoint == b.get("drive_root")]
    
    if not target_batches:
        # Si la ruta directa contiene fotos
        target_batches = [{"path": mountpoint, "period_str": "Muestreo General", "date_str": target_date or "Día 1"}]

    processed_results = []
    for b in target_batches:
        b_path = b["path"]
        p_name = b.get("period_str", "Muestreo")
        if target_date:
            p_name = f"{target_date} - {p_name}"
        try:
            r = vision_service.process_folder_batch(b_path, period=p_name, plant_id=int(plant_id))
            processed_results.append(r)
        except Exception as err:
            pass

    if not processed_results:
        return jsonify({"status": "error", "message": "No se encontraron fotos válidas para procesar en la unidad."}), 400

    return jsonify({
        "status": "success",
        "message": f"Se procesaron {len(processed_results)} turnos/lotes exitosamente para la Canastilla #{plant_id}.",
        "processed_batches": processed_results
    })

@api_bp.route('/api/upload_manual_batch', methods=['POST'])
def upload_manual_batch():
    files = request.files.getlist("images") or request.files.getlist("file") or request.files.getlist("files")
    crop_type = request.form.get("crop_type")
    period = request.form.get("period", "Día 1")
    plant_id = request.form.get("plant_id") or session.get("active_plant_id", 1)
    
    if not files or len(files) == 0 or (len(files) == 1 and files[0].filename == ''):
        return jsonify({"status": "error", "message": "No se seleccionaron archivos para subir."}), 400
        
    temp_dir = tempfile.mkdtemp(prefix="sifma_upload_")
    processed_results = []
    
    try:
        zip_files = []
        regular_files = []
        
        for f in files:
            safe_name = SecurityService.sanitize_filename(f.filename)
            if safe_name.lower().endswith(".zip"):
                zip_files.append((f, safe_name))
            else:
                regular_files.append((f, safe_name))

        # 1. Si se subieron archivos ZIP
        if zip_files:
            for f_obj, z_name in zip_files:
                z_path = os.path.join(temp_dir, z_name)
                f_obj.save(z_path)
                
                extract_subfolder = os.path.join(temp_dir, "extracted_" + z_name.replace(".zip", ""))
                os.makedirs(extract_subfolder, exist_ok=True)
                
                with zipfile.ZipFile(z_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_subfolder)
                    
                # Buscar subcarpetas por turnos (manana, medio_dia, tarde)
                found_turn_dirs = []
                for r_dir, d_list, f_list in os.walk(extract_subfolder):
                    imgs = [img for img in f_list if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    if imgs:
                        found_turn_dirs.append((r_dir, imgs))
                        
                if found_turn_dirs:
                    for t_dir, t_imgs in found_turn_dirs:
                        t_name = os.path.basename(t_dir).lower()
                        turn_label = "Muestreo"
                        if 'manana' in t_name or 'mañana' in t_name:
                            turn_label = "Mañana"
                        elif 'medio_dia' in t_name or 'mediodia' in t_name:
                            turn_label = "Mediodía"
                        elif 'tarde' in t_name:
                            turn_label = "Tarde"
                        else:
                            turn_label = os.path.basename(t_dir).replace('_', ' ').title()
                            
                        full_period_label = f"{period} - {turn_label}" if period else turn_label
                        
                        r_batch = vision_service.process_folder_batch(
                            t_dir, 
                            crop_type=crop_type, 
                            period=full_period_label,
                            plant_id=int(plant_id)
                        )
                        processed_results.append(r_batch)
                else:
                    r_batch = vision_service.process_folder_batch(
                        extract_subfolder, 
                        crop_type=crop_type, 
                        period=period,
                        plant_id=int(plant_id)
                    )
                    processed_results.append(r_batch)

        # 2. Si se subieron archivos de imagen regulares
        if regular_files:
            regular_dir = os.path.join(temp_dir, "regular_images")
            os.makedirs(regular_dir, exist_ok=True)
            for f_obj, img_name in regular_files:
                f_obj.save(os.path.join(regular_dir, img_name))
                
            r_batch = vision_service.process_folder_batch(
                regular_dir, 
                crop_type=crop_type, 
                period=period,
                plant_id=int(plant_id)
            )
            processed_results.append(r_batch)
            
        if not processed_results:
            return jsonify({"status": "error", "message": "No se encontraron imágenes válidas dentro del archivo subido."}), 400

        return jsonify({
            "status": "success",
            "message": f"Se procesaron {len(processed_results)} lotes/turnos de fotos exitosamente para la Canastilla #{plant_id}.",
            "data": processed_results[0] if len(processed_results) == 1 else processed_results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error procesando archivos: {e}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@api_bp.route('/api/upload', methods=['POST'])
def upload_capture_session():
    return upload_manual_batch()
