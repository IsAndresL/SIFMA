import os
import sys
import time
import argparse
from datetime import datetime

# Asegurar importaciones relativas desde la carpeta raspi_node
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
if NODE_DIR not in sys.path:
    sys.path.insert(0, NODE_DIR)

from services import OfflineStorageService, CameraCaptureService

# Constantes de tiempo operativas para el ciclo de media hora (~30 min total)
DEFAULT_BOOT_COOLDOWN_SEC = 300   # 5 minutos de espera inicial al encender la Raspberry Pi
DEFAULT_PHOTO_INTERVAL_SEC = 300  # 5 minutos de intervalo entre cada una de las 5 fotos
DEFAULT_PHOTOS_COUNT = 5          # 5 tomas fotográficas por período

def determine_period_by_hour():
    """
    Determina el período de cultivo según la hora local de la Raspberry Pi:
    - Antes de las 11:00: Mañana
    - Entre 11:00 y 14:59: Mediodía
    - A partir de las 15:00: Tarde
    """
    current_hour = datetime.now().hour
    if current_hour < 11:
        return "manana"
    elif current_hour < 15:
        return "medio_dia"
    else:
        return "tarde"

def execute_capture_sequence(
    period=None, 
    crop_type="cebollin", 
    plant_id=1, 
    photos_count=DEFAULT_PHOTOS_COUNT,
    photo_interval_sec=DEFAULT_PHOTO_INTERVAL_SEC
):
    """
    Secuencia autónoma de 5 tomas fotográficas (cenital y lateral) espaciadas por 5 minutos cada una.
    Registra la marca de tiempo exacta de cada toma en metadata.json y guarda directamente en la USB.
    """
    session_start_dt = datetime.now()
    
    print("\n=======================================================")
    print("SIFMA Raspberry Pi 5 - Captura Fotografica Autonoma")
    print(f"Inicio de Sesion: {session_start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuracion: {photos_count} fotos con intervalos de {photo_interval_sec // 60} min ({photo_interval_sec}s)")
    print("=======================================================\n")

    if not period:
        period = determine_period_by_hour()
        
    print(f"1. Periodo seleccionado: {period.upper()}")

    # 1. Crear carpeta del lote en la USB (espera a que la USB esté montada)
    print("2. Verificando unidad de almacenamiento USB...")
    batch_dir = OfflineStorageService.create_batch_directory(period=period, wait_for_usb=True)
    print(f"   Carpeta de destino en USB: {batch_dir}")

    cenital_success = 0
    lateral_success = 0
    photos_metadata_list = []

    # 2. Bucle de las 5 tomas espaciadas por 5 minutos cada una
    for photo_idx in range(1, photos_count + 1):
        if photo_idx > 1 and photo_interval_sec > 0:
            print(f"\n[INTERVALO] Esperando {photo_interval_sec // 60} minutos ({photo_interval_sec}s) antes de la toma #{photo_idx}...")
            time.sleep(photo_interval_sec)

        exact_photo_time = datetime.now()
        print(f"\n---> [TOMA #{photo_idx}/{photos_count}] Hora exacta: {exact_photo_time.strftime('%H:%M:%S')}")

        # Captura Cenital (Cámara 0)
        cenital_path = os.path.join(batch_dir, f"cenital_{photo_idx}.png")
        cen_ok = CameraCaptureService.capture_photo(cenital_path, camera_index=0)
        if cen_ok:
            cenital_success += 1
            print(f"   - Foto Cenital #{photo_idx} guardada.")
        
        time.sleep(2.0)

        # Captura Lateral (Cámara 1)
        lateral_path = os.path.join(batch_dir, f"lateral_{photo_idx}.png")
        lat_ok = CameraCaptureService.capture_photo(lateral_path, camera_index=1)
        if lat_ok:
            lateral_success += 1
            print(f"   - Foto Lateral #{photo_idx} guardada.")

        # Registrar metadatos precisos de la toma para el cruce cronológico
        photos_metadata_list.append({
            "photo_index": photo_idx,
            "timestamp": exact_photo_time.strftime("%Y-%m-%d %H:%M:%S"),
            "exact_time": exact_photo_time.strftime("%H:%M:%S"),
            "cenital_file": f"cenital_{photo_idx}.png",
            "lateral_file": f"lateral_{photo_idx}.png",
            "cenital_ok": cen_ok,
            "lateral_ok": lat_ok
        })

    session_end_dt = datetime.now()
    total_captured = cenital_success + lateral_success

    # 3. Guardar archivo metadata.json completo con el desglose por foto
    print("\n3. Guardando archivo de metadatos con timestamps individuales...")
    OfflineStorageService.save_batch_metadata(
        batch_dir=batch_dir,
        period=period,
        crop_type=crop_type,
        image_files_count=total_captured,
        plant_id=plant_id,
        session_start=session_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        session_end=session_end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        photos_info=photos_metadata_list
    )

    duration_min = round((session_end_dt - session_start_dt).total_seconds() / 60, 1)
    print("\n=======================================================")
    print("Secuencia de captura finalizada con exito.")
    print(f"Duracion total del ciclo: {duration_min} minutos.")
    print(f"Imagenes guardadas: {cenital_success} Cenitales + {lateral_success} Laterales = {total_captured} fotos.")
    print("=======================================================\n")
    return total_captured

