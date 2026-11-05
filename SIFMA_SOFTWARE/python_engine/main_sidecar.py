# SIFMA — Proceso Sidecar Principal (Python Subprocess IPC)
# Lee solicitudes JSON-RPC por stdin y responde por stdout.

import sys
import os
import json
import time
import numpy as np

# Ajustar PYTHONPATH local
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from core.protocol import JsonRpcProtocol
from core.logger import SidecarLogger
from vision.exg_segmentation import ExgSegmenter
from vision.morphological import MorphologicalFilter
from vision.biometric_cenital import CenitalBiometrics
from vision.biometric_lateral import LateralBiometrics
from ml_models.yolo_detector import YoloLeafDetector
from ml_models.anomaly_detector import PhytosanitaryAnomalyDetector

class SidecarDispatcher:
    def __init__(self):
        self.exg = ExgSegmenter()
        self.yolo = YoloLeafDetector()
        self.anomaly = PhytosanitaryAnomalyDetector()

    def dispatch(self, method: str, params: dict) -> dict:
        if method == "ping":
            return {"status": "pong", "engine": "SIFMA-Python-Sidecar", "version": "2.0.0"}

        elif method == "process_image":
            image_path = params.get("image_path", "")
            is_lateral = params.get("is_lateral", False)
            pixel_ratio = params.get("pixel_to_cm_ratio", 0.05)

            # Cargar imagen o generar matriz sintética para validación
            t0 = time.time()
            img = self._load_or_mock_image(image_path)
            mask = self.exg.generate_binary_mask(img, is_lateral=is_lateral)
            clean_mask = MorphologicalFilter.cleanup_mask(mask, is_lateral=is_lateral)
            contours = MorphologicalFilter.find_contours(clean_mask)

            cenital_res = CenitalBiometrics.calculate(img, clean_mask, contours, pixel_ratio)
            lateral_res = LateralBiometrics.calculate(img.shape, contours, pixel_ratio)
            elapsed_ms = round((time.time() - t0) * 1000, 2)

            return {
                "success": True,
                "elapsed_ms": elapsed_ms,
                "biometrics": {**cenital_res, **lateral_res}
            }

        elif method == "detect_organs":
            img = self._load_or_mock_image(params.get("image_path", ""))
            return self.yolo.predict(img)

        elif method == "detect_anomalies":
            img = self._load_or_mock_image(params.get("image_path", ""))
            return self.anomaly.predict(img)

        else:
            raise ValueError(f"Método '{method}' desconocido en el dispatcher")

    def _load_or_mock_image(self, path: str) -> np.ndarray:
        try:
            import cv2
            if path and os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    return img
        except ImportError:
            pass

        # Generar matriz sintética BGR de prueba (640x480 con franja verde)
        mock = np.zeros((480, 640, 3), dtype=np.uint8)
        mock[:, :] = [30, 25, 20] # Fondo neutro
        mock[180:360, 260:380] = [35, 180, 50] # Tejido vegetal verde
        return mock

def run_loop():
    SidecarLogger.info("Iniciando despachador Sidecar IPC de SIFMA...")
    dispatcher = SidecarDispatcher()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        req_id = None
        try:
            req = JsonRpcProtocol.parse_request(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            result = dispatcher.dispatch(method, params)
            response = JsonRpcProtocol.format_success(req_id, result)
            sys.stdout.write(response + "\n")
            sys.stdout.flush()

        except Exception as err:
            SidecarLogger.error(f"Error procesando solicitud: {str(err)}")
            err_response = JsonRpcProtocol.format_error(req_id, -32603, str(err))
            sys.stdout.write(err_response + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_loop()
