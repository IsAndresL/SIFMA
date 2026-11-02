# SIFMA — Nodo Embebido de Captura en Campo (Raspberry Pi 5)

Este directorio contiene la totalidad del software autónomo diseñado para operar en la computadora de placa reducida (SBC) **Raspberry Pi 5**, encargada del fenotipado foliar no destructivo y la adquisición periódica de imágenes en torres hidropónicas verticales.

---

## 1. Requisitos de Hardware del Nodo

1. **Placa Principal:** Raspberry Pi 5 (2 GB, 4 GB u 8 GB de memoria RAM).
2. **Cámaras Digitales CSI:** Dos cámaras de alta resolución conectadas a los puertos flexores nativos de la Raspberry Pi 5:
   - **Puerto `CAM/DISP 0`:** Cámara Cenital (orientación perpendicular superior al dosel vegetal).
   - **Puerto `CAM/DISP 1`:** Cámara Lateral (orientación ortogonal a la base del tallo).
   - Sensores soportados: Omnivision OV5647 (5 MP), Sony IMX219 (8 MP), Sony IMX708 (12 MP autofocus), Sony IMX477 (12.3 MP HQ).
3. **Pantalla de Operador:** Pantalla táctil oficial Raspberry Pi Touch Display (interfaz DSI) o monitor HDMI de servicio.
4. **Almacenamiento Local:** Memoria masiva USB extraíble formateada en FAT32, exFAT o NTFS, rotulada para el sistema.

---

## 2. Estructura de Directorios del Nodo

```text
raspi_node/
├── instalacion/
│   ├── 1_configurar_camaras_dual.sh       Habilita puertos CSI 0 y 1 en el firmware de arranque
│   ├── 2_instalar_dependencias.sh         Instala librerías APT del sistema y dependencias Python
│   ├── 3_activar_servicio_autonomo.sh     Registra servicio systemd y accesos directos de escritorio
│   └── instalar_todo.sh                   Script maestro de instalación guiada integral
├── services/
│   ├── camera_service.py                  Abstracción multi-backend (Picamera2, libcamera, OpenCV)
│   ├── storage_service.py                 Gestión de montajes USB y escrituras con POSIX sync
│   └── __init__.py                        Inicializador del paquete de servicios
├── desktop/
│   ├── SIFMA_Calibracion.desktop          Plantilla de acceso directo para calibrador óptico
│   └── SIFMA_Control.desktop              Plantilla de acceso directo para panel táctil
├── main_capture.py                        Motor autónomo de captura periódica (demonio del sistema)
├── calibrate_cameras.py                   Herramienta gráfica para enfoque óptico en tiempo real
├── panel_touch_lite.py                    Panel de control táctil de bajo consumo (< 15 MB RAM)
├── config.json                            Archivo de configuración de horarios y parámetros
├── dependencies.py                        Verificador e instalador dinámico de dependencias
├── requirements.txt                       Lista de dependencias Python para Raspberry Pi OS
└── README.md                              Este documento técnico de operación
```

---

## 3. Guía de Instalación Paso a Paso

Abra una terminal en la Raspberry Pi e ingrese al directorio del nodo:

```bash
cd ~/raspi_node
```

### Opción A: Instalación Automática Integral (Recomendada)

Ejecute el script unificado:

```bash
bash instalacion/instalar_todo.sh
```

### Opción B: Instalación Modular por Pasos

#### Paso 1: Configurar Puertos de Hardware para Cámaras Duales
```bash
bash instalacion/1_configurar_camaras_dual.sh
sudo reboot
```
*Este paso modifica `/boot/firmware/config.txt` para asignar los overlays del sensor a ambos puertos CSI. Requiere reiniciar el equipo.*

#### Paso 2: Instalar Paquetes del Sistema y Dependencias Python
```bash
bash instalacion/2_instalar_dependencias.sh
```
*Instala las librerías base de Linux (`python3-picamera2`, `libcamera-apps`, `python3-tk`, `python3-pil`) y los paquetes declarados en `requirements.txt`.*

#### Paso 3: Registrar Servicio Autónomo y Accesos Directos
```bash
bash instalacion/3_activar_servicio_autonomo.sh
```
*Configura el servicio `sifma-capture.service` en `/etc/systemd/system/` para arranque desatendido al encender la torre, y crea los lanzadores en el Escritorio del usuario.*

---

## 4. Procedimientos de Operación de Campo

### 4.1 Calibración y Enfoque Óptico de Cámaras
1. Haga doble clic en el acceso directo **"SIFMA Calibración de Cámaras CSI"** del Escritorio, o ejecute:
   ```bash
   python3 calibrate_cameras.py
   ```
2. La interfaz desplegará el video en vivo de ambas cámaras a 30 FPS.
3. Ajuste manualmente el anillo de enfoque del lente de cada cámara hasta maximizar la nitidez de la canastilla central y las nervaduras foliares.
4. Verifique que la cámara cenital cubra la totalidad del perímetro de la maceta y que la cámara lateral encuadre la línea basal del sustrato.
5. Cierre la ventana de calibración al terminar.

### 4.2 Operación con el Panel de Control Táctil
1. Haga doble clic en el acceso directo **"SIFMA Control Táctil Lite"** del Escritorio, o ejecute:
   ```bash
   python3 panel_touch_lite.py
   ```
2. La interfaz táctil permite al operador de campo:
   - Visualizar el estado del demonio autónomo (activo, en espera o en captura).
   - Ver la fecha y hora programada para el siguiente muestreo fotográfico.
   - Ejecutar una toma manual inmediata mediante el botón **"Captura Manual"**.
   - Cambiar la canastilla o estrato en evaluación (Nivel 1 Base a Nivel 4 Cúspide).
   - Verificar el espacio disponible en la memoria USB conectada.

### 4.3 Captura Autónoma y Estructura en Memoria USB
El demonio `main_capture.py` opera de forma invisible en segundo plano:
1. Al encender la torre hidropónica, espera un retardo de arranque seguro (`boot_delay_sec: 10`) para estabilización de voltajes.
2. Comprueba la presencia de una memoria USB montada en `/media/` o `/mnt/`.
3. Según la configuración (`config.json`), toma lotes fotográficos sincronizados en las franjas horarias programadas (por defecto: 07:05, 12:05 y 17:05).
4. Guarda las imágenes en la estructura estándar de directorios:
   ```text
   USB_DRIVE/
   └── SIFMA_CAPTURES/
       └── YYYY-MM-DD/
           ├── plant1_2026-11-02_07-05-00_cenital_01.jpg
           ├── plant1_2026-11-02_07-05-00_lateral_01.jpg
           ├── plant1_2026-11-02_07-05-00_cenital_02.jpg
           └── plant1_2026-11-02_07-05-00_lateral_02.jpg
   ```
5. Realiza una llamada `os.sync()` a nivel de kernel para asegurar que los búferes de escritura en memoria flash se vacíen físicamente antes de que el operador retire la memoria USB.

---

## 5. Comandos de Diagnóstico y Mantenimiento

- **Consultar estado del demonio del sistema:**
  ```bash
  sudo systemctl status sifma-capture
  ```
- **Monitorear el registro de eventos en tiempo real:**
  ```bash
  journalctl -u sifma-capture -f
  ```
- **Forzar un ciclo de captura manual de prueba:**
  ```bash
  python3 main_capture.py --now
  ```
- **Reiniciar el servicio de captura tras cambiar `config.json`:**
  ```bash
  sudo systemctl restart sifma-capture
  ```
