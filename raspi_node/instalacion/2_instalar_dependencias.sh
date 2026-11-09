#!/bin/bash
# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

# ====================================================================
# PASO 2: Instalación de Dependencias del Sistema y Paquetes Python
# ====================================================================

set -e

echo "================================================================================"
echo "SIFMA — PASO 2: INSTALACIÓN DE DEPENDENCIAS (RASPBERRY PI OS)"
echo "================================================================================"

INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"

echo "[INFO] Directorio del nodo: $INSTALL_DIR"
echo "[INFO] Actualizando repositorios APT..."
sudo apt-get update -y

echo "[INFO] Instalando paquetes base del sistema y soporte multimedia..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    python3-picamera2 \
    libcamera-apps \
    rpicam-apps

echo "[INFO] Instalando librerías científicas y de captura en Python..."
REQ_FILE="$INSTALL_DIR/requirements.txt"

if [ -f "$REQ_FILE" ]; then
    pip3 install -r "$REQ_FILE" --break-system-packages 2>/dev/null || pip3 install -r "$REQ_FILE"
else
    echo "[AVISO] No se localizó requirements.txt en $INSTALL_DIR."
fi

echo ""
echo "================================================================================"
echo "[ÉXITO] Dependencias de software instaladas satisfactoriamente."
echo "Proceda con el Paso 3 para registrar el servicio automático y accesos directos."
echo "================================================================================"

