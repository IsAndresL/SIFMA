import os
import sys
import time
import json
import shutil
import argparse
import requests
import subprocess
from datetime import datetime, timedelta

# Intentar importar picamera2 (estará disponible en la Raspberry Pi 5 con OS Bookworm)
HAS_PICAMERA2 = False
try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except (ImportError, OSError):
    pass

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp_captures")

def load_config():
    """Carga la configuración local de config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al leer config.json: {e}. Usando valores por defecto.")
    
    return {
        "server_url": "http://127.0.0.1:5000",
        "plant_id": 1,
        "scheduled_times": ["07:05", "12:05", "17:05"],
        "photos_per_period": 5,
        "capture_interval_sec": 2,
        "safe_shutdown_enabled": False
    }

def save_config(config):
    """Guarda la configuración en config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print("Configuración guardada en archivo local.")
    except Exception as e:
        print(f"Error al guardar config.json: {e}")

def sync_config_with_server(config):
    """Sincroniza la configuración haciendo una petición GET al servidor local."""
    server_url = config.get("server_url", "http://127.0.0.1:5000")
    try:
        url = f"{server_url}/api/config"
        print(f"Sincronizando configuración con: {url}...")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            server_config = response.json()
            # Guardamos la URL local para evitar que el servidor la sobreescriba con 127.0.0.1
            local_url = config.get("server_url")
            config.update(server_config)
            if local_url:
                config["server_url"] = local_url
                
            save_config(config)
            print("Sincronización de configuración exitosa.")
        else:
            print(f"Servidor respondió con código {response.status_code}. Usando config local.")
    except Exception as e:
        print(f"No se pudo conectar con el servidor para sincronizar ({e}). Se usará config local.")
    return config

def determine_current_period(scheduled_times):
    """Determina el periodo de captura actual en base a la hora."""
    # Obtenemos la hora actual
    now = datetime.now()
    # Mapeamos los horarios a nombres de periodos comunes
    # Si hay 3 periodos: el primero suele ser mañana, segundo mediodía, tercero tarde
    # Formateamos los programados a timedelta
    times = []
    for t_str in scheduled_times:
        try:
            h, m = map(int, t_str.split(':'))
            times.append(timedelta(hours=h, minutes=m))
        except:
            pass
    
    if not times:
        return "mañana" # Default

    # Ordenamos tiempos
    times.sort()
    now_time = timedelta(hours=now.hour, minutes=now.minute)
    
    # Determinar qué periodo es en base al índice más cercano
    # Si estamos antes del segundo periodo, es "mañana", antes del tercero es "mediodía", si no "tarde"
    if len(times) >= 3:
        if now_time <= times[0] + timedelta(minutes=30):
            return "mañana"
        elif now_time <= times[1] + timedelta(minutes=30):
            return "mediodía"
        else:
            return "tarde"
    
    return "mañana"

def wait_for_scheduled_time(scheduled_times):
    """
    Calcula si hay un horario programado cercano en el futuro.
    Si está en un rango de 15 minutos, duerme hasta ese momento exacto.
    """
    now = datetime.now()
    now_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    
    closest_diff_seconds = None
    target_time_str = None
    
    for t_str in scheduled_times:
        try:
            h, m = map(int, t_str.split(':'))
            scheduled_delta = timedelta(hours=h, minutes=m)
            
            # Calculamos la diferencia
            diff = (scheduled_delta - now_time).total_seconds()
            
            # Buscamos la hora programada futura más cercana (diferencia positiva y menor a 15 minutos)
            if 0 <= diff <= 900: # 900 seg = 15 min
                if closest_diff_seconds is None or diff < closest_diff_seconds:
                    closest_diff_seconds = diff
                    target_time_str = t_str
        except Exception as e:
            print(f"Error procesando horario '{t_str}': {e}")
            
    if closest_diff_seconds is not None:
        print(f"Horario de captura detectado: {target_time_str} (en {closest_diff_seconds:.1f} segundos).")
        print("El nodo entrará en modo de espera (sleep) para alinearse exactamente...")
        # Dormimos los segundos necesarios
        time.sleep(closest_diff_seconds)
        print("¡Es hora del muestreo programado! Despertando...")
    else:
        print("No se detectaron capturas programadas en los próximos 15 minutos.")
        print("Procediendo a captura inmediata debido al arranque manual / test.")

