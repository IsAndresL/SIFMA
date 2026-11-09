#!/bin/bash
# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

# ====================================================================
# INSTALADOR INTEGRAL: NODO DE CAPTURA RASPBERRY PI 5 (SIFMA)
# Ejecuta en secuencia:
#   1. Configuración de hardware de cámaras duales
#   2. Instalación de paquetes del sistema y librerías
#   3. Registro del demonio autónomo y accesos directos
# ====================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "================================================================================"
echo "SIFMA — INSTALACIÓN ASISTIDA DEL NODO EMBEBIDO EN CAMPO (RASPBERRY PI)"
echo "================================================================================"

echo ""
echo "[PASO 1 DE 3] Configuración de hardware de cámaras duales..."
bash "$SCRIPT_DIR/1_configurar_camaras_dual.sh"

echo ""
echo "[PASO 2 DE 3] Instalación de dependencias de software..."
bash "$SCRIPT_DIR/2_instalar_dependencias.sh"

echo ""
echo "[PASO 3 DE 3] Registro de servicio systemd y accesos de escritorio..."
bash "$SCRIPT_DIR/3_activar_servicio_autonomo.sh"

echo ""
echo "================================================================================"
echo "¡DESPLIEGUE FINALIZADO CON ÉXITO!"
echo "Recuerde reiniciar el equipo (sudo reboot) para aplicar la configuración CSI."
echo "================================================================================"

