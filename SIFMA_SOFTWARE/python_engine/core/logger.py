# SIFMA — Logger Diagnóstico para Python Sidecar
# Escribe exclusivamente a sys.stderr para mantener sys.stdout limpio para el stream JSON-RPC.

import sys
from datetime import datetime

class SidecarLogger:
    @staticmethod
    def log(level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] [SIDECAR-{level}] {message}\n")
        sys.stderr.flush()

    @staticmethod
    def info(message: str):
        SidecarLogger.log("INFO", message)

    @staticmethod
    def warn(message: str):
        SidecarLogger.log("WARN", message)

    @staticmethod
    def error(message: str):
        SidecarLogger.log("ERROR", message)

