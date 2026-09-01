import sys
import glob
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

from .mock_adapter import MockTelemetryAdapter

logger = logging.getLogger("SIFMA")

class SerialTelemetryAdapter:
    """
    Adaptador de puerto serie / antena receptora USB para adquisición física en tiempo real.
    Compatible con módulos XBee (PRO S2B, S2C, Series 1) y adaptadores USB-UART (FTDI, CP210x, CH340).
    """
    def __init__(self, port: str = "USB_ANTENNA_AUTO", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[Any] = None
        self.active_port: Optional[str] = None
        self.fallback_mock = MockTelemetryAdapter()
        self.last_valid_sample = {
            "temperature": 23.5,
            "humidity": 65.0,
            "uv_solar": 0.0,
            "motor_current": 0.0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_available_ports(self) -> List[str]:
        """Retorna lista de puertos COM físicos detectados en el sistema operativo."""
        detected = []
        if HAS_SERIAL:
            try:
                for p in serial.tools.list_ports.comports():
                    detected.append(p.device)
            except Exception as e:
                logger.warning(f"Error listando puertos seriales: {e}")

        # Si pyserial no detectó nada, probar fallback por plataforma
        if not detected:
            if sys.platform.startswith('win'):
                for i in range(1, 12):
                    detected.append(f"COM{i}")
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                detected.extend(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
            elif sys.platform.startswith('darwin'):
                detected.extend(glob.glob('/dev/tty.*'))

        ports = ["USB_ANTENNA_AUTO"] + sorted(list(set(detected)))
        ports.append("SIMULADOR_ANTENA_TEST")
        return ports

    def _resolve_port(self) -> Optional[str]:
        """Resuelve el puerto real a usar si está en modo AUTO o manual."""
        if self.port != "USB_ANTENNA_AUTO" and self.port != "SIMULADOR_ANTENA_TEST":
            return self.port

        if HAS_SERIAL:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            if ports:
                # Priorizar el primer puerto COM disponible (ej. COM6)
                return ports[0]

        return None

    def _connect(self) -> bool:
        """Abre la conexión serial si no está ya abierta."""
        if not HAS_SERIAL:
            return False

        target_port = self._resolve_port()
        if not target_port:
            return False

        # Si ya está conectado al puerto destino
        if self.serial_conn and self.serial_conn.is_open and self.active_port == target_port:
            return True

        self._disconnect()

        try:
            self.serial_conn = serial.Serial(
                port=target_port,
                baudrate=self.baudrate,
                timeout=1.5,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.active_port = target_port
            # Limpiar búfer inicial
            self.serial_conn.reset_input_buffer()
            logger.info(f"[SIFMA] Conectado exitosamente a antena XBee en {target_port} @ {self.baudrate} baud.")
            return True
        except Exception as e:
            logger.warning(f"[SIFMA] No se pudo abrir {target_port}: {e}")
            self.serial_conn = None
            self.active_port = None
            return False

    def _disconnect(self):
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None
            self.active_port = None

    def read_sample(self) -> Dict[str, Any]:
        """
        Lee y decodifica una muestra real desde la antena XBee.
        Formato de trama esperado: 'uv,temperatura,humedad,corriente' (ej: '0.0,33.6,64.9,-0.0').
        """
        if self.port == "SIMULADOR_ANTENA_TEST":
            return self.fallback_mock.read_sample()

        if self._connect() and self.serial_conn:
            try:
                raw_line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if raw_line:
                    parts = [p.strip() for p in raw_line.split(',')]
                    if len(parts) >= 4:
                        try:
                            uv_val = max(0.0, float(parts[0]))
                            temp_val = float(parts[1])
                            hum_val = min(100.0, max(0.0, float(parts[2])))
                            curr_val = abs(float(parts[3]))

                            sample = {
                                "temperature": round(temp_val, 2),
                                "humidity": round(hum_val, 2),
                                "uv_solar": round(uv_val, 1),
                                "motor_current": round(curr_val, 3),
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "raw": raw_line,
                                "source": f"XBee ({self.active_port})"
                            }
                            self.last_valid_sample = sample
                            return sample
                        except ValueError:
                            pass
            except Exception as e:
                logger.warning(f"[SIFMA] Error de lectura en antena: {e}")
                self._disconnect()

        # Si no hubo lectura válida del puerto físico, retornar última muestra válida o mock
        if self.last_valid_sample:
            sample = dict(self.last_valid_sample)
            sample["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return sample

        return self.fallback_mock.read_sample()
