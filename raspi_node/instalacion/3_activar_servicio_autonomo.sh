#!/bin/bash
# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

# ====================================================================
# PASO 3: Registro de Servicio Autónomo systemd y Accesos de Escritorio
# ====================================================================

set -e

echo "================================================================================"
echo "SIFMA — PASO 3: REGISTRO DE SERVICIO Y ACCESOS DIRECTOS"
echo "================================================================================"

NODE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
CURRENT_USER=$(logname 2>/dev/null || echo "$USER")

echo "[INFO] Usuario del sistema: $CURRENT_USER"
echo "[INFO] Directorio base del nodo: $NODE_DIR"

# 1. Configurar servicio systemd para captura autónoma en segundo plano
SERVICE_FILE="/etc/systemd/system/sifma-capture.service"

echo "[INFO] Creando definición de servicio systemd en $SERVICE_FILE..."
cat <<EOF | sudo tee "$SERVICE_FILE" >/dev/null
[Unit]
Description=Servicio de Captura Fotografica Autonoma SIFMA (Lite)
After=local-fs.target time-sync.target
Wants=local-fs.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$NODE_DIR
ExecStart=/usr/bin/python3 $NODE_DIR/main_capture.py --daemon
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 "$SERVICE_FILE"

# 2. Configurar accesos directos en el Escritorio (Desktop o Escritorio)
DESKTOP_DIRS=(
    "/home/$CURRENT_USER/Desktop"
    "/home/$CURRENT_USER/Escritorio"
)

for DDIR in "${DESKTOP_DIRS[@]}"; do
    if [ -d "$DDIR" ]; then
        echo "[INFO] Instalando accesos directos en $DDIR..."
        
        # SIFMA Control Táctil Lite
        cat <<EOF > "$DDIR/SIFMA_Control.desktop"
[Desktop Entry]
Name=SIFMA Control Táctil Lite
Comment=Panel de Control Nativo Ultraligero para Pantalla LCD DSI
Exec=/usr/bin/python3 $NODE_DIR/panel_touch_lite.py
Icon=camera-photo
Terminal=false
Type=Application
Categories=Utility;Application;
StartupNotify=true
EOF
        chmod +x "$DDIR/SIFMA_Control.desktop"

        # SIFMA Calibración de Cámaras CSI
        cat <<EOF > "$DDIR/SIFMA_Calibracion.desktop"
[Desktop Entry]
Name=SIFMA Calibración de Cámaras CSI
Comment=Herramienta de Enfoque en Tiempo Real y Alineación de Cámaras Arducam
Exec=/usr/bin/python3 $NODE_DIR/calibrate_cameras.py
Icon=camera-video
Terminal=false
Type=Application
Categories=Utility;Application;
StartupNotify=true
EOF
        chmod +x "$DDIR/SIFMA_Calibracion.desktop"
    fi
done

# 3. Recargar systemd y arrancar el servicio
echo "[INFO] Habilitando e iniciando servicio sifma-capture..."
sudo systemctl daemon-reload
sudo systemctl enable sifma-capture.service
sudo systemctl restart sifma-capture.service

echo ""
echo "================================================================================"
echo "[ÉXITO] Nodo SIFMA desplegado y activo."
echo ""
echo "Comandos útiles de verificación:"
echo "  - Estado del servicio:   sudo systemctl status sifma-capture"
echo "  - Monitoreo en vivo:     journalctl -u sifma-capture -f"
echo "  - Muestreo manual:       python3 $NODE_DIR/main_capture.py --now"
echo "  - Iniciar panel táctil:  python3 $NODE_DIR/panel_touch_lite.py"
echo "================================================================================"

