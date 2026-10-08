#!/bin/bash
# ====================================================================
# Script de Habilitacion de Camaras Duales Arducam en Raspberry Pi 5
# Configura los puertos flexores CAM/DISP 0 y CAM/DISP 1
# ====================================================================

echo "======================================================="
echo "Configurando Camaras Duales CSI en Raspberry Pi 5"
echo "======================================================="

CONFIG_TXT="/boot/firmware/config.txt"
[ ! -f "$CONFIG_TXT" ] && CONFIG_TXT="/boot/config.txt"

echo "Archivo de configuracion detectado: $CONFIG_TXT"

# Preguntar o detectar tipo de sensor Arducam
echo ""
echo "Selecciona el sensor de tus camaras Arducam:"
echo "1) OV5647 (Camara V1 de 5MP / Vision Nocturna / Estandar)"
echo "2) IMX219 (Camara V2 de 8MP)"
echo "3) IMX708 (Camara V3 de 12MP / Autofocus)"
echo "4) IMX477 (Camara de Alta Calidad HQ de 12.3MP)"
echo "5) Arducam 64MP / 16MP Autofocus"
echo ""
read -p "Opcion [1-5] (Por defecto 1 - OV5647): " opt
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

echo ""
echo "Aplicando configuracion para sensor: $OVERLAY_NAME en CAM/DISP 0 y CAM/DISP 1..."

# Respaldar config.txt
sudo cp "$CONFIG_TXT" "$CONFIG_TXT.backup_sifma"

# Limpiar posibles lineas previas para evitar duplicados
sudo sed -i '/camera_auto_detect/d' "$CONFIG_TXT"
sudo sed -i "/dtoverlay=$OVERLAY_NAME/d" "$CONFIG_TXT"

# Agregar configuracion dual
echo "" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "# SIFMA - Configuracion Camaras Duales CSI (Arducam $OVERLAY_NAME)" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "camera_auto_detect=0" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "dtoverlay=$OVERLAY_NAME,cam0" | sudo tee -a "$CONFIG_TXT" >/dev/null
echo "dtoverlay=$OVERLAY_NAME,cam1" | sudo tee -a "$CONFIG_TXT" >/dev/null

echo ""
echo "======================================================="
echo "Configuracion completada exitosamente en $CONFIG_TXT."
echo "Para que el kernel reconozca la Camara 1 en CAM/DISP 1,"
echo "es necesario REINICIAR la Raspberry Pi ahora."
echo ""
echo "Comando para reiniciar: sudo reboot"
echo "======================================================="
