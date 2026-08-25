import os
import sys
import time
from datetime import datetime

# Asegurar importaciones modulares de la carpeta local
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
if NODE_DIR not in sys.path:
    sys.path.insert(0, NODE_DIR)

from services import OfflineStorageService, CameraCaptureService, SensorReadingService

def determine_period():
    current_hour = datetime.now().hour
    if current_hour < 10:
        return "manana"
    elif current_hour < 15:
        return "medio_dia"
    else:
        return "tarde"

def run_offline_capture():
    print("\n===============================================")
    print(f"SIFMA Raspberry Pi 5 - Captura Offline Autónoma")
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("===============================================\n")

    period = determine_period()
    print(f"1. Período detectado por reloj local: {period.upper()}")

    # 1. Leer sensores
    sensor_data = SensorReadingService.read_environmental_sensors()
    print(f"2. Sensores leídos: Temp={sensor_data['temperature']}°C, Hum={sensor_data['humidity']}%, UV={sensor_data['uv_solar']} lux")

    # 2. Crear carpeta de lote en la USB conectada (SIFMA_CAPTURES/YYYY-MM-DD/periodo/)
    batch_dir = OfflineStorageService.create_batch_directory(period=period)
    print(f"3. Carpeta de destino creada en la Memoria USB: {batch_dir}")

    # 3. Tomar 5 fotos cenitales
    print("4. Iniciando captura de 5 fotos Cenitales...")
    for i in range(1, 6):
        out_path = os.path.join(batch_dir, f"cenital_{i}.png")
        CameraCaptureService.capture_photo(out_path, camera_index=0)
        time.sleep(1)

    # 4. Tomar 5 fotos laterales
    print("5. Iniciando captura de 5 fotos Laterales...")
    for i in range(1, 6):
        out_path = os.path.join(batch_dir, f"lateral_{i}.png")
        CameraCaptureService.capture_photo(out_path, camera_index=1)
        time.sleep(1)

    # 5. Guardar metadatos JSON
    OfflineStorageService.save_batch_metadata(
        batch_dir=batch_dir,
        period=period,
        crop_type="cebollin",
        sensor_data=sensor_data,
        image_files_count=10,
        plant_id=1
    )

    print("\n===============================================")
    print("Captura offline completada y guardada en USB con éxito.")
    print("===============================================\n")

if __name__ == "__main__":
    run_offline_capture()
