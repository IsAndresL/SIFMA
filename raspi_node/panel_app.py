import os
import sys
import json
import time
import base64
import subprocess
import threading
import platform
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

# Asegurar importaciones relativas
NODE_DIR = os.path.dirname(os.path.abspath(__file__))
if NODE_DIR not in sys.path:
    sys.path.insert(0, NODE_DIR)

from dependencies import ensure_dependencies
ensure_dependencies()

from services.storage_service import OfflineStorageService
from services.camera_service import CameraCaptureService

CONFIG_FILE = os.path.join(NODE_DIR, "config.json")
STATUS_FILE = os.path.join(NODE_DIR, "sifma_daemon_status.json")
PREVIEW_CACHE_DIR = os.path.join(NODE_DIR, ".preview_cache")
os.makedirs(PREVIEW_CACHE_DIR, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(NODE_DIR, "templates"))

camera_lock = threading.Lock()
manual_capture_thread = None

def get_node_config():
    defaults = {
        "plant_id": 1,
        "crop_type": "cebollin",
        "capture_mode": "interval",
        "interval_minutes": 60,
        "scheduled_times": ["07:05", "12:05", "17:05"],
        "photos_per_session": 3,
        "interval_between_photos_sec": 5,
        "boot_delay_sec": 10,
        "capture_on_boot": True,
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
        except Exception:
            pass
    return defaults

def save_node_config(new_cfg):
    current = get_node_config()
    current.update(new_cfg)
    temp_path = CONFIG_FILE + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    os.replace(temp_path, CONFIG_FILE)
    return current

def check_process_running():
    """Comprueba si el demonio main_capture.py esta en ejecucion."""
    try:
        if platform.system() != "Windows":
            res = subprocess.run(["systemctl", "is-active", "sifma-capture"], capture_output=True, text=True)
            if "active" in res.stdout.strip():
                return True
        
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
                pid = st.get("pid")
                if pid:
                    import psutil
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if "python" in proc.name().lower():
                            return True
    except Exception:
        pass
    return False

def get_storage_status():
    """Detecta estado de la memoria USB externa y espacio disponible."""
    target_dir = OfflineStorageService._find_target_storage_directory_once()
    is_usb = "SIFMA_OFFLINE_STORAGE" not in target_dir
    free_gb = 0
    total_gb = 0
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.path.dirname(target_dir) if os.path.exists(target_dir) else target_dir)
        free_gb = round(free / (1024 ** 3), 1)
        total_gb = round(total / (1024 ** 3), 1)
    except Exception:
        pass

    return {
        "target_path": target_dir,
        "is_usb_mounted": is_usb,
        "free_gb": free_gb,
        "total_gb": total_gb,
        "label": "Memoria USB Conectada" if is_usb else "Almacenamiento Local Interno (Sin USB externa)"
    }

@app.route("/")
def index():
    config = get_node_config()
    storage = get_storage_status()
    return render_template("index.html", config=config, storage=storage)

@app.route("/api/status", methods=["GET"])
def api_status():
    config = get_node_config()
    storage = get_storage_status()
    daemon_running = check_process_running()
    
    daemon_status = {
        "status": "En espera",
        "is_running": daemon_running,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_capture": None,
        "next_capture": None
    }
    
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                loaded_st = json.load(f)
                daemon_status.update(loaded_st)
                daemon_status["is_running"] = daemon_running or loaded_st.get("is_running", False)
        except Exception:
            pass

    return jsonify({
        "status": "ok",
        "config": config,
        "storage": storage,
        "daemon": daemon_status,
        "server_time": datetime.now().strftime("%H:%M:%S"),
        "server_date": datetime.now().strftime("%Y-%m-%d")
    })

@app.route("/api/config", methods=["POST"])
def api_save_config():
    try:
        data = request.get_json() or {}
        
        updates = {}
        if "plant_id" in data:
            updates["plant_id"] = int(data["plant_id"])
        if "crop_type" in data:
            updates["crop_type"] = str(data["crop_type"]).strip().lower()
        if "capture_mode" in data and data["capture_mode"] in ["interval", "scheduled"]:
            updates["capture_mode"] = str(data["capture_mode"])
        if "interval_minutes" in data:
            updates["interval_minutes"] = max(1, int(data["interval_minutes"]))
        if "photos_per_session" in data:
            updates["photos_per_session"] = max(1, min(20, int(data["photos_per_session"])))
        if "interval_between_photos_sec" in data:
            updates["interval_between_photos_sec"] = max(1, int(data["interval_between_photos_sec"]))
        if "boot_delay_sec" in data:
            updates["boot_delay_sec"] = max(0, int(data["boot_delay_sec"]))
        if "capture_on_boot" in data:
            updates["capture_on_boot"] = bool(data["capture_on_boot"])
        if "cenital_camera_index" in data:
            updates["cenital_camera_index"] = int(data["cenital_camera_index"])
        if "lateral_camera_index" in data:
            updates["lateral_camera_index"] = int(data["lateral_camera_index"])
        if "scheduled_times" in data and isinstance(data["scheduled_times"], list):
            valid_times = []
            for t in data["scheduled_times"]:
                t_str = str(t).strip()
                if len(t_str) == 5 and ":" in t_str:
                    valid_times.append(t_str)
            updates["scheduled_times"] = sorted(list(set(valid_times)))

        updated = save_node_config(updates)
        return jsonify({"status": "ok", "message": "Configuracion guardada exitosamente", "config": updated})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/preset", methods=["POST"])
