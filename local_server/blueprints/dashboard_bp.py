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
    from services.telemetry_service import TelemetryService
    from services.analytics_service import AnalyticsCrossService
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    
    telemetry = TelemetryService.get_instance()
    telemetry_status = telemetry.get_status()
    available_ports = telemetry.get_available_ports()

    requested_date = request.args.get('date', 'auto')
    sensor_data = AnalyticsCrossService.get_sensor_timeline_data(target_date=requested_date)

    return render_template('sensors.html', 
                           config=config, 
                           sensor_data=sensor_data,
                           telemetry_status=telemetry_status,
                           available_ports=available_ports,
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

    # Traer TODAS las sesiones registradas para esta Canastilla
    sessions = CaptureSession.query.filter_by(
        plant_id=active_plant_id
    ).order_by(CaptureSession.timestamp.desc()).all()
    
    gallery_sessions = []
    for s in sessions:
        if s.metrics:
            # Obtener promedio y fotos individuales
            avg_metric = next((m for m in s.metrics if m.is_average or m.photo_index == 0), s.metrics[0])
            individual_photos = [m.to_dict() for m in s.metrics if not m.is_average and m.photo_index > 0]
            individual_photos.sort(key=lambda x: x["photo_index"])

            gallery_sessions.append({
                "session": s,
                "avg_metric": avg_metric.to_dict(),
                "individual_photos": individual_photos,
                "all_metrics_json": [m.to_dict() for m in s.metrics]
            })
            
    return render_template('gallery.html',
                           config=config,
                           profiles=profiles,
                           sessions=sessions,
                           gallery_sessions=gallery_sessions,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/cross_analysis')
def cross_analysis():
    from services.analytics_service import AnalyticsCrossService
    from services.telemetry_service import TelemetryService
    from database import AgronomicConclusion
    
    config = Config.query.first()
    active_plant_id = get_active_plant_id()
    profiles = CropProfile.query.all()
    
    telemetry = TelemetryService.get_instance()
    telemetry_status = telemetry.get_status()
    available_ports = telemetry.get_available_ports()
    
    cross_data = AnalyticsCrossService.get_cross_referenced_dataset(plant_id=active_plant_id)
    correlations = AnalyticsCrossService.calculate_agronomic_correlations(cross_data)
    
    # Obtener fechas únicas disponibles en las sesiones
    dates_query = db.session.query(
        db.func.strftime('%Y-%m-%d', CaptureSession.timestamp)
    ).filter_by(plant_id=active_plant_id).distinct().all()
    available_dates = [d[0] for d in dates_query if d[0]]
    if not available_dates:
        # Fallback a fechas de sensores
        dates_sensor = db.session.query(
            db.func.strftime('%Y-%m-%d', SensorReading.timestamp)
        ).distinct().all()
        available_dates = [d[0] for d in dates_sensor if d[0]]
        
    available_dates.sort(reverse=True)
    
    conclusions = AgronomicConclusion.query.filter_by(
        plant_id=active_plant_id
    ).order_by(AgronomicConclusion.timestamp.desc()).all()
    
    return render_template('cross_analysis.html',
                           config=config,
                           profiles=profiles,
                           active_plant_id=active_plant_id,
                           cross_data=cross_data,
                           correlations=correlations,
                           available_dates=available_dates,
                           conclusions=[c.to_dict() for c in conclusions],
                           telemetry_status=telemetry_status,
                           available_ports=available_ports)

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
