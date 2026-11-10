# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

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
    UserService,
    WeatherService,
    AuditService,
    UpdateService,
    ReportArchiveService,
    BackupService
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
weather_service = WeatherService.get_instance()
audit_service = AuditService.get_instance()
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

from domain.models.user import ALL_MODULE_PERMISSIONS

def get_current_user_profile():
    """Retorna los datos del usuario en sesión para renderizar el pie de la barra lateral y validar permisos."""
    u_id = session.get("user_id")
    perms = session.get("user_permissions")
    user_role = session.get("user_role", "investigador")
    is_admin = user_role == "admin" or session.get("username", "").lower() == "admin"
    avatar_url = session.get("user_avatar_url")
    avatar_initials = session.get("user_avatar", "AL")

    if u_id:
        u_obj = user_service.get_user_by_id(u_id)
        if u_obj:
            perms = u_obj.get_permissions_dict()
            session['user_permissions'] = perms
            session['user_role'] = u_obj.role
            session['user_role_display'] = u_obj.role_display
            session['is_super_admin'] = u_obj.is_super_admin
            session['user_avatar'] = u_obj.avatar_initials
            session['user_avatar_url'] = u_obj.avatar_url
            is_admin = u_obj.is_super_admin
            avatar_url = u_obj.avatar_url
            avatar_initials = u_obj.avatar_initials

    if not perms:
        if is_admin:
            perms = {k: True for k, _, _, _ in ALL_MODULE_PERMISSIONS}
        else:
            perms = {k: False for k, _, _, _ in ALL_MODULE_PERMISSIONS}

    return {
        "id": session.get("user_id", 1),
        "username": session.get("username", "admin"),
        "name": session.get("user_name", "Andres Luna"),
        "role": session.get("user_role", "admin"),
        "role_display": session.get("user_role_display", "Super Usuario (Admin)"),
        "is_super_admin": is_admin,
        "avatar": avatar_initials,
        "avatar_url": avatar_url,
        "permissions": perms
    }

def role_required(*allowed_roles):
    """Decorador para proteger rutas según el rol del usuario."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('dashboard.login'))
            user_role = session.get('user_role', 'investigador')
            if user_role not in allowed_roles and user_role != 'admin' and session.get('username', '').lower() != 'admin':
                return render_template('error.html', 
                                       error_title="Acceso Restringido", 
                                       error_message="Esta sección es exclusiva del Super Usuario / Administrador Principal."), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission_key: str, module_name: str = "este módulo"):
    """Decorador para proteger rutas según los permisos granulares asignados por el Super Usuario."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('dashboard.login'))
            
            if session.get('user_role') == 'admin' or session.get('username', '').lower() == 'admin':
                return f(*args, **kwargs)

            perms = session.get('user_permissions')
            if not perms or not isinstance(perms, dict):
                u_id = session.get("user_id")
                if u_id:
                    u_obj = user_service.get_user_by_id(u_id)
                    if u_obj:
                        perms = u_obj.get_permissions_dict()
                        session['user_permissions'] = perms
            
            perms = perms or {}
            if not perms.get(permission_key, False):
                # Si el usuario intenta entrar al index('/') pero no tiene dashboard, redirigir a su primer módulo habilitado
                if request.endpoint == 'dashboard.index':
                    for alt_key, alt_endpoint in [
                        ('calendar', 'dashboard.calendar_view'),
                        ('sensors', 'dashboard.detailed_sensors'),
                        ('cross_analysis', 'dashboard.cross_analysis'),
                        ('gallery', 'dashboard.gallery'),
                        ('timelapse', 'dashboard.timelapse_viewer'),
                        ('processing', 'dashboard.processing_panel'),
                        ('config', 'dashboard.configuration_panel')
                    ]:
                        if perms.get(alt_key):
                            return redirect(url_for(alt_endpoint))

                return render_template('error.html', 
                                       error_title="Acceso Restringido", 
                                       error_message=f"Tu cuenta no posee permisos para acceder a '{module_name}'. Solicita al Administrador Principal que te habilite esta función."), 403
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
        "plant_profiles_map": plant_profiles_map,
        "all_permissions_list": ALL_MODULE_PERMISSIONS
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
        
        user = user_service.authenticate(username, password)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_name'] = user.full_name
            session['user_role'] = user.role
            session['user_role_display'] = user.role_display
            session['user_avatar'] = user.avatar_initials
            session['user_permissions'] = user.get_permissions_dict()
            session['is_super_admin'] = user.is_super_admin
            session.permanent = True

            audit_service.log(
                action="LOGIN",
                module="AUTENTICACION",
                description=f"Inicio de sesión exitoso en la plataforma SIFMA.",
                level="info",
                user_id=user.id,
                username=user.username,
                user_fullname=user.full_name,
                user_role=user.role_display,
                action_display="Inicio de Sesión"
            )

            return redirect(url_for('dashboard.index'))
        else:
            audit_service.log(
                action="LOGIN_FAILED",
                module="AUTENTICACION",
                description=f"Intento fallido de inicio de sesión con el identificador '{username}'.",
                level="warning",
                username=username or "desconocido",
                action_display="Fallo de Autenticación"
            )
            error = "Usuario o contraseña incorrectos, o cuenta inactiva."

    # En la primera ejecución absoluta en un PC nuevo (0 inicios de sesión registrados),
    # mostrar al operador las credenciales locales autogeneradas en %APPDATA%\SIFMA\.env
    first_boot_info = None
    try:
        from domain.models.audit_log import AuditLog
        has_any_login = AuditLog.query.filter_by(action="LOGIN").first() is not None
        if not has_any_login and app_settings.ADMIN_DEFAULT_PASSWORD:
            first_boot_info = {
                "username": app_settings.ADMIN_USERNAME,
                "password": app_settings.ADMIN_DEFAULT_PASSWORD,
                "env_path": app_settings.ENV_FILE_PATH,
            }
    except Exception:
        pass
            
    return render_template('login.html', error=error, first_boot_info=first_boot_info)

