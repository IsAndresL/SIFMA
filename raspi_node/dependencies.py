import sys
import subprocess
import importlib

# Mapeo de (nombre_modulo_python, nombre_paquete_pip)
RASPI_REQUIRED_PACKAGES = [
    ("flask", "flask>=3.0.0"),
    ("cv2", "opencv-python-headless>=4.8.0"),
    ("PIL", "pillow>=10.2.0"),
    ("psutil", "psutil>=5.9.0"),
    ("requests", "requests>=2.31.0")
]

def install_package(package_name: str) -> bool:
    """Instala un paquete pip detectando automáticamente flags de compatibilidad para Raspberry Pi OS / Linux."""
    print(f"[AUTO-INSTALADOR SIFMA] Instalando paquete ausente: '{package_name}'...")
    base_cmd = [sys.executable, "-m", "pip", "install", package_name]
    
    try:
        # Intento estándar
        res = subprocess.run(base_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[AUTO-INSTALADOR SIFMA] '{package_name}' instalado exitosamente.")
            return True
        
        # En Raspberry Pi OS (Debian Bookworm con PEP 668), se requiere flag especial
        if "externally-managed-environment" in res.stderr.lower() or sys.platform.startswith("linux"):
            print(f"[AUTO-INSTALADOR SIFMA] Reintentando instalacion con --break-system-packages para Raspberry Pi OS...")
            res_break = subprocess.run(base_cmd + ["--break-system-packages"], capture_output=True, text=True)
            if res_break.returncode == 0:
                print(f"[AUTO-INSTALADOR SIFMA] '{package_name}' instalado exitosamente con --break-system-packages.")
                return True
            else:
                print(f"[AUTO-INSTALADOR AVISO] Error al instalar '{package_name}': {res_break.stderr}")
                return False
        else:
            print(f"[AUTO-INSTALADOR AVISO] Error al instalar '{package_name}': {res.stderr}")
            return False
    except Exception as e:
        print(f"[AUTO-INSTALADOR ERROR] Excepcion al ejecutar pip: {e}")
        return False

def ensure_dependencies():
    """Verifica todas las dependencias requeridas y las instala automáticamente si alguna falta."""
    missing = []
    for module_name, pip_name in RASPI_REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append((module_name, pip_name))

    if missing:
        print("\n=======================================================")
        print(f"[AUTO-INSTALADOR SIFMA] Se detectaron {len(missing)} librerias faltantes.")
        print("Instalando dependencias necesarias de forma automatica...")
        print("=======================================================\n")
        
        for module_name, pip_name in missing:
            ok = install_package(pip_name)
            if ok:
                try:
                    importlib.invalidate_caches()
                    importlib.import_module(module_name)
                except Exception:
                    pass
        print("\n[AUTO-INSTALADOR SIFMA] Verificacion de dependencias completada.\n")

if __name__ == "__main__":
    ensure_dependencies()
