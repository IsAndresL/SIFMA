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
            "temperature": 28.5,
            "humidity": 68.0,
            "uv_solar": 0.0,
            "motor_current": 0.0,
            "ec_conductivity": 1650.0,
            "water_ph": 6.2,
            "turbidity_ntu": 3.8,
            "dissolved_oxygen_mg_l": 7.4,
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
        Soporta tramas posicionales (4 u 8 parámetros) y tramas clave-valor (T:, H:, UV:, I:, EC:, PH:, TURB:, DO:).
        Ejemplos:
          - '0.0,33.6,64.9,1.65,1680.0,6.20,4.2,7.6'
          - 'T:33.6,H:64.9,UV:0.0,I:1.65,EC:1680,PH:6.2,TURB:4.2,DO:7.6'
        """
        if self.port == "SIMULADOR_ANTENA_TEST":
            return self.fallback_mock.read_sample()

        if self._connect() and self.serial_conn:
            try:
                raw_line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if raw_line:
                    # Delimitador coma o punto y coma
                    delim = ';' if ';' in raw_line else ','
                    parts = [p.strip() for p in raw_line.split(delim)]
                    
                    sample_dict = dict(self.last_valid_sample)
                    parsed_any = False
                    
                    # 1. Modo Clave-Valor
                    if any(':' in p for p in parts):
                        for p in parts:
                            if ':' in p:
                                k, v = p.split(':', 1)
                                k = k.strip().upper()
                                try:
                                    v_num = float(v.replace(',', '.').strip())
                                    if k in ['T', 'TEMP', 'TEMPERATURA']:
                                        sample_dict['temperature'] = round(v_num, 2)
                                        parsed_any = True
                                    elif k in ['H', 'HUM', 'HUMEDAD', 'HR']:
                                        sample_dict['humidity'] = round(min(100.0, max(0.0, v_num)), 1)
                                        parsed_any = True
                                    elif k in ['UV', 'RAD', 'SOLAR', 'LUX']:
                                        sample_dict['uv_solar'] = round(max(0.0, v_num), 1)
                                        parsed_any = True
                                    elif k in ['I', 'CURR', 'AMP', 'CORRIENTE', 'BOMBA']:
                                        sample_dict['motor_current'] = round(abs(v_num), 3)
                                        parsed_any = True
                                    elif k in ['EC', 'COND', 'CONDUCTIVIDAD']:
                                        sample_dict['ec_conductivity'] = round(max(0.0, v_num), 1)
                                        parsed_any = True
                                    elif k in ['PH', 'ACIDEZ']:
                                        sample_dict['water_ph'] = round(min(14.0, max(0.0, v_num)), 2)
                                        parsed_any = True
                                    elif k in ['TURB', 'TURBIDEZ', 'NTU']:
                                        sample_dict['turbidity_ntu'] = round(max(0.0, v_num), 2)
                                        parsed_any = True
                                    elif k in ['DO', 'OD', 'OXIGENO', 'MG/L']:
                                        sample_dict['dissolved_oxygen_mg_l'] = round(max(0.0, v_num), 2)
                                        parsed_any = True
                                except ValueError:
                                    pass
                    
                    # 2. Modo Posicional
                    elif len(parts) >= 4:
                        try:
                            p_nums = []
                            for p in parts:
                                try:
                                    p_nums.append(float(p.replace(',', '.').strip()))
                                except ValueError:
                                    pass
                            if len(p_nums) >= 4:
                                # Si primer valor es grande (>100) es UV, si es <60 es Temperatura
                                if p_nums[0] > 60.0 and p_nums[1] < 60.0:
                                    sample_dict['uv_solar'] = round(max(0.0, p_nums[0]), 1)
                                    sample_dict['temperature'] = round(p_nums[1], 2)
                                    sample_dict['humidity'] = round(min(100.0, max(0.0, p_nums[2])), 1)
                                    sample_dict['motor_current'] = round(abs(p_nums[3]), 3)
                                else:
                                    sample_dict['temperature'] = round(p_nums[0], 2)
                                    sample_dict['humidity'] = round(min(100.0, max(0.0, p_nums[1])), 1)
                                    sample_dict['uv_solar'] = round(max(0.0, p_nums[2]), 1)
                                    sample_dict['motor_current'] = round(abs(p_nums[3]), 3)
                                
                                if len(p_nums) >= 5:
                                    sample_dict['ec_conductivity'] = round(max(0.0, p_nums[4]), 1)
                                if len(p_nums) >= 6:
                                    sample_dict['water_ph'] = round(min(14.0, max(0.0, p_nums[5])), 2)
                                if len(p_nums) >= 7:
                                    sample_dict['turbidity_ntu'] = round(max(0.0, p_nums[6]), 2)
                                if len(p_nums) >= 8:
                                    sample_dict['dissolved_oxygen_mg_l'] = round(max(0.0, p_nums[7]), 2)
                                    
                                parsed_any = True
                        except Exception:
                            pass
                            
                    if parsed_any:
                        sample_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        sample_dict["raw"] = raw_line
                        sample_dict["source"] = f"XBee ({self.active_port})"
                        self.last_valid_sample = sample_dict
                        return sample_dict
            except Exception as e:
                logger.warning(f"[SIFMA] Error de lectura en antena: {e}")
                self._disconnect()

        # Si no hubo lectura válida del puerto físico, retornar última muestra válida o mock
        if self.last_valid_sample:
            sample = dict(self.last_valid_sample)
            sample["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return sample

        return self.fallback_mock.read_sample()
