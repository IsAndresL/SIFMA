# SIFMA - Nodo Raspberry Pi (Guia Rapida de Despliegue)

Este paquete contiene todo el software autonomo para la **Raspberry Pi 5** (captura fotografica dual CSI, almacenamiento en USB y panel de control tactil).

---

## Paso a Paso para Despliegue en la Raspberry Pi

### 1. Habilitar Camaras Duales CSI (Solo la primera vez)
Si es la primera vez que conectas las dos camaras CSI a los puertos `CAM/DISP 0` y `CAM/DISP 1`:
```bash
bash configurar_camaras_dual.sh
sudo reboot
```

### 2. Instalar y Activar Servicio Automatico
Ejecuta el script de instalacion una sola vez:
```bash
bash install_autostart.sh
```

---

## Descripcion de Archivos del Nodo

| Archivo / Carpeta | Descripcion |
| :--- | :--- |
| **`install_autostart.sh`** | Instalador unico. Instala librerias, registra el servicio en segundo plano y crea los accesos en el escritorio. |
| **`configurar_camaras_dual.sh`** | Configura el `/boot/firmware/config.txt` para habilitar `CAM/DISP 0` y `CAM/DISP 1`. |
| **`config.json`** | Archivo de configuracion con parametros predeterminados (horarios, cantidad de fotos, especie de cultivo, etc.). |
| **`main_capture.py`** | Motor principal de captura autonoma. Corre como servicio invisible en segundo plano (`sifma-capture.service`). |
| **`calibrate_cameras.py`** | Herramienta con interfaz grafica para enfocar lentes y alinear los angulos de las camaras en vivo. |
| **`panel_touch_lite.py`** | Panel de control tactil de ultra bajo consumo (<15 MB RAM) para operar con los dedos en la pantalla oficial de Raspberry. |
| **`panel_app.py`** | Panel web alternativo (Flask) por si se desea acceder desde el navegador local. |
| **`services/`** | Modulos internos para gestion de almacenamiento en USB y controladores de camara (Picamera2, libcamera, OpenCV). |
| **`SIFMA_Calibracion.desktop`** | Acceso directo para el Escritorio (Calibrador). |
| **`SIFMA_Control.desktop`** | Acceso directo para el Escritorio (Panel Tactil). |

---

## Comandos de Mantenimiento Utiles

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
