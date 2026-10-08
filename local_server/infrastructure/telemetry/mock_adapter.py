import random
from datetime import datetime
from typing import List, Dict, Any

class MockTelemetryAdapter:
    """Adaptador de telemetría para simulación realista y pruebas."""
    
    def __init__(self):
        self.ph_base = 6.12
        self.ec_base = 1649.6
        self.turb_base = 4.06
        self.do_base = 7.6
        self.water_temp_base = 20.0
        self.temp_base = 25.49
        self.hum_base = 83.2
        self.motor_state_base = 1
        self.uv_base = 0.0

    def get_available_ports(self) -> List[str]:
        return ["USB_ANTENNA_AUTO", "ANTENA_RF_LOCAL_PORT_1", "ANTENA_RF_LOCAL_PORT_2", "SIMULADOR_ANTENA_TEST"]

    def read_sample(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "water_ph": round(max(0.0, min(14.0, self.ph_base + random.uniform(-0.08, 0.08))), 2),
            "ec_conductivity": round(max(0.0, self.ec_base + random.uniform(-20.0, 20.0)), 1),
            "turbidity_ntu": round(max(0.1, self.turb_base + random.uniform(-0.3, 0.3)), 2),
            "dissolved_oxygen_mg_l": round(max(0.0, self.do_base + random.uniform(-0.2, 0.2)), 2),
            "water_temp": round(self.water_temp_base + random.uniform(-0.4, 0.4), 2),
            "temperature": round(self.temp_base + random.uniform(-0.5, 0.5), 2),
            "humidity": round(min(100.0, max(0.0, self.hum_base + random.uniform(-1.0, 1.0))), 1),
            "motor_state": self.motor_state_base,
            "motor_current": float(self.motor_state_base),
            "uv_solar": 0.0
        }
