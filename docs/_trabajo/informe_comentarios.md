# SIFMA — Informe de Limpieza de Comentarios y Normalización de Cabeceras (Fase 1)

**Fecha:** 2 de noviembre de 2026  
**Rama:** `preparacion-registro`  
**Autores (desarrolladores del código):** Andrés Felipe Luna Camargo y Cristian David Peña Martínez  
**Titular patrimonial:** `[POR DEFINIR]` (pendiente de formalización con la Universidad del Magdalena)  

---

## 1. Resumen Ejecutivo de la Fase 1

- **Total de archivos intervenidos:** 108 archivos propios.
- **Archivos Python normalizados y verificados:** 82 archivos.
- **Cabecera de autoría DNDA insertada:** 100% de los archivos.
- **Comentarios obvios / redundantes eliminados en Python:** 73.
- **Bloques de código muerto comentados eliminados:** 0 (el repositorio no contenía código activo comentado en desuso).
- **Total de líneas de comentarios antes:** 717.
- **Total de líneas de comentarios después:** 938 (incluyendo cabeceras normalizadas de 3 a 5 líneas por archivo).
- **Verificación sintáctica y AST (Abstract Syntax Tree):** 100% de los archivos Python conservan identidad exacta de árbol sintáctico (equivalencia estricta antes vs después).
- **Verificación de compilación:** Todos los módulos Python compilaron exitosamente con `py_compile` sin advertencias.

---

## 2. Cabeceras Estandarizadas Insertadas

En cumplimiento de los requerimientos de la DNDA, cada archivo fuente ahora incluye en su cabecera superior la atribución formal a los desarrolladores del software:

```python
# SIFMA — Sistema Integral de Fenotipado y Monitoreo Agrícola
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.
```

---

## 3. Comentarios Técnicos y Algorítmicos Preservados

Se conservaron de forma íntegra todos los comentarios con valor de propiedad intelectual y documentación científica:
1. **Pipeline de Visión Artificial:**
   - Fórmula y justificación del Índice de Exceso de Verde ($ExG = 2G - R - B$).
   - Umbrales en espacio HSV para discriminación de clorofila y LAB para eliminación de ruido de fondo blanco.
   - Rotaciones físicas angulares obligatorias: Cenital (180°) y Lateral (90° horario).
   - Filtro de componentes conectados espaciales anti-plantas vecinas.
   - Gradiente horizontal de Sobel para detección de paredes verticales cilíndricas del tallo.
2. **Telemetría y Hardware:**
   - Mapeo de posiciones físicas de sensores (Pos 1: pH, Pos 2: EC, Pos 3: Turbidez, Pos 4: DO, Pos 5: Temp Agua, Pos 6: Temp Exterior, Pos 7: Humedad Relativa, Pos 8: Estado Motor).
   - Prioridad de controladores de cámara Raspberry Pi (Picamera2 CSI > rpicam-still > V4L2 OpenCV).
3. **Docstrings:**
   - El 100% de los docstrings de clases, métodos y servicios se mantuvieron intactos.

---

## 4. Detalle Archivo por Archivo

