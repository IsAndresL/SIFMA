import random

class SensorReadingService:
    """
    Servicio para lectura de sensores ambientales y de corriente del motor.
    """
    
    @staticmethod
    def read_environmental_sensors():
        """
        Retorna las lecturas de los sensores (o valores simulados realistas).
        """
        return {
            "temperature": round(random.uniform(20.0, 28.0), 2),
            "humidity": round(random.uniform(55.0, 75.0), 2),
            "uv_solar": round(random.uniform(150.0, 650.0), 2),
            "motor_current": round(random.uniform(0.38, 0.46), 2)
        }