@dashboard_bp.route('/logout')
def logout():
    u_name = session.get('username', 'usuario')
    audit_service.log(
        action="LOGOUT",
        module="AUTENTICACION",
        description=f"El usuario '@{u_name}' cerró su sesión.",
        level="info",
        action_display="Cierre de Sesión"
    )
    session.clear()
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/')
@permission_required('dashboard', 'Resumen Diario')
def index():
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    
    target_date = request.args.get('date', 'auto')
    
    # Obtener el análisis diario consolidado para la fecha seleccionada
    daily_data = analytics_service.get_daily_summary_data(target_date=target_date, plant_id=active_plant_id)
    
    # Obtener clima exterior actual para la ubicación de la torre (Open-Meteo API / Caché / Fallback)
    current_weather = weather_service.get_current_weather(
        lat=getattr(config, 'latitude', None) or 11.2408,
        lon=getattr(config, 'longitude', None) or -74.1990,
        city_name=getattr(config, 'city_name', None) or "Santa Marta, Magdalena"
    )
    
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    archived_reports = ReportArchiveService.list_reports()
    reports_dir = ReportArchiveService.get_reports_dir()

    return render_template('dashboard.html', 
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           daily=daily_data,
                           weather=current_weather,
                           target_date=daily_data["target_date"],
                           available_dates=daily_data["available_dates"],
                           active_plant_id=active_plant_id,
                           archived_reports=archived_reports,
                           reports_dir=reports_dir)

@dashboard_bp.route('/sensors')
@permission_required('sensors', 'Sensores Ambientales')
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
@permission_required('calendar', 'Calendario de Muestreos')
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
@permission_required('cross_analysis', 'Benchmark Comparativo')
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
@permission_required('timelapse', 'Time-Lapse Evolutivo')
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

