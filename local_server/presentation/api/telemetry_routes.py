from flask import request, jsonify, Response, current_app, session
from application.services import TelemetryApplicationService, AnalyticsApplicationService
from infrastructure.database.repositories import SensorRepository
from . import api_bp

telemetry_service = TelemetryApplicationService.get_instance()
analytics_service = AnalyticsApplicationService()
sensor_repo = SensorRepository()

@api_bp.route('/api/telemetry/ports', methods=['GET'])
@api_bp.route('/api/scan_ports', methods=['GET'])
def get_telemetry_ports():
    ports = telemetry_service.get_available_ports()
    return jsonify({"status": "success", "ports": ports})

@api_bp.route('/api/telemetry/start', methods=['POST'])
@api_bp.route('/api/start_telemetry_recording', methods=['POST'])
def start_telemetry():
    data = request.json or {}
    port = data.get("port", "USB_ANTENNA_AUTO")
    res = telemetry_service.start_acquisition(port=port, app=current_app._get_current_object())
    if res.get("status") == "error":
        return jsonify(res), 400
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/stop', methods=['POST'])
@api_bp.route('/api/stop_telemetry_recording', methods=['POST'])
def stop_telemetry():
    res = telemetry_service.stop_acquisition()
    return jsonify({"status": "success", "data": res})

@api_bp.route('/api/telemetry/status', methods=['GET'])
def get_telemetry_status():
    status = telemetry_service.get_status()
    return jsonify({"status": "success", "telemetry": status})

@api_bp.route('/api/telemetry/live', methods=['GET'])
def get_live_telemetry_sample():
    sample = telemetry_service.adapter.read_sample()
    return jsonify({"status": "success", "sample": sample})

@api_bp.route('/api/telemetry/timeline', methods=['GET'])
def get_telemetry_timeline():
    target_date = request.args.get("date")
    plant_id = request.args.get("plant_id", type=int) or session.get("active_plant_id", 1)
    timeline_data = analytics_service.get_sensor_timeline_data(target_date=target_date, plant_id=plant_id)
    return jsonify(timeline_data)

@api_bp.route('/api/telemetry/upload_csv', methods=['POST'])
@api_bp.route('/api/import_tower_csv', methods=['POST'])
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
        return jsonify({"status": "error", "message": f"Error al procesar el archivo CSV: {str(e)}"}), 500

@api_bp.route('/api/delete_telemetry_by_date', methods=['POST'])
def handle_delete_telemetry_by_date():
    data = request.json or {}
    date_str = data.get("date_str") or request.args.get('date')
    plant_id = data.get("plant_id") or request.args.get('plant_id', type=int) or session.get("active_plant_id", 1)

    if not date_str:
        return jsonify({"status": "error", "message": "Debe especificar la fecha a eliminar."}), 400

    try:
        from application.services import SystemService
        from infrastructure.database.repositories import CaptureSessionRepository
        from infrastructure.database.connection import db
        sys_svc = SystemService()
        cfg = sys_svc.get_config()
        shared_telemetry = getattr(cfg, 'shared_telemetry', True)

        if not shared_telemetry and int(plant_id) > 1:
            s_repo = CaptureSessionRepository()
            sessions = s_repo.get_by_date_and_plant(date_str, int(plant_id))
            unlinked = 0
            for s in sessions:
                if s.sensor_reading_id:
                    s.sensor_reading_id = None
                    unlinked += 1
            db.session.commit()
            return jsonify({
                "status": "success", 
                "message": f"Se desvincularon las lecturas de telemetría de {unlinked} sesiones en la Canastilla #{plant_id}.",
                "deleted_count": unlinked
            })
        else:
            deleted = sensor_repo.delete_by_date(date_str)
            return jsonify({"status": "success", "message": f"Se eliminaron {deleted} registros de telemetría.", "deleted_count": deleted})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al eliminar registros: {str(e)}"}), 500

@api_bp.route('/api/telemetry/sync_tower', methods=['POST'])
@api_bp.route('/api/sync_tower_telemetry', methods=['POST'])
def handle_sync_tower_telemetry():
    try:
        res = analytics_service.sync_tower_telemetry_across_canastillas()
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al sincronizar telemetría: {str(e)}"}), 500

