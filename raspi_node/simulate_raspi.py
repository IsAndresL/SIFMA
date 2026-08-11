import os
import shutil
import time
import requests
import json
import random
import argparse
from datetime import datetime

# Paths to generated images in the brain folder
BRAIN_IMAGES = {
    "lettuce_cenital": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\cenital_lettuce_1780150717483.png",
    "lettuce_lateral": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\lateral_lettuce_1780150732801.png",
    
    "tomato_cenital": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\tomato_cenital_1780152886199.png",
    "tomato_lateral": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\tomato_lateral_1780152862927.png",
    
    "ornamental_cenital": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\ornamental_cenital_1780152912569.png",
    "ornamental_lateral": r"C:\Users\AF\.gemini\antigravity-ide\brain\82e2ac01-5461-4d58-be15-b07a3af36fec\ornamental_lateral_1780152934238.png"
}

# Local folder setup
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_images")
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Copy the images to the local node directory
LOCAL_PATHS = {}
for key, src_path in BRAIN_IMAGES.items():
    dest_path = os.path.join(SAMPLE_DIR, f"{key}.png")
    LOCAL_PATHS[key] = dest_path
    
    if os.path.exists(src_path) and not os.path.exists(dest_path):
        shutil.copy(src_path, dest_path)
        print(f"Copiada imagen de prueba '{key}' a {dest_path}")

# Fallback in case they don't exist
for key, dest_path in LOCAL_PATHS.items():
    if not os.path.exists(dest_path):
        # Create small dummy file
        with open(dest_path, "w") as f:
            f.write(f"dummy {key}")

def run_simulation(server_url="http://127.0.0.1:5000", period="mañana", plant_id=1, force_crop=None,
                   force_temp=None, force_hum=None, force_uv=None, force_curr=None):
    """
    Simula la subida de un lote de fotos (5 cenitales y 5 laterales) 
    dependiendo de la especie cultivada activa en el servidor o forzada por CLI.
    """
    print(f"\n--- SIFMA: Iniciando Simulación de Captura ---")
    
    # 1. Obtener configuración del servidor local (sincronización)
    crop_type = "lechuga"  # Default
    try:
        print(f"1. Conectando con servidor local para sincronizar config: {server_url}/api/config")
        config_resp = requests.get(f"{server_url}/api/config", timeout=5)
        if config_resp.status_code == 200:
            config_data = config_resp.json()
            crop_type = config_data.get("selected_crop_type", "lechuga")
            print(f"   Sincronizado. Cultivo activo en la Torre: {crop_type.upper()}")
        else:
            print(f"   Servidor respondió con código: {config_resp.status_code}. Usando lechuga.")
    except Exception as e:
        print(f"   No se pudo sincronizar config ({e}). Usando valor por defecto.")

    # Sobreescribir con el argumento CLI si se proporcionó
    if force_crop:
        crop_type = force_crop
        print(f"   [FORZADO] Forzando tipo de cultivo por argumento CLI: {crop_type.upper()}")

    # Seleccionar las imágenes adecuadas basadas en el cultivo
    # Mapeamos a nuestras llaves locales
    if crop_type == "tomate_cherry":
        prefix = "tomato"
    elif crop_type == "ornamentales":
        prefix = "ornamental"
    else:
        prefix = "lettuce"

    cenital_path = LOCAL_PATHS[f"{prefix}_cenital"]
    lateral_path = LOCAL_PATHS[f"{prefix}_lateral"]
    
    print(f"   -> Usando lote de imágenes: {prefix.upper()} ({os.path.basename(cenital_path)} / {os.path.basename(lateral_path)})")

    # 2. Simular lectura de sensores ambientales (con posibilidad de forzar valores)
    sensor_data = {
        "temperature": float(force_temp) if force_temp is not None else round(random.uniform(20.0, 30.0), 2),
        "humidity": float(force_hum) if force_hum is not None else round(random.uniform(55.0, 75.0), 2),
        "uv_solar": float(force_uv) if force_uv is not None else round(random.uniform(100.0, 800.0), 2),
        "motor_current": float(force_curr) if force_curr is not None else round(random.uniform(0.35, 0.48), 2)
    }
    print(f"2. Sensores leídos (simulados): Temp={sensor_data['temperature']}C, Hum={sensor_data['humidity']}%, UV={sensor_data['uv_solar']} lux, Curr={sensor_data['motor_current']} A")

    # 3. Preparar el lote de imágenes (5 cenitales y 5 laterales)
    files = []
    opened_files = []
    
    print("3. Preparando lote de 10 imágenes secuenciales...")
    for i in range(5):
        f_c = open(cenital_path, 'rb')
        opened_files.append(f_c)
        files.append(('cenital_images', (f'cenital_{i}.png', f_c, 'image/png')))

    for i in range(5):
        f_l = open(lateral_path, 'rb')
        opened_files.append(f_l)
        files.append(('lateral_images', (f'lateral_{i}.png', f_l, 'image/png')))

    # 4. Formar metadatos y enviar
    payload = {
        "plant_id": plant_id,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "sensor_data": json.dumps(sensor_data)
    }

    try:
        upload_url = f"{server_url}/api/upload"
        print(f"4. Enviando lote al PC Local ({upload_url})...")
        start_time = time.time()
        
        response = requests.post(upload_url, data=payload, files=files, timeout=30)
        
        elapsed = time.time() - start_time
        print(f"   Transmisión completada en {elapsed:.2f} segundos.")
        
        if response.status_code == 200:
            print("5. ¡ÉXITO! El PC local recibió y procesó las imágenes.")
            print("Respuesta del servidor:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"5. ERROR en servidor. Código de estado: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"5. ERROR de conexión al enviar fotos: {e}")
    finally:
        # Cerrar los file handles abiertos
        for f in opened_files:
            f.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de Raspberry Pi SIFMA")
    parser.add_argument("--crop", "-c", choices=["lechuga", "tomate_cherry", "ornamentales"], help="Forzar tipo de cultivo a simular")
    parser.add_argument("--period", "-p", default="mañana", choices=["mañana", "mediodía", "tarde"], help="Periodo del día a simular")
    parser.add_argument("--temp", "-t", type=float, help="Forzar temperatura ambiente en Celsius")
    parser.add_argument("--hum", type=float, help="Forzar humedad relativa (porcentaje)")
    parser.add_argument("--uv", type=float, help="Forzar radiación solar UV en lux")
    parser.add_argument("--curr", type=float, help="Forzar corriente de motor en A")
    args = parser.parse_args()
    
    run_simulation(period=args.period, force_crop=args.crop,
                   force_temp=args.temp, force_hum=args.hum, force_uv=args.uv, force_curr=args.curr)
