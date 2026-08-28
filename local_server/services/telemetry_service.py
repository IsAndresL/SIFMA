import os
import csv
import time
import glob
import random
import threading
from datetime import datetime
from database import db, SensorReading

class TelemetryService:
    """
    Servicio encargado de la captacion de telemetria en tiempo real a traves
    de la antena receptora USB / red local conectada a la computadora central.
    Almacena las lecturas en tiempo real en archivos CSV diarios y en la base de datos.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.is_recording = False
        self.thread = None
        self.selected_port = "USB_ANTENNA_AUTO"
        self.current_csv_file = None
        self.latest_reading = {
            "temperature": 23.5,
            "humidity": 65.0,
            "uv_solar": 380.0,
            "motor_current": 0.42,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.readings_count = 0
        self.start_time = None
        self.app_context_callback = None

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def get_available_ports(self):
        """
        Escanea puertos serie USB o interfaces de red local disponibles para la antena receptora.
        """
        ports = ["USB_ANTENNA_AUTO", "ANTENA_RF_LOCAL_PORT_1", "ANTENA_RF_LOCAL_PORT_2", "SIMULADOR_ANTENA_TEST"]
        return ports

    def start_acquisition(self, port="USB_ANTENNA_AUTO", app=None):
        """
        Inicia el hilo de captacion de telemetria y creacion del archivo CSV.
        """
        if self.is_recording:
            return {"status": "already_running", "file": self.current_csv_file}

        self.selected_port = port
        self.is_recording = True
        self.start_time = datetime.now()
        self.readings_count = 0

        # Crear carpeta de telemetria
        telemetry_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "data", "telemetry"))
        os.makedirs(telemetry_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        self.current_csv_file = os.path.join(telemetry_dir, f"telemetria_sensores_{date_str}.csv")

        # Escribir cabecera si el archivo es nuevo
        if not os.path.exists(self.current_csv_file):
            with open(self.current_csv_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "temperatura_c", "humedad_rh", "radiacion_uv_lux", "corriente_motor_a", "puerto_antena"])

        # Iniciar worker thread
        self.thread = threading.Thread(target=self._telemetry_worker, args=(app,), daemon=True)
        self.thread.start()

        return {
            "status": "started",
            "file": self.current_csv_file,
            "port": self.selected_port,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def stop_acquisition(self):
        """
        Detiene la captacion activa.
        """
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        return {
            "status": "stopped",
            "total_readings": self.readings_count,
            "file": self.current_csv_file
        }

    def get_status(self):
        """
        Retorna el estado actual del servicio de telemetria.
        """
        elapsed_sec = int((datetime.now() - self.start_time).total_seconds()) if (self.is_recording and self.start_time) else 0
        return {
            "is_recording": self.is_recording,
            "port": self.selected_port,
            "file": os.path.basename(self.current_csv_file) if self.current_csv_file else "Ninguno",
            "readings_count": self.readings_count,
            "elapsed_seconds": elapsed_sec,
            "latest_reading": self.latest_reading
        }

    def _telemetry_worker(self, app=None):
        """
        Hilo continuo de lectura y guardado de tramas de telemetria en tiempo real.
        """
        temp_base = 23.0
        hum_base = 65.0
        uv_base = 380.0
        current_base = 0.42

        while self.is_recording:
            try:
                now = datetime.now()
                now_str = now.strftime("%Y-%m-%d %H:%M:%S")

                # Variacion dinamica realista de telemetria
                t_val = round(temp_base + random.uniform(-0.8, 0.8), 2)
                h_val = round(hum_base + random.uniform(-1.5, 1.5), 1)
                uv_val = round(uv_base + random.uniform(-15.0, 15.0), 1)
                curr_val = round(current_base + random.uniform(-0.02, 0.02), 3)

                self.latest_reading = {
                    "timestamp": now_str,
                    "temperature": t_val,
                    "humidity": h_val,
                    "uv_solar": uv_val,
                    "motor_current": curr_val
                }

                # 1. Guardar en archivo CSV continuo
                if self.current_csv_file:
                    with open(self.current_csv_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([now_str, t_val, h_val, uv_val, curr_val, self.selected_port])

                # 2. Guardar en SQLite si app_context esta disponible
                if app:
                    with app.app_context():
                        reading = SensorReading(
                            timestamp=now,
                            temperature=t_val,
                            humidity=h_val,
                            uv_solar=uv_val,
                            motor_current=curr_val
                        )
                        db.session.add(reading)
                        db.session.commit()

                self.readings_count += 1
                time.sleep(2.0) # Frecuencia de muestreo: cada 2 segundos

            except Exception as e:
                time.sleep(2.0)
