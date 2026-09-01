import os
import time

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
    Servicio de captura física de imágenes para Raspberry Pi 5 y cámaras USB.
    Gestiona la cámara cenital (0) y la cámara lateral (1) de forma robusta.
    """
    
    @staticmethod
    def capture_photo(output_path, camera_index=0, max_retries=2):
        """
        Toma una fotografía de la cámara especificada (0=Cenital, 1=Lateral)
        y la guarda en la ruta indicada.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        for attempt in range(1, max_retries + 1):
            # 1. Intentar con Picamera2 (Hardware oficial Raspberry Pi Camera Module)
            if HAS_PICAMERA2:
                try:
                    picam2 = Picamera2(camera_index)
                    picam2.start()
                    time.sleep(1.0) # Calibrar exposición automática y balance de blancos
                    picam2.capture_file(output_path)
                    picam2.stop()
                    picam2.close()
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                        print(f"[CAMARA] Foto capturada con Picamera2 (Cam {camera_index}): {os.path.basename(output_path)}")
                        return True
                except Exception as e:
                    print(f"[CAMARA] Intento {attempt} con Picamera2 (Cam {camera_index}): {e}")
                    
            # 2. Intentar con cámara USB convencional (OpenCV VideoCapture)
            if HAS_OPENCV:
                cap = None
                try:
                    cap = cv2.VideoCapture(camera_index)
                    if cap.isOpened():
                        # Descartar los primeros frames para permitir autoexposición del sensor
                        for _ in range(3):
                            cap.read()
                            time.sleep(0.05)
                        ret, frame = cap.read()
                        cap.release()
                        if ret and frame is not None:
                            cv2.imwrite(output_path, frame)
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                                print(f"[CAMARA] Foto capturada con camara USB (Cam {camera_index}): {os.path.basename(output_path)}")
                                return True
                    else:
                        # Si no pudo abrir el dispositivo en el intento 1, no reintentar innecesariamente
                        if cap is not None:
                            cap.release()
                        break
                except Exception as e:
                    print(f"[CAMARA] Intento {attempt} con OpenCV (Cam {camera_index}): {e}")
                finally:
                    if cap is not None and cap.isOpened():
                        cap.release()
                        
            time.sleep(0.5)
            
        print(f"[CAMARA AVISO] No se detecto camara activa en el indice {camera_index} para guardar {os.path.basename(output_path)}")
        return False
