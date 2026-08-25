import os
import json
import shutil
import tempfile
import zipfile
from flask import Blueprint, request, jsonify, session
from database import Config
from services.db_service import DatabaseService
from services.batch_processor import BatchProcessorService

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/config', methods=['GET'])
def get_config():
    config = DatabaseService.get_config()
    return jsonify(config.to_json())

@api_bp.route('/api/scan_usb', methods=['GET'])
def scan_usb_drives():
    try:
        batches = BatchProcessorService.detect_connected_usb_drives()
        return jsonify({
            "status": "success",
            "count": len(batches),
            "batches": batches
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
        res = BatchProcessorService.process_folder_batch(
            folder_path, 
            crop_type=crop_type, 
            period=period,
            plant_id=plant_id
        )
        return jsonify({
            "status": "success",
            "message": f"Lote de USB procesado con éxito para la Torre {plant_id} ({period})",
            "data": res
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            filename = f.filename
            if filename.endswith(".zip"):
                zip_path = os.path.join(temp_dir, filename)
                f.save(zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            else:
                f.save(os.path.join(temp_dir, filename))
                
        res = BatchProcessorService.process_folder_batch(
            temp_dir, 
            crop_type=crop_type, 
            period=period,
            plant_id=plant_id
        )
        return jsonify({
            "status": "success",
            "message": f"Archivos procesados con éxito para la Torre {plant_id} ({period})",
            "data": res
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            f.save(os.path.join(temp_dir, f.filename))
            
        res = BatchProcessorService.process_folder_batch(
            temp_dir, 
            crop_type=crop_type, 
            period=period, 
            sensor_data=sensor_data,
            plant_id=plant_id
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