@api_bp.route('/api/telemetry/download_csv', methods=['GET'])
@api_bp.route('/api/telemetry/download_active_csv', methods=['GET'])
def download_telemetry_csv():
    import io
    import csv
    from datetime import datetime

    target_date = request.args.get('date') or datetime.now().strftime("%Y-%m-%d")
    filename = f"telemetria_actualizada_{target_date}.csv"

    readings = sensor_repo.get_by_date(target_date)
    if not readings:
        readings = sensor_repo.get_by_date("todos")

    output = io.StringIO()
    # Delimitador punto y coma ';' con codificación UTF-8 BOM para apertura directa en Excel en columnas nativas
    writer = csv.writer(output, delimiter=';', lineterminator='\r\n')
    writer.writerow([
        "Fecha",
        "Hora",
        "pH Solución",
        "Turbidez (NTU)",
        "Conductividad Eléctrica (µS/cm)",
        "Oxigeno Disuelto (mg/L)",
        "temperatura de agua",
        "estado motor: 1-0",
        "Temperatura exterior (°C)",
        "Humedad relativa exterior (% HR)"
    ])
    
    for r in readings:
        fecha_str = r.timestamp.strftime("%d/%m/%Y") if r.timestamp else ""
        hora_str = r.timestamp.strftime("%I:%M:%S %p") if r.timestamp else ""
        
        ph_val = f"{r.water_ph:.2f}".replace('.', ',') if r.water_ph is not None else ""
        turb_val = f"{r.turbidity_ntu:.2f}".replace('.', ',') if r.turbidity_ntu is not None else ""
        ec_val = f"{r.ec_conductivity:.1f}".replace('.', ',') if r.ec_conductivity is not None else ""
        do_val = f"{r.dissolved_oxygen_mg_l:.2f}".replace('.', ',') if r.dissolved_oxygen_mg_l is not None else ""
        water_t_val = f"{r.water_temp:.1f}".replace('.', ',') if getattr(r, 'water_temp', None) is not None else ""
        motor_st_val = int(r.motor_state) if getattr(r, 'motor_state', None) is not None else (1 if (r.motor_current and r.motor_current > 0.1) else 0)
        temp_val = f"{r.temperature:.2f}".replace('.', ',') if r.temperature is not None else ""
        hum_val = f"{r.humidity:.1f}".replace('.', ',') if r.humidity is not None else ""

        writer.writerow([
            fecha_str,
            hora_str,
            ph_val,
            turb_val,
            ec_val,
            do_val,
            water_t_val,
            motor_st_val,
            temp_val,
            hum_val
        ])

    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

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

@api_bp.route('/api/daily_summary/export_csv', methods=['GET'])
@api_bp.route('/api/export_daily_summary_csv', methods=['GET'])
def export_daily_summary_csv():
    from datetime import datetime
    target_date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    plant_id = request.args.get("plant_id", type=int) or session.get("active_plant_id", 1)
    csv_content = analytics_service.generate_daily_summary_csv(target_date=target_date, plant_id=plant_id)
    
    filename = f"sifma_resumen_diario_{target_date}_canastilla_{plant_id}.csv"
    return Response(
        csv_content.encode('utf-8-sig'),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@api_bp.route('/api/calendar/month_data', methods=['GET'])
def get_calendar_month_data_api():
    from datetime import datetime
    now = datetime.now()
    year = request.args.get('year', type=int) or now.year
    month = request.args.get('month', type=int) or now.month
    plant_id = request.args.get('plant_id', type=int) or session.get('active_plant_id', 1)
    data = analytics_service.get_calendar_month_data(year=year, month=month, plant_id=plant_id)
    return jsonify(data)

@api_bp.route('/api/calendar/day_detail', methods=['GET'])
def get_calendar_day_detail_api():
    date_str = request.args.get('date')
    plant_id = request.args.get('plant_id', type=int) or session.get('active_plant_id', 1)
    if not date_str:
        return jsonify({"status": "error", "message": "Parámetro date requerido"}), 400
    data = analytics_service.get_day_detail(date_str=date_str, plant_id=plant_id)
    return jsonify(data)

@api_bp.route('/api/benchmark/data', methods=['GET'])
def get_benchmark_data_api():
    data = analytics_service.get_inter_plant_benchmark_data()
    return jsonify(data)

@api_bp.route('/api/weather', methods=['GET'])
def get_weather_api():
    from application.services import WeatherService, SystemService
    sys_svc = SystemService()
    cfg = sys_svc.get_config()
    lat = getattr(cfg, 'latitude', None) or 11.2408
    lon = getattr(cfg, 'longitude', None) or -74.1990
    city = getattr(cfg, 'city_name', None) or "Santa Marta, Magdalena"
    
    w_svc = WeatherService.get_instance()
    w_data = w_svc.get_current_weather(lat=lat, lon=lon, city_name=city)
    return jsonify({"status": "success", "weather": w_data, "location": {"lat": lat, "lon": lon, "city": city}})

@api_bp.route('/api/config/location', methods=['POST'])
def update_location_api():
    from application.services import SystemService, WeatherService
    from infrastructure.database.connection import db
    
    data = request.json or {}
    lat = data.get('latitude')
    lon = data.get('longitude')
    city = data.get('city_name')
    
    if lat is None or lon is None:
        return jsonify({"status": "error", "message": "Latitud y longitud son requeridas."}), 400
        
    try:
        sys_svc = SystemService()
        cfg = sys_svc.get_config()
        cfg.latitude = float(lat)
        cfg.longitude = float(lon)
        if city:
            cfg.city_name = str(city).strip()
        db.session.commit()
        
        w_svc = WeatherService.get_instance()
        w_svc.clear_cache()
        new_weather = w_svc.get_current_weather(lat=cfg.latitude, lon=cfg.longitude, city_name=cfg.city_name)
        
        return jsonify({
            "status": "success",
            "message": f"Ubicación actualizada a {cfg.city_name} ({cfg.latitude}, {cfg.longitude})",
            "weather": new_weather
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al guardar ubicación: {str(e)}"}), 500

