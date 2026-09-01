import random
from datetime import datetime
from typing import List, Dict, Any

class MockTelemetryAdapter:
    """Adaptador de telemetría para simulación realista y pruebas."""
    
    def __init__(self):
        self.temp_base = 23.0
        self.hum_base = 65.0
        self.uv_base = 380.0
        self.current_base = 0.42

    def get_available_ports(self) -> List[str]:
        return ["USB_ANTENNA_AUTO", "ANTENA_RF_LOCAL_PORT_1", "ANTENA_RF_LOCAL_PORT_2", "SIMULADOR_ANTENA_TEST"]

    def read_sample(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": round(self.temp_base + random.uniform(-0.8, 0.8), 2),
            "humidity": round(self.hum_base + random.uniform(-1.5, 1.5), 1),
            "uv_solar": round(self.uv_base + random.uniform(-15.0, 15.0), 1),
            "motor_current": round(self.current_base + random.uniform(-0.02, 0.02), 3)
        }
