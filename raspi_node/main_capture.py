import os
import sys
import time
import json
import argparse
import signal
from datetime import datetime, timedelta

# Asegurar importaciones relativas desde la carpeta raspi_node
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
if NODE_DIR not in sys.path:
    sys.path.insert(0, NODE_DIR)

from dependencies import ensure_dependencies
ensure_dependencies()

from services import OfflineStorageService, CameraCaptureService

CONFIG_FILE = os.path.join(NODE_DIR, "config.json")
STATUS_FILE = os.path.join(NODE_DIR, "sifma_daemon_status.json")

def load_node_config():
    """Carga la configuración actual desde config.json con valores por defecto seguros."""
    defaults = {
        "plant_id": 1,
        "crop_type": "cebollin",
        "capture_mode": "interval",           # "interval" (cada X minutos) o "scheduled" (horas fijas)
        "interval_minutes": 60,               # Frecuencia de captura (60 = 1 hora para exhibición)
        "scheduled_times": ["07:05", "12:05", "17:05"],
        "photos_per_session": 3,              # Número de fotos por sesión
        "interval_between_photos_sec": 5,     # Intervalo entre fotos de la misma toma
        "boot_delay_sec": 10,                 # Retardo inicial al encender (10s para exhibición rápida)
        "capture_on_boot": True,              # Tomar fotos inmediatamente al encender
        "cenital_camera_index": 0,
        "lateral_camera_index": 1,
        "server_url": "http://192.168.0.3:5000",
        "safe_shutdown_enabled": False
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                defaults.update(loaded)
        except Exception as e:
            print(f"[CONFIG AVISO] Error al leer config.json ({e}). Usando valores predeterminados.")
    return defaults

def save_daemon_status(status_text="En espera", last_capture_info=None, next_capture_dt=None, is_running=True):
    """Guarda el estado operativo en un archivo JSON para que el Panel de Control Web lo consulte en vivo."""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_data = {
            "status": status_text,
            "is_running": is_running,
            "updated_at": now_str,
            "pid": os.getpid(),
            "next_capture": next_capture_dt.strftime("%Y-%m-%d %H:%M:%S") if next_capture_dt else None,
            "next_capture_human": next_capture_dt.strftime("%H:%M:%S") if next_capture_dt else "N/A"
        }
        if last_capture_info:
            status_data["last_capture"] = last_capture_info
        elif os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f_prev:
                    prev = json.load(f_prev)
                    if "last_capture" in prev:
                        status_data["last_capture"] = prev["last_capture"]
            except Exception:
                pass

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        pass

def determine_period_by_time(dt=None):
    """
    Determina el nombre canónico del período según la hora:
    - 06:00 a 10:59 -> manana
    - 11:00 a 14:59 -> medio_dia
    - 15:00 en adelante -> tarde
    Incluye la hora exacta en el sufijo si son tomas horarias continuas para no sobreescribir lotes.
    """
    if dt is None:
        dt = datetime.now()
    hour = dt.hour
    time_tag = dt.strftime("%H%M")
    
    if hour < 11:
        base = "manana"
    elif hour < 15:
        base = "medio_dia"
    else:
        base = "tarde"
        
    return f"{base}_{time_tag}"

def execute_capture_sequence(
    period=None, 
    crop_type=None, 
    plant_id=None, 
    photos_count=None,
    photo_interval_sec=None,
    cenital_cam=0,
    lateral_cam=1
):
    """
    Secuencia autónoma de tomas fotográficas (cenital y lateral) guardadas en la USB.
    Registra metadatos de alta resolución y actualiza el estado en vivo.
    """
    cfg = load_node_config()
    crop_type = crop_type or cfg.get("crop_type", "cebollin")
    plant_id = plant_id if plant_id is not None else cfg.get("plant_id", 1)
    photos_count = photos_count or cfg.get("photos_per_session", 3)
    photo_interval_sec = photo_interval_sec if photo_interval_sec is not None else cfg.get("interval_between_photos_sec", 5)
    cenital_cam = cenital_cam if cenital_cam is not None else cfg.get("cenital_camera_index", 0)
    lateral_cam = lateral_cam if lateral_cam is not None else cfg.get("lateral_camera_index", 1)

    session_start_dt = datetime.now()
    
    if not period:
        period = determine_period_by_time(session_start_dt)
        
    print("\n=======================================================")
    print("SIFMA Raspberry Pi 5 - Captura Fotografica Autonoma")
    print(f"Inicio de Sesion: {session_start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Periodo: {period.upper()} | Canastilla: #{plant_id} ({crop_type})")
    print(f"Configuracion: {photos_count} fotos | Intervalo: {photo_interval_sec}s")
    print(f"Camaras: Cenital (ID {cenital_cam}) / Lateral (ID {lateral_cam})")
    print("=======================================================\n")

    save_daemon_status(status_text=f"Capturando fotos del lote: {period}...")

    # 1. Crear carpeta del lote en la USB
    print("1. Verificando unidad de almacenamiento USB...")
    batch_dir = OfflineStorageService.create_batch_directory(period=period, wait_for_usb=True)
    print(f"   Carpeta de destino: {batch_dir}")

    cenital_success = 0
    lateral_success = 0
    photos_metadata_list = []

    # 2. Bucle de capturas
    for photo_idx in range(1, photos_count + 1):
        if photo_idx > 1 and photo_interval_sec > 0:
            print(f"\n[INTERVALO] Esperando {photo_interval_sec}s antes de la toma #{photo_idx}...")
            save_daemon_status(status_text=f"Esperando {photo_interval_sec}s para toma #{photo_idx}/{photos_count}...")
            time.sleep(photo_interval_sec)

        exact_photo_time = datetime.now()
        print(f"\n---> [TOMA #{photo_idx}/{photos_count}] Hora exacta: {exact_photo_time.strftime('%H:%M:%S')}")
        save_daemon_status(status_text=f"Disparando foto #{photo_idx}/{photos_count} ({exact_photo_time.strftime('%H:%M:%S')})...")

        # Captura Cenital
        cenital_path = os.path.join(batch_dir, f"cenital_{photo_idx}.png")
        cen_ok = CameraCaptureService.capture_photo(cenital_path, camera_index=cenital_cam)
        if cen_ok:
            cenital_success += 1
            print(f"   - Foto Cenital #{photo_idx} OK.")
        
        time.sleep(1.0)

        # Captura Lateral
        lateral_path = os.path.join(batch_dir, f"lateral_{photo_idx}.png")
        lat_ok = CameraCaptureService.capture_photo(lateral_path, camera_index=lateral_cam)
        if lat_ok:
            lateral_success += 1
            print(f"   - Foto Lateral #{photo_idx} OK.")

        # Registrar metadatos precisos
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

    # 3. Guardar archivo metadata.json completo
    print("\n2. Guardando archivo metadata.json con timestamps...")
    meta_file = OfflineStorageService.save_batch_metadata(
        batch_dir=batch_dir,
        period=period,
        crop_type=crop_type,
        image_files_count=total_captured,
        plant_id=plant_id,
        session_start=session_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        session_end=session_end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        photos_info=photos_metadata_list
    )

    duration_sec = round((session_end_dt - session_start_dt).total_seconds(), 1)
    print("\n=======================================================")
    print("Secuencia de captura finalizada con exito.")
    print(f"Duracion: {duration_sec}s | Fotos: {cenital_success} Cenitales + {lateral_success} Laterales = {total_captured} total.")
    print(f"Lote almacenado en: {batch_dir}")
    print("=======================================================\n")

    last_info = {
        "timestamp": session_end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "period": period,
        "plant_id": plant_id,
        "crop_type": crop_type,
        "photos_count": total_captured,
        "batch_dir": batch_dir,
        "cenital_count": cenital_success,
        "lateral_count": lateral_success
    }
    save_daemon_status(status_text="En espera para el próximo ciclo", last_capture_info=last_info)
    return total_captured

def run_continuous_daemon():
    """
    Demonio autónomo de captura continua para Raspberry Pi 5.
    Lee dinámicamente config.json y admite:
    - Modo Intervalo (por ejemplo: cada 60 minutos / 1 hora para exhibición).
    - Modo Horas Fijas (por ejemplo: 07:05, 12:05, 17:05).
    - Captura inmediata tras el encendido si capture_on_boot es True.
    """
    cfg = load_node_config()
    boot_delay = cfg.get("boot_delay_sec", 10)
    capture_on_boot = cfg.get("capture_on_boot", True)
    
    print("\n=======================================================")
    print("SIFMA DEMONIO AUTONOMO - Raspberry Pi 5")
    print(f"Modo de operacion: {cfg.get('capture_mode', 'interval').upper()}")
    if cfg.get("capture_mode") == "interval":
        print(f"Frecuencia configurada: Cada {cfg.get('interval_minutes', 60)} minutos (1 hora)")
    else:
        print(f"Horarios configurados: {cfg.get('scheduled_times', [])}")
    print(f"Fotos por sesion: {cfg.get('photos_per_session', 3)} tomas")
    print("=======================================================\n")

    # Cooldown inicial al encender la Raspberry Pi
    if boot_delay > 0:
        print(f"[ARRANQUE] Esperando retardo inicial de {boot_delay}s para estabilizacion de hardware...")
        save_daemon_status(status_text=f"Iniciando: esperando retardo de {boot_delay}s...")
        time.sleep(boot_delay)

    # Si está configurado para disparar al encender:
    if capture_on_boot:
        print("\n[ARRANQUE] Ejecutando primera sesion automatica tras encendido...")
        try:
            execute_capture_sequence()
        except Exception as e:
            print(f"[ERROR EN CAPTURA INICIAL]: {e}")

    last_trigger_time = datetime.now()
    last_scheduled_hour = None

    while True:
        try:
            # Recargar configuración fresca en cada iteración
            cfg = load_node_config()
            mode = cfg.get("capture_mode", "interval")
            now = datetime.now()

            if mode == "interval":
                interval_min = max(1, int(cfg.get("interval_minutes", 60)))
                interval_sec = interval_min * 60
                elapsed = (now - last_trigger_time).total_seconds()
                next_trigger = last_trigger_time + timedelta(seconds=interval_sec)
                
                remaining_sec = max(0, int(interval_sec - elapsed))
                rem_min = remaining_sec // 60
                rem_s = remaining_sec % 60
                
                save_daemon_status(
                    status_text=f"Modo Intervalo ({interval_min} min): Próxima toma en {rem_min}m {rem_s}s",
                    next_capture_dt=next_trigger
                )

                if elapsed >= interval_sec:
                    print(f"\n[CRON INTERVALO] Tiempo cumplido ({interval_min} min). Iniciando nueva sesion de captura...")
                    execute_capture_sequence()
                    last_trigger_time = datetime.now()

            elif mode == "scheduled":
                sched_times = cfg.get("scheduled_times", ["07:05", "12:05", "17:05"])
                current_hm = now.strftime("%H:%M")
                
                # Calcular la próxima hora programada
                next_time_str = None
                for t_str in sorted(sched_times):
                    if t_str > current_hm:
                        next_time_str = t_str
                        break
                if not next_time_str and sched_times:
                    next_time_str = sorted(sched_times)[0]
                    
                save_daemon_status(
                    status_text=f"Modo Horas Fijas: Próxima sesión a las {next_time_str or 'N/A'}",
                    next_capture_dt=None
                )

                if current_hm in sched_times and (now.date(), current_hm) != last_scheduled_hour:
                    print(f"\n[CRON HORARIO] Hora programada alcanzada ({current_hm}). Iniciando sesion...")
                    execute_capture_sequence()
                    last_scheduled_hour = (now.date(), current_hm)

            time.sleep(5)

        except KeyboardInterrupt:
            print("\n[DEMONIO] Detenido por el usuario.")
            save_daemon_status(status_text="Detenido", is_running=False)
            break
        except Exception as e:
            print(f"[DEMONIO ERROR]: {e}")
            save_daemon_status(status_text=f"Error en ejecucion: {e}")
            time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIFMA Raspberry Pi Node - Captura Autonoma")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar en modo demonio continuo con programador")
    parser.add_argument("--period", type=str, default=None, help="Forzar periodo especifico (manana, medio_dia, tarde)")
    parser.add_argument("--boot-delay", type=int, default=None, help="Segundos de espera inicial al encender")
    parser.add_argument("--interval", type=int, default=None, help="Segundos de intervalo entre fotos individuales")
    parser.add_argument("--photos", type=int, default=None, help="Cantidad de fotos por sesion")
    parser.add_argument("--crop", type=str, default=None, help="Especie de cultivo")
    parser.add_argument("--plant", type=int, default=None, help="ID de canastilla (1-4)")
    parser.add_argument("--now", action="store_true", help="Disparar captura inmediata y salir")
    
    args = parser.parse_args()

    if args.now:
        execute_capture_sequence(
            period=args.period,
            crop_type=args.crop,
            plant_id=args.plant,
            photos_count=args.photos,
            photo_interval_sec=args.interval
        )
    elif args.daemon:
        run_continuous_daemon()
    else:
        # Ejecución única
        cfg = load_node_config()
        b_delay = args.boot_delay if args.boot_delay is not None else cfg.get("boot_delay_sec", 10)
        if b_delay > 0:
            print(f"[COOLDOWN] Esperando {b_delay}s antes de iniciar la sesion...")
            time.sleep(b_delay)
        execute_capture_sequence(
            period=args.period,
            crop_type=args.crop,
            plant_id=args.plant,
            photos_count=args.photos,
            photo_interval_sec=args.interval
        )

