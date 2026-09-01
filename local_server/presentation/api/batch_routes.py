import os
import json
import shutil
import tempfile
import zipfile
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
            "batches": batches
        })
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al escanear unidades USB."}), 500

@api_bp.route('/api/process_usb_path', methods=['POST'])
def process_usb_path():
    data = request.json or {}
    folder_path = data.get("folder_path")
    crop_type = data.get("crop_type")
    period = data.get("period", "Día 1")
    plant_id = data.get("plant_id") or session.get("active_plant_id", 1)
    
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({"status": "error", "message": f"Ruta no válida: {folder_path}"}), 400
        
    try:
        res = vision_service.process_folder_batch(
            folder_path, 
            crop_type=crop_type, 
            period=period,
            plant_id=int(plant_id)
        )
        return jsonify({
            "status": "success",
            "message": f"Lote de USB procesado con éxito para la Torre {plant_id} ({period})",
            "data": res
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al procesar lote USB: {e}"}), 500

@api_bp.route('/api/upload_manual_batch', methods=['POST'])
def upload_manual_batch():
    files = request.files.getlist("images") or request.files.getlist("file")
    crop_type = request.form.get("crop_type")
    period = request.form.get("period", "Día 1")
    plant_id = request.form.get("plant_id") or session.get("active_plant_id", 1)
    
    if not files:
        return jsonify({"status": "error", "message": "No se recibieron archivos para procesar."}), 400
        
    temp_dir = tempfile.mkdtemp(prefix="sifma_upload_")
    try:
        for f in files:
            safe_name = SecurityService.sanitize_filename(f.filename)
            if safe_name.endswith(".zip"):
                zip_path = os.path.join(temp_dir, safe_name)
                f.save(zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        filename = os.path.basename(member)
                        if not filename:
                            continue
                        source = zip_ref.open(member)
                        target = open(os.path.join(temp_dir, SecurityService.sanitize_filename(filename)), "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)
            else:
                f.save(os.path.join(temp_dir, safe_name))
                
        res = vision_service.process_folder_batch(
            temp_dir, 
            crop_type=crop_type, 
            period=period,
            plant_id=int(plant_id)
        )
        return jsonify({
            "status": "success",
            "message": f"Archivos procesados con éxito para la Torre {plant_id} ({period})",
            "data": res
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error procesando archivos subidos: {e}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@api_bp.route('/api/upload', methods=['POST'])
def upload_capture_session():
    files = request.files.getlist("files") or request.files.getlist("images")
    if not files:
        return jsonify({"status": "error", "message": "No files attached"}), 400
        
    temp_dir = tempfile.mkdtemp(prefix="sifma_online_")
    try:
        period = request.form.get("period", "Día 1")
        crop_type = request.form.get("crop_type")
        plant_id = request.form.get("plant_id") or session.get("active_plant_id", 1)
        sensor_json = request.form.get("sensor_data", "{}")
        sensor_data = json.loads(sensor_json) if isinstance(sensor_json, str) else sensor_json
        
        for f in files:
            safe_name = SecurityService.sanitize_filename(f.filename)
            f.save(os.path.join(temp_dir, safe_name))
            
        res = vision_service.process_folder_batch(
            temp_dir, 
            crop_type=crop_type, 
            period=period, 
            sensor_data=sensor_data,
            plant_id=int(plant_id)
        )
        return jsonify({
            "status": "success",
            "message": "Lote procesado",
            "data": res
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
