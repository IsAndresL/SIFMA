# SIFMA — Plan Maestro de Migración a Aplicación de Escritorio Híbrida (Rust + Python)

**Proyecto:** SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola  
**Versión de Destino:** SIFMA Desktop 2.0.0 (Híbrido Rust/Tauri 2.0 + Motor Científico Python)  
**Fecha:** Noviembre de 2026  
**Rama de Trabajo:** `migracion-a-rust`  
**Autores:** Andrés Felipe Luna Camargo y Cristian David Peña Martínez  

---

## 1. Justificación y Visión Arquitectónica

### 1.1 Objetivo del Cambio
Evolucionar el sistema central actual (`local_server`), que opera como un servidor web Flask dependiente de navegadores externos y entornos virtuales pesados, hacia una **aplicación de escritorio nativa, moderna, ultraligera y de alto rendimiento**, distribuible mediante un único instalador `.msi` para Windows.

### 1.2 Por qué Arquitectura Híbrida (Rust + Python)
1. **Rust (Tauri 2.0) en el Núcleo de Escritorio:**
   - Control de la ventana nativa del sistema operativo mediante WebView2 sin sobrecosto de Chromium embebido (consumo de RAM de ~40-60 MB frente a los ~350 MB actuales).
   - Gestión multihilo asíncrona y segura para la adquisición de telemetría por puerto serie COM (`serialport-rs`), garantizando cero pérdidas de datos.
   - Motor de persistencia SQLite ultrarrápido y seguro (`rusqlite` / `sqlx`) con transacciones ACID directas y tiempos de respuesta en microsegundos.
   - Cálculos estadísticos y matrices de correlación de Pearson ejecutados a velocidad nativa de CPU.
2. **Python en el Motor Científico e Inteligencia Artificial:**
   - Preservación inmediata del pipeline validado de visión por computadora (`cv2`, NumPy, filtros $ExG$, Sobel, HSV/LAB).
   - **Preparación directa para la siguiente fase de Machine Learning:** Facilita la incorporación futura de modelos entrenados de Deep Learning (PyTorch, ONNX Runtime, YOLOv8/v11 para detección de frutos o clasificadores de patologías foliares) sin tener que reinventar las librerías científicas en Rust.
   - Comunicación de baja latencia entre Rust y Python mediante un protocolo estructurado JSON-RPC a través de canales estándar (`stdin`/`stdout`) o sockets de dominio local.

---

## 2. Reglas Estrictas de Diseño y Código

Para erradicar la deuda técnica y el código monolítico:

1. **Límite de Tamaño de Archivo:** Ningún archivo de código fuente (Rust, Python, JS o CSS) superará las **300 a 400 líneas de código**. Si un módulo tiende a crecer, debe fragmentarse en submódulos de responsabilidad única (Single Responsibility Principle).
2. **Cero Monolitos en la Interfaz (Separación Estricta de Recursos):**
   - **Prohibido** incrustar bloques `<style>` extensos dentro de archivos HTML.
   - **Prohibido** incrustar bloques `<script>` extensos dentro de archivos HTML.
   - Toda funcionalidad de la interfaz tendrá su carpeta modular con sus tres archivos independientes: `[modulo].html`, `[modulo].css` y `[modulo].js`.
3. **Arquitectura Limpia en Rust (DDD / Hexagonal):**
   - Dominio desacoplado de la persistencia y de la interfaz gráfica.
   - Interfaces abstractas (Traits) para repositorios y controladores de hardware.
4. **Pruebas Automatizadas de No Regresión:**
   - Toda fórmula matemática (Pearson, media, varianza, $ExG$) debe contar con pruebas unitarias en Rust y validarse contra las salidas conocidas de Python con discrepancia de 0.0%.

---

## 3. Estructura de Carpetas Propuesta

