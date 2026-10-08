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
                writer.writerow([
                    "Fecha", "Hora", "pH Solución", "Turbidez (NTU)", 
                    "Conductividad Eléctrica (µS/cm)", "Oxigeno Disuelto (mg/L)", 
                    "temperatura de agua", "estado motor: 1-0", 
                    "Temperatura exterior (°C)", "Humedad relativa exterior (% HR)"
                ])

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

                now_dt = datetime.now()
                now_str = sample.get("timestamp", now_dt.strftime("%Y-%m-%d %H:%M:%S"))
                try:
                    dt_obj = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt_obj = now_dt

                ph_val = sample.get("water_ph", 6.12)
                turb_val = sample.get("turbidity_ntu", 4.06)
                ec_val = sample.get("ec_conductivity", 1649.6)
                do_val = sample.get("dissolved_oxygen_mg_l", 7.6)
                water_t_val = sample.get("water_temp", 20.0)
                mot_st_val = sample.get("motor_state", 1)
                temp_val = sample.get("temperature", 25.49)
                hum_val = sample.get("humidity", 83.2)

                # 1. Guardar en archivo CSV continuo con el orden exacto oficial SIFMA
                if self.current_csv_file:
                    with open(self.current_csv_file, mode='a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            dt_obj.strftime("%d/%m/%Y"),
                            dt_obj.strftime("%I:%M:%S %p"),
                            ph_val,
                            turb_val,
                            ec_val,
                            do_val,
                            water_t_val,
                            mot_st_val,
                            temp_val,
                            hum_val
                        ])

                # 2. Guardar en SQLite si app_context está activo
                if app:
                    with app.app_context():
                        reading = SensorReading(
                            timestamp=dt_obj,
                            water_ph=ph_val,
                            turbidity_ntu=turb_val,
                            ec_conductivity=ec_val,
                            dissolved_oxygen_mg_l=do_val,
                            water_temp=water_t_val,
                            motor_state=mot_st_val,
                            motor_current=float(mot_st_val),
                            temperature=temp_val,
                            humidity=hum_val,
                            uv_solar=0.0
                        )
                        db.session.add(reading)
                        db.session.commit()

                self.readings_count += 1
                time.sleep(2.0)

            except Exception as e:
                time.sleep(2.0)
