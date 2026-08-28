from datetime import datetime
from database import db, Config, CropProfile, SensorReading, CaptureSession, BiometricMetric

class DatabaseService:
    """
    Capa de servicio encargada de las operaciones CRUD en la base de datos.
    """
    
    @staticmethod
    def get_config():
        config = Config.query.first()
        if not config:
            config = Config()
            db.session.add(config)
            db.session.commit()
        return config

    @staticmethod
    def get_crop_profile(crop_type=None):
        if not crop_type:
            config = DatabaseService.get_config()
            crop_type = config.selected_crop_type
            
        profile = CropProfile.query.filter_by(crop_type=crop_type).first()
        if not profile:
            profile = CropProfile.query.filter_by(crop_type="lechuga").first()
        return profile

    @staticmethod
    def save_capture_session_with_metrics(period, crop_type, sensor_data, final_metrics, individual_metrics=None, cenital_paths=None, lateral_paths=None, plant_id=1):
        """
        Guarda o sobreescribe una sesión de captura y sus métricas (tanto las individuales como el promedio).
        """
        if not cenital_paths: cenital_paths = {}
        if not lateral_paths: lateral_paths = {}
        if not sensor_data: sensor_data = {}

        # Asociar lectura de sensor real si viene en la solicitud o buscar en la base de datos
        sensor_id = None
        if sensor_data and any(sensor_data.values()):
            sensor_record = SensorReading(
                temperature=float(sensor_data.get("temperature", 0.0)),
                humidity=float(sensor_data.get("humidity", 0.0)),
                uv_solar=float(sensor_data.get("uv_solar", 0.0)),
                motor_current=float(sensor_data.get("motor_current", 0.0))
            )
            db.session.add(sensor_record)
            db.session.flush()
            sensor_id = sensor_record.id
        else:
            # Buscar lectura real más cercana en base de datos si existe
            nearest_sensor = SensorReading.query.order_by(
                db.func.abs(db.func.strftime('%s', SensorReading.timestamp) - db.func.strftime('%s', datetime.now()))
            ).first()
            sensor_id = nearest_sensor.id if nearest_sensor else None

        # Verificar si ya existe un registro para esta fecha/periodo en esta Canastilla (Sobreescritura)
        existing_session = CaptureSession.query.filter_by(
            plant_id=int(plant_id),
            period=period
        ).first()

        if existing_session:
            session_record = existing_session
            session_record.timestamp = datetime.now()
            session_record.crop_type = crop_type
            if sensor_id:
                session_record.sensor_reading_id = sensor_id

            # Limpiar métricas anteriores para sobreescritura limpia
            for m in list(session_record.metrics):
                db.session.delete(m)
            db.session.flush()

        else:
            session_record = CaptureSession(
                period=period,
                plant_id=int(plant_id),
                crop_type=crop_type,
                sensor_reading_id=sensor_id,
                timestamp=datetime.now()
            )
            db.session.add(session_record)
            db.session.flush()

        # 1. Guardar el registro de Promedio Consolidado (photo_index = 0, is_average = True)
        avg_record = BiometricMetric(
            session_id=session_record.id,
            photo_index=0,
            is_average=True,
            capture_exact_time=datetime.now(),
            foliar_area_cm2=final_metrics.get("foliar_area_cm2", 0.0),
            plant_height_cm=final_metrics.get("plant_height_cm", 0.0),
            stem_diameter_mm=final_metrics.get("stem_diameter_mm", 0.0),
            health_index=final_metrics.get("health_index", 100.0),
            compacity_index=final_metrics.get("compacity_index", 0.0),
            spots_count=final_metrics.get("spots_count", 0),
            fruits_count=final_metrics.get("fruits_count", 0),
            image_path_cenital_orig=cenital_paths.get("orig"),
            image_path_cenital_proc=cenital_paths.get("proc"),
            image_path_lateral_orig=lateral_paths.get("orig"),
            image_path_lateral_proc=lateral_paths.get("proc")
        )
        db.session.add(avg_record)

        # 2. Guardar cada foto individual si se proporcionaron (photo_index = 1..5, is_average = False)
        if individual_metrics:
            for item in individual_metrics:
                idx = item.get("photo_index", 1)
                ind_record = BiometricMetric(
                    session_id=session_record.id,
                    photo_index=idx,
                    is_average=False,
                    capture_exact_time=item.get("capture_time", datetime.now()),
                    foliar_area_cm2=item.get("foliar_area_cm2", 0.0),
                    plant_height_cm=item.get("plant_height_cm", 0.0),
                    stem_diameter_mm=item.get("stem_diameter_mm", 0.0),
                    health_index=item.get("health_index", 100.0),
                    compacity_index=item.get("compacity_index", 0.0),
                    spots_count=item.get("spots_count", 0),
                    fruits_count=item.get("fruits_count", 0),
                    image_path_cenital_orig=item.get("cenital_orig"),
                    image_path_cenital_proc=item.get("cenital_proc"),
                    image_path_lateral_orig=item.get("lateral_orig"),
                    image_path_lateral_proc=item.get("lateral_proc")
                )
                db.session.add(ind_record)

        db.session.commit()
        return session_record.id, avg_record
