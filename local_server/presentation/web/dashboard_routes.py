from flask import Blueprint, render_template, request, redirect, url_for, session
from core.config import config as app_settings
from core.security import SecurityService
from application.services import (
    SystemService, 
    TelemetryApplicationService, 
    AnalyticsApplicationService, 
    ConclusionApplicationService
)
from infrastructure.database.repositories import (
    SensorRepository, 
    CaptureSessionRepository
)

dashboard_bp = Blueprint('dashboard', __name__)

system_service = SystemService()
telemetry_service = TelemetryApplicationService.get_instance()
analytics_service = AnalyticsApplicationService()
conclusion_service = ConclusionApplicationService()
sensor_repo = SensorRepository()
session_repo = CaptureSessionRepository()

def get_active_plant_id():
    """Devuelve la Canastilla activa guardada en la sesión de usuario (1 a 4)."""
    return session.get('active_plant_id', 1)

@dashboard_bp.before_request
def require_login():
    allowed_endpoints = [
        'dashboard.login', 
        'static', 
        'batch_api.upload_capture_session', 
        'batch_api.get_config', 
        'batch_api.scan_usb_drives'
    ]
    if request.endpoint and not any(request.endpoint.startswith(ep) for ep in allowed_endpoints):
        if not session.get('logged_in'):
            return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/set_active_plant/<int:plant_id>')
def set_active_plant(plant_id: int):
    """Cambia la Canastilla/Nodo activo en la sesión de usuario (Canastillas 1 a 4)."""
    if 1 <= plant_id <= app_settings.MAX_PLANT_NODES:
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
        
        # Verificación segura de credenciales
        if username == app_settings.ADMIN_USERNAME and SecurityService.verify_password(password, app_settings.ADMIN_PASSWORD_HASH):
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
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()

    sensors = sensor_repo.get_recent(30)
    sessions = session_repo.get_all_by_plant(active_plant_id)

    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile(config.selected_crop_type)

    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    for s in chronological_sessions:
        if s.metrics:
            metric = s.get_average_metric()
            if metric:
                growth_data.append({
                    "date": s.period,
                    "area": round(metric.foliar_area_cm2, 2),
                    "height": round(metric.plant_height_cm, 2),
                    "diameter": round(metric.stem_diameter_mm, 2),
                    "health": round(metric.health_index, 1),
                    "period": s.period.upper()
                })

    latest_session = sessions[0] if sessions else None
    latest_metric = latest_session.get_average_metric() if latest_session else None
    latest_sensor = sensor_repo.get_latest()

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
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    
    telemetry_status = telemetry_service.get_status()
    available_ports = telemetry_service.get_available_ports()

    requested_date = request.args.get('date', 'auto')
    sensor_data = analytics_service.get_sensor_timeline_data(target_date=requested_date)

    return render_template('sensors.html', 
                           config=config, 
                           sensor_data=sensor_data,
                           telemetry_status=telemetry_status,
                           available_ports=available_ports,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/processing')
def processing_panel():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile(config.selected_crop_type)
    
    sessions = session_repo.get_all_by_plant(active_plant_id)
    latest_session = sessions[0] if sessions else None
    latest_metric = latest_session.get_average_metric() if latest_session else None
    processed_periods = [s.period for s in sessions if s.period]

    growth_data = []
    chronological_sessions = list(sessions)
    chronological_sessions.reverse()
    for s in chronological_sessions:
        if s.metrics:
            metric = s.get_average_metric()
            if metric:
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
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()

    sessions = session_repo.get_all_by_plant(active_plant_id)
    gallery_sessions = []
    
    for s in sessions:
        if s.metrics:
            avg_metric = s.get_average_metric()
            individual_photos = [m.to_dict() for m in s.get_individual_photos()]

            gallery_sessions.append({
                "session": s,
                "avg_metric": avg_metric.to_dict() if avg_metric else {},
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
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    
    telemetry_status = telemetry_service.get_status()
    available_ports = telemetry_service.get_available_ports()
    
    cross_data = analytics_service.get_cross_referenced_dataset(plant_id=active_plant_id)
    correlations = analytics_service.calculate_agronomic_correlations(cross_data)
    
    available_dates = session_repo.get_available_dates(active_plant_id)
    if not available_dates:
        available_dates = sensor_repo.get_available_dates()
        
    conclusions = conclusion_service.get_conclusions(plant_id=active_plant_id)
    
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
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            crop_type = request.form.get('crop_type')
            system_service.update_config(selected_crop_type=crop_type)
            profile = system_service.get_profile(crop_type)
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
                system_service.update_profile(profile)
                
        return redirect(url_for('dashboard.configuration_panel', crop_type=config.selected_crop_type))

    requested_crop = request.args.get('crop_type', config.selected_crop_type)
    selected_profile = system_service.get_profile(requested_crop)
    return render_template('config.html', 
                           config=config, 
                           profiles=profiles, 
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)