@dashboard_bp.route('/reports')
@dashboard_bp.route('/dossier')
@dashboard_bp.route('/scientific_report')
@dashboard_bp.route('/report/scientific')
@permission_required('reports', 'Dossier y Reportes')
def scientific_report_view():
    config = system_service.get_config()
    req_plant_id = request.args.get('plant_id', type=int)
    active_plant_id = req_plant_id if (req_plant_id and 1 <= req_plant_id <= app_settings.MAX_PLANT_NODES) else get_active_plant_id()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)
    plant_profiles_map = system_service.get_all_plant_profiles_map()
    raw_date = request.args.get('date', '').strip()
    target_date = raw_date if raw_date else 'auto'
    
    dossier = analytics_service.get_scientific_dossier_data(target_date=target_date, plant_id=active_plant_id)
    
    return render_template('scientific_report.html',
                           config=config,
                           dossier=dossier,
                           selected_profile=selected_profile,
                           plant_profiles_map=plant_profiles_map,
                           active_plant_id=active_plant_id)

@dashboard_bp.route('/processing')
@permission_required('processing', 'Procesamiento de Imágenes')
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
@permission_required('gallery', 'Galería de Lotes')
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
            if avg_metric:
                vision_service.ensure_metric_ai_analysis(avg_metric, s.sensor_reading)
            for ind_m in s.get_individual_photos():
                vision_service.ensure_metric_ai_analysis(ind_m, s.sensor_reading)
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
@permission_required('cross_analysis', 'Cruce y Correlaciones')
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
@permission_required('config', 'Parámetros de Cultivo')
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

                # Parámetros dedicados para Cámara Lateral (Perfil Vertical)
                profile.lat_h_min = int(request.form.get('lat_h_min', getattr(profile, 'lat_h_min', profile.h_min)))
                profile.lat_h_max = int(request.form.get('lat_h_max', getattr(profile, 'lat_h_max', profile.h_max)))
                profile.lat_s_min = int(request.form.get('lat_s_min', getattr(profile, 'lat_s_min', profile.s_min)))
                profile.lat_s_max = int(request.form.get('lat_s_max', getattr(profile, 'lat_s_max', profile.s_max)))
                profile.lat_v_min = int(request.form.get('lat_v_min', getattr(profile, 'lat_v_min', profile.v_min)))
                profile.lat_v_max = int(request.form.get('lat_v_max', getattr(profile, 'lat_v_max', profile.v_max)))
                
                profile.lat_l_min = int(request.form.get('lat_l_min', getattr(profile, 'lat_l_min', profile.l_min)))
                profile.lat_l_max = int(request.form.get('lat_l_max', getattr(profile, 'lat_l_max', profile.l_max)))
                profile.lat_a_min = int(request.form.get('lat_a_min', getattr(profile, 'lat_a_min', profile.a_min)))
                profile.lat_a_max = int(request.form.get('lat_a_max', getattr(profile, 'lat_a_max', profile.a_max)))
                profile.lat_b_min = int(request.form.get('lat_b_min', getattr(profile, 'lat_b_min', profile.b_min)))
                profile.lat_b_max = int(request.form.get('lat_b_max', getattr(profile, 'lat_b_max', profile.b_max)))
                
                profile.lat_pixel_to_cm_ratio = float(request.form.get('lat_pixel_to_cm_ratio', getattr(profile, 'lat_pixel_to_cm_ratio', profile.pixel_to_cm_ratio)))
                profile.lat_min_area = int(request.form.get('lat_min_area', getattr(profile, 'lat_min_area', 60)))
                profile.lat_filter_isolated = 'lat_filter_isolated' in request.form
                profile.lat_draw_contours = 'lat_draw_contours' in request.form

                system_service.update_profile(profile)
                
            return redirect(url_for('dashboard.configuration_panel', crop_type=crop_type))

        # 3. Calibrar ROI Cenital Interactivo
        elif action == 'update_cenital_roi':
            try:
                cx = float(request.form.get('cenital_roi_cx', 0.4955))
                cy = float(request.form.get('cenital_roi_cy', 0.4408))
                radius = float(request.form.get('cenital_roi_radius', 0.1450))
                mode = request.form.get('cenital_roi_mode', 'dynamic_conn')
                system_service.update_config(
                    cenital_roi_cx=cx,
                    cenital_roi_cy=cy,
                    cenital_roi_radius=radius,
                    cenital_roi_mode=mode
                )
            except Exception:
                pass
            return redirect(url_for('dashboard.configuration_panel'))

        # 4. Calibrar Línea Base Lateral y Zona de Tallo Interactiva
        elif action in ['update_lateral_baseline', 'update_lateral_stem']:
            try:
                update_dict = {}
                if 'lateral_baseline_y' in request.form:
                    update_dict['lateral_baseline_y'] = float(request.form.get('lateral_baseline_y', 0.7200))
                if 'lateral_baseline_mode' in request.form:
                    update_dict['lateral_baseline_mode'] = request.form.get('lateral_baseline_mode', 'manual_baseline')
                
                if 'lateral_stem_roi_y' in request.form:
                    update_dict['lateral_stem_roi_y'] = float(request.form.get('lateral_stem_roi_y', 0.6600))
                if 'lateral_stem_roi_height' in request.form:
                    update_dict['lateral_stem_roi_height'] = float(request.form.get('lateral_stem_roi_height', 0.0500))
                if 'lateral_stem_roi_x' in request.form:
                    update_dict['lateral_stem_roi_x'] = float(request.form.get('lateral_stem_roi_x', 0.5000))
                if 'lateral_stem_roi_width' in request.form:
                    update_dict['lateral_stem_roi_width'] = float(request.form.get('lateral_stem_roi_width', 0.2000))
                if 'lateral_stem_mode' in request.form:
                    update_dict['lateral_stem_mode'] = request.form.get('lateral_stem_mode', 'auto_edge')

                if update_dict:
                    system_service.update_config(**update_dict)
            except Exception:
                pass
            return redirect(url_for('dashboard.configuration_panel'))

    requested_crop = request.args.get('crop_type', system_service.get_crop_for_plant(active_plant_id))
    selected_profile = system_service.get_profile(requested_crop)
    plant_profiles_map = system_service.get_all_plant_profiles_map()

    # Obtener la última foto cenital y lateral procesada o capturada para los canvas interactivos
    sessions = session_repo.get_all_by_plant(active_plant_id, order_asc=False)
    latest_cenital_img = None
    latest_lateral_img = None
    if sessions:
        for s in sessions:
            if s.metrics:
                for m in s.metrics:
                    if not latest_cenital_img and m.image_path_cenital_orig:
                        latest_cenital_img = m.image_path_cenital_orig
                    if not latest_lateral_img and m.image_path_lateral_orig:
                        latest_lateral_img = m.image_path_lateral_orig
                    if latest_cenital_img and latest_lateral_img:
                        break
            if latest_cenital_img and latest_lateral_img:
                break

    backup_summary = BackupService.get_backup_summary()

    return render_template('config.html', 
                           config=config, 
                           profiles=profiles, 
                           selected_profile=selected_profile, 
                           plant_profiles_map=plant_profiles_map,
                           latest_cenital_img=latest_cenital_img,
                           latest_lateral_img=latest_lateral_img,
                           active_plant_id=active_plant_id,
                           backup_summary=backup_summary)

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

