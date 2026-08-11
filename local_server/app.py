import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

from database import db, Config, CropProfile, SensorReading, CaptureSession, BiometricMetric, init_db_data
import vision_pipeline

app = Flask(__name__)

# Configuración de base de datos local SQLite
db_path = os.path.join(os.path.dirname(__file__), "sifma.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sifma_secret_key_12345'

# Inicializar Base de Datos con la App
db.init_app(app)

# ----------------- FILTRO DE AUTENTICACIÓN (LOGIN) -----------------
@app.before_request
def require_login():
    """Intercepta peticiones para forzar inicio de sesión en vistas privadas."""
    # Endpoints que no requieren autenticación (API del nodo e imágenes estáticas)
    allowed_endpoints = ['login', 'static', 'upload_capture_session', 'get_config']
    
    if request.endpoint and request.endpoint not in allowed_endpoints:
        if not session.get('logged_in'):
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Vista de inicio de sesión premium."""
    error = None
    if session.get('logged_in'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Credenciales de acceso seguras por defecto para SIFMA
        if username == 'admin' and password == 'sifma2026':
            session['logged_in'] = True
            session.permanent = True  # Dura hasta que se cierre el navegador
            return redirect(url_for('index'))
        else:
            error = "Usuario o contraseña incorrectos."
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Cierra la sesión de usuario y redirige al inicio de sesión."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Asegurar carpetas estáticas para guardar imágenes subidas y procesadas
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "data", "uploads")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "static", "data", "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ----------------- RUTAS DEL DASHBOARD WEB -----------------

@app.route('/')
def index():
    """Ruta principal: Muestra el Dashboard con gráficas y datos en tiempo real."""
    # Obtener configuración actual
    config = Config.query.first()
    if not config:
        # Fallback por si no se ha inicializado
        return "Inicializando base de datos... Por favor recarga la página."

    # Obtener lecturas de sensores (últimas 30 para las gráficas)
    sensors = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(30).all()
    # Invertir para orden cronológico
    sensors.reverse()

    # Obtener histórico de métricas biométricas filtrado por la especie seleccionada
    sessions = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).all()
    
    # Obtener perfiles de cultivos para el selector
    profiles = CropProfile.query.all()
    selected_profile = CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()

    # Consolidar datos de crecimiento por sesión individual en orden cronológico (izquierda a derecha)
    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    
    for s in chronological_sessions:
        if s.metrics:
            metric = s.metrics[0] # Tomamos la primera métrica asociada
            label_str = s.timestamp.strftime('%d/%m %H:%M')
            growth_data.append({
                "date": label_str,
                "area": round(metric.foliar_area_cm2, 2),
                "height": round(metric.plant_height_cm, 2),
                "diameter": round(metric.stem_diameter_mm, 2),
                "health": round(metric.health_index, 2)
            })

    # Últimas métricas registradas para el cultivo activo
    latest_metric = None
    latest_session = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).first()
    if latest_session and latest_session.metrics:
        latest_metric = latest_session.metrics[0]

    # Obtener las últimas 5 sesiones de captura para el historial de la tabla (filtrado por cultivo activo)
    recent_sessions = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).limit(5).all()

    # Último sensor leído
    latest_sensor = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()

    return render_template(
        'dashboard.html',
        config=config,
        selected_profile=selected_profile,
        profiles=profiles,
        sensors=sensors,
        latest_sensor=latest_sensor,
        latest_metric=latest_metric,
        latest_session=latest_session,
        recent_sessions=recent_sessions,
        growth_data=growth_data
    )

@app.route('/gallery')
def gallery():
    """Muestra la galería interactiva de imágenes (original vs. procesado)."""
    config = Config.query.first()
    sessions = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).all()
    return render_template('gallery.html', sessions=sessions, config=config)

@app.route('/config')
def configuration_panel():
    """Muestra el panel de configuración del sistema y perfiles de segmentación."""
    config = Config.query.first()
    profiles = CropProfile.query.all()
    selected_profile = CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()
    
    return render_template(
        'config.html', 
        config=config, 
        profiles=profiles, 
        selected_profile=selected_profile
    )

@app.route('/sensors')
def detailed_sensors():
    """Muestra la telemetría detallada con gráficos individuales para cada sensor."""
    config = Config.query.first()
    sensors = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(30).all()
    sensors.reverse()
    
    # Obtener última lectura de sensores para las tarjetas KPI de telemetría con alertas
    latest_sensor = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()
    
    return render_template('sensors.html', config=config, sensors=sensors, latest_sensor=latest_sensor)

@app.route('/processing')
def processing_panel():
    """Muestra las previsualizaciones de procesamiento e historial de fenotipado."""
    config = Config.query.first()
    profiles = CropProfile.query.all()
    selected_profile = CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()
    
    # Obtener histórico de métricas biométricas filtrado por la especie seleccionada
    sessions = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).all()
    recent_sessions = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).limit(5).all()
    
    latest_metric = None
    latest_session = CaptureSession.query.filter_by(crop_type=config.selected_crop_type).order_by(CaptureSession.timestamp.desc()).first()
    if latest_session and latest_session.metrics:
        latest_metric = latest_session.metrics[0]
        
    # Consolidar datos de crecimiento por sesión individual en orden cronológico (izquierda a derecha)
    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    
    for s in chronological_sessions:
        if s.metrics:
            metric = s.metrics[0]
            label_str = s.timestamp.strftime('%d/%m %H:%M')
            growth_data.append({
                "date": label_str,
                "area": round(metric.foliar_area_cm2, 2),
                "height": round(metric.plant_height_cm, 2),
                "diameter": round(metric.stem_diameter_mm, 2),
                "health": round(metric.health_index, 2)
            })

    return render_template(
        'processing.html',
        config=config,
        selected_profile=selected_profile,
        profiles=profiles,
        sessions=sessions,
        recent_sessions=recent_sessions,
        latest_session=latest_session,
        latest_metric=latest_metric,
        growth_data=growth_data
    )



# ----------------- ENDPOINTS API (PARA LA RASPBERRY PI Y AJAX) -----------------

@app.route('/api/config', methods=['GET'])
def get_config():
    """API para entregar la configuración actual a la Raspberry Pi."""
    config = Config.query.first()
    if not config:
        return jsonify({"error": "Config not initialized"}), 500
    return jsonify(config.to_json())

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Actualiza la configuración del sistema desde el panel del dashboard."""
    config = Config.query.first()
    if not config:
        return jsonify({"error": "Config not found"}), 404
        
    # Puede recibir JSON o Form
    if request.is_json:
        data = request.json
    else:
        data = request.form

    config.plant_id = int(data.get('plant_id', config.plant_id))
    config.photos_per_period = int(data.get('photos_per_period', config.photos_per_period))
    config.capture_interval_sec = int(data.get('capture_interval_sec', config.capture_interval_sec))
    config.selected_crop_type = data.get('selected_crop_type', config.selected_crop_type)
    config.safe_shutdown_enabled = 'safe_shutdown_enabled' in data or data.get('safe_shutdown_enabled') == 'true' or data.get('safe_shutdown_enabled') is True
    
    # Procesar horarios (de lista JSON o string separado por comas)
    if 'scheduled_times' in data:
        times = data.get('scheduled_times')
        if isinstance(times, list):
            config.scheduled_times = times
        else:
            # Si viene como string
            config.scheduled_times_str = str(times)
    elif 'scheduled_times_str' in data:
        config.scheduled_times_str = data.get('scheduled_times_str')

    db.session.commit()
    
    if request.is_json:
        return jsonify({"status": "success", "message": "Config updated successfully", "config": config.to_json()})
    return redirect(url_for('configuration_panel'))

@app.route('/api/crop_profile/update', methods=['POST'])
def update_crop_profile():
    """Actualiza los umbrales de segmentación de color de una especie vegetal."""
    if request.is_json:
        data = request.json
    else:
        data = request.form

    crop_type = data.get('crop_type')
    profile = CropProfile.query.filter_by(crop_type=crop_type).first()
    
    if not profile:
        return jsonify({"error": f"Crop profile '{crop_type}' not found"}), 404
        
    profile.h_min = int(data.get('h_min', profile.h_min))
    profile.h_max = int(data.get('h_max', profile.h_max))
    profile.s_min = int(data.get('s_min', profile.s_min))
    profile.s_max = int(data.get('s_max', profile.s_max))
    profile.v_min = int(data.get('v_min', profile.v_min))
    profile.v_max = int(data.get('v_max', profile.v_max))
    
    profile.l_min = int(data.get('l_min', profile.l_min))
    profile.l_max = int(data.get('l_max', profile.l_max))
    profile.a_min = int(data.get('a_min', profile.a_min))
    profile.a_max = int(data.get('a_max', profile.a_max))
    profile.b_min = int(data.get('b_min', profile.b_min))
    profile.b_max = int(data.get('b_max', profile.b_max))
    
    profile.pixel_to_cm_ratio = float(data.get('pixel_to_cm_ratio', profile.pixel_to_cm_ratio))
    profile.has_stem = 'has_stem' in data or data.get('has_stem') == 'true' or data.get('has_stem') is True

    db.session.commit()
    
    if request.is_json:
        return jsonify({"status": "success", "message": "Crop profile updated", "profile": profile.to_json()})
    return redirect(url_for('configuration_panel'))



@app.route('/api/upload', methods=['POST'])
def upload_capture_session():
    """
    Endpoint principal para recibir el lote de fotos desde la Raspberry Pi.
    Recibe multipart/form-data con:
    - plant_id (int)
    - period (str: "mañana", "mediodía", "tarde")
    - timestamp (str: ISO Format)
    - sensor_data (str: JSON estructurado)
    - files: cenital_images (múltiples)
    - files: lateral_images (múltiples)
    """
    try:
        # 1. Obtener metadatos de la sesión
        plant_id = int(request.form.get('plant_id', 1))
        period = request.form.get('period', 'mañana')
        timestamp_str = request.form.get('timestamp', datetime.now().isoformat())
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except:
            timestamp = datetime.now()
            
        date_folder = timestamp.strftime('%Y-%m-%d')
        
        # 2. Obtener configuración y perfil de color activo
        config = Config.query.first()
        crop_type = config.selected_crop_type if config else "lechuga"
        profile = CropProfile.query.filter_by(crop_type=crop_type).first()
        
        # 3. Procesar datos de sensores (Fase 2)
        sensor_json_str = request.form.get('sensor_data')
        sensor_reading_id = None
        
        if sensor_json_str:
            try:
                s_data = json.loads(sensor_json_str)
                sensor_rec = SensorReading(
                    timestamp=timestamp,
                    temperature=float(s_data.get('temperature', 0.0)),
                    humidity=float(s_data.get('humidity', 0.0)),
                    uv_solar=float(s_data.get('uv_solar', 0.0)),
                    motor_current=float(s_data.get('motor_current', 0.0))
                )
                db.session.add(sensor_rec)
                db.session.flush() # Para obtener el ID generado antes del commit
                sensor_reading_id = sensor_rec.id
                print(f"Lectura de sensores registrada en base de datos: ID {sensor_reading_id}")
            except Exception as e:
                print(f"Error procesando datos de sensores: {e}")

        # Mapeo a ASCII seguro para evitar problemas de codificación de rutas físicas en Windows
        ascii_period = period.replace('ñ', 'n').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('ú', 'u')

        # 4. Crear Carpeta física en disco para guardar archivos
        session_upload_dir = os.path.join(UPLOAD_DIR, date_folder, ascii_period)
        session_processed_dir = os.path.join(PROCESSED_DIR, date_folder, ascii_period)
        os.makedirs(session_upload_dir, exist_ok=True)
        os.makedirs(session_processed_dir, exist_ok=True)

        # 5. Guardar archivos de imagen recibidos y procesarlos uno por uno
        cenital_files = request.files.getlist('cenital_images')
        lateral_files = request.files.getlist('lateral_images')
        
        print(f"Recibidas {len(cenital_files)} fotos cenitales y {len(lateral_files)} laterales.")

        cenital_results = []
        best_cenital_orig = None
        best_cenital_proc = None
        
        # Procesar cenitales
        for idx, file in enumerate(cenital_files):
            if file.filename:
                orig_filename = f"cenital_{idx}.png"
                orig_path = os.path.join(session_upload_dir, orig_filename)
                file.save(orig_path)
                
                # Ruta física para guardar el procesado
                proc_filename = f"cenital_proc_{idx}.png"
                proc_path = os.path.join(session_processed_dir, proc_filename)
                
                # Correr pipeline de visión
                res = vision_pipeline.process_cenital_image(
                    orig_path, proc_path, profile
                )
                if res:
                    cenital_results.append(res)
                    # Guardamos rutas de la primera imagen procesada con éxito como representativa
                    if best_cenital_orig is None:
                        # Rutas relativas para mostrar en la web
                        best_cenital_orig = f"data/uploads/{date_folder}/{ascii_period}/{orig_filename}"
                        best_cenital_proc = f"data/processed/{date_folder}/{ascii_period}/{proc_filename}"

        lateral_results = []
        best_lateral_orig = None
        best_lateral_proc = None

        # Procesar laterales
        for idx, file in enumerate(lateral_files):
            if file.filename:
                orig_filename = f"lateral_{idx}.png"
                orig_path = os.path.join(session_upload_dir, orig_filename)
                file.save(orig_path)
                
                proc_filename = f"lateral_proc_{idx}.png"
                proc_path = os.path.join(session_processed_dir, proc_filename)
                
                # Correr pipeline
                res = vision_pipeline.process_lateral_image(
                    orig_path, proc_path, profile
                )
                if res:
                    lateral_results.append(res)
                    if best_lateral_orig is None:
                        best_lateral_orig = f"data/uploads/{date_folder}/{ascii_period}/{orig_filename}"
                        best_lateral_proc = f"data/processed/{date_folder}/{ascii_period}/{proc_filename}"

        # 6. Promediar resultados y eliminar atípicos
        averaged_metrics = vision_pipeline.filter_and_average_metrics(cenital_results, lateral_results)
        
        # 7. Crear y Guardar Sesión de Captura y Métricas Promediadas en la base de datos
        session = CaptureSession(
            timestamp=timestamp,
            period=period,
            plant_id=plant_id,
            crop_type=crop_type,
            sensor_reading_id=sensor_reading_id
        )
        db.session.add(session)
        db.session.flush()

        metrics_record = BiometricMetric(
            session_id=session.id,
            foliar_area_cm2=averaged_metrics["foliar_area_cm2"],
            plant_height_cm=averaged_metrics["plant_height_cm"],
            stem_diameter_mm=averaged_metrics["stem_diameter_mm"],
            health_index=averaged_metrics["health_index"],
            compacity_index=averaged_metrics["compacity_index"],
            spots_count=averaged_metrics["spots_count"],
            fruits_count=averaged_metrics["fruits_count"],
            image_path_cenital_orig=best_cenital_orig,
            image_path_cenital_proc=best_cenital_proc,
            image_path_lateral_orig=best_lateral_orig,
            image_path_lateral_proc=best_lateral_proc
        )
        db.session.add(metrics_record)
        db.session.commit()
        
        print(f"Lote de fotos SIFMA procesado y guardado con éxito. Sesión ID: {session.id}")
        
        return jsonify({
            "status": "success",
            "message": "Capture session received and analyzed successfully",
            "session_id": session.id,
            "averaged_metrics": {
                "foliar_area_cm2": metrics_record.foliar_area_cm2,
                "plant_height_cm": metrics_record.plant_height_cm,
                "stem_diameter_mm": metrics_record.stem_diameter_mm,
                "health_index": metrics_record.health_index,
                "spots_count": metrics_record.spots_count,
                "fruits_count": metrics_record.fruits_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error grave en upload: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Server failed to process upload: {e}"}), 500

# ----------------- EJECUCIÓN DEL SERVIDOR -----------------

if __name__ == '__main__':
    # Crear tablas y sembrar base de datos si es necesario
    init_db_data(app)
    
    print("\n==============================================")
    print("Servidor Local SIFMA iniciado exitosamente.")
    print("Abre tu navegador en: http://127.0.0.1:5000")
    print("==============================================\n")
    
    # Correr servidor Flask en modo debug en puerto 5000 (abierto en la red local)
    app.run(host='0.0.0.0', port=5000, debug=True)