```text
SIFMA/
├── desktop_app/                       # Aplicación de escritorio principal
│   ├── src-tauri/                     # NÚCLEO NATIVO EN RUST (Tauri 2.0)
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json
│   │   └── src/
│   │       ├── main.rs                # Punto de entrada mínimo (~40 líneas)
│   │       ├── lib.rs                 # Inicialización de plugins y runtime
│   │       ├── domain/                # ENTIDADES PURAS Y MODELOS DE NEGOCIO
│   │       │   ├── mod.rs
│   │       │   ├── crop_profile.rs    # Perfil botánico y umbrales de especie
│   │       │   ├── sensor_reading.rs  # Lecturas fisicoquímicas y ambientales
│   │       │   ├── capture_session.rs # Registro de lotes y fotografías
│   │       │   ├── biometric_metric.rs# Métricas morfométricas (área, altura, tallo)
│   │       │   ├── user.rs            # Usuario, roles RBAC y autenticación
│   │       │   └── audit_log.rs       # Trazabilidad y eventos del sistema
│   │       ├── infrastructure/        # ADAPTADORES DE INFRAESTRUCTURA
│   │       │   ├── mod.rs
│   │       │   ├── db/                # Persistencia SQLite con rusqlite
│   │       │   │   ├── connection.rs  # Pool de conexiones SQLite WAL
│   │       │   │   ├── schema.rs      # DDL y migraciones de esquemas
│   │       │   │   ├── seed.rs        # Sembrado de datos iniciales
│   │       │   │   └── repositories/  # Un repositorio por entidad (<180 líneas c/u)
│   │       │   │       ├── crop_repo.rs
│   │       │   │       ├── sensor_repo.rs
│   │       │   │       ├── session_repo.rs
│   │       │   │       ├── biometric_repo.rs
│   │       │   │       └── user_repo.rs
│   │       ├── serial/            # Conexión asíncrona con hardware sensor
│   │       │   ├── reader.rs      # Bucle continuo de lectura
│   │       │   ├── parser.rs      # Decodificación de tramas ($pH...#)
│   │       │   └── ports.rs       # Enumeración de puertos COM disponibles
│   │       └── sidecar/           # Orquestador del motor Python
│   │           ├── runner.rs      # Control del ciclo de vida del subproceso
│   │           ├── protocol.rs    # Serialización y tipado de peticiones IPC
│   │           └── health.rs      # Supervisión y recuperación de caídas
│   │       ├── application/           # CASOS DE USO Y SERVICIOS
│   │       │   ├── mod.rs
│   │       │   ├── telemetry_service.rs
│   │       │   ├── analytics_service.rs # Cálculo de Pearson y estadísticas en Rust
│   │       │   ├── session_service.rs
│   │       │   └── auth_service.rs
│   │       └── commands/              # CONTROLADORES IPC (INICIALIZADOS POR TAURI)
│   │           ├── mod.rs
│   │           ├── telemetry_cmd.rs   # Invocado desde JS para telemetría
│   │           ├── session_cmd.rs     # Invocado desde JS para lotes y fotos
│   │           ├── analytics_cmd.rs   # Invocado desde JS para correlaciones
│   │           ├── config_cmd.rs      # Invocado desde JS para parámetros
│   │           └── auth_cmd.rs        # Invocado desde JS para inicio de sesión
│   │
│   ├── frontend/                      # INTERFAZ MODULAR (SEPARACIÓN ESTRICTA HTML/CSS/JS)
│   │   ├── core/                      # Estilos globales, layout base y librerías
│   │   │   ├── styles/
│   │   │   │   ├── reset.css          # Normalización de caja
│   │   │   │   ├── variables.css      # Colores institucionales (#0f172a, #059669)
│   │   │   │   ├── typography.css     # Fuentes: Philosopher, Literata, Inter, JetBrains Mono
│   │   │   │   └── layout.css         # Sidebar maestro, contenedor principal y grid
│   │   │   ├── scripts/
│   │   │   │   ├── tauri_bridge.js    # Envoltorio seguro para invoke() de Tauri
│   │   │   │   ├── navigation.js      # Enrutador dinámico SPA sin recarga de página
│   │   │   │   └── notifications.js   # Sistema de alertas no intrusivas
│   │   │   └── vendor/
│   │   │       └── chart.umd.min.js   # Chart.js local (sin dependencias de CDN)
│   │   │
│   │   └── modules/                   # MÓDULOS VERTICALES POR FUNCIONALIDAD
│   │       ├── dashboard/
│   │       │   ├── dashboard.html     # Estructura semántica pura
│   │       │   ├── dashboard.css      # Estilos locales de tarjetas KPI
│   │       │   └── dashboard.js       # Lógica y actualización de gráficos
│   │       ├── calendar/
│   │       │   ├── calendar.html
│   │       │   ├── calendar.css
│   │       │   └── calendar.js
│   │       ├── vision_processing/
│   │       │   ├── vision_processing.html
│   │       │   ├── vision_processing.css
│   │       │   └── vision_processing.js
│   │       ├── gallery/
│   │       │   ├── gallery.html
│   │       │   ├── gallery.css
│   │       │   └── gallery.js
│   │       ├── timelapse/
│   │       │   ├── timelapse.html
│   │       │   ├── timelapse.css
│   │       │   └── timelapse.js
│   │       ├── telemetry_sensors/
│   │       │   ├── telemetry_sensors.html
│   │       │   ├── telemetry_sensors.css
│   │       │   └── telemetry_sensors.js
│   │       ├── cross_analysis/
│   │       │   ├── cross_analysis.html
│   │       │   ├── cross_analysis.css
│   │       │   └── cross_analysis.js
│   │       ├── scientific_dossier/
│   │       │   ├── scientific_dossier.html
│   │       │   ├── scientific_dossier.css
│   │       │   └── scientific_dossier.js
│   │       ├── crop_config/
│   │       │   ├── crop_config.html
│   │       │   ├── crop_config.css
│   │       │   └── crop_config.js
│   │       ├── user_management/
│   │       │   ├── user_management.html
│   │       │   ├── user_management.css
│   │       │   └── user_management.js
│   │       ├── audit_logs/
│   │       │   ├── audit_logs.html
│   │       │   ├── audit_logs.css
│   │       │   └── audit_logs.js
│   │       └── system_info/
│   │           ├── system_info.html
│   │           ├── system_info.css
│   │           └── system_info.js
│   │
│   └── python_engine/                 # MOTOR CIENTÍFICO Y MACHINE LEARNING (SIDECAR)
│       ├── engine_main.py             # Despachador de tareas JSON-RPC por stdin/stdout
│       ├── requirements.txt           # opencv, numpy, pillow (+ pytorch/onnx a futuro)
│       ├── core/
│       │   ├── config.py
│       │   └── protocol.py            # Deserializador seguro de peticiones IPC
│       ├── vision/                    # Pipeline actual descompuesto en micro-módulos
│       │   ├── exg_filter.py          # Cálculo del índice ExG (2G - R - B)
│       │   ├── color_segmentation.py  # Filtros HSV y CIELAB canal A
│       │   ├── morphological.py       # Aperturas, contornos y centroides
│       │   ├── basket_detector.py     # Localización de maceta azul y ROI
│       │   ├── stem_measurement.py    # Convolución horizontal Sobel y diámetro
│       │   └── height_measurement.py  # Distancia vertical basal-apical
│       └── ml_models/                 # PREPARADO PARA MODELOS ENTRENADOS DE IA
│           ├── __init__.py
│           ├── base_model.py          # Interfaz abstracta para inferencia de modelos
│           ├── yolo_fruit_detector.py # Inferencia para conteo de frutos / flores
│           ├── leaf_disease_classifier.py # Clasificación patológica / clorosis
│           └── weights/               # Pesos entrenados (.onnx, .pt, .tflite)
```