@dashboard_bp.route('/about')
@dashboard_bp.route('/system_info')
def system_info():
    """Vista institucional de información del sistema, créditos, autores y términos de licencia."""
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()
    profiles = system_service.get_all_profiles()
    selected_profile = system_service.get_profile_for_plant(active_plant_id)

    system_metadata = {
        "version": app_settings.APP_VERSION,
        "release_name": "SIFMA PhenoCore Desktop",
        "release_date": "Noviembre 2026",
        "author": "Ing. Andrés Luna & Cristian",
        "lead_developer": "Ing. Andrés Luna",
        "co_developer": "Cristian",
        "scientific_advisor": "Prof. Críspulo Enrique Deluque",
        "founding_professors": "Prof. Críspulo Enrique Deluque y Comité Docente",
        "institution": "Laboratorio de Automatización, Visión Artificial & Fenotipado Digital",
        "license": "Licencia Cerrada Exclusiva (Torre SIFMA)",
        "python_version": "3.10+",
        "opencv_version": "4.8+",
        "architecture": "Clean Architecture / Hexagonal (Nativo PyWebView)"
    }
    protected_data = UpdateService.get_protected_data_summary()

    return render_template('about.html',
                           config=config,
                           profiles=profiles,
                           selected_profile=selected_profile,
                           active_plant_id=active_plant_id,
                           system_meta=system_metadata,
                           protected_data=protected_data)

