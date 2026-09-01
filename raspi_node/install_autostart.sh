#!/bin/bash
# ====================================================================
# Script de Instalación del Servicio de Autoarranque SIFMA Raspberry Pi
# ====================================================================

echo "======================================================="
echo "Instalando servicio de autoarranque SIFMA para Raspberry Pi"
echo "======================================================="

# Obtener directorio actual del script
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CURRENT_USER=$(logname || echo $USER)

echo "Usuario detectado: $CURRENT_USER"
echo "Directorio de trabajo: $CURRENT_DIR"

# 1. Crear archivo de servicio temporal con las rutas absolutas correctas
SERVICE_FILE="/etc/systemd/system/sifma-capture.service"

cat <<EOF > /tmp/sifma-capture.service
[Unit]
Description=Servicio de Captura Fotografica Autonoma SIFMA
After=local-fs.target time-sync.target
Wants=local-fs.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/main_capture.py --boot-delay 15
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 2. Mover el servicio a systemd con permisos de superusuario
echo "Copiando archivo a /etc/systemd/system/sifma-capture.service..."
sudo cp /tmp/sifma-capture.service $SERVICE_FILE
sudo chmod 644 $SERVICE_FILE

# 3. Recargar el demonio de systemd y habilitar el servicio en el arranque
echo "Habilitando servicio en systemd..."
sudo systemctl daemon-reload
sudo systemctl enable sifma-capture.service

echo ""
echo "======================================================="
echo "Instalacion completada con exito."
echo "El script se ejecutara automaticamente cada vez que la Raspberry Pi se encienda."
echo ""
echo "Comandos utiles:"
echo "  - Iniciar manualmente: sudo systemctl start sifma-capture"
echo "  - Ver estado:          sudo systemctl status sifma-capture"
echo "  - Ver logs en vivo:    journalctl -u sifma-capture -f"
echo "======================================================="