---

## 4. Fases de Ejecución Detalladas y Criterios de Aceptación

### Fase 1: Andamiaje de Tauri 2.0, Frontend Modular y Persistencia en Rust
**Objetivo:** Crear la aplicación de escritorio ejecutable, configurar el layout modular base y portar el motor relacional de base de datos a Rust.
- Tareas:
  1. Inicializar `desktop_app` con Tauri 2.0 (`tauri.conf.json`).
  2. Construir layout base en `frontend/core/` (reset, variables, typography, enrutador SPA sin recarga).
  3. Migrar las 3 primeras vistas: `dashboard/`, `user_management/`, `system_info/` separando estrictamente `.html`, `.css` y `.js`.
  4. Implementar base de datos SQLite en modo WAL con `rusqlite` en Rust (8 tablas + seed automático).
  5. Conectar comandos IPC iniciales (`auth_cmd.rs`, `config_cmd.rs`).
- Criterios de Aceptación:
  - `cargo test`: pruebas unitarias de persistencia y DDL en memoria exitosas.
  - `cargo tauri dev`: arranque en ventana nativa en < 300 ms, login funcional y dashboard renderizado sin errores.

---

### Fase 2: Integración del Motor Científico Python (Sidecar IPC)
**Objetivo:** Conectar el núcleo en Rust con el pipeline de visión de Python de forma no bloqueante y modular.
- Tareas:
  1. Desarrollar el orquestador en Rust (`infrastructure/sidecar/runner.rs`) con supervisión y canal JSON-RPC.
  2. Descomponer el pipeline de visión de Python en archivos atómicos < 150 líneas (`exg_filter.py`, `color_segmentation.py`, `stem_measurement.py`).
  3. Migrar las vistas: `vision_processing/`, `gallery/`, `timelapse/` en su tríada modular (`.html`, `.css`, `.js`).
