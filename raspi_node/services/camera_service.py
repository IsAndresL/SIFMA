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
    """
    
    @staticmethod
    def capture_photo(output_path, camera_index=0):
        """
        Toma una fotografía de la cámara especificada y la guarda en la ruta indicada.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 1. Intentar Picamera2 (Hardware oficial Raspberry Pi 5)
        if HAS_PICAMERA2:
            try:
                picam2 = Picamera2()
                picam2.start()
                time.sleep(1) # Calibrar exposición y brillo
                picam2.capture_file(output_path)
                picam2.stop()
                picam2.close()
                print(f"[CAMERA] Foto capturada con Picamera2: {os.path.basename(output_path)}")
                return True
            except Exception as e:
                print(f"[CAMERA] Error con Picamera2: {e}")
                
        # 2. Captura con cámara USB convencional (OpenCV VideoCapture)
        if HAS_OPENCV:
            try:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    time.sleep(0.5)
                    ret, frame = cap.read()
                    cap.release()
                    if ret and frame is not None:
                        cv2.imwrite(output_path, frame)
                        print(f"[CAMERA] Foto capturada con cámara USB: {os.path.basename(output_path)}")
                        return True
            except Exception as e:
                print(f"[CAMERA] Error con OpenCV camera (índice {camera_index}): {e}")
                
        print(f"[CAMERA ERROR] No se detectó ninguna cámara activa para guardar {os.path.basename(output_path)}")
        return False
