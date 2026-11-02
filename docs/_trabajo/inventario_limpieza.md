# SIFMA — Inventario de Limpieza de Archivos y Dependencias (Fase 2)

**Fecha:** 2 de noviembre de 2026  
**Rama:** `preparacion-registro`  
**Autores (desarrolladores del código):** Andrés Felipe Luna Camargo y Cristian David Peña Martínez  
**Titular patrimonial:** `[POR DEFINIR]` (pendiente de formalización con la Universidad del Magdalena)  

---

## 1. Resumen de la Auditoría

En cumplimiento de las reglas operativas de la Fase 2, se realizó un análisis exhaustivo del grafo de dependencias de código, plantillas y archivos estáticos para identificar elementos huérfanos o en desuso producto de refactorizaciones previas hacia arquitectura limpia.

| Categoría | Total Auditados | En Uso Activo | Candidatos a Eliminación |
| :--- | :---: | :---: | :---: |
| **Plantillas HTML (`templates/`)** | 16 | 16 | 0 |
| **Módulos y Façades Legacy (`local_server/`)** | 9 | 0 | 9 |
| **Archivos en `static/img/`** | 10 | 3 | 2 (CSVs extraviados) + 5 (Variantes logo) |
| **Bases de datos en Git (`local_server/sifma.db`)** | 1 | 0 (Debe salir de Git) | 1 (Untrack en índice) |
| **Dependencias `requirements.txt`** | 14 | 8 | 6 infladas sin importación |

---

## 2. Detalle de Archivos Candidatos a Eliminación

### 2.1 Módulos y Façades de Compatibilidad en Desuso

Durante la evolución arquitectónica de SIFMA hacia capas desacopladas (Hexagonal / Clean Architecture), se implementaron las capas definitivas:
- `application/services/` (Casos de uso y orquestación)
- `domain/models/` (Entidades agrónomas y telemetría)
- `infrastructure/database/` (ORM y repositorios)
- `infrastructure/vision/` (Procesamiento de imágenes)
- `presentation/api/` y `presentation/web/` (Rutas y controladores)

Los módulos listados a continuación quedaron como meras fachadas re-exportadoras y **no reciben ninguna importación** desde el servidor en producción:

| Archivo | Motivo de No Uso | Comprobación Realizada | Acción |
| :--- | :--- | :--- | :---: |
| `local_server/database.py` | Façade legacy que re-exportaba `db` y modelos. Toda la aplicación importa directamente desde `infrastructure.database` y `domain.models`. | Búsqueda global de `import database` y `from database import`: **0 referencias**. | **Eliminar** |
| `local_server/blueprints/__init__.py` | Módulo legacy de empaquetado de blueprints. | Búsqueda global de `import blueprints`: **0 referencias**. | **Eliminar** |
| `local_server/blueprints/api_bp.py` | Façade legacy que re-exportaba `presentation.api`. | `app.py` importa directamente `presentation.api.api_bp`. **0 referencias**. | **Eliminar** |
| `local_server/blueprints/dashboard_bp.py` | Façade legacy que re-exportaba `presentation.web.dashboard_routes`. | `app.py` importa directamente `presentation.web.dashboard_bp`. **0 referencias**. | **Eliminar** |
| `local_server/services/__init__.py` | Módulo contenedor legacy de servicios. | Búsqueda global en `local_server`: **0 referencias**. | **Eliminar** |
| `local_server/services/analytics_service.py` | Clase estática envoltorio (`AnalyticsCrossService`) hacia `application.services.AnalyticsApplicationService`. | Búsqueda global de `AnalyticsCrossService`: **0 referencias**. | **Eliminar** |
| `local_server/services/batch_processor.py` | Façade legacy hacia `VisionApplicationService`. | Búsqueda global de `BatchProcessor`: **0 referencias**. | **Eliminar** |
| `local_server/services/db_service.py` | Façade legacy hacia repositorios SQLAlchemy. | Búsqueda global de `DatabaseService`: **0 referencias**. | **Eliminar** |
| `local_server/services/telemetry_service.py` | Façade legacy hacia `application.services.TelemetryApplicationService`. | Búsqueda global de importaciones en `local_server`: **0 referencias**. | **Eliminar** |

> [!NOTE]
> La carpeta `raspi_node/services/` (`camera_service.py`, `storage_service.py`) **se conserva íntegramente**, dado que es el núcleo activo del firmware del nodo Raspberry Pi y es importada por `main_capture.py` y los paneles táctiles.

---

### 2.2 Archivos Huérfanos en `static/img/`

