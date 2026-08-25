import os
import json
import platform
from datetime import datetime

class OfflineStorageService:
    """
    Servicio encargado de detectar automáticamente unidades USB conectadas
    y guardar los lotes de capturas de forma estructurada e independiente.
    Estructura en la USB: SIFMA_CAPTURES/YYYY-MM-DD/periodo/
    """
    
    @staticmethod
    def find_target_storage_directory():
        """
        Busca memorias USB montadas. Retorna la mejor ruta disponible.
        """
        system = platform.system()
        possible_usb_roots = []
        
        if system == "Windows":
            import string
            for letter in string.ascii_uppercase:
                if letter not in ['C']:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        possible_usb_roots.append(drive)
        else: # Linux / Raspberry Pi
            possible_usb_roots = ["/media/pi", "/media", "/mnt/usb", "/mnt"]
            
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
    def create_batch_directory(period="manana"):
        """
        Crea una carpeta de lote con jerarquía: SIFMA_CAPTURES/YYYY-MM-DD/periodo/
        """
        base_dir = OfflineStorageService.find_target_storage_directory()
        date_str = datetime.now().strftime("%Y-%m-%d")
        period_clean = period.lower().replace("ñ", "n").replace("í", "i").replace(" ", "_")
        
        batch_dir = os.path.join(base_dir, date_str, period_clean)
        os.makedirs(batch_dir, exist_ok=True)
        return batch_dir

    @staticmethod
    def save_batch_metadata(batch_dir, period, crop_type, sensor_data, image_files_count, plant_id=1):
        """
        Guarda el archivo metadata.json en el lote de la USB.
        """
        meta_path = os.path.join(batch_dir, "metadata.json")
        payload = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "period": period,
            "crop_type": crop_type,
            "plant_id": plant_id,
            "images_count": image_files_count,
            "sensor_data": sensor_data
        }
        with open(meta_path, "w") as f:
            json.dump(payload, f, indent=2)
            
        print(f"[STORAGE] Metadatos guardados con éxito en: {meta_path}")
        return meta_path