def run_continuous_daemon(boot_delay_sec=DEFAULT_BOOT_COOLDOWN_SEC, photo_interval_sec=DEFAULT_PHOTO_INTERVAL_SEC):
    """
    Modo demonio continuo: espera el cooldown inicial y ejecuta capturas
    programadas en los turnos 07:05 (Mañana), 12:05 (Mediodía) y 17:05 (Tarde).
    """
    scheduled_hours = {
        7: "manana",
        12: "medio_dia",
        17: "tarde"
    }
    last_triggered_date_hour = None
    
    print("[MODO DEMONIO] SIFMA Monitoreo Continuo Activo en Raspberry Pi 5.")
    print("Horarios programados: 07:05 (Mañana), 12:05 (Mediodía), 17:05 (Tarde)")
    
    # Cooldown inicial al encender la Raspberry Pi (5 minutos)
    if boot_delay_sec > 0:
        print(f"\n[COOLDOWN INICIAL] Esperando {boot_delay_sec // 60} minutos ({boot_delay_sec}s) para estabilizacion de camaras y sensores...")
        time.sleep(boot_delay_sec)

    # Disparar la primera secuencia del período actual
    execute_capture_sequence(photo_interval_sec=photo_interval_sec)

    while True:
        now = datetime.now()
        current_date_hour = (now.date(), now.hour)
        
        # Disparar si es la hora programada y pasaron al menos 5 minutos
        if now.hour in scheduled_hours and now.minute >= 5:
            if current_date_hour != last_triggered_date_hour:
                period = scheduled_hours[now.hour]
                print(f"\n[PROGRAMADOR] Disparando secuencia programada del periodo: {period.upper()}")
                execute_capture_sequence(period=period, photo_interval_sec=photo_interval_sec)
                last_triggered_date_hour = current_date_hour

        time.sleep(20)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIFMA Raspberry Pi Node - Captura Autonoma")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en modo demonio continuo con programador")
    parser.add_argument("--period", type=str, default=None, help="Forzar periodo especifico (manana, medio_dia, tarde)")
    parser.add_argument("--boot-delay", type=int, default=DEFAULT_BOOT_COOLDOWN_SEC, help="Segundos de espera inicial al encender la Raspberry (defecto: 300s = 5 min)")
    parser.add_argument("--interval", type=int, default=DEFAULT_PHOTO_INTERVAL_SEC, help="Segundos de intervalo entre fotos (defecto: 300s = 5 min)")
    
    args = parser.parse_args()

    if args.daemon:
        run_continuous_daemon(boot_delay_sec=args.boot_delay, photo_interval_sec=args.interval)
    else:
        # En ejecución directa única, aplicar el cooldown inicial si se especificó
        if args.boot_delay > 0:
            print(f"[COOLDOWN] Esperando {args.boot_delay // 60} minutos ({args.boot_delay}s) antes de iniciar la sesion...")
            time.sleep(args.boot_delay)
        execute_capture_sequence(period=args.period, photo_interval_sec=args.interval)
