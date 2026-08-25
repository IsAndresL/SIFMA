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
    def save_capture_session_with_metrics(period, crop_type, sensor_data, final_metrics, cenital_paths, lateral_paths, plant_id=1):
        """
        Guarda o sobreescribe una sesión de captura y sus métricas asociadas a la Canastilla y fecha dada.
        """
        # Verificar si ya existe un registro para esta fecha/periodo en esta Canastilla (Sobreescritura)
        existing_session = CaptureSession.query.filter_by(
            plant_id=int(plant_id),
            period=period
        ).first()

        if existing_session:
            session_record = existing_session
            session_record.timestamp = datetime.now()
            session_record.crop_type = crop_type
            
            # Actualizar sensor asociados
            if session_record.sensor_reading:
                sensor_record = session_record.sensor_reading
                sensor_record.temperature = float(sensor_data.get("temperature", 22.0))
                sensor_record.humidity = float(sensor_data.get("humidity", 60.0))
                sensor_record.uv_solar = float(sensor_data.get("uv_solar", 300.0))
                sensor_record.motor_current = float(sensor_data.get("motor_current", 0.4))
            else:
                sensor_record = SensorReading(
                    temperature=float(sensor_data.get("temperature", 22.0)),
                    humidity=float(sensor_data.get("humidity", 60.0)),
                    uv_solar=float(sensor_data.get("uv_solar", 300.0)),
                    motor_current=float(sensor_data.get("motor_current", 0.4))
                )
                db.session.add(sensor_record)
                db.session.flush()
                session_record.sensor_reading_id = sensor_record.id

            # Actualizar métrica asociada
            if session_record.metrics:
                metrics_record = session_record.metrics[0]
                metrics_record.foliar_area_cm2 = final_metrics.get("foliar_area_cm2", 0.0)
                metrics_record.plant_height_cm = final_metrics.get("plant_height_cm", 0.0)
                metrics_record.stem_diameter_mm = final_metrics.get("stem_diameter_mm", 0.0)
                metrics_record.health_index = final_metrics.get("health_index", 100.0)
                metrics_record.compacity_index = final_metrics.get("compacity_index", 0.0)
                metrics_record.spots_count = final_metrics.get("spots_count", 0)
                metrics_record.fruits_count = final_metrics.get("fruits_count", 0)
                metrics_record.image_path_cenital_orig = cenital_paths.get("orig")
                metrics_record.image_path_cenital_proc = cenital_paths.get("proc")
                metrics_record.image_path_lateral_orig = lateral_paths.get("orig")
                metrics_record.image_path_lateral_proc = lateral_paths.get("proc")
            else:
                metrics_record = BiometricMetric(
                    session_id=session_record.id,
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
                db.session.add(metrics_record)
                
            db.session.commit()
            return session_record.id, metrics_record

        # Si no existe, crear nuevo registro
        sensor_record = SensorReading(
            temperature=float(sensor_data.get("temperature", 22.0)),
            humidity=float(sensor_data.get("humidity", 60.0)),
            uv_solar=float(sensor_data.get("uv_solar", 300.0)),
            motor_current=float(sensor_data.get("motor_current", 0.4))
        )
        db.session.add(sensor_record)
        db.session.flush()
        
        session_record = CaptureSession(
            period=period,
            plant_id=int(plant_id),
            crop_type=crop_type,
            sensor_reading_id=sensor_record.id,
            timestamp=datetime.now()
        )
        db.session.add(session_record)
        db.session.flush()
        
        metrics_record = BiometricMetric(
            session_id=session_record.id,
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
        db.session.add(metrics_record)
        db.session.commit()
        
        return session_record.id, metrics_record