def capture_sequential_real(photos_per_period, interval_sec):
    """
    Captura imágenes reales de forma secuencial de los puertos MIPI Flex 0 y Flex 1.
    Primero inicializa Flex 0, toma las fotos y lo libera. 
    Luego inicializa Flex 1, toma las fotos y lo libera.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 1. Cámara Cenital (MIPI Flex 0)
    print("\n[CENITAL] Inicializando cámara en puerto 0...")
    try:
        # En picamera2 se puede seleccionar la cámara pasando el índice en el constructor
        # Si se usa RPi 5 con picamera2, Picamera2(0) selecciona la primera cámara detectada
        pic0 = Picamera2(0)
        pic0.start()
        
        # Esperar a que la cámara ajuste la exposición automáticamente
        time.sleep(1.5)
        
        for i in range(photos_per_period):
            filename = f"cenital_{i}.png"
            path = os.path.join(TEMP_DIR, filename)
            pic0.capture_file(path)
            print(f"   [CENITAL] Foto {i+1}/{photos_per_period} guardada en {path}")
            if i < photos_per_period - 1:
                time.sleep(interval_sec)
                
        pic0.stop()
        pic0.close()
        print("[CENITAL] Cámara 0 liberada con éxito.")
        
    except Exception as e:
        print(f"[CENITAL] ERROR al capturar con Cámara 0: {e}")
        # Intentar crear imágenes ficticias para que no falle todo el proceso
        create_fallback_images("cenital", photos_per_period)
        
    # Espera corta para asegurar la liberación completa de recursos y del bus CSI
    time.sleep(1.5)
    
    # 2. Cámara Lateral (MIPI Flex 1)
    print("\n[LATERAL] Inicializando cámara en puerto 1...")
    try:
        pic1 = Picamera2(1)
        pic1.start()
        
        # Esperar exposición
        time.sleep(1.5)
        
        for i in range(photos_per_period):
            filename = f"lateral_{i}.png"
            path = os.path.join(TEMP_DIR, filename)
            pic1.capture_file(path)
            print(f"   [LATERAL] Foto {i+1}/{photos_per_period} guardada en {path}")
            if i < photos_per_period - 1:
                time.sleep(interval_sec)
                
        pic1.stop()
        pic1.close()
        print("[LATERAL] Cámara 1 liberada con éxito.")
        
    except Exception as e:
        print(f"[LATERAL] ERROR al capturar con Cámara 1: {e}")
        create_fallback_images("lateral", photos_per_period)

def create_fallback_images(camera_type, count):
    """Copia imágenes de muestra locales en caso de que falle la cámara real."""
    print(f"   [FALLBACK] Copiando imágenes simuladas para {camera_type}...")
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_images")
    src = os.path.join(sample_dir, f"{camera_type}.png")
    
    if os.path.exists(src):
        for i in range(count):
            dest = os.path.join(TEMP_DIR, f"{camera_type}_{i}.png")
            shutil.copy(src, dest)
    else:
        # Si no hay muestra, crea archivos dummy de texto para no romper la petición
        for i in range(count):
            dest = os.path.join(TEMP_DIR, f"{camera_type}_{i}.png")
            with open(dest, "w") as f:
                f.write(f"dummy content {camera_type}")

def capture_simulated(photos_per_period):
    """Simula la captura copiando fotos de muestra de raspi_node/sample_images/."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    print("\n[SIMULACIÓN] Iniciando captura virtual...")
    create_fallback_images("cenital", photos_per_period)
    create_fallback_images("lateral", photos_per_period)
    print("[SIMULACIÓN] Captura virtual completada.")

