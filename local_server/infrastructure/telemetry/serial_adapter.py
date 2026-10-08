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
            "water_ph": 6.12,
            "ec_conductivity": 1649.6,
            "turbidity_ntu": 4.06,
            "dissolved_oxygen_mg_l": 7.6,
            "water_temp": 20.0,
            "temperature": 25.49,
            "humidity": 83.2,
            "motor_state": 1,
            "motor_current": 1.0,
            "uv_solar": 0.0,
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
        Lee y decodifica la trama real transmitida por la antena en formato posicional o clave-valor.
        Estructura Oficial SIFMA ($...#):
          Pos 1: pH Solución (pH)
          Pos 2: Conductividad Eléctrica (µS/cm)
          Pos 3: Turbidez (NTU)
          Pos 4: Oxígeno Disuelto (mg/L)
          Pos 5: Temperatura del Agua (°C)
          Pos 6: Temperatura Exterior (°C)
          Pos 7: Humedad Relativa Exterior (% HR)
          Pos 8: Estado Motor (1-0)
        Ejemplo real: '$7.75,1000.0,2.7,0.00,23.9,25.5,60.2,0,0,0#'
        """
        if self.port == "SIMULADOR_ANTENA_TEST":
            return self.fallback_mock.read_sample()

        if self._connect() and self.serial_conn:
            try:
                raw_line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if raw_line:
                    # Limpiar delimitadores envolventes $ y #
                    cleaned_line = raw_line.strip().strip('$#').strip()
                    delim = ';' if ';' in cleaned_line else ','
                    parts = [p.strip() for p in cleaned_line.split(delim)]
                    
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
                                    if k in ['PH', 'ACIDEZ']:
                                        sample_dict['water_ph'] = round(min(14.0, max(0.0, v_num)), 2)
                                        parsed_any = True
                                    elif k in ['EC', 'COND', 'CONDUCTIVIDAD']:
                                        sample_dict['ec_conductivity'] = round(max(0.0, v_num), 1)
                                        parsed_any = True
                                    elif k in ['TURB', 'TURBIDEZ', 'NTU']:
                                        sample_dict['turbidity_ntu'] = round(max(0.0, v_num), 2)
                                        parsed_any = True
                                    elif k in ['DO', 'OD', 'OXIGENO', 'MG/L']:
                                        sample_dict['dissolved_oxygen_mg_l'] = round(max(0.0, v_num), 2)
                                        parsed_any = True
                                    elif k in ['TW', 'TAGUA', 'TEMPWATER', 'TEMP_AGUA']:
                                        sample_dict['water_temp'] = round(v_num, 2)
                                        parsed_any = True
                                    elif k in ['T', 'TEMP', 'TEMPERATURA', 'TEXT', 'TEMP_EXT']:
                                        sample_dict['temperature'] = round(v_num, 2)
                                        parsed_any = True
                                    elif k in ['H', 'HUM', 'HUMEDAD', 'HR']:
                                        sample_dict['humidity'] = round(min(100.0, max(0.0, v_num)), 1)
                                        parsed_any = True
                                    elif k in ['M', 'MOT', 'MOTOR', 'BOMBA', 'ESTADO_MOTOR', 'I', 'CURR']:
                                        sample_dict['motor_state'] = 1 if v_num >= 0.5 else 0
                                        sample_dict['motor_current'] = round(abs(v_num), 3)
                                        parsed_any = True
                                    elif k in ['UV', 'RAD', 'SOLAR', 'LUX']:
                                        sample_dict['uv_solar'] = round(max(0.0, v_num), 1)
                                        parsed_any = True
                                except ValueError:
                                    pass
                    
                    # 2. Modo Posicional Oficial SIFMA
                    elif len(parts) >= 4:
                        try:
                            p_nums = []
                            for p in parts:
                                try:
                                    p_nums.append(float(p.replace(',', '.').strip()))
                                except ValueError:
                                    pass
                                    
                            if len(p_nums) >= 4:
                                # Pos 1: pH Solución
                                sample_dict['water_ph'] = round(min(14.0, max(0.0, p_nums[0])), 2)
                                # Pos 2: Conductividad Eléctrica µS/cm
                                sample_dict['ec_conductivity'] = round(max(0.0, p_nums[1]), 1)
                                # Pos 3: Turbidez NTU
                                sample_dict['turbidity_ntu'] = round(max(0.0, p_nums[2]), 2)
                                # Pos 4: Oxígeno Disuelto mg/L
                                sample_dict['dissolved_oxygen_mg_l'] = round(max(0.0, p_nums[3]), 2)
                                
                                # Pos 5: Temperatura del Agua (°C)
                                if len(p_nums) >= 5:
                                    sample_dict['water_temp'] = round(p_nums[4], 2)
                                # Pos 6: Temperatura Exterior (°C)
                                if len(p_nums) >= 6:
                                    sample_dict['temperature'] = round(p_nums[5], 2)
                                # Pos 7: Humedad Relativa Exterior (% HR)
                                if len(p_nums) >= 7:
                                    sample_dict['humidity'] = round(min(100.0, max(0.0, p_nums[6])), 1)
                                # Pos 8: Estado Motor (1-0)
                                if len(p_nums) >= 8:
                                    sample_dict['motor_state'] = 1 if p_nums[7] >= 0.5 else 0
                                    sample_dict['motor_current'] = round(p_nums[7], 2)
                                    
                                parsed_any = True
                        except Exception as e:
                            logger.warning(f"Error parseando trama posicional: {e}")
                            
                    if parsed_any:
                        sample_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        sample_dict["raw"] = raw_line
                        sample_dict["source"] = f"Antena ({self.active_port})"
                        self.last_valid_sample = sample_dict
                        return sample_dict
            except Exception as e:
                logger.warning(f"[SIFMA] Error de lectura en antena: {e}")
                self._disconnect()

        # Si no hubo lectura válida del puerto físico, retornar última muestra válida
        if self.last_valid_sample:
            sample = dict(self.last_valid_sample)
            sample["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return sample

        return self.fallback_mock.read_sample()
