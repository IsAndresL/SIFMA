# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import sys
import subprocess
import importlib

SERVER_REQUIRED_PACKAGES = [
    ("flask", "Flask==3.1.3"),
    ("flask_sqlalchemy", "Flask-SQLAlchemy==3.1.1"),
    ("sqlalchemy", "SQLAlchemy==2.0.52"),
    ("cv2", "opencv-python==4.11.0.86"),
    ("numpy", "numpy==2.4.6"),
    ("serial", "pyserial==3.5"),
    ("dotenv", "python-dotenv==1.2.4")
]

def install_package(package_name: str) -> bool:
    """Instala automáticamente un paquete de Python utilizando pip."""
    print(f"[AUTO-INSTALADOR SIFMA] Instalando paquete ausente: '{package_name}'...")
    base_cmd = [sys.executable, "-m", "pip", "install", package_name]
    
    try:
        res = subprocess.run(base_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[AUTO-INSTALADOR SIFMA] '{package_name}' instalado exitosamente.")
            return True
        
        # En Linux con restricciones de entorno gestionado externamente (PEP 668)
        if "externally-managed-environment" in res.stderr.lower() or sys.platform.startswith("linux"):
            print(f"[AUTO-INSTALADOR SIFMA] Reintentando con --break-system-packages...")
            res_break = subprocess.run(base_cmd + ["--break-system-packages"], capture_output=True, text=True)
            if res_break.returncode == 0:
                print(f"[AUTO-INSTALADOR SIFMA] '{package_name}' instalado exitosamente.")
                return True
            else:
                print(f"[AUTO-INSTALADOR AVISO] No se pudo instalar '{package_name}': {res_break.stderr}")
                return False
        else:
            print(f"[AUTO-INSTALADOR AVISO] No se pudo instalar '{package_name}': {res.stderr}")
            return False
    except Exception as e:
        print(f"[AUTO-INSTALADOR ERROR] Excepción al ejecutar pip: {e}")
        return False

def ensure_dependencies():
    """Verifica e instala automáticamente las librerías necesarias del servidor SIFMA."""
    # Si la aplicación se ejecuta congelada dentro del ejecutable (.exe), todas las librerías ya están incluidas
    if getattr(sys, "frozen", False):
        return

    missing = []
    for module_name, pip_name in SERVER_REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append((module_name, pip_name))

    if missing:
        print("\n=======================================================")
        print(f"[AUTO-INSTALADOR SIFMA] Detectadas {len(missing)} dependencias faltantes.")
        print("Instalando automáticamente mediante PIP...")
        print("=======================================================\n")
        
        for module_name, pip_name in missing:
            ok = install_package(pip_name)
            if ok:
                try:
                    importlib.invalidate_caches()
                    importlib.import_module(module_name)
                except Exception:
                    pass
        print("\n[AUTO-INSTALADOR SIFMA] Dependencias listas para producción.\n")

if __name__ == "__main__":
    ensure_dependencies()
