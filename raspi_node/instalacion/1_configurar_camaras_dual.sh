#!/bin/bash
# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

# ====================================================================
# PASO 1: Habilitación de Cámaras Duales CSI en Raspberry Pi 5
# Configura los puertos flexores CAM/DISP 0 y CAM/DISP 1 en config.txt
# ====================================================================

set -e

echo "================================================================================"
echo "SIFMA — PASO 1: CONFIGURACIÓN DE CÁMARAS DUALES CSI (RASPBERRY PI 5)"
echo "================================================================================"

CONFIG_TXT="/boot/firmware/config.txt"
[ ! -f "$CONFIG_TXT" ] && CONFIG_TXT="/boot/config.txt"

if [ ! -f "$CONFIG_TXT" ]; then
    echo "[ERROR] No se localizó el archivo de configuración de arranque (config.txt)."
    exit 1
fi

echo "[INFO] Archivo de configuración detectado: $CONFIG_TXT"

echo ""
echo "Seleccione el tipo de sensor de sus cámaras CSI:"
echo "  1) OV5647 (Estándar 5MP / Gran Angular / Visión Infrarroja)"
echo "  2) IMX219 (Cámara V2 oficial de 8MP)"
echo "  3) IMX708 (Cámara V3 oficial de 12MP / Autofocus)"
echo "  4) IMX477 (Cámara HQ oficial de 12.3MP con montura C/CS)"
echo "  5) Arducam 64MP / 16MP Autofocus"
echo ""
read -p "Opción [1-5] (Por defecto 1 - OV5647): " opt
opt=${opt:-1}

OVERLAY_NAME="ov5647"
case $opt in
    1) OVERLAY_NAME="ov5647";;
    2) OVERLAY_NAME="imx219";;
    3) OVERLAY_NAME="imx708";;
    4) OVERLAY_NAME="imx477";;
    5) OVERLAY_NAME="arducam-64mp";;
    *) OVERLAY_NAME="ov5647";;
esac

echo "[INFO] Aplicando overlay '$OVERLAY_NAME' para puertos CAM0 y CAM1..."

# Crear copia de seguridad
sudo cp "$CONFIG_TXT" "$CONFIG_TXT.backup_sifma_$(date +%Y%m%d_%H%M%S)"

# Limpiar posibles entradas previas
sudo sed -i '/camera_auto_detect/d' "$CONFIG_TXT"
sudo sed -i "/dtoverlay=$OVERLAY_NAME/d" "$CONFIG_TXT"

# Añadir configuración limpia de hardware dual
echo "" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "# ====================================================================" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "# SIFMA - Configuración de Cámaras Duales CSI ($OVERLAY_NAME)" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "camera_auto_detect=0" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "dtoverlay=$OVERLAY_NAME,cam0" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "dtoverlay=$OVERLAY_NAME,cam1" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "# ====================================================================" | sudo tee -a "$CONFIG_TXT" >/dev/null

echo ""
echo "================================================================================"
echo "[ÉXITO] Configuración de hardware aplicada correctamente."
echo "Para que el firmware del GPU reconozca ambos puertos CSI, debe reiniciar el equipo:"
echo "  sudo reboot"
echo "================================================================================"

