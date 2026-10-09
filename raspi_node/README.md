# 🍓 SIFMA - Nodo Raspberry Pi (Guía Rápida de Despliegue)

Este paquete contiene todo el software autónomo para la **Raspberry Pi 5** (captura fotográfica dual CSI, almacenamiento en USB y panel de control táctil).

---

## ⚡ Paso a Paso para Despliegue en la Raspberry Pi

### 1. Habilitar Cámaras Duales CSI (Solo la primera vez)
Si es la primera vez que conectas las dos cámaras CSI a los puertos `CAM/DISP 0` y `CAM/DISP 1`:
```bash
bash configurar_camaras_dual.sh
sudo reboot
```

### 2. Instalar y Activar Servicio Automático
Ejecuta el script de instalación una sola vez:
```bash
bash install_autostart.sh
```

---

## 📂 ¿Qué hace cada archivo?

| Archivo / Carpeta | Descripción |
| :--- | :--- |
| **`install_autostart.sh`** | Instalador único. Instala librerías, registra el servicio en segundo plano y crea los accesos en el escritorio. |
| **`configurar_camaras_dual.sh`** | Configura el `/boot/firmware/config.txt` para habilitar `CAM/DISP 0` y `CAM/DISP 1`. |
| **`config.json`** | Archivo de configuración con parámetros predeterminados (horarios, cantidad de fotos, especie de cultivo, etc.). |
| **`main_capture.py`** | Motor principal de captura autónoma. Corre como servicio invisible en segundo plano (`sifma-capture.service`). |
| **`calibrate_cameras.py`** | Herramienta con interfaz gráfica para enfocar lentes y alinear los ángulos de las cámaras en vivo. |
| **`panel_touch_lite.py`** | Panel de control táctil de ultra bajo consumo (<15 MB RAM) para operar con los dedos en la pantalla oficial de Raspberry. |
| **`panel_app.py`** | Panel web alternativo (Flask) por si se desea acceder desde el navegador local. |
| **`services/`** | Módulos internos para gestión de almacenamiento en USB y controladores de cámara (Picamera2, libcamera, OpenCV). |
| **`SIFMA_Calibracion.desktop`** | Acceso directo para el Escritorio (Calibrador). |
| **`SIFMA_Control.desktop`** | Acceso directo para el Escritorio (Panel Táctil). |

---

## 🛠️ Comandos de Mantenimiento Útiles

* **Ver estado del servicio automático:**
  ```bash
  sudo systemctl status sifma-capture
  ```
* **Ver logs de capturas en vivo:**
  ```bash
  journalctl -u sifma-capture -f
  ```
* **Hacer una captura manual de prueba:**
  ```bash
  python3 main_capture.py --now
  ```
