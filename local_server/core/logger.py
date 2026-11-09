# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import logging
import os
import sys

def setup_logger(name: str = "SIFMA") -> logging.Logger:
    """Configura un logger estructurado para toda la aplicación (compatible con modo consola y ventana nativa .exe)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        if sys.stdout is not None:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # En modo escritorio o ejecutable sin consola, registrar también en %APPDATA%\SIFMA\sifma_desktop.log
        if getattr(sys, "frozen", False) or os.getenv("SIFMA_DESKTOP_MODE", "0") == "1" or sys.stdout is None:
            try:
                appdata_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SIFMA")
                os.makedirs(appdata_dir, exist_ok=True)
                log_file = os.path.join(appdata_dir, "sifma_desktop.log")
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception:
                pass
    return logger

logger = setup_logger()