| Archivo | Diagnóstico y Uso | Comprobación | Acción |
| :--- | :--- | :--- | :---: |
| `local_server/static/img/sifma_investigacion_canastilla_1.csv` | Archivo CSV de datos de investigación descargado/guardado erróneamente en el directorio de imágenes. | Sin referencias en templates ni código. | **Eliminar** |
| `local_server/static/img/telemetria_actualizada_2026-10-08.csv` | Archivo CSV de 1.682 filas guardado erróneamente en el directorio de imágenes. | Sin referencias en templates ni código. | **Eliminar** |
| `local_server/static/img/blanco con texo (1).svg` | Variante de logotipo con fondo blanco y tipografía antigua. | Sin referencias (todas las vistas usan `sifma_sin_texto.svg`). | **[DUDA: consultar titular]** |
| `local_server/static/img/sifma_con_texto.svg` | Variante de logotipo oficial horizontal con texto. | Sin referencias en plantillas activas. | **[DUDA: consultar titular]** |
| `local_server/static/img/sifma_logo.svg` | Variante vectorial cuadrada previa. | Sin referencias en plantillas activas. | **[DUDA: consultar titular]** |
| `local_server/static/img/sin texto blanco.svg` | Variante blanca monocromática para fondos oscuros. | Sin referencias en plantillas activas. | **[DUDA: consultar titular]** |
| `local_server/static/img/sifma_icon.png` | Versión PNG rasterizada del favicon. El acceso directo usa `sifma_icon.ico` y la web usa `sifma_sin_texto.svg`. | Sin referencias directas. | **[DUDA: consultar titular]** |

> [!IMPORTANT]
> Siguiendo la regla 4 de operación ("Las dudas se listan y se preguntan; no se borran"), las 5 variantes del logotipo **se conservan** intactas hasta que el titular decida si desea preservarlas como material gráfico complementario o descartarlas.

---

### 2.3 Tratamiento de la Base de Datos (`local_server/sifma.db`)

1. **Estado actual en Git:** Rastreado en el historial.
2. **Problema para el registro DNDA:** Una base de datos SQLite con datos de prueba o usuario local no debe depositarse como código fuente. El software debe ser capaz de autoinicializar su esquema en frío.
3. **Prueba de reproducibilidad realizada:**
   - Se ejecutó un arranque simulado en un archivo nuevo (`test_clean_bootstrap.db`).
   - Se verificó que `create_app()` ejecuta `db.create_all()` e `init_db_data(app)`.
   - Se crearon automáticamente las 8 tablas requeridas: `users`, `crop_profile`, `config`, `sensor_reading`, `capture_session`, `biometric_metric`, `agronomic_conclusion`, `audit_logs`.
   - Se sembró con éxito el Super Administrador y los 6 perfiles botánicos por defecto (`cebollin`, `lechuga`, `fresa`, `albahaca`, `espinaca`, `cilantro`).
4. **Acción:**
   - Desvincular del índice de Git: `git rm --cached local_server/sifma.db`.
   - Mantener el archivo físico local para no interrumpir el servidor en ejecución del usuario.
   - Reforzar `.gitignore` con `*.db`, `*.sqlite`, `*.sqlite3`.

---

### 2.4 Depuración de `requirements.txt`

En `local_server/requirements.txt` se encontraban listadas dependencias pesadas que **nunca fueron importadas** por el código fuente de SIFMA:

| Paquete Declarado | Estado en Código Fuente | Acción |
| :--- | :--- | :---: |
| `Flask` | Importado intensivamente en `app.py`, rutas y controladores. | **Conservar (`==3.1.3`)** |
| `Flask-SQLAlchemy` | Importado en `infrastructure.database`. | **Conservar (`==3.1.1`)** |
| `SQLAlchemy` | Importado para modelos, eventos WAL y tipos de datos. | **Conservar (`==2.0.52`)** |
| `opencv-python` | Núcleo del pipeline de visión artificial (`cv2`). | **Conservar (`==4.11.0.86`)** |
| `plantcv` | **Nunca importado** en ningún algoritmo. Todo el fenotipado usa OpenCV y NumPy nativo. | **Eliminar de requirements** |
| `numpy` | Cálculos matriciales, máscaras binarias y percentiles. | **Conservar (`==2.4.6`)** |
| `matplotlib` | **Nunca importado**. Las gráficas son renderizadas en cliente con Chart.js en HTML5 Canvas. | **Eliminar de requirements** |
| `pandas` | **Nunca importado**. Todo el procesamiento de series, CSV y métricas usa Python estándar y NumPy. | **Eliminar de requirements** |
| `scipy` | **Nunca importado**. Correlaciones y estadísticas usan fórmulas matemáticas explícitas nativas. | **Eliminar de requirements** |
| `pyserial` | Driver de comunicación con hardware Arduino / ESP32. | **Conservar (`==3.5`)** |
| `requests` | **Nunca importado** en servidor local (`WeatherService` usa `urllib.request` nativo). | **Eliminar de requirements** |
| `Pillow` | **Nunca importado** en servidor local (se usa OpenCV y Werkzeug). | **Eliminar de requirements** |
| `Werkzeug` | Utilidades de seguridad, hashing de contraseñas y sanitización de nombres de archivo. | **Conservar (`==3.1.8`)** |
| `python-dotenv` | Lectura segura de variables de entorno `.env`. | **Conservar (`==1.2.4`)** |

También se actualizó `local_server/core/dependencies.py` para remover las comprobaciones de librerías innecesarias (`plantcv`, `matplotlib`, `pandas`, `scipy`, `requests`).

