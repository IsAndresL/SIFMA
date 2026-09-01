import os
import csv
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.config import config
from domain.models import SensorReading
from infrastructure.database.repositories import SensorRepository
from infrastructure.telemetry import SerialTelemetryAdapter, MockTelemetryAdapter
from infrastructure.database.connection import db

class TelemetryApplicationService:
    """
    Caso de uso: Gestión y adquisición continua de telemetría ambiental (Thread-Safe Singleton).
    (SOLID: SRP, DIP, Singleton Pattern)
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self, sensor_repo: Optional[SensorRepository] = None):
        self.sensor_repo = sensor_repo or SensorRepository()
        self.adapter = SerialTelemetryAdapter()
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

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def get_available_ports(self) -> List[str]:
        return self.adapter.get_available_ports()

    def start_acquisition(self, port: str = "USB_ANTENNA_AUTO", app=None) -> Dict[str, Any]:
        if self.is_recording:
            return {"status": "already_running", "file": self.current_csv_file}

        self.selected_port = port
        self.adapter.port = port
        self.is_recording = True
        self.start_time = datetime.now()
        self.readings_count = 0

        telemetry_dir = config.TELEMETRY_DIR
        os.makedirs(telemetry_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        self.current_csv_file = os.path.join(telemetry_dir, f"telemetria_sensores_{date_str}.csv")

        if not os.path.exists(self.current_csv_file):
            with open(self.current_csv_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "temperatura_c", "humedad_rh", "radiacion_uv_lux", "corriente_motor_a", "puerto_antena"])

        self.thread = threading.Thread(target=self._telemetry_worker, args=(app,), daemon=True)
        self.thread.start()

        return {
            "status": "started",
            "file": self.current_csv_file,
            "port": self.selected_port,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def stop_acquisition(self) -> Dict[str, Any]:
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        return {
            "status": "stopped",
            "total_readings": self.readings_count,
            "file": self.current_csv_file
        }

    def get_status(self) -> Dict[str, Any]:
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
        while self.is_recording:
            try:
                sample = self.adapter.read_sample()
                self.latest_reading = sample

                now_str = sample.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                t_val = sample.get("temperature", 0.0)
                h_val = sample.get("humidity", 0.0)
                uv_val = sample.get("uv_solar", 0.0)
                curr_val = sample.get("motor_current", 0.0)

                # 1. Guardar en archivo CSV continuo
                if self.current_csv_file:
                    with open(self.current_csv_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([now_str, t_val, h_val, uv_val, curr_val, self.selected_port])

                # 2. Guardar en SQLite si app_context está activo
                if app:
                    with app.app_context():
                        reading = SensorReading(
                            timestamp=datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S"),
                            temperature=t_val,
                            humidity=h_val,
                            uv_solar=uv_val,
                            motor_current=curr_val
                        )
                        db.session.add(reading)
                        db.session.commit()

                self.readings_count += 1
                time.sleep(2.0)

            except Exception:
                time.sleep(2.0)
