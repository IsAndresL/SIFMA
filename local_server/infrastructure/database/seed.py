from infrastructure.database.connection import db
from core.security import SecurityService
from core.logger import logger

def init_db_data(app):
    """
    Inicializa la base de datos con tablas y configuraciones por defecto si no existen.
    Ejecuta migraciones idempotentes y siembra los perfiles botánicos y el Administrador Principal.
    """
    from domain.models.config import Config
    from domain.models.crop_profile import CropProfile
    from domain.models.user import User

    with app.app_context():
        db.create_all()
        
        # Migración segura de columnas en SQLite
        with db.engine.connect() as conn:
            for col_sql in [
                "ALTER TABLE biometric_metric ADD COLUMN photo_index INTEGER DEFAULT 0",
                "ALTER TABLE biometric_metric ADD COLUMN is_average BOOLEAN DEFAULT 0",
                "ALTER TABLE biometric_metric ADD COLUMN capture_exact_time DATETIME",
                "ALTER TABLE config ADD COLUMN plant_1_crop VARCHAR(50) DEFAULT 'cebollin'",
                "ALTER TABLE config ADD COLUMN plant_2_crop VARCHAR(50) DEFAULT 'albahaca'",
                "ALTER TABLE config ADD COLUMN plant_3_crop VARCHAR(50) DEFAULT 'lechuga'",
                "ALTER TABLE config ADD COLUMN plant_4_crop VARCHAR(50) DEFAULT 'fresa'",
                "ALTER TABLE config ADD COLUMN shared_telemetry BOOLEAN DEFAULT 1",
                "ALTER TABLE config ADD COLUMN telemetry_mode VARCHAR(50) DEFAULT 'shared_tower'",
                "ALTER TABLE crop_profile ADD COLUMN lat_h_min INTEGER DEFAULT 26",
                "ALTER TABLE crop_profile ADD COLUMN lat_h_max INTEGER DEFAULT 92",
                "ALTER TABLE crop_profile ADD COLUMN lat_s_min INTEGER DEFAULT 35",
                "ALTER TABLE crop_profile ADD COLUMN lat_s_max INTEGER DEFAULT 255",
                "ALTER TABLE crop_profile ADD COLUMN lat_v_min INTEGER DEFAULT 30",
                "ALTER TABLE crop_profile ADD COLUMN lat_v_max INTEGER DEFAULT 255",
                "ALTER TABLE crop_profile ADD COLUMN lat_l_min INTEGER DEFAULT 20",
                "ALTER TABLE crop_profile ADD COLUMN lat_l_max INTEGER DEFAULT 255",
                "ALTER TABLE crop_profile ADD COLUMN lat_a_min INTEGER DEFAULT 0",
                "ALTER TABLE crop_profile ADD COLUMN lat_a_max INTEGER DEFAULT 124",
                "ALTER TABLE crop_profile ADD COLUMN lat_b_min INTEGER DEFAULT 120",
                "ALTER TABLE crop_profile ADD COLUMN lat_b_max INTEGER DEFAULT 255",
                "ALTER TABLE crop_profile ADD COLUMN lat_pixel_to_cm_ratio FLOAT DEFAULT 0.038",
                "ALTER TABLE crop_profile ADD COLUMN lat_min_area INTEGER DEFAULT 60",
                "ALTER TABLE crop_profile ADD COLUMN lat_filter_isolated BOOLEAN DEFAULT 1"
            ]:
                try:
                    conn.execute(db.text(col_sql))
                    conn.commit()
                except Exception:
                    pass

        # 1. Sembrar Administrador Principal por defecto si no existe
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                full_name="Andres Luna",
                email="admin@sifma.local",
                password_hash=SecurityService.hash_password("sifma2026"),
                role="admin",
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Usuario Administrador Principal 'admin' creado exitosamente.")
        else:
            if admin_user.role != "admin":
                admin_user.role = "admin"
                db.session.commit()
        
        # 2. Configuración inicial del sistema
        if not Config.query.first():
            default_config = Config(
                server_url="http://127.0.0.1:5000",
                plant_id=1,
                photos_per_period=5,
                capture_interval_sec=2,
                scheduled_times_str="07:05,12:05,17:05",
                safe_shutdown_enabled=False,
                selected_crop_type="cebollin"
            )
            db.session.add(default_config)

        # 3. Perfiles botánicos por defecto calibrados para fenotipado en entorno real
        default_profiles = [
            CropProfile(
                crop_type="cebollin",
                display_name="Cebollín",
                h_min=26, h_max=92, s_min=35, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=255, a_min=0, a_max=124, b_min=120, b_max=255,
                pixel_to_cm_ratio=0.038, has_stem=True,
                lat_h_min=30, lat_h_max=88, lat_s_min=40, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            ),
            CropProfile(
                crop_type="lechuga",
                display_name="Lechuga",
                h_min=28, h_max=88, s_min=40, s_max=255, v_min=35, v_max=255,
                l_min=25, l_max=245, a_min=0, a_max=123, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False,
                lat_h_min=30, lat_h_max=88, lat_s_min=40, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            ),
            CropProfile(
                crop_type="fresa",
                display_name="Fresa",
                h_min=30, h_max=86, s_min=45, s_max=255, v_min=35, v_max=255,
                l_min=20, l_max=240, a_min=0, a_max=124, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False,
                lat_h_min=32, lat_h_max=86, lat_s_min=45, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            ),
            CropProfile(
                crop_type="albahaca",
                display_name="Albahaca",
                h_min=28, h_max=90, s_min=40, s_max=255, v_min=35, v_max=255,
                l_min=20, l_max=245, a_min=0, a_max=124, b_min=120, b_max=250,
                pixel_to_cm_ratio=0.038, has_stem=True,
                lat_h_min=30, lat_h_max=88, lat_s_min=40, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            ),
            CropProfile(
                crop_type="espinaca",
                display_name="Espinaca",
                h_min=26, h_max=88, s_min=45, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=240, a_min=0, a_max=122, b_min=122, b_max=245,
                pixel_to_cm_ratio=0.038, has_stem=False,
                lat_h_min=30, lat_h_max=88, lat_s_min=45, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            ),
            CropProfile(
                crop_type="cilantro",
                display_name="Cilantro",
                h_min=26, h_max=90, s_min=35, s_max=255, v_min=30, v_max=255,
                l_min=20, l_max=245, a_min=0, a_max=124, b_min=120, b_max=250,
                pixel_to_cm_ratio=0.038, has_stem=True,
                lat_h_min=30, lat_h_max=88, lat_s_min=40, lat_s_max=255, lat_v_min=35, lat_v_max=255,
                lat_l_min=20, lat_l_max=255, lat_a_min=0, lat_a_max=118, lat_b_min=125, lat_b_max=255,
                lat_pixel_to_cm_ratio=0.025, lat_min_area=50, lat_filter_isolated=True
            )
        ]

        for p in default_profiles:
            existing = CropProfile.query.filter_by(crop_type=p.crop_type).first()
            if not existing:
                db.session.add(p)
            else:
                existing.h_min = p.h_min
                existing.h_max = p.h_max
                existing.s_min = p.s_min
                existing.s_max = p.s_max
                existing.v_min = p.v_min
                existing.v_max = p.v_max
                existing.a_max = p.a_max
                existing.b_min = p.b_min
                existing.lat_h_min = p.lat_h_min
                existing.lat_h_max = p.lat_h_max
                existing.lat_s_min = p.lat_s_min
                existing.lat_s_max = p.lat_s_max
                existing.lat_v_min = p.lat_v_min
                existing.lat_v_max = p.lat_v_max
                existing.lat_l_min = p.lat_l_min
                existing.lat_l_max = p.lat_l_max
                existing.lat_a_min = p.lat_a_min
                existing.lat_a_max = p.lat_a_max
                existing.lat_b_min = p.lat_b_min
                existing.lat_b_max = p.lat_b_max
                existing.lat_pixel_to_cm_ratio = p.lat_pixel_to_cm_ratio
                existing.lat_min_area = p.lat_min_area
                existing.lat_filter_isolated = p.lat_filter_isolated

        db.session.commit()
        logger.info("Base de datos SIFMA inicializada y perfiles verificados.")
