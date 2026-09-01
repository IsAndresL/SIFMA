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

def execute_capture_sequence(period=None, crop_type="cebollin", plant_id=1, photos_count=5):
    """
    Secuencia autónoma de captura fotográfica cenital y lateral.
    Guarda las imágenes directamente en la memoria USB conectada.
    """
    print("\n=======================================================")
    print("SIFMA Raspberry Pi 5 - Captura Fotografica Autonoma")
    print(f"Fecha y Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=======================================================\n")

    if not period:
        period = determine_period_by_hour()
        
    print(f"1. Periodo seleccionado: {period.upper()}")

    # 1. Crear carpeta del lote en la USB (espera a que la USB este lista)
    print("2. Verificando unidad de almacenamiento USB...")
    batch_dir = OfflineStorageService.create_batch_directory(period=period, wait_for_usb=True)
    print(f"   Carpeta de destino en USB: {batch_dir}")

    # 2. Captura de fotos Cenitales (Camara 0)
    print(f"\n3. Iniciando captura de {photos_count} fotos CENITALES (Camara 0)...")
    cenital_success = 0
    for i in range(1, photos_count + 1):
        out_path = os.path.join(batch_dir, f"cenital_{i}.png")
        if CameraCaptureService.capture_photo(out_path, camera_index=0):
            cenital_success += 1
        time.sleep(1.5)

    # 3. Captura de fotos Laterales (Camara 1)
    print(f"\n4. Iniciando captura de {photos_count} fotos LATERALES (Camara 1)...")
    lateral_success = 0
    for i in range(1, photos_count + 1):
        out_path = os.path.join(batch_dir, f"lateral_{i}.png")
        if CameraCaptureService.capture_photo(out_path, camera_index=1):
            lateral_success += 1
        time.sleep(1.5)

    total_captured = cenital_success + lateral_success

    # 4. Guardar metadatos del lote en la USB
    print("\n5. Guardando archivo de metadatos...")
    OfflineStorageService.save_batch_metadata(
        batch_dir=batch_dir,
        period=period,
        crop_type=crop_type,
        image_files_count=total_captured,
        plant_id=plant_id
    )

    print("\n=======================================================")
    print(f"Captura completada con exito en USB.")
    print(f"Total imagenes guardadas: {total_captured}/{photos_count * 2} ({cenital_success} Cenitales, {lateral_success} Laterales)")
    print("=======================================================\n")
    return total_captured

def run_continuous_daemon():
    """
    Modo demonio continuo: permanece en ejecucion y dispara la captura
    automaticamente en los horarios programados (07:05, 12:05, 17:05).
    """
    scheduled_hours = {
        7: "manana",
        12: "medio_dia",
        17: "tarde"
    }
    last_triggered_date_hour = None
    
    print("[MODO DEMONIO] SIFMA Monitoreo Continuo Activo.")
    print("Horarios programados de captura: 07:05 (Mañana), 12:05 (Mediodía), 17:05 (Tarde)")
    
    # Realizar una captura inmediata al encender para verificar operatividad
    execute_capture_sequence()

    while True:
        now = datetime.now()
        current_date_hour = (now.date(), now.hour)
        
        # Disparar si es la hora programada y pasaron al menos 5 minutos
        if now.hour in scheduled_hours and now.minute >= 5:
            if current_date_hour != last_triggered_date_hour:
                period = scheduled_hours[now.hour]
                print(f"\n[PROGRAMADOR] Disparando captura programada del periodo: {period.upper()}")
                execute_capture_sequence(period=period)
                last_triggered_date_hour = current_date_hour

        time.sleep(20)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIFMA Raspberry Pi Node - Captura Autonoma")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en modo demonio continuo con programador")
    parser.add_argument("--period", type=str, default=None, help="Forzar periodo especifico (manana, medio_dia, tarde)")
    parser.add_argument("--boot-delay", type=int, default=10, help="Segundos de espera inicial al encender la Raspberry")
    
    args = parser.parse_args()

    # Si se inicia al arrancar el sistema, esperar a que los controladores USB y camaras esten listos
    if args.boot_delay > 0:
        print(f"[INICIO] Esperando {args.boot_delay} segundos para inicializacion del hardware del sistema...")
        time.sleep(args.boot_delay)

    if args.daemon:
        run_continuous_daemon()
    else:
        execute_capture_sequence(period=args.period)
