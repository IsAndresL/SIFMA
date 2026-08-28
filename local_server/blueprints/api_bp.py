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

# =========================================================================
# ENDPOINTS DE TELEMETRIA Y ANTENA USB EN TIEMPO REAL
# =========================================================================

@api_bp.route('/api/telemetry/ports', methods=['GET'])
def get_telemetry_ports():
    from services.telemetry_service import TelemetryService
    telemetry = TelemetryService.get_instance()
    ports = telemetry.get_available_ports()
    return jsonify({"status": "success", "ports": ports})

@api_bp.route('/api/telemetry/start', methods=['POST'])
def start_telemetry():
    from flask import current_app
    from services.telemetry_service import TelemetryService
    data = request.json or {}
    port = data.get("port", "USB_ANTENNA_AUTO")
    
    telemetry = TelemetryService.get_instance()
    res = telemetry.start_acquisition(port=port, app=current_app._get_current_object())
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/stop', methods=['POST'])
def stop_telemetry():
    from services.telemetry_service import TelemetryService
    telemetry = TelemetryService.get_instance()
    res = telemetry.stop_acquisition()
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/status', methods=['GET'])
def get_telemetry_status():
    from services.telemetry_service import TelemetryService
    telemetry = TelemetryService.get_instance()
    status = telemetry.get_status()
    return jsonify({"status": "success", "telemetry": status})

@api_bp.route('/api/cross_analysis/export_csv', methods=['GET'])
def export_cross_analysis_csv():
    from flask import Response
    from services.analytics_service import AnalyticsCrossService
    plant_id = request.args.get("plant_id", session.get("active_plant_id", 1))
    
    cross_data = AnalyticsCrossService.get_cross_referenced_dataset(plant_id=plant_id)
    csv_content = AnalyticsCrossService.generate_research_csv(cross_data)
    
    filename = f"sifma_investigacion_canastilla_{plant_id}.csv"
    return Response(
        csv_content.encode('utf-8-sig'),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@api_bp.route('/api/telemetry/upload_csv', methods=['POST'])
def upload_telemetry_csv():
    from services.analytics_service import AnalyticsCrossService
    if 'file' not in request.files and 'csv_file' not in request.files:
        return jsonify({"status": "error", "message": "No se recibió ningún archivo CSV."}), 400
        
    f = request.files.get('file') or request.files.get('csv_file')
    if not f or f.filename == '':
        return jsonify({"status": "error", "message": "Archivo no válido."}), 400

    try:
        res = AnalyticsCrossService.import_tower_csv(f.stream)
        if res.get("status") == "error":
            return jsonify(res), 400
        return jsonify(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Error al procesar el archivo CSV: {e}"}), 500

@api_bp.route('/api/telemetry/timeline', methods=['GET'])
def get_telemetry_timeline():
    from services.analytics_service import AnalyticsCrossService
    target_date = request.args.get("date")
    timeline_data = AnalyticsCrossService.get_sensor_timeline_data(target_date=target_date)
    return jsonify(timeline_data)

# =========================================================================
# ENDPOINTS DE CONCLUSIONES E INFERENCIAS AGRONOMICAS DEL INVESTIGADOR
# =========================================================================

@api_bp.route('/api/agronomic_conclusions', methods=['GET', 'POST'])
def handle_agronomic_conclusions():
    from database import db, AgronomicConclusion
    if request.method == 'GET':
        plant_id = request.args.get('plant_id', session.get('active_plant_id', 1))
        date_str = request.args.get('date_str')
        period_type = request.args.get('period_type')
        
        query = AgronomicConclusion.query.filter_by(plant_id=int(plant_id))
        if date_str and date_str != 'todos':
            query = query.filter_by(date_str=date_str)
        if period_type and period_type != 'todos':
            query = query.filter_by(period_type=period_type)
            
        conclusions = query.order_by(AgronomicConclusion.timestamp.desc()).all()
        return jsonify({
            "status": "success",
            "count": len(conclusions),
            "conclusions": [c.to_dict() for c in conclusions]
        })
        
    elif request.method == 'POST':
        data = request.json or {}
        date_str = data.get('date_str')
        general_conclusion = data.get('general_conclusion', '').strip()
        
        if not date_str or not general_conclusion:
            return jsonify({"status": "error", "message": "La fecha y la conclusión general son requeridas."}), 400
            
        plant_id = data.get('plant_id') or session.get('active_plant_id', 1)
        new_note = AgronomicConclusion(
            plant_id=int(plant_id),
            date_str=date_str,
            period_type=data.get('period_type', 'diario'),
            growth_obs=data.get('growth_obs', ''),
            climate_obs=data.get('climate_obs', ''),
            nutrition_obs=data.get('nutrition_obs', ''),
            general_conclusion=general_conclusion,
            author=data.get('author', 'Investigador SIFMA')
        )
        db.session.add(new_note)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Conclusión agronómica guardada con éxito.",
            "note": new_note.to_dict()
        })

