import os
import sys
import time
import threading
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox

# Asegurar importación de librerías de imagen
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

HAS_PICAMERA2 = False
try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except (ImportError, OSError):
    pass

class CameraCalibrationApp(tk.Tk):
    """
    Herramienta Independiente de Calibración y Enfoque en Vivo para Cámaras Arducam (MIPI CSI).
    - Monocámara activa: Solo activa UNA cámara a la vez (Cenital 0 o Lateral 1).
    - Rotación física en tiempo real:
      * Cenital (CAM 0): Rotada 180° + Detección de ROI Circular de Canastilla Azul.
      * Lateral (CAM 1): Rotada 90° a la derecha (sentido horario) para orientación vertical del tallo.
    - Corrección de Color BGR/RGB: Elimina tonos azules no deseados en la piel y muestra colores botánicos reales.
    - Medidor de Nitidez / Enfoque en Tiempo Real (Laplacian Variance).
    - Grilla de alineación vertical de dosel y tallo.
    """
    def __init__(self):
        super().__init__()
        self.title("SIFMA - Calibración y Enfoque en Vivo (Arducam CSI)")
        self.geometry("880x680")
        self.minsize(780, 580)
        self.configure(bg="#0a0f18")

        self.current_camera_index = None
        self.is_streaming = False
        self.stream_thread = None
        self.picam2_instance = None
        self.cap_cv = None
        self.show_grid = True
        
        # Por defecto invertimos canales BGR a RGB para corregir el tono azul
        self.swap_rb_channels = True

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Escaneo inicial no bloqueante
        self.after(500, self.diagnose_cameras)

    def setup_ui(self):
        # 1. Header
        header = tk.Frame(self, bg="#111a2e", padx=12, pady=8, highlightbackground="#1e2d4d", highlightthickness=1)
        header.pack(fill=tk.X, padx=8, pady=(8, 4))

        title_box = tk.Frame(header, bg="#111a2e")
        title_box.pack(side=tk.LEFT)
        tk.Label(title_box, text="CALIBRACIÓN Y ENFOQUE DE CÁMARAS CSI", font=("Segoe UI", 12, "bold"), fg="#10b981", bg="#111a2e").pack(anchor="w")
        self.lbl_cam_detected = tk.Label(title_box, text="Detectando puertos CSI flex...", font=("Segoe UI", 8), fg="#94a3b8", bg="#111a2e")
        self.lbl_cam_detected.pack(anchor="w")

        self.lbl_fps = tk.Label(header, text="FPS: 0 | Enfoque: --", font=("Courier", 10, "bold"), fg="#38bdf8", bg="#111a2e")
        self.lbl_fps.pack(side=tk.RIGHT)

        # 2. Barra de Selección de Cámara (Exclusión Mutua: 0 o 1)
        btn_bar = tk.Frame(self, bg="#0a0f18", padx=4, pady=4)
        btn_bar.pack(fill=tk.X, padx=8, pady=4)

        self.btn_cam0 = tk.Button(
            btn_bar, 
            text="1. CÁMARA CENITAL (CAM 0: 180° + ROI CANASTILLA)", 
            font=("Segoe UI", 9, "bold"), 
            bg="#1e293b", 
            fg="#f8fafc", 
            activebackground="#059669", 
            relief="flat", 
            pady=10, 
            command=lambda: self.switch_camera(0)
        )
        self.btn_cam0.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_cam1 = tk.Button(
            btn_bar, 
            text="2. CÁMARA LATERAL (CAM 1: ROTADA 90° DERECHA)", 
            font=("Segoe UI", 9, "bold"), 
            bg="#1e293b", 
            fg="#f8fafc", 
            activebackground="#2563eb", 
            relief="flat", 
            pady=10, 
            command=lambda: self.switch_camera(1)
        )
        self.btn_cam1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_stop = tk.Button(
            btn_bar, 
            text="DETENER VIDEO", 
            font=("Segoe UI", 9, "bold"), 
            bg="#7f1d1d", 
            fg="#ffffff", 
            activebackground="#991b1b", 
            relief="flat", 
            padx=10, 
            pady=10, 
            command=self.stop_current_stream
        )
        self.btn_stop.pack(side=tk.LEFT, padx=3)

        self.btn_color_fix = tk.Button(
            btn_bar, 
            text="COLOR (RGB/BGR)", 
            font=("Segoe UI", 8, "bold"), 
            bg="#d97706", 
            fg="#ffffff", 
            activebackground="#b45309", 
            relief="flat", 
            padx=8, 
            pady=10, 
            command=self.toggle_color_format
        )
        self.btn_color_fix.pack(side=tk.LEFT, padx=3)

        # 3. Visor Central de Video
        self.video_container = tk.Frame(self, bg="#000000", highlightbackground="#1e2d4d", highlightthickness=2)
        self.video_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self.lbl_video = tk.Label(self.video_container, bg="#000000", text="Seleccione una cámara arriba para iniciar transmisión en vivo", font=("Segoe UI", 11), fg="#64748b")
        self.lbl_video.pack(fill=tk.BOTH, expand=True)

        # 4. Barra de Enfoque y Herramientas
        bottom_bar = tk.Frame(self, bg="#111a2e", padx=12, pady=8, highlightbackground="#1e2d4d", highlightthickness=1)
        bottom_bar.pack(fill=tk.X, padx=8, pady=(4, 8))

        # Indicador de Enfoque Visual
        focus_box = tk.Frame(bottom_bar, bg="#111a2e")
        focus_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_focus_text = tk.Label(focus_box, text="Nitidez: -- (Gire la lente Arducam hasta obtener el valor máximo)", font=("Segoe UI", 9, "bold"), fg="#f8fafc", bg="#111a2e")
        self.lbl_focus_text.pack(anchor="w")

        self.focus_meter = tk.Canvas(focus_box, height=12, bg="#0f172a", highlightthickness=0)
        self.focus_meter.pack(fill=tk.X, pady=(2, 0))

        # Checkbox Grilla
        self.chk_grid_btn = tk.Button(bottom_bar, text="Guías: ACTIVADAS", font=("Segoe UI", 8, "bold"), bg="#065f46", fg="#fff", relief="flat", padx=8, pady=4, command=self.toggle_grid)
        self.chk_grid_btn.pack(side=tk.RIGHT, padx=4)

        # Botón Diagnóstico
        btn_diag = tk.Button(bottom_bar, text="Escanear CSI", font=("Segoe UI", 8, "bold"), bg="#1e293b", fg="#94a3b8", relief="flat", padx=8, pady=4, command=self.diagnose_cameras)
        btn_diag.pack(side=tk.RIGHT, padx=4)

    def toggle_color_format(self):
        self.swap_rb_channels = not self.swap_rb_channels
        state_str = "RGB (Natural)" if self.swap_rb_channels else "BGR (Directo)"
        self.btn_color_fix.configure(text=f"COLOR: {state_str}")

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.chk_grid_btn.configure(
            text="Guías: ACTIVADAS" if self.show_grid else "Guías: DESACTIVADAS",
            bg="#065f46" if self.show_grid else "#374151"
        )

    def diagnose_cameras(self):
        found = []
        cmd_tool = shutil.which("rpicam-hello") or shutil.which("libcamera-hello")
        if cmd_tool:
            try:
                res = subprocess.run([cmd_tool, "--list-cameras"], capture_output=True, text=True, timeout=4)
                out = res.stdout + "\n" + res.stderr
                for line in out.splitlines():
                    if "available" in line.lower() or ":" in line:
                        found.append(line.strip())
            except Exception:
                pass

        if not found and HAS_PICAMERA2:
            for idx in [0, 1]:
                try:
                    p = Picamera2(idx)
                    found.append(f"CAM {idx} activa")
                    p.close()
                except Exception:
                    pass

        if found:
            self.lbl_cam_detected.configure(text=f"Hardware CSI: {' | '.join(found)}", fg="#34d399")
        else:
            self.lbl_cam_detected.configure(
                text="Aviso: CAM/DISP 1 no detectada por el kernel. Verifique flexor o agregue dtoverlay en config.txt", 
                fg="#f59e0b"
            )

    def switch_camera(self, target_cam_index):
        if self.current_camera_index == target_cam_index and self.is_streaming:
            return

        self.stop_current_stream()
        time.sleep(0.3)

        self.current_camera_index = target_cam_index
        self.btn_cam0.configure(bg="#059669" if target_cam_index == 0 else "#1e293b", fg="#fff")
        self.btn_cam1.configure(bg="#2563eb" if target_cam_index == 1 else "#1e293b", fg="#fff")

        self.is_streaming = True
        self.lbl_video.configure(text=f"Conectando a Cámara {target_cam_index} por flexor CSI...", image="")
        
        self.stream_thread = threading.Thread(target=self._run_camera_loop, args=(target_cam_index,), daemon=True)
        self.stream_thread.start()

    def stop_current_stream(self):
        self.is_streaming = False
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)

        if self.picam2_instance is not None:
            try:
                self.picam2_instance.stop()
                self.picam2_instance.close()
            except Exception:
                pass
            self.picam2_instance = None

        if self.cap_cv is not None:
            try:
                self.cap_cv.release()
            except Exception:
                pass
            self.cap_cv = None

        self.current_camera_index = None
        self.btn_cam0.configure(bg="#1e293b", fg="#f8fafc")
        self.btn_cam1.configure(bg="#1e293b", fg="#f8fafc")
        self.lbl_video.configure(text="Video detenido. Cámaras libres para captura regular.", image="")
        self.lbl_fps.configure(text="FPS: 0 | Enfoque: --")
        self.lbl_focus_text.configure(text="Nitidez: -- (Video detenido)", fg="#94a3b8")
        self.focus_meter.delete("all")

    def _run_camera_loop(self, cam_idx):
        use_picam2 = False

        if HAS_PICAMERA2:
            try:
                self.picam2_instance = Picamera2(cam_idx)
                preview_cfg = self.picam2_instance.create_preview_configuration(main={"size": (640, 480)})
                self.picam2_instance.configure(preview_cfg)
                self.picam2_instance.start()
                use_picam2 = True
                print(f"[CALIBRACIÓN] Picamera2 iniciada en Puerto #{cam_idx}")
            except Exception as e:
                print(f"[CALIBRACIÓN] No se pudo abrir Picamera2 en puerto {cam_idx}: {e}")
                if self.picam2_instance is not None:
                    try: self.picam2_instance.close()
                    except Exception: pass
                self.picam2_instance = None

        if not use_picam2 and HAS_OPENCV:
            try:
                if sys.platform.startswith("linux"):
                    self.cap_cv = cv2.VideoCapture(cam_idx, cv2.CAP_V4L2)
                else:
                    self.cap_cv = cv2.VideoCapture(cam_idx)
                    
                if self.cap_cv.isOpened():
                    self.cap_cv.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap_cv.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    print(f"[CALIBRACIÓN] OpenCV VideoCapture abierto en Puerto #{cam_idx}")
            except Exception as e:
                print(f"[CALIBRACIÓN] Error en OpenCV: {e}")

        if not use_picam2 and (self.cap_cv is None or not self.cap_cv.isOpened()):
            cam_name = "CENITAL (CAM 0)" if cam_idx == 0 else "LATERAL (CAM 1)"
            self.after(0, self._show_camera_error, cam_name, cam_idx)
            return

        frame_count = 0
        last_time = time.time()
        fps = 0.0

        while self.is_streaming:
            raw_frame = None

            if use_picam2 and self.picam2_instance is not None:
                try:
                    raw_frame = self.picam2_instance.capture_array()
                except Exception:
                    break
            elif self.cap_cv is not None and self.cap_cv.isOpened():
                ret, frame_bgr = self.cap_cv.read()
                if ret and frame_bgr is not None:
                    raw_frame = frame_bgr
                else:
                    time.sleep(0.05)
                    continue

            if raw_frame is None:
                time.sleep(0.05)
                continue

            # Formato de canales
            if len(raw_frame.shape) == 3 and raw_frame.shape[2] == 4:
                raw_frame = raw_frame[:, :, :3]

            # Inversión de color BGR a RGB para corregir tonos azules
            if self.swap_rb_channels:
                if len(raw_frame.shape) == 3 and raw_frame.shape[2] >= 3:
                    frame_oriented = raw_frame[:, :, ::-1].copy()
                else:
                    frame_oriented = raw_frame
            else:
                frame_oriented = raw_frame.copy()

            # APLICAR ROTACIÓN FÍSICA SEGÚN CÁMARA
            if cam_idx == 0:
                # Cámara 0 Cenital: Rotar 180°
                frame_oriented = cv2.rotate(frame_oriented, cv2.ROTATE_180)
            else:
                # Cámara 1 Lateral: Rotar 90° en sentido horario
                frame_oriented = cv2.rotate(frame_oriented, cv2.ROTATE_90_CLOCKWISE)

            h, w, _ = frame_oriented.shape
            display_frame = frame_oriented.copy()

            # Calcular Nitidez sobre el área central
            gray = cv2.cvtColor(display_frame, cv2.COLOR_RGB2GRAY)
            lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # DIBUJAR GUÍAS DE CALIBRACIÓN
            if self.show_grid:
                if cam_idx == 0:
                    # Guía Cenital: ROI Circular Automático de la Canastilla Azul donde está la planta
                    # 1. Segmentación previa de vegetación (planta/dosel)
                    hsv = cv2.cvtColor(frame_oriented, cv2.COLOR_RGB2HSV) if self.swap_rb_channels else cv2.cvtColor(frame_oriented, cv2.COLOR_BGR2HSV)
                    lower_green = np.array([25, 30, 30])
                    upper_green = np.array([88, 255, 255])
                    mask_green = cv2.inRange(hsv, lower_green, upper_green)
                    
                    if self.swap_rb_channels:
                        # frame_oriented is RGB -> split R, G, B
                        r_ch, g_ch, b_ch = cv2.split(frame_oriented.astype(np.float32))
                    else:
                        b_ch, g_ch, r_ch = cv2.split(frame_oriented.astype(np.float32))
                    exg = 2.0 * g_ch - r_ch - b_ch
                    exg_mask = np.uint8((exg > 15) & (g_ch > r_ch) & (g_ch > b_ch)) * 255
                    plant_mask = cv2.bitwise_or(mask_green, exg_mask)
                    
                    # 2. Segmentación de la canastilla azul
                    lower_blue = np.array([90, 45, 35])
                    upper_blue = np.array([140, 255, 255])
                    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
                    mask_blue_clean = cv2.morphologyEx(mask_blue, cv2.MORPH_CLOSE, kernel)
                    mask_blue_clean = cv2.morphologyEx(mask_blue_clean, cv2.MORPH_OPEN, kernel)
                    
                    b_contours, _ = cv2.findContours(mask_blue_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    found_basket = False
                    if b_contours:
                        min_r = int(min(w, h) * 0.05)
                        max_r = int(min(w, h) * 0.45)
                        candidates = []
                        
                        for c in b_contours:
                            area = cv2.contourArea(c)
                            if area < 400:
                                continue
                            (bcx, bcy), brad = cv2.minEnclosingCircle(c)
                            brad = int(brad)
                            if brad < min_r or brad > max_r:
                                continue
                                
                            peri = cv2.arcLength(c, True)
                            circ = (4 * np.pi * area) / (peri * peri) if peri > 0 else 0
                            bx, by, bw, bh = cv2.boundingRect(c)
                            aspect = float(bw) / float(bh) if bh > 0 else 0
                            
                            c_mask = np.zeros((h, w), dtype=np.uint8)
                            cv2.circle(c_mask, (int(bcx), int(bcy)), brad, 255, -1)
                            green_in = cv2.countNonZero(cv2.bitwise_and(plant_mask, c_mask))
                            
                            aspect_diff = abs(1.0 - aspect)
                            score = (green_in * 5.0) + (circ * 300.0) - (aspect_diff * 150.0)
                            if bcy > h * 0.30:
                                score += 200.0
                            if by < h * 0.08:
                                score -= 500.0
                                
                            candidates.append({'cx': int(bcx), 'cy': int(bcy), 'r': brad, 'score': score})
                            
                        if candidates:
                            best = max(candidates, key=lambda k: k['score'])
                            bcx, bcy, brad = best['cx'], best['cy'], int(best['r'] * 1.03)
                            cv2.circle(display_frame, (bcx, bcy), brad, (255, 180, 0), 2)
                            cv2.putText(display_frame, "CANASTILLA AZUL (ROI)", (max(10, bcx - 90), max(25, bcy - brad - 8)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 180, 0), 2)
                            found_basket = True
                            
                    if not found_basket:
                        # Guía circular por defecto en la zona de la planta
                        cx, cy = w // 2, int(h * 0.60)
                        r = int(min(w, h) * 0.22)
                        cv2.circle(display_frame, (cx, cy), r, (0, 255, 255), 2)
                        cv2.putText(display_frame, "ZONA OBJETIVO CANASTILLA", (cx - 100, cy - r - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

                    # Cruz central suave
                    cv2.line(display_frame, (w // 2 - 25, h // 2), (w // 2 + 25, h // 2), (0, 255, 0), 1)
                    cv2.line(display_frame, (w // 2, h // 2 - 25), (w // 2, h // 2 + 25), (0, 255, 0), 1)

                else:
                    # Guía Lateral: Eje vertical del tallo y nivel de sustrato basal
                    cx = w // 2
                    # Línea de medición vertical
                    cv2.line(display_frame, (cx, int(h * 0.15)), (cx, int(h * 0.85)), (0, 255, 255), 2)
                    cv2.line(display_frame, (cx - 25, int(h * 0.15)), (cx + 25, int(h * 0.15)), (0, 255, 255), 2)
                    cv2.line(display_frame, (cx - 25, int(h * 0.85)), (cx + 25, int(h * 0.85)), (0, 255, 255), 2)
                    
                    # Línea de base del sustrato (abajo)
                    cv2.line(display_frame, (int(w * 0.2), int(h * 0.85)), (int(w * 0.8), int(h * 0.85)), (0, 0, 255), 2)
                    cv2.putText(display_frame, "BASE SUSTRATO / CANASTILLA", (int(w * 0.2), int(h * 0.85) + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    cv2.putText(display_frame, "CRECIMIENTO VERTICAL ->", (cx + 10, int(h * 0.5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

            # Cálculo de FPS
            frame_count += 1
            if time.time() - last_time >= 1.0:
                fps = frame_count / (time.time() - last_time)
                frame_count = 0
                last_time = time.time()

            # Convertir a imagen Tkinter
            if HAS_PIL:
                pil_img = Image.fromarray(display_frame)
                vw = self.video_container.winfo_width()
                vh = self.video_container.winfo_height()
                if vw > 100 and vh > 100:
                    pil_img.thumbnail((vw - 10, vh - 10))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.after(0, self._update_frame_ui, tk_img, lap_var, fps, cam_idx)

            time.sleep(0.03)

        if self.picam2_instance is not None:
            try:
                self.picam2_instance.stop()
                self.picam2_instance.close()
            except Exception:
                pass
            self.picam2_instance = None

        if self.cap_cv is not None:
            try:
                self.cap_cv.release()
            except Exception:
                pass
            self.cap_cv = None

    def _show_camera_error(self, cam_name, cam_idx):
        self.lbl_video.configure(
            text=f"No se pudo conectar a {cam_name} en el puerto flex CAM/DISP {cam_idx}.\n\n"
                 "Causas comunes:\n"
                 "1. Cable flexor mal encajado o invertido en CAM/DISP 1.\n"
                 "2. Falta agregar el overlay de la cámara en /boot/firmware/config.txt.\n"
                 "   Ejemplo: dtoverlay=imx477,cam1\n\n"
                 "Ejecute 'rpicam-hello --list-cameras' en la terminal para diagnosticar.",
            image="",
            fg="#ef4444"
        )
        self.lbl_fps.configure(text=f"Error en Puerto {cam_idx}")

    def _update_frame_ui(self, tk_img, lap_var, fps, cam_idx):
        if not self.is_streaming:
            return
            
        self.lbl_video.img_ref = tk_img
        self.lbl_video.configure(image=tk_img, text="")

        if lap_var < 50:
            quality = "DESENFOCADO (Girar lente)"
            color = "#ef4444"
        elif lap_var < 150:
            quality = "ENFOQUE MEDIO"
            color = "#f59e0b"
        else:
            quality = "EXCELENTE ENFOQUE (Optimo)"
            color = "#10b981"

        cam_name = "Cenital 180° (Cam 0)" if cam_idx == 0 else "Lateral 90° (Cam 1)"
        self.lbl_fps.configure(text=f"{cam_name} | FPS: {fps:.1f} | Nitidez: {lap_var:.1f}")
        self.lbl_focus_text.configure(text=f"Índice de Nitidez: {lap_var:.1f} -> {quality}", fg=color)

        self.focus_meter.delete("all")
        bar_w = self.focus_meter.winfo_width()
        meter_fill = min(bar_w, int((lap_var / 350.0) * bar_w))
        self.focus_meter.create_rectangle(0, 0, meter_fill, 12, fill=color, width=0)

    def on_close(self):
        self.stop_current_stream()
        self.destroy()

if __name__ == "__main__":
    app = CameraCalibrationApp()
    app.mainloop()