def api_apply_preset():
    try:
        data = request.get_json() or {}
        preset_name = data.get("preset")

        if preset_name == "exhibicion":
            # Modo Exhibicion: cada 1 hora (60m), 3 fotos rapidas (5s), cooldown 10s, captura al encender
            preset_cfg = {
                "capture_mode": "interval",
                "interval_minutes": 60,
                "photos_per_session": 3,
                "interval_between_photos_sec": 5,
                "boot_delay_sec": 10,
                "capture_on_boot": True
            }
        elif preset_name == "exhibicion_rapida":
            # Demostracion Rapida: cada 15 min, 2 fotos
            preset_cfg = {
                "capture_mode": "interval",
                "interval_minutes": 15,
                "photos_per_session": 2,
                "interval_between_photos_sec": 3,
                "boot_delay_sec": 5,
                "capture_on_boot": True
            }
        elif preset_name == "agronomico":
            # Modo Agronomico Estandar: 3 jornadas diarias (07:05, 12:05, 17:05), 5 fotos
            preset_cfg = {
                "capture_mode": "scheduled",
                "scheduled_times": ["07:05", "12:05", "17:05"],
                "photos_per_session": 5,
                "interval_between_photos_sec": 300,
                "boot_delay_sec": 300,
                "capture_on_boot": False
            }
        else:
            return jsonify({"status": "error", "message": "Preset no reconocido"}), 400

        updated = save_node_config(preset_cfg)
        return jsonify({"status": "ok", "message": f"Preset '{preset_name}' aplicado correctamente", "config": updated})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/trigger_capture", methods=["POST"])
def api_trigger_capture():
    global manual_capture_thread
    if manual_capture_thread and manual_capture_thread.is_alive():
        return jsonify({"status": "error", "message": "Ya hay una secuencia de captura en ejecucion."}), 409

    def _run_bg():
        try:
            cmd = [sys.executable, os.path.join(NODE_DIR, "main_capture.py"), "--now"]
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"[ERROR DISPARO MANUAL]: {e}")

    manual_capture_thread = threading.Thread(target=_run_bg, daemon=True)
    manual_capture_thread.start()
    return jsonify({"status": "ok", "message": "Secuencia de captura iniciada en segundo plano."})

@app.route("/api/preview_camera/<int:camera_index>", methods=["GET"])
def api_preview_camera(camera_index):
    """Toma una foto de prueba instantanea y la devuelve en base64 para alinear la camara."""
    with camera_lock:
        preview_file = os.path.join(PREVIEW_CACHE_DIR, f"preview_cam_{camera_index}.jpg")
        ok = CameraCaptureService.capture_photo(preview_file, camera_index=camera_index, max_retries=1)
        if ok and os.path.exists(preview_file):
            try:
                with open(preview_file, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                return jsonify({
                    "status": "ok",
                    "camera_index": camera_index,
                    "image_b64": f"data:image/jpeg;base64,{b64}",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({
                "status": "error", 
                "message": f"No se pudo capturar vista previa de la Camara ID {camera_index}. Verifique la conexion del cable o modulo."
            }), 404

@app.route("/api/daemon/<action>", methods=["POST"])
def api_daemon_control(action):
    """Inicia, detiene o reinicia el demonio de captura."""
    if action not in ["start", "stop", "restart"]:
        return jsonify({"status": "error", "message": "Accion no valida"}), 400

    try:
        if platform.system() != "Windows":
            cmd = ["sudo", "systemctl", action, "sifma-capture"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return jsonify({"status": "ok", "message": f"Servicio sifma-capture ejecutado: {action}"})
            else:
                return jsonify({"status": "error", "message": res.stderr or "Error ejecutando systemctl"}), 500
        else:
            return jsonify({"status": "ok", "message": f"Accion {action} simulada en entorno de desarrollo."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("\n=======================================================")
    print("SIFMA PANEL DE CONTROL TACTIL - RASPBERRY PI")
    print("Iniciando servidor web en http://0.0.0.0:8080")
    print("Acceda desde la pantalla tactil o desde un telefono/laptop en la red")
    print("=======================================================\n")
    app.run(host="0.0.0.0", port=8080, debug=False)
