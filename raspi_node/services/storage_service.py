import os
import json
import time
import platform
from datetime import datetime

class OfflineStorageService:
    """
    Servicio encargado de detectar automáticamente memorias USB conectadas a la Raspberry Pi
    y estructurar el almacenamiento por fecha y período:
    Estructura en USB: SIFMA_CAPTURES/YYYY-MM-DD/periodo/
    """
    
    @staticmethod
    def wait_and_find_storage_directory(timeout_sec=10):
        """
        Espera a que el sistema operativo monte la memoria USB al encender.
        Si tras el tiempo límite no se detecta USB, utiliza almacenamiento local de respaldo.
        """
        # 1. Comprobación inmediata
        initial_check = OfflineStorageService._find_target_storage_directory_once()
        if initial_check and "SIFMA_OFFLINE_STORAGE" not in initial_check:
            print(f"[ALMACENAMIENTO] Memoria USB detectada en: {initial_check}")
            return initial_check

        start_time = time.time()
        print(f"[ALMACENAMIENTO] Esperando deteccion de memoria USB (maximo {timeout_sec}s)...")
        
        while time.time() - start_time < timeout_sec:
            target_path = OfflineStorageService._find_target_storage_directory_once()
            if target_path and "SIFMA_OFFLINE_STORAGE" not in target_path:
                print(f"[ALMACENAMIENTO] Memoria USB detectada y montada en: {target_path}")
                return target_path
            time.sleep(1.5)
            
        print("[ALMACENAMIENTO AVISO] No se detecto memoria USB externa. Usando almacenamiento local de respaldo.")
        return OfflineStorageService._find_target_storage_directory_once()

    @staticmethod
    def _find_target_storage_directory_once():
        system = platform.system()
        possible_usb_roots = []
        
        if system == "Windows":
            import string
            for letter in string.ascii_uppercase:
                if letter not in ['C']:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        possible_usb_roots.append(drive)
        else: # Linux / Raspberry Pi OS
            possible_usb_roots = [
                "/media/computo1",
                "/media/pi",
                "/media",
                "/mnt/usb",
                "/mnt"
            ]
            
        target_usb_path = None
        for root in possible_usb_roots:
            if os.path.exists(root):
                if os.access(root, os.W_OK):
                    target_usb_path = os.path.join(root, "SIFMA_CAPTURES")
                    break
                else:
                    try:
                        subdirs = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
                        for sd in subdirs:
                            if os.access(sd, os.W_OK):
                                target_usb_path = os.path.join(sd, "SIFMA_CAPTURES")
                                break
                    except Exception:
                        pass
                if target_usb_path:
                    break
                    
        if not target_usb_path:
            local_fallback = os.path.join(os.path.dirname(os.path.dirname(__file__)), "SIFMA_OFFLINE_STORAGE")
            target_usb_path = local_fallback
            
        return target_usb_path

    @staticmethod
    def create_batch_directory(period="manana", wait_for_usb=True):
        """
        Crea una carpeta de lote en la USB con la jerarquía:
        SIFMA_CAPTURES/YYYY-MM-DD/periodo/
        """
        if wait_for_usb:
            base_dir = OfflineStorageService.wait_and_find_storage_directory(timeout_sec=10)
        else:
            base_dir = OfflineStorageService._find_target_storage_directory_once()
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        period_clean = period.lower().replace("ñ", "n").replace("í", "i").replace(" ", "_")
        
        batch_dir = os.path.join(base_dir, date_str, period_clean)
        os.makedirs(batch_dir, exist_ok=True)
        return batch_dir

    @staticmethod
    def save_batch_metadata(batch_dir, period, crop_type="cebollin", image_files_count=10, plant_id=1):
        """
        Guarda el archivo metadata.json en el lote de la USB y sincroniza el disco.
        """
        meta_path = os.path.join(batch_dir, "metadata.json")
        payload = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "exact_time": datetime.now().strftime("%H:%M:%S"),
            "period": period,
            "crop_type": crop_type,
            "plant_id": plant_id,
            "images_count": image_files_count
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
        # Forzar sincronización física en la memoria USB
        try:
            if hasattr(os, 'sync'):
                os.sync()
        except Exception:
            pass
            
        print(f"[ALMACENAMIENTO] Metadatos guardados y sincronizados en USB: {meta_path}")
        return meta_path
