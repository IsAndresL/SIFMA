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
    Soporta múltiples formatos de fecha/hora (incluyendo formato regional español con 'p, m,' o 'p.m.'),
    delimitadores (; , y tabuladores) y números con coma o punto decimal.
    """
    
    def __init__(self, sensor_repo: Optional[SensorRepository] = None, session_repo: Optional[CaptureSessionRepository] = None):
        self.sensor_repo = sensor_repo or SensorRepository()
        self.session_repo = session_repo or CaptureSessionRepository()

    @staticmethod
    def parse_time_str(time_str: str):
        if not time_str:
            return None
        ts = str(time_str).strip()
        
        # Limpiar caracteres invisibles, espacios duros y puntuación regional
        ts = ts.replace('\xa0', ' ').replace('\u202f', ' ').replace('\t', ' ')
        
        # Normalizar sufijos de mañana y tarde en español (ej: "p, m,", "p. m.", "p.m.", "pm", "a, m,")
        ts = re.sub(r'p[\.,\s]+m[\.,\s]*', ' PM', ts, flags=re.IGNORECASE)
        ts = re.sub(r'a[\.,\s]+m[\.,\s]*', ' AM', ts, flags=re.IGNORECASE)
        ts = re.sub(r'\s+', ' ', ts).strip()
        
        formats = [
            '%I:%M:%S %p', 
            '%H:%M:%S', 
            '%I:%M %p', 
            '%H:%M',
            '%I:%M:%S%p',
            '%I:%M%p'
        ]
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
        ds = str(date_str).strip().replace('\xa0', ' ')
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%y']
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
        # Detección inteligente de delimitador
        if ';' in first_line:
            delimiter = ';'
        elif '\t' in first_line:
            delimiter = '\t'
        else:
            delimiter = ','
        
        reader = csv.reader(lines, delimiter=delimiter)
        try:
            raw_header = next(reader)
            header = [h.strip().lower() for h in raw_header]
        except StopIteration:
            return {"status": "error", "message": "Formato de archivo inválido."}
        
        col_fecha = next((i for i, h in enumerate(header) if any(k in h for k in ['fecha', 'date', 'timestamp', 'tiempo'])), 0)
        col_hora = next((i for i, h in enumerate(header) if any(k in h for k in ['hora', 'time'])), None)
        col_temp = next((i for i, h in enumerate(header) if any(k in h for k in ['temp', 'temperatura'])), None)
        col_hr = next((i for i, h in enumerate(header) if any(k in h for k in ['hr', 'hum', 'humedad'])), None)
        
        # Priorizar columna de radiación solar sobre co2 si ambas existen
        col_rad = next((i for i, h in enumerate(header) if any(k in h for k in ['rad', 'solar', 'uv', 'lux', 'luz', 'irradiancia'])), None)
        if col_rad is None:
            col_rad = next((i for i, h in enumerate(header) if 'co2' in h), None)
            
        col_amp = next((i for i, h in enumerate(header) if any(k in h for k in ['amp', 'curr', 'corr', 'motor', 'bomba', 'corriente'])), None)

        imported_count = 0
        readings_batch = []
        dates_seen = set()

        def safe_float(val, default=0.0):
            if not val: return default
            try:
                # Soporte para coma decimal (ej. "27,1" -> "27.1")
                cleaned_val = str(val).replace(',', '.').strip()
                return float(cleaned_val)
            except ValueError:
                return default

        for row in reader:
            if not row or len(row) < 2:
                continue

            try:
                d = self.parse_date_str(row[col_fecha])
                t = self.parse_time_str(row[col_hora]) if (col_hora is not None and col_hora < len(row)) else None
                
                # Si no se obtuvieron por separado, intentar parsear fecha/hora completa en una celda
                if not d or not t:
                    raw_dt_str = str(row[col_fecha]).strip()
                    dt = None
                    for dt_fmt in ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            dt = datetime.strptime(raw_dt_str, dt_fmt)
                            d = dt.date()
                            t = dt.time()
                            break
                        except Exception:
                            pass
                    if not dt:
                        continue
                else:
                    dt = datetime.combine(d, t)

                dates_seen.add(d.strftime("%Y-%m-%d"))

                temp_val = safe_float(row[col_temp]) if col_temp is not None and col_temp < len(row) else 0.0
                hr_val = safe_float(row[col_hr]) if col_hr is not None and col_hr < len(row) else 0.0
                rad_val = safe_float(row[col_rad]) if col_rad is not None and col_rad < len(row) else 0.0
                amp_val = safe_float(row[col_amp]) if col_amp is not None and col_amp < len(row) else 0.0

                readings_batch.append(SensorReading(
                    timestamp=dt,
                    temperature=temp_val,
                    humidity=hr_val,
                    uv_solar=rad_val,
                    motor_current=amp_val
                ))
                imported_count += 1

                # Inserción en lotes de 1000 para máximo rendimiento
                if len(readings_batch) >= 1000:
                    self.sensor_repo.bulk_add(readings_batch)
                    readings_batch = []

            except Exception:
                continue

        if readings_batch:
            self.sensor_repo.bulk_add(readings_batch)

        # Reasociar sesiones de captura existentes con las nuevas lecturas de sensores
        try:
            sessions = self.session_repo.get_all()
            for s in sessions:
                if not s.sensor_reading_id or (s.sensor_reading and s.sensor_reading.temperature == 0.0):
                    nearest_sensor = self.sensor_repo.find_nearest(s.timestamp)
                    if nearest_sensor:
                        s.sensor_reading_id = nearest_sensor.id
            db.session.commit()
        except Exception:
            pass

        return {
            "status": "success",
            "imported_records": imported_count,
            "imported_rows": imported_count,
            "dates_found": sorted(list(dates_seen)),
            "message": f"Se importaron {imported_count} lecturas de telemetría exitosamente."
        }
