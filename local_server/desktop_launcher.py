# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import os
import socket
import sys
import threading
import time
import urllib.request

# 1. Activar modo escritorio antes de importar la configuración de SIFMA
os.environ["SIFMA_DESKTOP_MODE"] = "1"

# 2. En modo ejecutable sin consola (windowed), redirigir stdout/stderr a archivo de log seguro
if sys.stdout is None or sys.stderr is None:
    try:
        appdata_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SIFMA")
        os.makedirs(appdata_dir, exist_ok=True)
        stream_log = open(os.path.join(appdata_dir, "sifma_runtime.log"), "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = stream_log
        if sys.stderr is None:
            sys.stderr = stream_log
    except Exception:
        pass

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from werkzeug.serving import make_server
from app import app
from core.config import config
from core.logger import logger


def find_available_port(preferred_port: int = 5000) -> int:
    """Intenta usar el puerto 5000; si está ocupado, asigna un puerto local libre automáticamente."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred_port)) != 0:
            return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_server_ready(url: str, timeout_sec: float = 12.0) -> bool:
    """Espera a que el motor interno Flask responda antes de abrir la ventana nativa."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status in (200, 302):
                    return True
        except Exception:
            time.sleep(0.1)
    return False


def main():
    port = find_available_port(5000)
    local_url = f"http://127.0.0.1:{port}"

    logger.info("==========================================================")
    logger.info(f"Iniciando SIFMA Desktop v{config.APP_VERSION}")
    logger.info(f"Bóveda de datos protegida: {config.USER_DATA_DIR}")
    logger.info(f"Base de datos activa: {config.DB_PATH}")
    logger.info(f"Motor interno escuchando en: {local_url}")
    logger.info("==========================================================")

    http_server = make_server("127.0.0.1", port, app, threaded=True)
    server_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    server_thread.start()

    wait_for_server_ready(f"{local_url}/login")

    try:
        import webview

        icon_path = os.path.join(config.STATIC_DIR, "img", "sifma_icon.ico")
        window = webview.create_window(
            title="SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola",
            url=local_url,
            width=1380,
            height=860,
            min_size=(1024, 680),
            text_select=True,
        )

        def on_closed():
            logger.info("Ventana de escritorio cerrada. Apagando servidor interno SIFMA...")
            try:
                http_server.shutdown()
            except Exception:
                pass

        window.events.closed += on_closed

        if os.path.exists(icon_path):
            webview.start(icon=icon_path)
        else:
            webview.start()

    except Exception as e:
        logger.error(f"Error al inicializar ventana nativa PyWebView: {e}")
    finally:
        try:
            http_server.shutdown()
        except Exception:
            pass
        os._exit(0)


if __name__ == "__main__":
    main()

