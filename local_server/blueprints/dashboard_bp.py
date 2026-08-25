import os
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database import db, Config, CropProfile, SensorReading, CaptureSession, BiometricMetric

dashboard_bp = Blueprint('dashboard', __name__)

def get_active_plant_id():
    """Devuelve la Canastilla activa guardada en la sesión de usuario (1 a 4). Por defecto Canastilla 1."""
    return session.get('active_plant_id', 1)

@dashboard_bp.before_request
def require_login():
    allowed_endpoints = ['dashboard.login', 'static', 'api.upload_capture_session', 'api.get_config', 'api.scan_usb_drives']
    if request.endpoint and not any(request.endpoint.startswith(ep) for ep in allowed_endpoints):
        if not session.get('logged_in'):
            return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/set_active_plant/<int:plant_id>')
def set_active_plant(plant_id):
    """Cambia la Canastilla/Nodo activo en la sesión de usuario (Canastillas 1 a 4)."""
    if 1 <= plant_id <= 4:
        session['active_plant_id'] = plant_id
    referrer = request.referrer or url_for('dashboard.index')
    return redirect(referrer)

@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if session.get('logged_in'):
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'sifma2026':
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('dashboard.index'))
        else:
            error = "Usuario o contraseña incorrectos."
    return render_template('login.html', error=error)

@dashboard_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/')
def index():
    config = Config.query.first()
    if not config:
        return "Inicializando base de datos... Por favor recarga la página."

    active_plant_id = get_active_plant_id()

    # Lecturas de sensores reales de la canastilla activa
    sensors = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(30).all()
    sensors.reverse()

    # Muestreos y sesiones de la canastilla activa (TODAS las especies)
    sessions = CaptureSession.query.filter_by(
        plant_id=active_plant_id
    ).order_by(CaptureSession.timestamp.desc()).all()

    profiles = CropProfile.query.all()
    selected_profile = CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()

    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    for s in chronological_sessions:
        if s.metrics:
            metric = s.metrics[0]
            label_str = f"{s.period}"
            growth_data.append({
                "date": label_str,
                "area": round(metric.foliar_area_cm2, 2),
                "height": round(metric.plant_height_cm, 2),
                "diameter": round(metric.stem_diameter_mm, 2),
                "health": round(metric.health_index, 1),
                "period": s.period.upper()
            })

    latest_session = sessions[0] if sessions else None
    latest_metric = latest_session.metrics[0] if (latest_session and latest_session.metrics) else None
    latest_sensor = SensorReading.query.order_by(SensorReading.timestamp.desc()).first()

    return render_template('dashboard.html', 
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           sensors=sensors,
                           growth_data=growth_data,
                           latest_session=latest_session,
                           latest_metric=latest_metric,
                           latest_sensor=latest_sensor,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/sensors')
def detailed_sensors():
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    
    sensors = SensorReading.query.order_by(SensorReading.timestamp.desc()).limit(100).all()
    sensors_chrono = list(sensors)
    sensors_chrono.reverse()
    
    sensor_history = []
    for s in sensors_chrono:
        sensor_history.append({
            "timestamp": s.timestamp.strftime('%H:%M:%S (%d/%m)'),
            "temperature": round(s.temperature, 2),
            "humidity": round(s.humidity, 2),
            "uv_solar": round(s.uv_solar, 2),
            "motor_current": round(s.motor_current, 2)
        })
        
    latest_sensor = sensors[0] if sensors else None
    return render_template('sensors.html', 
                           config=config, 
                           sensors=sensors, 
                           latest_sensor=latest_sensor,
                           sensor_history=sensor_history,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/processing')
def processing_panel():
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    
    profiles = CropProfile.query.all()
    selected_profile = CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()
    
    sessions = CaptureSession.query.filter_by(plant_id=active_plant_id).order_by(CaptureSession.timestamp.desc()).all()
    latest_session = sessions[0] if sessions else None
    latest_metric = latest_session.metrics[0] if (latest_session and latest_session.metrics) else None
    processed_periods = [s.period for s in sessions if s.period]

    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    for s in chronological_sessions:
        if s.metrics:
            metric = s.metrics[0]
            growth_data.append({
                "date": s.period,
                "area": round(metric.foliar_area_cm2, 2),
                "height": round(metric.plant_height_cm, 2),
                "diameter": round(metric.stem_diameter_mm, 2),
                "health": round(metric.health_index, 1),
                "period": s.period.upper()
            })

    return render_template('processing.html',
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           sessions=sessions,
                           latest_session=latest_session,
                           latest_metric=latest_metric,
                           processed_periods=processed_periods,
                           growth_data=growth_data,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/gallery')
def gallery():
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    
    profiles = CropProfile.query.all()

    # Traer TODAS las sesiones registradas para esta Canastilla sin filtrar por cultivo
    sessions = CaptureSession.query.filter_by(
        plant_id=active_plant_id
    ).order_by(CaptureSession.timestamp.desc()).all()
    
    gallery_items = []
    for s in sessions:
        if s.metrics:
            metric = s.metrics[0]
            gallery_items.append({
                "session": s,
                "metric": metric
            })
            
    return render_template('gallery.html',
                           config=config,
                           profiles=profiles,
                           sessions=sessions,
                           gallery_items=gallery_items,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/config', methods=['GET', 'POST'])
def configuration_panel():
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    profiles = CropProfile.query.all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            crop_type = request.form.get('crop_type')
            config.selected_crop_type = crop_type
            profile = CropProfile.query.filter_by(crop_type=crop_type).first()
            if profile:
                profile.h_min = int(request.form.get('h_min', profile.h_min))
                profile.h_max = int(request.form.get('h_max', profile.h_max))
                profile.s_min = int(request.form.get('s_min', profile.s_min))
                profile.s_max = int(request.form.get('s_max', profile.s_max))
                profile.v_min = int(request.form.get('v_min', profile.v_min))
                profile.v_max = int(request.form.get('v_max', profile.v_max))
                
                profile.l_min = int(request.form.get('l_min', profile.l_min))
                profile.l_max = int(request.form.get('l_max', profile.l_max))
                profile.a_min = int(request.form.get('a_min', profile.a_min))
                profile.a_max = int(request.form.get('a_max', profile.a_max))
                profile.b_min = int(request.form.get('b_min', profile.b_min))
                profile.b_max = int(request.form.get('b_max', profile.b_max))
                
                profile.pixel_to_cm_ratio = float(request.form.get('pixel_to_cm_ratio', profile.pixel_to_cm_ratio))
                profile.has_stem = 'has_stem' in request.form
                db.session.commit()
                
        return redirect(url_for('dashboard.configuration_panel', crop_type=config.selected_crop_type))

    requested_crop = request.args.get('crop_type', config.selected_crop_type)
    selected_profile = CropProfile.query.filter_by(crop_type=requested_crop).first() or CropProfile.query.filter_by(crop_type=config.selected_crop_type).first()
    return render_template('config.html', 
                           config=config, 
                           profiles=profiles, 
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)