- Criterios de Aceptación:
  - Procesamiento de lote fotográfico de prueba desde Tauri.
  - Verificación de no regresión del 100% frente a las métricas del pipeline previo ($cm^2$, salud %, altura, diámetro).

---

### Fase 3: Telemetría Serial Nativa en Rust y Analítica de Pearson
**Objetivo:** Adquisición de hardware y análisis matemático ejecutados a velocidad nativa en Rust.
- Tareas:
  1. Driver serie asíncrono con `serialport-rs` y parser de tramas `$pH,EC...#`.
  2. Módulo de cálculo estadístico en Rust (`analytics_service.rs`): correlación de Pearson ($r$), media, varianza, IQR y CV%.
  3. Migrar las vistas: `telemetry_sensors/`, `cross_analysis/` en su estructura de tres archivos.
- Criterios de Aceptación:
  - Recepción de 10.000 tramas seriales simuladas sin caída ni fugas de memoria.
  - Pearson en Rust comparado contra `numpy.corrcoef` con diferencia $< 10^{-6}$.

---

### Fase 4: Dossier Científico, Firmas y Arquitectura para Machine Learning
**Objetivo:** Generación de reportes y preparación del motor de IA para futuros modelos entrenados.
- Tareas:
  1. Migrar módulo `scientific_dossier/` (`.html`, `.css`, `.js`).
  2. Implementar generación nativa de reportes en PDF desde el backend de Rust.
  3. Estructurar la capa `python_engine/ml_models/` con la interfaz abstracta `BaseCropModel` y soporte para inferencia ultraligera con ONNX Runtime.
- Criterios de Aceptación:
  - Generación de informe PDF con firma táctil digitalizada.
  - Prueba de inferencia de modelo simulado (mock) mediante protocolo IPC en < 50 ms.

---

### Fase 5: Auditoría de Código, Pruebas de Estrés y Empaquetado Final
**Objetivo:** Auditar calidad de código y compilar el instalador oficial.
- Tareas:
  1. Auditoría automática: validar que ningún archivo exceda 350-400 líneas y cero estilos/scripts incrustados en HTML.
  2. Benchmark comparativo de rendimiento frente a la versión previa de Flask.
  3. Compilación del instalador oficial `.msi` / `.exe` de Windows (`cargo tauri build`).
- Criterios de Aceptación:
  - Instalador ejecutable autónomo sin requerir instalación manual de Python en el sistema anfitrión.
  - Memoria RAM en reposo $\le 65$ MB; tiempo de inicio $\le 300$ ms.