@dashboard_bp.route('/audit-logs')
@dashboard_bp.route('/logs')
@role_required('admin')
def audit_logs():
    """Vista de registro de auditoría, trazabilidad y logs de movimientos (exclusiva para Super Administrador)."""
    search_query = request.args.get('search', '').strip()
    module_filter = request.args.get('module', '').strip()
    level_filter = request.args.get('level', '').strip()
    action_filter = request.args.get('action', '').strip()
    date_filter = request.args.get('date', '').strip()

    start_date = None
    end_date = None
    if date_filter:
        try:
            start_date = datetime.strptime(date_filter, '%Y-%m-%d')
            end_date = start_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    logs = audit_service.get_logs(
        limit=300,
        module=module_filter if module_filter else None,
        action=action_filter if action_filter else None,
        level=level_filter if level_filter else None,
        search=search_query if search_query else None,
        start_date=start_date,
        end_date=end_date
    )

    stats = audit_service.get_stats()
    config = system_service.get_config()
    active_plant_id = get_active_plant_id()

    # Módulos y niveles disponibles para filtros
    available_modules = ["AUTENTICACION", "USUARIOS", "CONFIGURACION", "LOTES", "FENOTIPADO", "TELEMETRIA", "REPORTES", "SISTEMA"]
    available_levels = [
        ("info", "Informativo"),
        ("success", "Éxito / Creación"),
        ("warning", "Advertencia / Pausa"),
        ("danger", "Crítico / Eliminación")
    ]

    return render_template(
        'audit_logs.html',
        logs=logs,
        stats=stats,
        search_query=search_query,
        module_filter=module_filter,
        level_filter=level_filter,
        action_filter=action_filter,
        date_filter=date_filter,
        available_modules=available_modules,
        available_levels=available_levels,
        config=config,
        active_plant_id=active_plant_id
    )

@dashboard_bp.route('/audit-logs/export')
@role_required('admin')
def export_audit_logs():
    """Exporta los logs de auditoría filtrados en formato CSV descargable."""
    from flask import Response
    
    search_query = request.args.get('search', '').strip()
    module_filter = request.args.get('module', '').strip()
    level_filter = request.args.get('level', '').strip()
    date_filter = request.args.get('date', '').strip()

    start_date = None
    end_date = None
    if date_filter:
        try:
            start_date = datetime.strptime(date_filter, '%Y-%m-%d')
            end_date = start_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    logs = audit_service.get_logs(
        limit=2000,
        module=module_filter if module_filter else None,
        level=level_filter if level_filter else None,
        search=search_query if search_query else None,
        start_date=start_date,
        end_date=end_date
    )

    csv_data = audit_service.generate_csv(logs)
    filename = f"sifma_auditoria_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    audit_service.log(
        action="EXPORT_DATA",
        module="REPORTES",
        description=f"Exportó {len(logs)} registros de auditoría a CSV.",
        level="info",
        action_display="Exportación de Logs"
    )

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

@dashboard_bp.route('/api/audit-logs/<int:log_id>', methods=['DELETE'])
@role_required('admin')
def delete_single_audit_log(log_id: int):
    """Elimina un log de auditoría individual."""
    from flask import jsonify
    success = audit_service.delete_log(log_id)
    if not success:
        return jsonify({"status": "error", "message": "Registro de log no encontrado."}), 404
    return jsonify({"status": "success", "message": f"Registro de auditoría #{log_id} eliminado exitosamente."})

@dashboard_bp.route('/api/audit-logs/clear', methods=['POST', 'DELETE'])
@role_required('admin')
def clear_all_audit_logs():
    """Vacía completamente la tabla de logs de auditoría."""
    from flask import jsonify
    count = audit_service.clear_all_logs()
    
    audit_service.log(
        action="CLEAR_LOGS",
        module="SISTEMA",
        description=f"El Administrador Principal vació el historial de auditoría ({count} registros eliminados).",
        level="warning",
        action_display="Vaciado de Logs"
    )

    return jsonify({
        "status": "success", 
        "message": f"Se han eliminado {count} registros del historial de logs.",
        "deleted_count": count
    })

