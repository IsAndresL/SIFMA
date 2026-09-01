from flask import request, jsonify, Response, current_app, session
from application.services import TelemetryApplicationService, AnalyticsApplicationService
from . import api_bp

telemetry_service = TelemetryApplicationService.get_instance()
analytics_service = AnalyticsApplicationService()

@api_bp.route('/api/telemetry/ports', methods=['GET'])
def get_telemetry_ports():
    ports = telemetry_service.get_available_ports()
    return jsonify({"status": "success", "ports": ports})

@api_bp.route('/api/telemetry/start', methods=['POST'])
def start_telemetry():
    data = request.json or {}
    port = data.get("port", "USB_ANTENNA_AUTO")
    res = telemetry_service.start_acquisition(port=port, app=current_app._get_current_object())
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/stop', methods=['POST'])
def stop_telemetry():
    res = telemetry_service.stop_acquisition()
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/status', methods=['GET'])
def get_telemetry_status():
    status = telemetry_service.get_status()
    return jsonify({"status": "success", "telemetry": status})

@api_bp.route('/api/telemetry/timeline', methods=['GET'])
def get_telemetry_timeline():
    target_date = request.args.get("date")
    timeline_data = analytics_service.get_sensor_timeline_data(target_date=target_date)
    return jsonify(timeline_data)

@api_bp.route('/api/telemetry/upload_csv', methods=['POST'])
def upload_telemetry_csv():
    if 'file' not in request.files and 'csv_file' not in request.files:
        return jsonify({"status": "error", "message": "No se recibió ningún archivo CSV."}), 400
        
    f = request.files.get('file') or request.files.get('csv_file')
    if not f or f.filename == '':
        return jsonify({"status": "error", "message": "Archivo no válido."}), 400

    try:
        res = analytics_service.import_tower_csv(f.stream)
        if res.get("status") == "error":
            return jsonify(res), 400
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": "Error al procesar el archivo CSV."}), 500

@api_bp.route('/api/cross_analysis/export_csv', methods=['GET'])
def export_cross_analysis_csv():
    plant_id = request.args.get("plant_id", session.get("active_plant_id", 1))
    cross_data = analytics_service.get_cross_referenced_dataset(plant_id=int(plant_id))
    csv_content = analytics_service.generate_research_csv(cross_data)
    
    filename = f"sifma_investigacion_canastilla_{plant_id}.csv"
    return Response(
        csv_content.encode('utf-8-sig'),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
