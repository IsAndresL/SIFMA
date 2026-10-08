import os
import sys
import json
import time
import subprocess
import threading
import platform
from datetime import datetime

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

import tkinter as tk
from tkinter import ttk, messagebox
try:
    from PIL import Image, ImageTk
    HAS_PIL_TK = True
except ImportError:
    HAS_PIL_TK = False

def load_config():
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
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults

def save_config(cfg):
    try:
        temp = CONFIG_FILE + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(temp, CONFIG_FILE)
    except Exception as e:
        print(f"[ERROR CONFIG]: {e}")

class SifmaLiteTouchApp(tk.Tk):
    """
    Panel de Control Táctil Ultraligero para Raspberry Pi (Consumo < 15MB RAM).
    100% interactivo mediante toques/clics. Sin navegador ni servidores pesados.
    """
    def __init__(self):
        super().__init__()
        self.title("SIFMA - Panel Táctil Lite")
        self.geometry("860x560")
        self.minsize(780, 500)
        self.configure(bg="#0a0f18")

        self.cfg = load_config()
        self.default_hours = [
            "06:00", "07:05", "08:00", "09:00", "10:00",
            "11:00", "12:05", "13:00", "14:00", "15:00",
            "16:00", "17:05", "18:00", "19:00", "20:00"
        ]

        self.setup_ui()
        self.update_ui_from_config()
        self.refresh_timer()

    def setup_ui(self):
        # 1. Barra Superior (Header)
        header_frame = tk.Frame(self, bg="#111a2e", padx=12, pady=8, highlightbackground="#1e2d4d", highlightthickness=1)
        header_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        # Título y Versión
        title_box = tk.Frame(header_frame, bg="#111a2e")
        title_box.pack(side=tk.LEFT)
        tk.Label(title_box, text="SIFMA LITE", font=("Segoe UI", 14, "bold"), fg="#10b981", bg="#111a2e").pack(anchor="w")
        tk.Label(title_box, text="Centro Táctil Raspberry Pi (Bajo Consumo)", font=("Segoe UI", 8), fg="#94a3b8", bg="#111a2e").pack(anchor="w")

        # Badges de Estado
        status_box = tk.Frame(header_frame, bg="#111a2e")
        status_box.pack(side=tk.RIGHT)

        self.lbl_usb = tk.Label(status_box, text="USB: Verificando...", font=("Segoe UI", 9, "bold"), fg="#60a5fa", bg="#0f172a", padx=8, pady=4, relief="ridge")
        self.lbl_usb.pack(side=tk.LEFT, padx=4)

        self.lbl_daemon = tk.Label(status_box, text="Demonio: Activo", font=("Segoe UI", 9, "bold"), fg="#34d399", bg="#0f172a", padx=8, pady=4, relief="ridge")
        self.lbl_daemon.pack(side=tk.LEFT, padx=4)

        self.lbl_clock = tk.Label(status_box, text="--:--:--", font=("Courier", 11, "bold"), fg="#f8fafc", bg="#111a2e", padx=6)
        self.lbl_clock.pack(side=tk.LEFT, padx=4)

        # 2. Contenedor Principal (2 Columnas)
        main_box = tk.Frame(self, bg="#0a0f18")
        main_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Columna Izquierda: Presets y Temporizador
        left_col = tk.Frame(main_box, bg="#111a2e", padx=10, pady=10, highlightbackground="#1e2d4d", highlightthickness=1)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        # Presets Rápidos
        tk.Label(left_col, text="PRESETS RAPIDOS A 1 CLIC", font=("Segoe UI", 9, "bold"), fg="#34d399", bg="#111a2e").pack(anchor="w", pady=(0, 4))
        preset_box = tk.Frame(left_col, bg="#111a2e")
        preset_box.pack(fill=tk.X, pady=(0, 8))

        btn_pre1 = tk.Button(preset_box, text="Modo Exhibicion\n(Cada 1h / 3 fotos)", font=("Segoe UI", 8, "bold"), bg="#064e3b", fg="#ffffff", activebackground="#059669", activeforeground="#ffffff", relief="flat", padx=6, pady=6, command=lambda: self.apply_preset("exhibicion"))
        btn_pre1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        btn_pre2 = tk.Button(preset_box, text="Demo Rapida\n(Cada 15m / 2 fotos)", font=("Segoe UI", 8, "bold"), bg="#1e3a8a", fg="#ffffff", activebackground="#2563eb", activeforeground="#ffffff", relief="flat", padx=6, pady=6, command=lambda: self.apply_preset("exhibicion_rapida"))
        btn_pre2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        btn_pre3 = tk.Button(preset_box, text="Agronomico\n(3 turnos / 5 fotos)", font=("Segoe UI", 8, "bold"), bg="#374151", fg="#ffffff", activebackground="#4b5563", activeforeground="#ffffff", relief="flat", padx=6, pady=6, command=lambda: self.apply_preset("agronomico"))
        btn_pre3.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Modo de Captura (Intervalo vs Horas)
        tk.Label(left_col, text="TIPO DE PROGRAMADOR", font=("Segoe UI", 9, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(4, 2))
        mode_box = tk.Frame(left_col, bg="#111a2e")
        mode_box.pack(fill=tk.X, pady=(0, 6))

        self.btn_mode_interval = tk.Button(mode_box, text="Intervalo Periodico", font=("Segoe UI", 9, "bold"), relief="flat", pady=6, command=lambda: self.set_mode("interval"))
        self.btn_mode_interval.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_mode_sched = tk.Button(mode_box, text="Horas Programadas", font=("Segoe UI", 9, "bold"), relief="flat", pady=6, command=lambda: self.set_mode("scheduled"))
        self.btn_mode_sched.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Frecuencia de Intervalo (Minutos)
        self.interval_frame = tk.Frame(left_col, bg="#111a2e")
        self.interval_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(self.interval_frame, text="FRECUENCIA DE CAPTURA", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w")
        
        freq_chips = tk.Frame(self.interval_frame, bg="#111a2e")
        freq_chips.pack(fill=tk.X, pady=2)
        for m in [5, 15, 30, 60, 120, 240]:
            lbl_text = f"{m}m" if m < 60 else f"{m//60}h"
            btn = tk.Button(freq_chips, text=lbl_text, font=("Segoe UI", 8, "bold"), bg="#0f172a", fg="#f8fafc", relief="flat", width=4, pady=4, command=lambda val=m: self.set_interval(val))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        stepper_box = tk.Frame(self.interval_frame, bg="#111a2e")
        stepper_box.pack(fill=tk.X, pady=2)
        tk.Button(stepper_box, text="-15m", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#fff", relief="flat", padx=8, pady=4, command=lambda: self.step_interval(-15)).pack(side=tk.LEFT)
        self.lbl_interval_val = tk.Label(stepper_box, text="60 min (1.0h)", font=("Courier", 11, "bold"), fg="#34d399", bg="#0f172a", relief="ridge", pady=4)
        self.lbl_interval_val.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        tk.Button(stepper_box, text="+15m", font=("Segoe UI", 9, "bold"), bg="#1e293b", fg="#fff", relief="flat", padx=8, pady=4, command=lambda: self.step_interval(15)).pack(side=tk.LEFT)

        # Horas Programadas (Grid)
        self.sched_frame = tk.Frame(left_col, bg="#111a2e")
        tk.Label(self.sched_frame, text="HORAS ACTIVAS (Clic para activar/desactivar)", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w")
        self.hours_buttons = {}
        grid_h = tk.Frame(self.sched_frame, bg="#111a2e")
        grid_h.pack(fill=tk.X, pady=2)
        for idx, h in enumerate(self.default_hours):
            r, c = idx // 5, idx % 5
            btn = tk.Button(grid_h, text=h, font=("Courier", 8, "bold"), bg="#0f172a", fg="#94a3b8", relief="flat", padx=2, pady=4, command=lambda val=h: self.toggle_hour(val))
            btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
            self.hours_buttons[h] = btn
        for i in range(5):
            grid_h.columnconfigure(i, weight=1)

        # Rango de Fotos por Sesión
        tk.Label(left_col, text="CANTIDAD DE FOTOS POR SESION", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(6, 2))
        photos_chips = tk.Frame(left_col, bg="#111a2e")
        photos_chips.pack(fill=tk.X)
        for cnt in [1, 2, 3, 5, 8, 10]:
            btn = tk.Button(photos_chips, text=f"{cnt}", font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#f8fafc", relief="flat", width=3, pady=4, command=lambda val=cnt: self.set_photos_count(val))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        # Espaciado entre Fotos
        tk.Label(left_col, text="ESPACIADO ENTRE TOMAS", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(6, 2))
        spacing_chips = tk.Frame(left_col, bg="#111a2e")
        spacing_chips.pack(fill=tk.X)
        for sec, lbl in [(3, "3s"), (5, "5s"), (10, "10s"), (30, "30s"), (60, "1m"), (300, "5m")]:
            btn = tk.Button(spacing_chips, text=lbl, font=("Segoe UI", 8, "bold"), bg="#0f172a", fg="#f8fafc", relief="flat", pady=4, command=lambda val=sec: self.set_spacing(val))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        # Columna Derecha: Acciones, Canastilla, Calibración y Estado
        right_col = tk.Frame(main_box, bg="#111a2e", padx=10, pady=10, highlightbackground="#1e2d4d", highlightthickness=1)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        # Botón Gigante de Disparo Inmediato
        btn_fire = tk.Button(right_col, text="DISPARAR CAPTURA AHORA", font=("Segoe UI", 11, "bold"), bg="#059669", fg="#ffffff", activebackground="#047857", activeforeground="#ffffff", relief="flat", pady=12, command=self.trigger_now)
        btn_fire.pack(fill=tk.X, pady=(0, 8))

        # Calibración de Cámaras (Prueba de Enfoque y Encuadre)
        tk.Label(right_col, text="CALIBRACION DE CAMARAS EN VIVO", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#111a2e").pack(anchor="w", pady=(0, 2))
        cam_box = tk.Frame(right_col, bg="#111a2e")
        cam_box.pack(fill=tk.X, pady=(0, 8))

        btn_cam0 = tk.Button(cam_box, text="Probar Cenital (ID 0)", font=("Segoe UI", 8, "bold"), bg="#1e293b", fg="#f8fafc", activebackground="#334155", relief="flat", pady=6, command=lambda: self.preview_camera(0))
        btn_cam0.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        btn_cam1 = tk.Button(cam_box, text="Probar Lateral (ID 1)", font=("Segoe UI", 8, "bold"), bg="#1e293b", fg="#f8fafc", activebackground="#334155", relief="flat", pady=6, command=lambda: self.preview_camera(1))
        btn_cam1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Canastilla / Planta
        tk.Label(right_col, text="CANASTILLA / PLANTA ASIGNADA", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(0, 2))
        plant_box = tk.Frame(right_col, bg="#111a2e")
        plant_box.pack(fill=tk.X, pady=(0, 8))
        self.plant_buttons = {}
        for pid in [1, 2, 3, 4]:
            btn = tk.Button(plant_box, text=f"Planta #{pid}", font=("Segoe UI", 8, "bold"), relief="flat", pady=5, command=lambda val=pid: self.set_plant(val))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
            self.plant_buttons[pid] = btn

        # Captura al encender
        tk.Label(right_col, text="CAPTURA AL ENCENDER", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(0, 2))
        boot_box = tk.Frame(right_col, bg="#111a2e")
        boot_box.pack(fill=tk.X, pady=(0, 8))
        self.btn_boot_on = tk.Button(boot_box, text="Activada (Exhibicion)", font=("Segoe UI", 8, "bold"), relief="flat", pady=4, command=lambda: self.set_boot_capture(True))
        self.btn_boot_on.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        self.btn_boot_off = tk.Button(boot_box, text="Desactivada", font=("Segoe UI", 8, "bold"), relief="flat", pady=4, command=lambda: self.set_boot_capture(False))
        self.btn_boot_off.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

        # Panel de Estado en Vivo (Log Feed)
        tk.Label(right_col, text="ESTADO DEL DEMONIO Y ALMACENAMIENTO", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#111a2e").pack(anchor="w", pady=(0, 2))
        self.status_text_box = tk.Label(right_col, text="Iniciando...", font=("Courier", 8), fg="#cbd5e1", bg="#0a0f18", justify="left", anchor="w", padx=8, pady=6, relief="ridge")
        self.status_text_box.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Control del Servicio Demonio
        daemon_ctrl_box = tk.Frame(right_col, bg="#111a2e")
        daemon_ctrl_box.pack(fill=tk.X)
        tk.Button(daemon_ctrl_box, text="Iniciar Demonio", font=("Segoe UI", 8, "bold"), bg="#064e3b", fg="#fff", relief="flat", pady=5, command=lambda: self.control_daemon("start")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(daemon_ctrl_box, text="Detener", font=("Segoe UI", 8, "bold"), bg="#7f1d1d", fg="#fff", relief="flat", pady=5, command=lambda: self.control_daemon("stop")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)
        tk.Button(daemon_ctrl_box, text="Reiniciar", font=("Segoe UI", 8, "bold"), bg="#1e3a8a", fg="#fff", relief="flat", pady=5, command=lambda: self.control_daemon("restart")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

    def update_ui_from_config(self):
        is_interval = self.cfg.get("capture_mode", "interval") == "interval"
        self.btn_mode_interval.configure(bg="#10b981" if is_interval else "#0f172a", fg="#000" if is_interval else "#fff")
        self.btn_mode_sched.configure(bg="#10b981" if not is_interval else "#0f172a", fg="#000" if not is_interval else "#fff")

        if is_interval:
            self.sched_frame.pack_forget()
            self.interval_frame.pack(fill=tk.X, pady=(0, 6))
        else:
            self.interval_frame.pack_forget()
            self.sched_frame.pack(fill=tk.X, pady=(0, 6))

        m = self.cfg.get("interval_minutes", 60)
        self.lbl_interval_val.configure(text=f"{m} min ({(m/60):.1f}h)")

        # Horas programadas
        sched = self.cfg.get("scheduled_times", ["07:05", "12:05", "17:05"])
        for h, btn in self.hours_buttons.items():
            active = h in sched
            btn.configure(bg="#059669" if active else "#0f172a", fg="#ffffff" if active else "#94a3b8")

        # Canastilla
        current_pid = self.cfg.get("plant_id", 1)
        for pid, btn in self.plant_buttons.items():
            btn.configure(bg="#10b981" if pid == current_pid else "#0f172a", fg="#000" if pid == current_pid else "#fff")

        # Boot
        boot_on = self.cfg.get("capture_on_boot", True)
        self.btn_boot_on.configure(bg="#10b981" if boot_on else "#0f172a", fg="#000" if boot_on else "#fff")
        self.btn_boot_off.configure(bg="#10b981" if not boot_on else "#0f172a", fg="#000" if not boot_on else "#fff")

    def set_mode(self, mode):
        self.cfg["capture_mode"] = mode
        save_config(self.cfg)
        self.update_ui_from_config()

    def set_interval(self, minutes):
        self.cfg["interval_minutes"] = max(1, minutes)
        save_config(self.cfg)
        self.update_ui_from_config()

    def step_interval(self, delta):
        cur = self.cfg.get("interval_minutes", 60)
        self.set_interval(cur + delta)

    def set_photos_count(self, count):
        self.cfg["photos_per_session"] = max(1, min(20, count))
        save_config(self.cfg)
        self.update_ui_from_config()

    def set_spacing(self, sec):
        self.cfg["interval_between_photos_sec"] = max(1, sec)
        save_config(self.cfg)
        self.update_ui_from_config()

    def set_plant(self, pid):
        self.cfg["plant_id"] = pid
        save_config(self.cfg)
        self.update_ui_from_config()

    def set_boot_capture(self, enable):
        self.cfg["capture_on_boot"] = enable
        save_config(self.cfg)
        self.update_ui_from_config()

    def toggle_hour(self, hour):
        sched = list(self.cfg.get("scheduled_times", ["07:05", "12:05", "17:05"]))
        if hour in sched:
            sched.remove(hour)
        else:
            sched.append(hour)
        self.cfg["scheduled_times"] = sorted(sched)
        save_config(self.cfg)
        self.update_ui_from_config()

    def apply_preset(self, name):
        if name == "exhibicion":
            self.cfg.update({
                "capture_mode": "interval",
                "interval_minutes": 60,
                "photos_per_session": 3,
                "interval_between_photos_sec": 5,
                "boot_delay_sec": 10,
                "capture_on_boot": True
            })
        elif name == "exhibicion_rapida":
            self.cfg.update({
                "capture_mode": "interval",
                "interval_minutes": 15,
                "photos_per_session": 2,
                "interval_between_photos_sec": 3,
                "boot_delay_sec": 5,
                "capture_on_boot": True
            })
        elif name == "agronomico":
            self.cfg.update({
                "capture_mode": "scheduled",
                "scheduled_times": ["07:05", "12:05", "17:05"],
                "photos_per_session": 5,
                "interval_between_photos_sec": 300,
                "boot_delay_sec": 300,
                "capture_on_boot": False
            })
        save_config(self.cfg)
        self.update_ui_from_config()

    def trigger_now(self):
        def _run():
            try:
                cmd = [sys.executable, os.path.join(NODE_DIR, "main_capture.py"), "--now"]
                subprocess.run(cmd, check=True)
            except Exception as e:
                print(f"[ERROR DISPARO]: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def preview_camera(self, cam_idx):
        win = tk.Toplevel(self)
        win.title(f"Calibración Cámara ID {cam_idx}")
        win.geometry("520x420")
        win.configure(bg="#0f172a")

        lbl_loading = tk.Label(win, text="Capturando fotograma de calibración...", font=("Segoe UI", 10), fg="#38bdf8", bg="#0f172a")
        lbl_loading.pack(pady=20)

        img_label = tk.Label(win, bg="#000")
        img_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def _capture_frame():
            preview_file = os.path.join(PREVIEW_CACHE_DIR, f"preview_cam_{cam_idx}.jpg")
            ok = CameraCaptureService.capture_photo(preview_file, camera_index=cam_idx, max_retries=1)
            if ok and os.path.exists(preview_file) and HAS_PIL_TK:
                try:
                    pil_img = Image.open(preview_file)
                    pil_img.thumbnail((480, 320))
                    tk_img = ImageTk.PhotoImage(pil_img)
                    img_label.img_ref = tk_img
                    img_label.configure(image=tk_img)
                    lbl_loading.configure(text=f"Frame capturado ({datetime.now().strftime('%H:%M:%S')})", fg="#34d399")
                except Exception as err:
                    lbl_loading.configure(text=f"Error cargando imagen: {err}", fg="#ef4444")
            else:
                lbl_loading.configure(text=f"No se detectó cámara activa en ID {cam_idx}", fg="#ef4444")

        threading.Thread(target=_capture_frame, daemon=True).start()

    def control_daemon(self, action):
        if platform.system() != "Windows":
            try:
                subprocess.run(["sudo", "systemctl", action, "sifma-capture"], check=False)
            except Exception:
                pass

    def refresh_timer(self):
        # 1. Reloj
        self.lbl_clock.configure(text=datetime.now().strftime("%H:%M:%S"))

        # 2. Estado de Demonio y Almacenamiento
        try:
            target_dir = OfflineStorageService._find_target_storage_directory_once()
            is_usb = "SIFMA_OFFLINE_STORAGE" not in target_dir
            if is_usb:
                self.lbl_usb.configure(text="USB: Conectada", fg="#60a5fa")
            else:
                self.lbl_usb.configure(text="Almacenamiento Local", fg="#f59e0b")

            status_text = "En espera..."
            next_cap = "--"
            last_cap_str = "Ninguno"
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    status_text = st.get("status", "En espera")
                    next_cap = st.get("next_capture_human", "--")
                    if "last_capture" in st and st["last_capture"]:
                        last_cap_str = f"{st['last_capture'].get('timestamp', '')} ({st['last_capture'].get('period', '')})"

            self.status_text_box.configure(
                text=f"Estado: {status_text}\n"
                     f"Proxima toma: {next_cap}\n"
                     f"Ultimo lote: {last_cap_str}\n"
                     f"Destino: {target_dir}"
            )
        except Exception:
            pass

        self.after(2000, self.refresh_timer)

if __name__ == "__main__":
    app = SifmaLiteTouchApp()
    app.mainloop()