@api_bp.route('/api/agronomic_conclusions/<int:note_id>', methods=['DELETE'])
def delete_agronomic_conclusion(note_id):
    from database import db, AgronomicConclusion
    note = AgronomicConclusion.query.get(note_id)
    if not note:
        return jsonify({"status": "error", "message": "Nota no encontrada."}), 404
        
    db.session.delete(note)
    db.session.commit()
    return jsonify({"status": "success", "message": "Conclusión eliminada exitosamente."})

# =========================================================================
# ENDPOINTS DE ELIMINACION DE PERIODOS DE FOTOS Y LECTURAS DE SENSORES
# =========================================================================

@api_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_capture_session(session_id):
    from database import db, CaptureSession
    from flask import current_app
    session_record = CaptureSession.query.get(session_id)
    if not session_record:
        return jsonify({"status": "error", "message": "Sesión no encontrada."}), 404

    # Eliminar archivos de imagen del disco
    static_folder = current_app.static_folder
    batch_dirs_to_clean = set()
    
    for m in session_record.metrics:
        for path_attr in ['image_path_cenital_orig', 'image_path_cenital_proc', 'image_path_lateral_orig', 'image_path_lateral_proc']:
            rel_path = getattr(m, path_attr, None)
            if rel_path:
                full_path = os.path.join(static_folder, rel_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        batch_dirs_to_clean.add(os.path.dirname(full_path))
                    except Exception:
                        pass

    # Eliminar carpetas de lote si quedaron vacias
    for b_dir in batch_dirs_to_clean:
        try:
            if os.path.exists(b_dir) and not os.listdir(b_dir):
                os.rmdir(b_dir)
        except Exception:
            pass

    db.session.delete(session_record)
    db.session.commit()
    return jsonify({"status": "success", "message": "Período de fotos y métricas eliminados exitosamente."})

@api_bp.route('/api/sessions/by_date', methods=['DELETE'])
def delete_sessions_by_date():
    from database import db, CaptureSession
    from flask import current_app
    date_str = request.args.get('date')
    plant_id = request.args.get('plant_id', session.get('active_plant_id', 1))

    if not date_str:
        return jsonify({"status": "error", "message": "Parámetro 'date' es requerido."}), 400

    query = CaptureSession.query.filter_by(plant_id=int(plant_id))
    if date_str != 'todos':
        query = query.filter(db.func.strftime('%Y-%m-%d', CaptureSession.timestamp) == date_str)

    sessions_to_del = query.all()
    count = len(sessions_to_del)
    static_folder = current_app.static_folder

    for s in sessions_to_del:
        for m in s.metrics:
            for path_attr in ['image_path_cenital_orig', 'image_path_cenital_proc', 'image_path_lateral_orig', 'image_path_lateral_proc']:
                rel_path = getattr(m, path_attr, None)
                if rel_path:
                    full_path = os.path.join(static_folder, rel_path)
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except Exception:
                            pass
        db.session.delete(s)

    db.session.commit()
    return jsonify({"status": "success", "message": f"Se eliminaron {count} períodos de fotos correspondientes a la fecha {date_str}."})

@api_bp.route('/api/telemetry/by_date', methods=['DELETE'])
def delete_telemetry_by_date():
    from database import db, SensorReading
    date_str = request.args.get('date')

    if not date_str:
        return jsonify({"status": "error", "message": "Parámetro 'date' es requerido."}), 400

    if date_str == 'todos':
        deleted_count = SensorReading.query.delete()
    else:
        deleted_count = SensorReading.query.filter(
            db.func.strftime('%Y-%m-%d', SensorReading.timestamp) == date_str
        ).delete()

    db.session.commit()
    return jsonify({"status": "success", "message": f"Se eliminaron {deleted_count} lecturas de sensores ({date_str}).", "deleted_count": deleted_count})


