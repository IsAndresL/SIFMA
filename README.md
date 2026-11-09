# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental

**Versión:** 1.0.0  
**Año de desarrollo:** 2026  
**Autores (desarrolladores del código):** Andrés Felipe Luna Camargo y Cristian David Peña Martínez  
 

---

## 1. Descripción General del Software

SIFMA (Sistema Integral de Fenotipado y Monitoreo Ambiental) es una plataforma computacional diseñada para la captura no destructiva, análisis biométrico por visión artificial y telemetría microclimática multivariable en torres hidropónicas verticales. El sistema procesa pares de imágenes (cenitales y laterales) mediante un pipeline de visión en espacios de color HSV, LAB y ExG para cuantificar el área foliar fotosintéticamente activa, la altura de planta, el diámetro del tallo basal y el índice de salud foliar, correlacionando dichos parámetros con ocho variables fisicoquímicas y ambientales adquiridas por sensores en tiempo real.

---

## 2. Requisitos del Sistema

### 2.1 Servidor Local de Procesamiento y Dashboard Web
- **Sistema Operativo:** Microsoft Windows 10 o Windows 11 (64 bits) / Linux Ubuntu 22.04 LTS o superior.
- **Intérprete:** Python 3.10, 3.11, 3.12 o 3.13 de 64 bits.
- **Memoria RAM:** Mínimo 4 GB (recomendado 8 GB).
- **Almacenamiento:** Mínimo 500 MB libres para entorno virtual y dependencias.
- **Navegador Web:** Google Chrome, Microsoft Edge, Mozilla Firefox o compatible con HTML5 y WebGL.

### 2.2 Nodo de Captura y Hardware en Campo (Opcional)
- **Placa de Computación:** Raspberry Pi 5 o Raspberry Pi 4 Model B (2 GB RAM mínimo).
- **Sistema Operativo:** Raspberry Pi OS (Bookworm de 64 bits).
- **Óptica:** Módulo dual de cámara CSI (Cenital: gran angular 180°; Lateral: encuadre vertical de tallo).

---

## 3. Guía de Instalación Rápida y Puesta en Marcha (Windows)

El proyecto incluye un flujo de instalación asistido estructurado en tres carpetas numeradas dentro del directorio `instalacion/`:

### Paso 1: Instalación Automatizada de Dependencias
1. Abra la carpeta `instalacion/1_instalar_dependencias/`.
2. Haga doble clic sobre el archivo ejecutable:
   ```text
   Instalar_Dependencias.bat
   ```
3. El script verificará la presencia de Python en el sistema, creará el entorno virtual `.venv`, actualizará el gestor `pip` e instalará las librerías oficiales listadas en `local_server/requirements.txt`.

### Paso 2: Inicio del Servidor Local
1. Abra la carpeta `instalacion/2_iniciar_servidor/`.
2. Haga doble clic sobre el archivo ejecutable:
   ```text
   Iniciar_Servidor.bat
   ```
3. La consola activará el entorno virtual, iniciará el servidor Flask en `http://127.0.0.1:5000` y abrirá automáticamente la interfaz web en su navegador predeterminado.
4. Mantenga abierta la ventana de la consola mientras opere el sistema. Para detener el servidor, presione `Ctrl + C` en la consola.

### Paso 3: Creación de Acceso Directo en el Escritorio (Opcional)
1. Abra la carpeta `instalacion/3_crear_acceso_directo/`.
2. Haga doble clic sobre:
   ```text
   Crear_Acceso_Directo.bat
   ```
3. Se generará en su Escritorio un acceso directo llamado **"SIFMA - Servidor Local"** con el icono institucional del proyecto para iniciar la plataforma con un solo clic en sesiones futuras.

---

## 4. Despliegue en Raspberry Pi (Nodo de Campo)

Para configurar el nodo de captura autónomo en una Raspberry Pi:
1. Navegue al directorio `raspi_node/`.
2. Habilite las cámaras duales CSI ejecutando:
   ```bash
   bash configurar_camaras_dual.sh
   sudo reboot
   ```
3. Active el servicio de captura desatendida y los paneles táctiles ejecutando:
   ```bash
   bash install_autostart.sh
   ```
Consulte las instrucciones completas en [`raspi_node/README.md`](raspi_node/README.md).

---

## 5. Estructura del Repositorio

```text
SIFMA/
|-- instalacion/                     Flujo guiado de instalacion y arranque
|   |-- 1_instalar_dependencias/     Paso 1: Creacion de .venv e instalacion de librerias
|   |-- 2_iniciar_servidor/          Paso 2: Lanzamiento del servidor web y navegador
|   `-- 3_crear_acceso_directo/      Paso 3: Generador de acceso directo en el Escritorio
|-- local_server/                    Nucleo del servidor de procesamiento y dashboard
|   |-- application/                 Casos de uso y servicios de aplicacion
|   |-- core/                        Configuracion global, seguridad y registro
|   |-- domain/                      Modelos de dominio e interfaces abstractas
|   |-- infrastructure/              Base de datos SQLAlchemy, vision y telemetria
|   |-- presentation/                Controladores web (HTML) y endpoints API REST
|   |-- static/                      Hojas de estilo CSS, scripts JS y emblemas
|   |-- templates/                   Plantillas Jinja2 de la interfaz de usuario
|   |-- app.py                       Punto de entrada de la aplicacion Flask
|   `-- requirements.txt             Especificacion de dependencias verificadas
|-- raspi_node/                      Software embebido para Raspberry Pi 5
|   |-- services/                    Controladores de camara CSI y almacenamiento USB
|   |-- main_capture.py              Demonio de captura fotografica programada
|   |-- panel_touch_lite.py          Panel de control tactil para pantalla embebida
|   `-- calibrate_cameras.py         Herramienta de calibracion y enfoque en vivo
|-- docs/                            Documentacion tecnica y preparacion DNDA
|   |-- _trabajo/                    Evidencias, inventarios de limpieza y auditorias
|   |-- arquitectura/                Documento tecnico de arquitectura de software
|   |-- manual_usuario/              Manual formal de operacion con figuras
|   `-- registro_dnda/               Paquete documental y codigos para deposito
`-- README.md                        Documento de presentacion e introduccion general
```

---

## 6. Documentación Adicional

- **Manual de Usuario:** [`docs/manual_usuario/MANUAL_DE_USUARIO.md`](docs/manual_usuario/MANUAL_DE_USUARIO.md)
- **Documento Técnico de Arquitectura:** [`docs/arquitectura/DOCUMENTO_TECNICO.md`](docs/arquitectura/DOCUMENTO_TECNICO.md)
- **Inventario Técnico Inicial (Fase 0):** [`docs/_trabajo/inventario_inicial.md`](docs/_trabajo/inventario_inicial.md)
- **Informe de Limpieza de Comentarios (Fase 1):** [`docs/_trabajo/informe_comentarios.md`](docs/_trabajo/informe_comentarios.md)
- **Inventario de Limpieza de Dependencias (Fase 2):** [`docs/_trabajo/inventario_limpieza.md`](docs/_trabajo/inventario_limpieza.md)
