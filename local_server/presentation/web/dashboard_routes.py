from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from core.config import config as app_settings
from core.security import SecurityService
from application.services import (
    SystemService, 
    TelemetryApplicationService, 
    AnalyticsApplicationService, 
    ConclusionApplicationService,
    UserService
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
user_service = UserService()
sensor_repo = SensorRepository()
session_repo = CaptureSessionRepository()

def get_active_plant_id():
    """Devuelve la Canastilla activa guardada en la sesión o recibida por query parameter (1 a 4)."""
    arg_id = request.args.get('plant_id')
    if arg_id:
        try:
            val = int(arg_id)
            if 1 <= val <= app_settings.MAX_PLANT_NODES:
                session['active_plant_id'] = val
                return val
        except (ValueError, TypeError):
            pass
    return session.get('active_plant_id', 1)

def get_current_user_profile():
    """Retorna los datos del usuario en sesión para renderizar el pie de la barra lateral."""
    return {
        "id": session.get("user_id", 1),
        "username": session.get("username", "admin"),
        "name": session.get("user_name", "Andres Luna"),
        "role": session.get("user_role", "admin"),
        "role_display": session.get("user_role_display", "Administrador Principal"),
        "avatar": session.get("user_avatar", "AL")
    }

def role_required(*allowed_roles):
    """Decorador para proteger rutas según el rol del usuario."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('dashboard.login'))
            user_role = session.get('user_role', 'investigador')
            if user_role not in allowed_roles and 'admin' not in user_role:
                return render_template('error.html', 
                                       error_title="Acceso Restringido", 
                                       error_message="No posees los privilegios requeridos para acceder a esta sección."), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@dashboard_bp.context_processor
def inject_user_context():
    """Inyecta el perfil de usuario, canastilla activa y perfiles asignados en todas las plantillas."""
    active_pid = get_active_plant_id()
    active_prof = system_service.get_profile_for_plant(active_pid)
    plant_profiles_map = system_service.get_all_plant_profiles_map()
    return {
        "current_user": get_current_user_profile(),
        "active_plant_id": active_pid,
        "active_crop_profile": active_prof,
        "plant_profiles_map": plant_profiles_map
    }

@dashboard_bp.before_request
def require_login():
    allowed_endpoints = [
        'dashboard.login', 
        'static', 
        'api.upload_capture_session', 
        'api.get_config', 
        'api.scan_usb_drives'
    ]
    if request.endpoint and not any(request.endpoint.startswith(ep) for ep in allowed_endpoints):
        if not session.get('logged_in'):
            return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/set_active_plant/<int:plant_id>')
def set_active_plant(plant_id: int):
    """Cambia la Canastilla/Torre activa en la sesión (1 a 4)."""
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
        username = (request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''
        
        # 1. Autenticar contra la base de datos de usuarios
        user = user_service.authenticate(username, password)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            session['user_role_display'] = user.role_display
            session['user_avatar'] = user.avatar_initials
            session.permanent = True
            return redirect(url_for('dashboard.index'))
            
        # 2. Fallback de desarrollo para admin maestro
        elif username == app_settings.ADMIN_USERNAME and SecurityService.verify_password(password, app_settings.ADMIN_PASSWORD_HASH):
            session['logged_in'] = True
            session['user_id'] = 1
            session['username'] = "admin"
            session['user_name'] = "Andres Luna"
            session['user_role'] = "admin"
            session['user_role_display'] = "Administrador Principal"
            session['user_avatar'] = "AL"
            session.permanent = True
            return redirect(url_for('dashboard.index'))
        else:
            error = "Usuario o contraseña incorrectos, o cuenta inactiva."
            
    return render_template('login.html', error=error)

@dashboard_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/')
def index():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    
    # Obtener fecha seleccionada o automática
    target_date = request.args.get('date', 'auto')
    
    # Obtener el análisis diario consolidado para la fecha seleccionada
    daily_data = analytics_service.get_daily_summary_data(target_date=target_date, plant_id=active_plant_id)
    
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)

    return render_template('dashboard.html', 
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           daily=daily_data,
                           target_date=daily_data["target_date"],
                           available_dates=daily_data["available_dates"],
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/sensors')
def detailed_sensors():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    
    target_date = request.args.get('date', 'auto')
    sensor_data = analytics_service.get_sensor_timeline_data(target_date=target_date, plant_id=active_plant_id)
    telemetry_status = telemetry_service.get_status()
    available_ports = telemetry_service.get_available_ports()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    
    return render_template('sensors.html',
                           config=config,
                           sensor_data=sensor_data,
                           available_dates=sensor_data.get('available_dates', []),
                           telemetry_status=telemetry_status,
                           available_ports=available_ports,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/calendar')
def calendar_view():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    
    now = datetime.now()
    year = request.args.get('year', type=int) or now.year
    month = request.args.get('month', type=int) or now.month
    
    cal_data = analytics_service.get_calendar_month_data(year=year, month=month, plant_id=active_plant_id)
    
    return render_template('calendar.html',
                           config=config,
                           cal_data=cal_data,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/benchmark')
def inter_plant_benchmark():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    benchmark_data = analytics_service.get_inter_plant_benchmark_data()
    
    return render_template('benchmark.html',
                           config=config,
                           benchmark_data=benchmark_data,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/timelapse')
def timelapse_viewer():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    timelapse_data = analytics_service.get_timelapse_data(plant_id=active_plant_id)
    
    return render_template('timelapse.html',
                           config=config,
                           timelapse_data=timelapse_data,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/scientific_report')
@dashboard_bp.route('/report/scientific')
def scientific_report_view():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    raw_date = request.args.get('date', '').strip()
    target_date = raw_date if raw_date else 'auto'
    
    dossier = analytics_service.get_scientific_dossier_data(target_date=target_date, plant_id=active_plant_id)
    
    return render_template('scientific_report.html',
                           config=config,
                           dossier=dossier,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/processing')
def processing_panel():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)

    sessions = session_repo.get_all_by_plant(active_plant_id, order_asc=True)
    latest_session = sessions[-1] if sessions else None
    latest_metric = latest_session.get_average_metric() if latest_session else None

    processed_periods = [s.period for s in sessions if s.period]

    growth_data = {
        "labels": [s.period for s in sessions],
        "foliar_areas": [(s.get_average_metric().foliar_area_cm2 if s.get_average_metric() else 0.0) for s in sessions],
        "plant_heights": [(s.get_average_metric().plant_height_cm if s.get_average_metric() else 0.0) for s in sessions],
        "stem_diameters": [(s.get_average_metric().stem_diameter_mm if s.get_average_metric() else 0.0) for s in sessions],
        "health_indices": [(s.get_average_metric().health_index if s.get_average_metric() else 0.0) for s in sessions]
    }

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
    selected_profile = system_service.get_profile_for_plant(active_plant_id)

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
                           selected_profile=selected_profile,
                           sessions=sessions,
                           gallery_sessions=gallery_sessions,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/cross_analysis')
def cross_analysis():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    
    telemetry_status = telemetry_service.get_status()
    available_ports = telemetry_service.get_available_ports()
    
    cross_data = analytics_service.get_cross_referenced_dataset(plant_id=active_plant_id)
    correlations = analytics_service.calculate_agronomic_correlations(cross_data)
    correlation_matrix = analytics_service.calculate_full_correlation_matrix(cross_data)
    
    available_dates = session_repo.get_available_dates(active_plant_id)
    if not available_dates:
        available_dates = sensor_repo.get_available_dates()
        
    conclusions = conclusion_service.get_conclusions(plant_id=active_plant_id)
    
    return render_template('cross_analysis.html',
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id,
                           cross_data=cross_data,
                           correlations=correlations,
                           correlation_matrix=correlation_matrix,
                           available_dates=available_dates,
                           conclusions=[c.to_dict() for c in conclusions],
                           telemetry_status=telemetry_status,
                           available_ports=available_ports)

@dashboard_bp.route('/config', methods=['GET', 'POST'])
@role_required('admin')
def configuration_panel():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 1. Asignar perfil de cultivo a una o todas las Canastillas
        if action == 'assign_plant_crops':
            p1 = request.form.get('plant_1_crop', 'cebollin')
            p2 = request.form.get('plant_2_crop', 'albahaca')
            p3 = request.form.get('plant_3_crop', 'lechuga')
            p4 = request.form.get('plant_4_crop', 'fresa')
            system_service.update_config(
                plant_1_crop=p1,
                plant_2_crop=p2,
                plant_3_crop=p3,
                plant_4_crop=p4,
                selected_crop_type=p1
            )
            return redirect(url_for('dashboard.configuration_panel'))

        elif action == 'update_telemetry_mode':
            telemetry_mode = request.form.get('telemetry_mode', 'shared_tower')
            shared_telemetry = (telemetry_mode == 'shared_tower')
            system_service.update_config(
                telemetry_mode=telemetry_mode,
                shared_telemetry=shared_telemetry
            )
            return redirect(url_for('dashboard.configuration_panel'))

        # 2. Calibrar umbrales HSV y LAB de un perfil botánico
        elif action == 'update_profile':
            crop_type = request.form.get('crop_type')
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
                
            return redirect(url_for('dashboard.configuration_panel', crop_type=crop_type))

    requested_crop = request.args.get('crop_type', system_service.get_crop_for_plant(active_plant_id))
    selected_profile = system_service.get_profile(requested_crop)
    plant_profiles_map = system_service.get_all_plant_profiles_map()

    return render_template('config.html', 
                           config=config, 
                           profiles=profiles, 
                           selected_profile=selected_profile,
                           plant_profiles_map=plant_profiles_map,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/users')
@role_required('admin')
def users_management():
    """Vista de administración de usuarios y roles (exclusiva para Administrador Principal)."""
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    users = user_service.get_all_users()
    
    return render_template('users.html',
                           config=config,
                           users=users,
                           active_plant_id=active_plant_id)
