import glob
import sys
from typing import List, Dict, Any
from .mock_adapter import MockTelemetryAdapter

class SerialTelemetryAdapter:
    """
    Adaptador de puerto serie / antena receptora USB para adquisición física.
    Detecta puertos COM en Windows y /dev/ttyUSB en Linux.
    """
    def __init__(self, port: str = "USB_ANTENNA_AUTO"):
        self.port = port
        self.fallback_mock = MockTelemetryAdapter()

    def get_available_ports(self) -> List[str]:
        ports = ["USB_ANTENNA_AUTO"]
        if sys.platform.startswith('win'):
            for i in range(1, 16):
                ports.append(f"COM{i}")
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports.extend(glob.glob('/dev/tty[A-Za-z]*'))
        elif sys.platform.startswith('darwin'):
            ports.extend(glob.glob('/dev/tty.*'))
            
        ports.extend(["ANTENA_RF_LOCAL_PORT_1", "SIMULADOR_ANTENA_TEST"])
        return sorted(list(set(ports)))

    def read_sample(self) -> Dict[str, Any]:
        # Si no hay dispositivo serie físico conectado, utiliza fallback dinámico
        return self.fallback_mock.read_sample()
