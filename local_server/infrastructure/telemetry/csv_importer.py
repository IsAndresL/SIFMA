import csv
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from domain.models import SensorReading
from infrastructure.database.repositories.sensor_repository import SensorRepository
from infrastructure.database.repositories.session_repository import CaptureSessionRepository
from infrastructure.database.connection import db

class TowerCsvImporter:
    """
    Parser robusto para importar archivos CSV emitidos por la torre hidropónica.
    Soporta múltiples formatos de fecha/hora, delimitadores (; y ,) y comas decimales.
    """
    
    def __init__(self, sensor_repo: Optional[SensorRepository] = None, session_repo: Optional[CaptureSessionRepository] = None):
        self.sensor_repo = sensor_repo or SensorRepository()
        self.session_repo = session_repo or CaptureSessionRepository()

    @staticmethod
    def parse_time_str(time_str: str):
        if not time_str:
            return None
        ts = str(time_str).strip()
        ts = ts.replace('p,m,', 'PM').replace('a,m,', 'AM')
        ts = ts.replace('p.m.', 'PM').replace('a.m.', 'AM')
        ts = ts.replace('p. m.', 'PM').replace('a. m.', 'AM')
        ts = re.sub(r'\s+', ' ', ts).strip()
        
        formats = ['%I:%M:%S %p', '%H:%M:%S', '%I:%M %p', '%H:%M']
        for fmt in formats:
            try:
                return datetime.strptime(ts, fmt).time()
            except Exception:
                pass
        return None

    @staticmethod
    def parse_date_str(date_str: str):
        if not date_str:
            return None
        ds = str(date_str).strip()
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
        for fmt in formats:
            try:
                return datetime.strptime(ds, fmt).date()
            except Exception:
                pass
        return None

    def import_csv(self, file_stream_or_path) -> Dict[str, Any]:
        if isinstance(file_stream_or_path, str):
            with open(file_stream_or_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            content = file_stream_or_path.read().decode('utf-8', errors='ignore')

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            return {"status": "error", "message": "El archivo CSV está vacío."}

        first_line = lines[0]
        delimiter = ';' if ';' in first_line else ','
        
        reader = csv.reader(lines, delimiter=delimiter)
        try:
            header = [h.strip().lower() for h in next(reader)]
        except StopIteration:
            return {"status": "error", "message": "Formato de archivo inválido."}
        
        col_fecha = next((i for i, h in enumerate(header) if 'fecha' in h or 'date' in h), 0)
        col_hora = next((i for i, h in enumerate(header) if 'hora' in h or 'time' in h), 1)
        col_temp = next((i for i, h in enumerate(header) if 'temp' in h), None)
        col_hr = next((i for i, h in enumerate(header) if 'hr' in h or 'hum' in h), None)
        col_co2_uv = next((i for i, h in enumerate(header) if 'co2' in h or 'uv' in h or 'lux' in h), None)
        col_amp = next((i for i, h in enumerate(header) if 'amp' in h or 'curr' in h or 'corr' in h), None)

        imported_count = 0
        readings_batch = []
        dates_seen = set()

        def safe_float(val, default=0.0):
            if not val: return default
            try:
                return float(str(val).replace(',', '.').strip())
            except ValueError:
                return default

        for row in reader:
            if not row or len(row) < 2:
                continue

            try:
                d = self.parse_date_str(row[col_fecha])
                t = self.parse_time_str(row[col_hora]) if col_hora < len(row) else None
                if not d or not t:
                    continue

                dt = datetime.combine(d, t)
                dates_seen.add(d.strftime("%Y-%m-%d"))

                temp_val = safe_float(row[col_temp]) if col_temp is not None and col_temp < len(row) else 0.0
                hr_val = safe_float(row[col_hr]) if col_hr is not None and col_hr < len(row) else 0.0
                co2_uv_val = safe_float(row[col_co2_uv]) if col_co2_uv is not None and col_co2_uv < len(row) else 0.0
                amp_val = safe_float(row[col_amp]) if col_amp is not None and col_amp < len(row) else 0.0

                readings_batch.append(SensorReading(
                    timestamp=dt,
                    temperature=temp_val,
                    humidity=hr_val,
                    uv_solar=co2_uv_val,
                    motor_current=amp_val
                ))
                imported_count += 1

                if len(readings_batch) >= 1000:
                    self.sensor_repo.bulk_add(readings_batch)
                    readings_batch = []

            except Exception:
                continue

        if readings_batch:
            self.sensor_repo.bulk_add(readings_batch)

        # Reasociar sesiones de captura existentes con las nuevas lecturas reales
        sessions = self.session_repo.get_all_by_plant(plant_id=1)
        for s in sessions:
            if not s.sensor_reading_id or (s.sensor_reading and s.sensor_reading.temperature == 0.0):
                nearest_sensor = self.sensor_repo.find_nearest(s.timestamp)
                if nearest_sensor:
                    s.sensor_reading_id = nearest_sensor.id
        db.session.commit()

        return {
            "status": "success",
            "imported_rows": imported_count,
            "dates_found": list(dates_seen),
            "message": f"Se importaron {imported_count} lecturas de telemetría exitosamente."
        }
