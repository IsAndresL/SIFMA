import os
import sys
import time
import subprocess
import shutil

HAS_PICAMERA2 = False
try:
    from picamera2 import Picamera2
    HAS_PICAMERA2 = True
except (ImportError, OSError):
    pass

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

class CameraCaptureService:
    """
    Servicio de captura física para Raspberry Pi 5 con cámaras ARDUCAM / MIPI CSI
    conectadas mediante cables flexores a los puertos CAM/DISP 0 (Cenital) y CAM/DISP 1 (Lateral).
    
    Aplica rotación de producción:
    - Cámara 0 (Cenital): Rotación 180° para orientación derecha del dosel.
    - Cámara 1 (Lateral): Rotación 90° a la derecha (sentido horario) para orientación vertical del tallo.
    """
    
    @staticmethod
    def _apply_orientation(output_path, camera_index=0):
        """Aplica la rotación correspondiente según la posición física de la cámara."""
        if not os.path.exists(output_path):
            return
            
        try:
            if HAS_OPENCV:
                img = cv2.imread(output_path)
                if img is not None:
                    if camera_index == 0:
                        # Cenital: Rotar 180 grados
                        rotated = cv2.rotate(img, cv2.ROTATE_180)
                    else:
                        # Lateral: Rotar 90 grados en sentido horario
                        rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    cv2.imwrite(output_path, rotated)
            else:
                from PIL import Image
                img = Image.open(output_path)
                if camera_index == 0:
                    rotated = img.rotate(180, expand=True)
                else:
                    rotated = img.rotate(270, expand=True) # 270 deg counter-clockwise = 90 deg clockwise
                rotated.save(output_path)
        except Exception as e:
            print(f"[CAMARA AVISO] Error al rotar imagen: {e}")

    @staticmethod
    def list_detected_cameras():
        """Consulta el hardware MIPI CSI para detectar las cámaras Arducam conectadas."""
        detected = []
        cmd_tool = shutil.which("rpicam-hello") or shutil.which("libcamera-hello")
        if cmd_tool:
            try:
                res = subprocess.run([cmd_tool, "--list-cameras"], capture_output=True, text=True, timeout=5)
                output = res.stdout + "\n" + res.stderr
                lines = [l.strip() for l in output.splitlines() if l.strip()]
                for line in lines:
                    if "available" in line.lower() or ":" in line:
                        detected.append(line)
            except Exception:
                pass

        if not detected and HAS_PICAMERA2:
            try:
                from picamera2 import Picamera2
                for idx in [0, 1]:
                    try:
                        p = Picamera2(idx)
                        detected.append(f"CSI Puerto {idx}: Camara Arducam detectada")
                        p.close()
                    except Exception:
                        pass
            except Exception:
                pass

        return detected

    @staticmethod
    def capture_photo(output_path, camera_index=0, max_retries=2):
        """
        Captura una imagen de alta calidad desde la cámara Arducam conectada al puerto flexor
        CAM/DISP correspondiente (0 = Cenital, 1 = Lateral).
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        for attempt in range(1, max_retries + 1):
            # 1. Estrategia Principal: Picamera2 (Controlador oficial CSI de Raspberry Pi 5)
            if HAS_PICAMERA2:
                picam2 = None
                try:
                    picam2 = Picamera2(camera_index)
                    still_config = picam2.create_still_configuration(main={"format": "RGB888"})
                    picam2.configure(still_config)
                    picam2.start()
                    time.sleep(0.8)  # Tiempo para calibración automática de fotometría del sensor Arducam
                    picam2.capture_file(output_path)
                    picam2.stop()
                    picam2.close()
                    picam2 = None
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        CameraCaptureService._apply_orientation(output_path, camera_index=camera_index)
                        print(f"[CAMARA CSI] Foto capturada y orientada en Puerto Flex #{camera_index}: {os.path.basename(output_path)}")
                        return True
                except Exception as e:
                    print(f"[CAMARA CSI] Intento {attempt} con Picamera2 (Puerto Flex {camera_index}): {e}")
                finally:
                    if picam2 is not None:
                        try:
                            picam2.close()
                        except Exception:
                            pass

            # 2. Estrategia Secundaria: Binario Nativo rpicam-still / libcamera-still
            rpicam_bin = shutil.which("rpicam-still") or shutil.which("libcamera-still")
            if rpicam_bin:
                try:
                    cmd = [
                        rpicam_bin,
                        "--camera", str(camera_index),
                        "-o", output_path,
                        "-t", "800",       # 800ms para autoexposición
                        "--nopreview",
                        "-n",              # Sin vista previa en ventana de servidor X
                        "--encoding", "png" if output_path.lower().endswith(".png") else "jpg"
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                    if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        CameraCaptureService._apply_orientation(output_path, camera_index=camera_index)
                        print(f"[CAMARA CSI] Foto capturada con {os.path.basename(rpicam_bin)} (Puerto Flex {camera_index}): {os.path.basename(output_path)}")
                        return True
                    else:
                        print(f"[CAMARA CSI] {os.path.basename(rpicam_bin)} fallo en puerto {camera_index}: {res.stderr}")
                except Exception as e:
                    print(f"[CAMARA CSI] Intento con {rpicam_bin} en puerto {camera_index}: {e}")

            # 3. Estrategia Terciaria: OpenCV VideoCapture (V4L2 CSI Backend)
            if HAS_OPENCV:
                cap = None
                try:
                    if sys.platform.startswith("linux"):
                        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                    else:
                        cap = cv2.VideoCapture(camera_index)
                        
                    if cap.isOpened():
                        for _ in range(4):
                            cap.read()
                            time.sleep(0.04)
                        ret, frame = cap.read()
                        cap.release()
                        if ret and frame is not None:
                            cv2.imwrite(output_path, frame)
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                CameraCaptureService._apply_orientation(output_path, camera_index=camera_index)
                                print(f"[CAMARA CSI] Foto capturada con OpenCV (Puerto {camera_index}): {os.path.basename(output_path)}")
                                return True
                    else:
                        if cap is not None:
                            cap.release()
                except Exception as e:
                    print(f"[CAMARA CSI] Intento con OpenCV (Puerto {camera_index}): {e}")
                finally:
                    if cap is not None and cap.isOpened():
                        cap.release()

            time.sleep(0.5)

        print(f"[CAMARA AVISO] No se pudo capturar foto en el Puerto Flex CAM/DISP #{camera_index} ({os.path.basename(output_path)})")
        return False
