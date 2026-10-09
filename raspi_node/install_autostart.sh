#!/bin/bash
# ====================================================================
# Script de Instalacion SIFMA LITE en Raspberry Pi (Bajo Consumo)
# ====================================================================

echo "======================================================="
echo "Instalando servicio SIFMA LITE para Raspberry Pi (2GB RAM)"
echo "======================================================="

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CURRENT_USER=$(logname || echo $USER)

echo "Usuario detectado: $CURRENT_USER"
echo "Directorio de trabajo: $CURRENT_DIR"

# 1. Asegurar dependencias del sistema y Python (incluye Tkinter)
echo "Verificando paquetes del sistema..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-dev python3-venv python3-tk python3-pil python3-pil.imagetk python3-picamera2 rpicam-apps libcamera-apps

echo "Instalando dependencias de Python..."
pip3 install -r $CURRENT_DIR/requirements.txt --break-system-packages 2>/dev/null || pip3 install -r $CURRENT_DIR/requirements.txt

# 2. Configurar servicio del Demonio de Captura (sifma-capture.service)
CAPTURE_SERVICE="/etc/systemd/system/sifma-capture.service"
cat <<EOF > /tmp/sifma-capture.service
[Unit]
Description=Servicio de Captura Fotografica Autonoma SIFMA (Lite)
After=local-fs.target time-sync.target
Wants=local-fs.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/main_capture.py --daemon
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/sifma-capture.service $CAPTURE_SERVICE
sudo chmod 644 $CAPTURE_SERVICE

# 3. Crear accesos directos en el Escritorio para el Panel Táctil y el Calibrador de Cámaras
if [ -d "/home/$CURRENT_USER/Desktop" ]; then
    sed "s|/home/nodo1/raspi_node|$CURRENT_DIR|g" $CURRENT_DIR/SIFMA_Control.desktop > /home/$CURRENT_USER/Desktop/SIFMA_Control.desktop
    sed "s|/home/nodo1/raspi_node|$CURRENT_DIR|g" $CURRENT_DIR/SIFMA_Calibracion.desktop > /home/$CURRENT_USER/Desktop/SIFMA_Calibracion.desktop
    chmod +x /home/$CURRENT_USER/Desktop/SIFMA_Control.desktop
    chmod +x /home/$CURRENT_USER/Desktop/SIFMA_Calibracion.desktop
    echo "Accesos directos 'SIFMA Control' y 'SIFMA Calibracion' creados en el Escritorio con rutas adaptadas a $CURRENT_DIR."
fi

# 4. Habilitar e iniciar servicio de captura
echo "Habilitando servicio de captura en segundo plano..."
sudo systemctl daemon-reload
sudo systemctl enable sifma-capture.service
sudo systemctl restart sifma-capture.service

echo ""
echo "======================================================="
echo "Instalacion completada con exito."
echo "1. Demonio de captura activo en segundo plano (consumo casi 0% CPU)."
echo "2. Panel Tactil Nativo Lite listo en el Escritorio (Consumo < 15MB RAM)."
echo "   (Hacer doble clic en 'SIFMA Control Tactil Lite' para abrir la interfaz)"
echo ""
echo "Comandos utiles:"
echo "  - Abrir panel manual:  python3 $CURRENT_DIR/panel_touch_lite.py"
echo "  - Ver estado Captura:  sudo systemctl status sifma-capture"
echo "  - Ver logs en vivo:    journalctl -u sifma-capture -f"
echo "======================================================="
