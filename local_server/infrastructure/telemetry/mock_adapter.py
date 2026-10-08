import random
from datetime import datetime
from typing import List, Dict, Any

class MockTelemetryAdapter:
    """Adaptador de telemetría para simulación realista y pruebas."""
    
    def __init__(self):
        self.temp_base = 28.5
        self.hum_base = 68.0
        self.uv_base = 45000.0
        self.current_base = 1.65
        self.ec_base = 1680.0
        self.ph_base = 6.20
        self.turb_base = 4.2
        self.do_base = 7.6

    def get_available_ports(self) -> List[str]:
        return ["USB_ANTENNA_AUTO", "ANTENA_RF_LOCAL_PORT_1", "ANTENA_RF_LOCAL_PORT_2", "SIMULADOR_ANTENA_TEST"]

    def read_sample(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": round(self.temp_base + random.uniform(-0.6, 0.6), 2),
            "humidity": round(self.hum_base + random.uniform(-1.2, 1.2), 1),
            "uv_solar": round(max(0.0, self.uv_base + random.uniform(-1500.0, 1500.0)), 1),
            "motor_current": round(max(0.0, self.current_base + random.uniform(-0.04, 0.04)), 3),
            "ec_conductivity": round(self.ec_base + random.uniform(-25.0, 25.0), 1),
            "water_ph": round(self.ph_base + random.uniform(-0.06, 0.06), 2),
            "turbidity_ntu": round(max(0.5, self.turb_base + random.uniform(-0.4, 0.4)), 2),
            "dissolved_oxygen_mg_l": round(max(1.0, self.do_base + random.uniform(-0.2, 0.2)), 2)
        }