| Archivo | Tipo | Líneas Coment. Antes | Líneas Coment. Después | Redundantes Eliminados | AST Idéntico |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `local_server/Crear_Acceso_Directo.ps1` | `.ps1` | 4 | 3 | 0 | N/A |
| `local_server/Iniciar_Servidor.bat` | `.bat` | 2 | 5 | 0 | N/A |
| `local_server/Instalar_Dependencias.bat` | `.bat` | 1 | 4 | 0 | N/A |
| `local_server/app.py` | `.py` | 7 | 4 | 6 | Sí (Verificado) |
| `local_server/application/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/application/services/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/application/services/analytics_service.py` | `.py` | 19 | 19 | 3 | Sí (Verificado) |
| `local_server/application/services/audit_service.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/application/services/conclusion_service.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/application/services/system_service.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/application/services/telemetry_service.py` | `.py` | 4 | 4 | 3 | Sí (Verificado) |
| `local_server/application/services/user_service.py` | `.py` | 4 | 4 | 3 | Sí (Verificado) |
| `local_server/application/services/vision_service.py` | `.py` | 13 | 15 | 1 | Sí (Verificado) |
| `local_server/application/services/weather_service.py` | `.py` | 2 | 5 | 0 | Sí (Verificado) |
| `local_server/blueprints/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/blueprints/api_bp.py` | `.py` | 1 | 3 | 1 | Sí (Verificado) |
| `local_server/blueprints/dashboard_bp.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/core/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/core/config.py` | `.py` | 5 | 7 | 1 | Sí (Verificado) |
| `local_server/core/dependencies.py` | `.py` | 2 | 4 | 1 | Sí (Verificado) |
| `local_server/core/logger.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/core/security.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/core/vision/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/core/vision/fruit_detector.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/core/vision/metrics.py` | `.py` | 4 | 7 | 0 | Sí (Verificado) |
| `local_server/core/vision/pipeline.py` | `.py` | 4 | 7 | 0 | Sí (Verificado) |
| `local_server/core/vision/segmentation.py` | `.py` | 8 | 11 | 0 | Sí (Verificado) |
| `local_server/database.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/interfaces/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/interfaces/repositories.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/interfaces/telemetry.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/interfaces/vision.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/models/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/models/agronomic_conclusion.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/models/audit_log.py` | `.py` | 2 | 3 | 2 | Sí (Verificado) |
| `local_server/domain/models/biometric_metric.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/models/capture_session.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/domain/models/config.py` | `.py` | 6 | 9 | 0 | Sí (Verificado) |
| `local_server/domain/models/crop_profile.py` | `.py` | 4 | 7 | 0 | Sí (Verificado) |
| `local_server/domain/models/sensor_reading.py` | `.py` | 2 | 5 | 0 | Sí (Verificado) |
| `local_server/domain/models/user.py` | `.py` | 2 | 5 | 0 | Sí (Verificado) |
| `local_server/infrastructure/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/connection.py` | `.py` | 1 | 3 | 1 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/audit_repository.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/conclusion_repository.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/config_repository.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/crop_repository.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/sensor_repository.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/session_repository.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/repositories/user_repository.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/database/seed.py` | `.py` | 9 | 10 | 2 | Sí (Verificado) |
| `local_server/infrastructure/telemetry/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/telemetry/csv_importer.py` | `.py` | 15 | 18 | 0 | Sí (Verificado) |
| `local_server/infrastructure/telemetry/mock_adapter.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/telemetry/serial_adapter.py` | `.py` | 15 | 14 | 4 | Sí (Verificado) |
| `local_server/infrastructure/vision/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/vision/biometric_calculator.py` | `.py` | 16 | 19 | 0 | Sí (Verificado) |
| `local_server/infrastructure/vision/pipeline_manager.py` | `.py` | 40 | 43 | 0 | Sí (Verificado) |
| `local_server/infrastructure/vision/strategies/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/infrastructure/vision/strategies/exg_segmentation.py` | `.py` | 8 | 11 | 0 | Sí (Verificado) |
| `local_server/presentation/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/presentation/api/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/presentation/api/batch_routes.py` | `.py` | 5 | 6 | 2 | Sí (Verificado) |
| `local_server/presentation/api/conclusion_routes.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/presentation/api/session_routes.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/presentation/api/telemetry_routes.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `local_server/presentation/api/user_routes.py` | `.py` | 5 | 3 | 5 | Sí (Verificado) |
| `local_server/presentation/web/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/presentation/web/dashboard_routes.py` | `.py` | 16 | 13 | 6 | Sí (Verificado) |
| `local_server/services/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/services/analytics_service.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/services/batch_processor.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/services/db_service.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/services/telemetry_service.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `local_server/static/css/index.css` | `.css` | 36 | 41 | 0 | N/A |
| `local_server/static/js/dashboard.js` | `.js` | 8 | 13 | 0 | N/A |
| `local_server/static/js/processing.js` | `.js` | 8 | 13 | 0 | N/A |
| `local_server/static/js/sensors.js` | `.js` | 8 | 13 | 0 | N/A |
| `local_server/templates/about.html` | `.html` | 13 | 14 | 0 | N/A |
| `local_server/templates/audit_logs.html` | `.html` | 15 | 16 | 0 | N/A |
| `local_server/templates/base.html` | `.html` | 27 | 28 | 0 | N/A |
| `local_server/templates/benchmark.html` | `.html` | 8 | 9 | 0 | N/A |
| `local_server/templates/calendar.html` | `.html` | 26 | 27 | 0 | N/A |
| `local_server/templates/config.html` | `.html` | 25 | 26 | 0 | N/A |
| `local_server/templates/cross_analysis.html` | `.html` | 28 | 29 | 0 | N/A |
| `local_server/templates/dashboard.html` | `.html` | 19 | 20 | 0 | N/A |
| `local_server/templates/error.html` | `.html` | 0 | 1 | 0 | N/A |
| `local_server/templates/gallery.html` | `.html` | 23 | 24 | 0 | N/A |
| `local_server/templates/login.html` | `.html` | 7 | 8 | 0 | N/A |
| `local_server/templates/processing.html` | `.html` | 17 | 18 | 0 | N/A |
| `local_server/templates/scientific_report.html` | `.html` | 53 | 54 | 0 | N/A |
| `local_server/templates/sensors.html` | `.html` | 26 | 27 | 0 | N/A |
| `local_server/templates/timelapse.html` | `.html` | 18 | 19 | 0 | N/A |
| `local_server/templates/users.html` | `.html` | 7 | 8 | 0 | N/A |
| `raspi_node/calibrate_cameras.py` | `.py` | 28 | 28 | 3 | Sí (Verificado) |
| `raspi_node/configurar_camaras_dual.sh` | `.sh` | 9 | 12 | 0 | N/A |
| `raspi_node/dependencies.py` | `.py` | 3 | 4 | 2 | Sí (Verificado) |
| `raspi_node/install_autostart.sh` | `.sh` | 8 | 11 | 0 | N/A |
| `raspi_node/main_capture.py` | `.py` | 12 | 8 | 7 | Sí (Verificado) |
| `raspi_node/panel_app.py` | `.py` | 4 | 6 | 1 | Sí (Verificado) |
| `raspi_node/panel_touch_lite.py` | `.py` | 24 | 8 | 19 | Sí (Verificado) |
| `raspi_node/services/__init__.py` | `.py` | 0 | 3 | 0 | Sí (Verificado) |
| `raspi_node/services/camera_service.py` | `.py` | 5 | 8 | 0 | Sí (Verificado) |
| `raspi_node/services/storage_service.py` | `.py` | 1 | 4 | 0 | Sí (Verificado) |
| `raspi_node/templates/index.html` | `.html` | 19 | 20 | 0 | N/A |