def send_data_to_server(config, period):
    """Prepara y envía los archivos y metadatos al PC Local por HTTP POST."""
    server_url = config.get("server_url", "http://127.0.0.1:5000")
    plant_id = config.get("plant_id", 1)
    photos_per_period = config.get("photos_per_period", 5)
    upload_url = f"{server_url}/api/upload"
    
    # Simulación de lectura de sensores ambientales (para mantener estructura Fase 2)
    # Mandamos datos nulos o simulados realistas
    sensor_data = {
        "temperature": 25.0,
        "humidity": 60.0,
        "uv_solar": 300.0,
        "motor_current": 0.40
    }
    
    payload = {
        "plant_id": plant_id,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "sensor_data": json.dumps(sensor_data)
    }
    
    # Agrupamos archivos
    files = []
    opened_files = []
    
    try:
        # Buscar cenitales
        for i in range(photos_per_period):
            filename = f"cenital_{i}.png"
            path = os.path.join(TEMP_DIR, filename)
            if os.path.exists(path):
                f = open(path, 'rb')
                opened_files.append(f)
                files.append(('cenital_images', (filename, f, 'image/png')))
                
        # Buscar laterales
        for i in range(photos_per_period):
            filename = f"lateral_{i}.png"
            path = os.path.join(TEMP_DIR, filename)
            if os.path.exists(path):
                f = open(path, 'rb')
                opened_files.append(f)
                files.append(('lateral_images', (filename, f, 'image/png')))

        print(f"\nTransmitiendo lote de {len(files)} imágenes al servidor: {upload_url}...")
        response = requests.post(upload_url, data=payload, files=files, timeout=40)
        
        if response.status_code == 200:
            print("¡Subida completada con éxito!")
            print("Respuesta de procesamiento del PC Local:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error del servidor al subir. Código de estado: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"Error de red al conectar al PC Local: {e}")
        return False
    finally:
        # Asegurarse de cerrar todos los archivos
        for f in opened_files:
            f.close()

def clean_temp_files():
    """Elimina las imágenes temporales creadas para liberar espacio en disco."""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            print("Carpeta temporal de capturas eliminada con éxito.")
        except Exception as e:
            print(f"No se pudo eliminar la carpeta temporal: {e}")

def main():
    parser = argparse.ArgumentParser(description="Agente de Captura SIFMA para Raspberry Pi 5")
    parser.add_argument("--test", action="store_true", help="Salta la espera horaria y ejecuta de inmediato")
    args = parser.parse_args()
    
    print("==================================================")
    print(f"Agente de Captura SIFMA iniciado el {datetime.now()}")
    print(f"Entorno: {'Raspberry Pi 5 (picamera2)' if HAS_PICAMERA2 else 'Simulación (PC/Windows)'}")
    print("==================================================")

    # 1. Cargar y sincronizar configuración
    config = load_config()
    config = sync_config_with_server(config)
    
    # 2. Espera de tiempo programado (si no es modo test)
    if not args.test:
        wait_for_scheduled_time(config.get("scheduled_times", []))
    else:
        print("[TEST] Bypasseando el planificador de tiempo. Captura inmediata.")

    # 3. Determinar periodo actual de muestreo
    period = determine_current_period(config.get("scheduled_times", []))
    print(f"Periodo de muestreo determinado: {period.upper()}")

    # 4. Captura secuencial
    photos_count = config.get("photos_per_period", 5)
    interval = config.get("capture_interval_sec", 2)
    
    if HAS_PICAMERA2:
        capture_sequential_real(photos_count, interval)
    else:
        capture_simulated(photos_count)

    # 5. Enviar fotos y metadatos
    success = send_data_to_server(config, period)
    
    # 6. Limpieza de disco
    clean_temp_files()
    
    # 7. Apagado seguro (si está habilitado y es el flujo autónomo - no en modo test manual)
    if success and config.get("safe_shutdown_enabled", False) and not args.test:
        print("\n[APAGADO] Lote enviado exitosamente y safe_shutdown habilitado.")
        print("Apagando la Raspberry Pi de forma segura en 10 segundos...")
        time.sleep(10)
        # Comando Linux para apagado seguro
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    else:
        print("\nAgente finalizó sus tareas. Permaneciendo encendido (safe_shutdown inactivo o modo test).")

if __name__ == "__main__":
    main()
