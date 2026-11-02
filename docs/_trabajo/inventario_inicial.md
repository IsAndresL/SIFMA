# Inventario Inicial y Línea Base de SIFMA
**Fecha y Hora de Generación:** 2026-11-02 12:21:55
**Rama de Trabajo:** `preparacion-registro`
**Etiqueta Inicial de Línea Base:** `base-previa-limpieza`
**Autores Desarrolladores del Código:** Andrés Felipe Luna Camargo y Cristian David Peña Martínez
**Titular de Derechos Patrimoniales:** `[POR DEFINIR]` (Acorde a definición institucional con Universidad del Magdalena / Docentes)

---

## 1. Resumen Ejecutivo del Estado Inicial

- **Total de Archivos Auditados en el Repositorio:** 1024
- **Tamaño Total en Disco (Código Fuente y Recursos):** 6036.92 MB
- **Total de Líneas de Texto Analizadas:** 29,523
- **Líneas de Código Efectivo:** 25,541
- **Líneas de Comentarios y Docstrings:** 952
- **Rutas / Endpoints HTTP Registrados en Servidor:** 72
- **Prueba de Pipeline de Visión Artificial:** Pipeline ejecutado exitosamente en 2.233s. Area foliar calculada: 62.15 cm2, Indice de salud: 82.8%, Compacidad: 0.000
- **Capturas de Pantalla de la Interfaz Generadas:** 13 en `docs/_trabajo/capturas_base/`

## 2. Distribución de Archivos por Extensión y Tipo de Archivo

| Extensión / Tipo | Cantidad | Tamaño (KB) | Líneas Totales | Líneas Código | Líneas Comentarios |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `.png` | 675 | 6,149,617.2 | 0 | 0 | 0 |
| `sin extensión` | 172 | 26,616.7 | 54 | 47 | 0 |
| `.pma` | 2 | 2,048.0 | 0 | 0 | 0 |
| `.bdic` | 1 | 766.7 | 0 | 0 | 0 |
| `.db` | 3 | 684.0 | 0 | 0 | 0 |
| `.html` | 17 | 650.3 | 12,374 | 10,866 | 331 |
| `.py` | 87 | 490.2 | 11,060 | 9,083 | 537 |
| `.svg` | 5 | 347.2 | 0 | 0 | 0 |
| `.log` | 10 | 158.0 | 0 | 0 | 0 |
| `.md` | 4 | 121.3 | 1,788 | 1,664 | 0 |
| `.csv` | 3 | 106.3 | 1,691 | 1,691 | 0 |
| `.ico` | 1 | 95.9 | 0 | 0 | 0 |
| `.css` | 1 | 38.9 | 1,789 | 1,546 | 36 |
| `.db-shm` | 1 | 32.0 | 0 | 0 | 0 |
| `.js` | 3 | 16.5 | 405 | 353 | 24 |
| `.sh` | 2 | 5.5 | 137 | 98 | 17 |
| `.db-wal` | 2 | 4.1 | 0 | 0 | 0 |
| `.bat` | 2 | 2.8 | 84 | 68 | 3 |
| `.old` | 18 | 2.7 | 0 | 0 | 0 |
| `.ps1` | 1 | 1.3 | 33 | 25 | 4 |
| `.service` | 2 | 0.8 | 34 | 30 | 0 |
| `.txt` | 2 | 0.6 | 26 | 23 | 0 |
| `.desktop` | 2 | 0.6 | 18 | 18 | 0 |
| `.json` | 2 | 0.4 | 20 | 20 | 0 |
| `.example` | 1 | 0.4 | 10 | 9 | 0 |
| `.dat` | 1 | 0.0 | 0 | 0 | 0 |
| `.baf` | 1 | 0.0 | 0 | 0 | 0 |
| `.baj` | 1 | 0.0 | 0 | 0 | 0 |
| `.db-journal` | 1 | 0.0 | 0 | 0 | 0 |
| `.journal` | 1 | 0.0 | 0 | 0 | 0 |

---

## 3. Dependencias de Software

### 3.1. Servidor Local (`local_server/requirements.txt`)
```text
# Dependencias del Servidor Local SIFMA
# Compatible con Python 3.10, 3.11, 3.12 y 3.13 en Windows / Linux

Flask>=3.0.0
Flask-SQLAlchemy>=3.1.0
SQLAlchemy>=2.0.25
opencv-python>=4.9.0
plantcv>=4.1.0
numpy>=1.26.0
matplotlib>=3.8.0
pandas>=2.2.0
scipy>=1.11.0
pyserial>=3.5
requests>=2.31.0
Pillow>=10.0.0
Werkzeug>=3.0.0
python-dotenv>=1.0.0
```

### 3.2. Nodo de Captura (`raspi_node/requirements.txt`)
```text
# Dependencias para el nodo de captura y panel táctil Raspberry Pi (raspi_node)
# Nota: python3-picamera2 viene preinstalado en Raspberry Pi OS Bookworm por defecto.

flask>=3.0.0
opencv-python-headless>=4.8.0
pillow>=10.2.0
psutil>=5.9.0
requests>=2.31.0
```


---

## 4. Inventario Completo de Endpoints y Rutas del Servidor Local

| Método(s) | Ruta URL | Endpoint | Descripción / Función |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | `dashboard.index` | Sin docstring |
| `GET` | `/about` | `dashboard.system_info` | Vista institucional de información del sistema, créditos, autores y términos de licencia. |
| `GET, POST` | `/api/agronomic_conclusions` | `api.handle_agronomic_conclusions` | Sin docstring |
| `DELETE` | `/api/agronomic_conclusions/<int:note_id>` | `api.delete_agronomic_conclusion` | Sin docstring |
| `DELETE` | `/api/audit-logs/<int:log_id>` | `dashboard.delete_single_audit_log` | Elimina un log de auditoría individual. |
| `DELETE, POST` | `/api/audit-logs/clear` | `dashboard.clear_all_audit_logs` | Vacía completamente la tabla de logs de auditoría. |
| `GET` | `/api/benchmark/data` | `api.get_benchmark_data_api` | Sin docstring |
| `GET` | `/api/calendar/day_detail` | `api.get_calendar_day_detail_api` | Sin docstring |
| `GET` | `/api/calendar/month_data` | `api.get_calendar_month_data_api` | Sin docstring |
| `GET, POST` | `/api/conclusions` | `api.handle_agronomic_conclusions` | Sin docstring |
| `DELETE` | `/api/conclusions/<int:note_id>` | `api.delete_agronomic_conclusion` | Sin docstring |
| `GET` | `/api/config` | `api.get_config` | Sin docstring |
| `POST` | `/api/config/location` | `api.update_location_api` | Sin docstring |
| `GET` | `/api/cross_analysis/export_csv` | `api.export_cross_analysis_csv` | Sin docstring |
| `GET` | `/api/daily_summary/export_csv` | `api.export_daily_summary_csv` | Sin docstring |
| `POST` | `/api/delete_telemetry_by_date` | `api.handle_delete_telemetry_by_date` | Sin docstring |
| `GET` | `/api/export_daily_summary_csv` | `api.export_daily_summary_csv` | Sin docstring |
| `POST` | `/api/import_tower_csv` | `api.upload_telemetry_csv` | Sin docstring |
| `POST` | `/api/process_usb_mount` | `api.process_usb_mount` | Procesa recursivamente todas las carpetas del día o lote detectado. |
| `POST` | `/api/process_usb_path` | `api.process_usb_path` | Sin docstring |
| `GET` | `/api/processing/progress` | `api.get_processing_progress` | Retorna el estado de progreso en tiempo real del procesamiento de imágenes. |
| `GET` | `/api/scan_ports` | `api.get_telemetry_ports` | Sin docstring |
| `GET` | `/api/scan_usb` | `api.scan_usb_drives` | Sin docstring |
| `DELETE` | `/api/sessions/<int:session_id>` | `api.delete_capture_session` | Sin docstring |
| `DELETE` | `/api/sessions/by_date` | `api.delete_sessions_by_date` | Sin docstring |
| `POST` | `/api/start_telemetry_recording` | `api.start_telemetry` | Sin docstring |
| `POST` | `/api/stop_telemetry_recording` | `api.stop_telemetry` | Sin docstring |
| `POST` | `/api/sync_tower_telemetry` | `api.handle_sync_tower_telemetry` | Sin docstring |
| `DELETE` | `/api/telemetry/by_date` | `api.delete_telemetry_by_date` | Sin docstring |
| `GET` | `/api/telemetry/download_active_csv` | `api.download_telemetry_csv` | Sin docstring |
| `GET` | `/api/telemetry/download_csv` | `api.download_telemetry_csv` | Sin docstring |
| `GET` | `/api/telemetry/live` | `api.get_live_telemetry_sample` | Sin docstring |
| `GET` | `/api/telemetry/ports` | `api.get_telemetry_ports` | Sin docstring |
| `POST` | `/api/telemetry/start` | `api.start_telemetry` | Sin docstring |
| `GET` | `/api/telemetry/status` | `api.get_telemetry_status` | Sin docstring |
| `POST` | `/api/telemetry/stop` | `api.stop_telemetry` | Sin docstring |
| `POST` | `/api/telemetry/sync_tower` | `api.handle_sync_tower_telemetry` | Sin docstring |
| `GET` | `/api/telemetry/timeline` | `api.get_telemetry_timeline` | Sin docstring |
| `POST` | `/api/telemetry/upload_csv` | `api.upload_telemetry_csv` | Sin docstring |
| `POST` | `/api/upload` | `api.upload_capture_session` | Sin docstring |
| `POST` | `/api/upload_manual_batch` | `api.upload_manual_batch` | Sin docstring |
| `GET` | `/api/users` | `api.get_users_list` | Sin docstring |
| `POST` | `/api/users` | `api.create_new_user` | Sin docstring |
| `PUT` | `/api/users/<int:user_id>` | `api.update_user_details` | Sin docstring |
| `DELETE` | `/api/users/<int:user_id>` | `api.delete_user` | Sin docstring |
| `POST` | `/api/users/<int:user_id>/avatar` | `api.upload_user_avatar` | Sin docstring |
| `DELETE` | `/api/users/<int:user_id>/avatar` | `api.remove_user_avatar` | Sin docstring |
| `POST` | `/api/users/<int:user_id>/reset_password` | `api.reset_user_password` | Sin docstring |
| `POST` | `/api/users/<int:user_id>/toggle_active` | `api.toggle_user_status` | Sin docstring |
| `GET` | `/api/weather` | `api.get_weather_api` | Sin docstring |
| `GET` | `/audit-logs` | `dashboard.audit_logs` | Vista de registro de auditoría, trazabilidad y logs de movimientos (exclusiva para Super Administrador). |
| `GET` | `/audit-logs/export` | `dashboard.export_audit_logs` | Exporta los logs de auditoría filtrados en formato CSV descargable. |
| `GET` | `/benchmark` | `dashboard.inter_plant_benchmark` | Sin docstring |
| `GET` | `/calendar` | `dashboard.calendar_view` | Sin docstring |
| `GET, POST` | `/config` | `dashboard.configuration_panel` | Sin docstring |
| `GET` | `/cross_analysis` | `dashboard.cross_analysis` | Sin docstring |
| `GET` | `/dossier` | `dashboard.scientific_report_view` | Sin docstring |
| `GET` | `/favicon.ico` | `favicon` | Sin docstring |
| `GET` | `/gallery` | `dashboard.gallery` | Sin docstring |
| `GET, POST` | `/login` | `dashboard.login` | Sin docstring |
| `GET` | `/logout` | `dashboard.logout` | Sin docstring |
| `GET` | `/logs` | `dashboard.audit_logs` | Vista de registro de auditoría, trazabilidad y logs de movimientos (exclusiva para Super Administrador). |
| `GET` | `/processing` | `dashboard.processing_panel` | Sin docstring |
| `GET` | `/report/scientific` | `dashboard.scientific_report_view` | Sin docstring |
| `GET` | `/reports` | `dashboard.scientific_report_view` | Sin docstring |
| `GET` | `/scientific_report` | `dashboard.scientific_report_view` | Sin docstring |
| `GET` | `/sensors` | `dashboard.detailed_sensors` | Sin docstring |
| `GET` | `/set_active_plant/<int:plant_id>` | `dashboard.set_active_plant` | Cambia la Canastilla/Torre activa en la sesión (1 a 4). |
| `GET` | `/static/<path:filename>` | `static` | Sin docstring |
| `GET` | `/system_info` | `dashboard.system_info` | Vista institucional de información del sistema, créditos, autores y términos de licencia. |
| `GET` | `/timelapse` | `dashboard.timelapse_viewer` | Sin docstring |
| `GET` | `/users` | `dashboard.users_management` | Vista de administración de usuarios y roles (exclusiva para Administrador Principal). |

---

## 5. Capturas de Pantalla de la Interfaz de Usuario (Línea Base)

Las siguientes capturas de pantalla a resolución 1920x1080 fueron generadas automáticamente y almacenadas en `docs/_trabajo/capturas_base/`:

- **`01_login.png`** (981.2 KB): URL `http://127.0.0.1:5025/login`
- **`02_dashboard_resumen.png`** (386.6 KB): URL `http://127.0.0.1:5025/`
- **`03_calendario_muestreos.png`** (303.0 KB): URL `http://127.0.0.1:5025/calendar`
- **`04_procesamiento_vision.png`** (279.4 KB): URL `http://127.0.0.1:5025/processing`
- **`05_galeria_lotes.png`** (565.9 KB): URL `http://127.0.0.1:5025/gallery`
- **`06_timelapse_evolutivo.png`** (982.0 KB): URL `http://127.0.0.1:5025/timelapse`
- **`07_sensores_ambientales.png`** (525.2 KB): URL `http://127.0.0.1:5025/sensors`
- **`08_cruce_correlaciones.png`** (251.8 KB): URL `http://127.0.0.1:5025/cross_analysis`
- **`09_dossier_reporte_cientifico.png`** (170.9 KB): URL `http://127.0.0.1:5025/reports`
- **`10_parametros_cultivo.png`** (514.2 KB): URL `http://127.0.0.1:5025/config`
- **`11_usuarios_roles.png`** (531.4 KB): URL `http://127.0.0.1:5025/users`
- **`12_registro_auditoria.png`** (560.8 KB): URL `http://127.0.0.1:5025/audit-logs`
- **`13_informacion_sistema.png`** (338.1 KB): URL `http://127.0.0.1:5025/about`

---

## 6. Árbol Completo de Archivos del Proyecto (con Tamaños)

```text
       613 B  .gitignore
    23,787 B  README.md
 1,004,683 B  docs/_trabajo/capturas_base/01_login.png
    15,493 B  docs/_trabajo/capturas_base/02_dashboard_resumen.png
    15,493 B  docs/_trabajo/capturas_base/03_calendario_muestreos.png
    15,493 B  docs/_trabajo/capturas_base/04_procesamiento_vision.png
    15,493 B  docs/_trabajo/capturas_base/05_galeria_lotes.png
    15,493 B  docs/_trabajo/capturas_base/06_timelapse_evolutivo.png
    15,493 B  docs/_trabajo/capturas_base/07_sensores_ambientales.png
    15,493 B  docs/_trabajo/capturas_base/08_cruce_correlaciones.png
    15,493 B  docs/_trabajo/capturas_base/09_dossier_reporte_cientifico.png
    15,493 B  docs/_trabajo/capturas_base/10_parametros_cultivo.png
    15,493 B  docs/_trabajo/capturas_base/11_usuarios_roles.png
    15,493 B  docs/_trabajo/capturas_base/12_registro_auditoria.png
    15,493 B  docs/_trabajo/capturas_base/13_informacion_sistema.png
    95,178 B  docs/_trabajo/inventario_inicial.md
         0 B  docs/_trabajo/temp_chrome_profile/Crashpad/metadata
        40 B  docs/_trabajo/temp_chrome_profile/Crashpad/settings.dat
 1,048,576 B  docs/_trabajo/temp_chrome_profile/CrashpadMetrics-active.pma
 1,048,576 B  docs/_trabajo/temp_chrome_profile/CrashpadMetrics.pma
    73,728 B  docs/_trabajo/temp_chrome_profile/Default/Account Web Data
         0 B  docs/_trabajo/temp_chrome_profile/Default/Account Web Data-journal
    53,248 B  docs/_trabajo/temp_chrome_profile/Default/Affiliation Database
         0 B  docs/_trabajo/temp_chrome_profile/Default/Affiliation Database-journal
         6 B  docs/_trabajo/temp_chrome_profile/Default/BookmarkMergedSurfaceOrdering
    45,056 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/data_1
 1,056,768 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/data_3
    39,868 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000001
    69,391 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000002
 9,637,009 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000003
    22,264 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000004
    85,672 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000005
   785,066 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000006
   785,066 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000007
   173,620 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000008
    39,868 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_000009
    69,391 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_00000a
 9,637,009 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_00000b
    69,391 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/f_00000c
   524,656 B  docs/_trabajo/temp_chrome_profile/Default/Cache/Cache_Data/index
         4 B  docs/_trabajo/temp_chrome_profile/Default/Cache/No_Vary_Search/journal.baj
        20 B  docs/_trabajo/temp_chrome_profile/Default/Cache/No_Vary_Search/snapshot.baf
         0 B  docs/_trabajo/temp_chrome_profile/Default/ClientCertificates/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/ClientCertificates/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/ClientCertificates/LOG.old
       298 B  docs/_trabajo/temp_chrome_profile/Default/Code Cache/js/ba678a2fbd8c358c_0
        24 B  docs/_trabajo/temp_chrome_profile/Default/Code Cache/js/index
        72 B  docs/_trabajo/temp_chrome_profile/Default/Code Cache/js/index-dir/the-real-index
        24 B  docs/_trabajo/temp_chrome_profile/Default/Code Cache/wasm/index
        48 B  docs/_trabajo/temp_chrome_profile/Default/Code Cache/wasm/index-dir/the-real-index
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnGraphiteCache/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/Default/DawnGraphiteCache/data_1
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnGraphiteCache/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnGraphiteCache/data_3
   262,512 B  docs/_trabajo/temp_chrome_profile/Default/DawnGraphiteCache/index
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnWebGPUCache/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/Default/DawnWebGPUCache/data_1
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnWebGPUCache/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/DawnWebGPUCache/data_3
   262,512 B  docs/_trabajo/temp_chrome_profile/Default/DawnWebGPUCache/index
        57 B  docs/_trabajo/temp_chrome_profile/Default/Extension Rules/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Extension Rules/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Extension Rules/LOCK
       339 B  docs/_trabajo/temp_chrome_profile/Default/Extension Rules/LOG
        41 B  docs/_trabajo/temp_chrome_profile/Default/Extension Rules/MANIFEST-000001
        57 B  docs/_trabajo/temp_chrome_profile/Default/Extension Scripts/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Extension Scripts/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Extension Scripts/LOCK
       343 B  docs/_trabajo/temp_chrome_profile/Default/Extension Scripts/LOG
        41 B  docs/_trabajo/temp_chrome_profile/Default/Extension Scripts/MANIFEST-000001
       171 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/LOCK
       380 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/LOG
       380 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/Extension State/MANIFEST-000001
    28,672 B  docs/_trabajo/temp_chrome_profile/Default/Favicons
         0 B  docs/_trabajo/temp_chrome_profile/Default/Favicons-journal
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/GPUCache/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/Default/GPUCache/data_1
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/GPUCache/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/Default/GPUCache/data_3
   262,512 B  docs/_trabajo/temp_chrome_profile/Default/GPUCache/index
   204,800 B  docs/_trabajo/temp_chrome_profile/Default/History
         0 B  docs/_trabajo/temp_chrome_profile/Default/History-journal
         0 B  docs/_trabajo/temp_chrome_profile/Default/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/LOG.old
        30 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/LOCK
       392 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/LOG
       392 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/Local Storage/leveldb/MANIFEST-000001
    40,960 B  docs/_trabajo/temp_chrome_profile/Default/Login Data
    40,960 B  docs/_trabajo/temp_chrome_profile/Default/Login Data For Account
         0 B  docs/_trabajo/temp_chrome_profile/Default/Login Data For Account-journal
         0 B  docs/_trabajo/temp_chrome_profile/Default/Login Data-journal
    20,480 B  docs/_trabajo/temp_chrome_profile/Default/Network/Cookies
         0 B  docs/_trabajo/temp_chrome_profile/Default/Network/Cookies-journal
    20,480 B  docs/_trabajo/temp_chrome_profile/Default/Network/Device Bound Sessions
         0 B  docs/_trabajo/temp_chrome_profile/Default/Network/Device Bound Sessions-journal
     2,477 B  docs/_trabajo/temp_chrome_profile/Default/Network/Network Persistent State
         0 B  docs/_trabajo/temp_chrome_profile/Default/Network/NetworkDataMigrated
    36,864 B  docs/_trabajo/temp_chrome_profile/Default/Network/Reporting and NEL
         0 B  docs/_trabajo/temp_chrome_profile/Default/Network/Reporting and NEL-journal
       355 B  docs/_trabajo/temp_chrome_profile/Default/Network/TransportSecurity
    36,864 B  docs/_trabajo/temp_chrome_profile/Default/Network/Trust Tokens
         0 B  docs/_trabajo/temp_chrome_profile/Default/Network/Trust Tokens-journal
         0 B  docs/_trabajo/temp_chrome_profile/Default/PersistentOriginTrials/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/PersistentOriginTrials/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/PersistentOriginTrials/LOG.old
    12,076 B  docs/_trabajo/temp_chrome_profile/Default/Preferences
       180 B  docs/_trabajo/temp_chrome_profile/Default/README
         0 B  docs/_trabajo/temp_chrome_profile/Default/Safe Browsing Network/NetworkDataMigrated
    14,270 B  docs/_trabajo/temp_chrome_profile/Default/Secure Preferences
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SegmentInfoDB/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SegmentInfoDB/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SegmentInfoDB/LOG.old
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalDB/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalDB/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalDB/LOG.old
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalStorageConfigDB/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalStorageConfigDB/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/Segmentation Platform/SignalStorageConfigDB/LOG.old
    20,480 B  docs/_trabajo/temp_chrome_profile/Default/ServerCertificate
         0 B  docs/_trabajo/temp_chrome_profile/Default/ServerCertificate-journal
     1,263 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/LOCK
       396 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/LOG
       396 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/Database/MANIFEST-000001
       472 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/ScriptCache/2cc80dabc69f58b6_0
    10,387 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/ScriptCache/4cb013792b196a35_0
     7,185 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/ScriptCache/4cb013792b196a35_1
        24 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/ScriptCache/index
        96 B  docs/_trabajo/temp_chrome_profile/Default/Service Worker/ScriptCache/index-dir/the-real-index
       125 B  docs/_trabajo/temp_chrome_profile/Default/Session Storage/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Session Storage/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Session Storage/LOCK
       339 B  docs/_trabajo/temp_chrome_profile/Default/Session Storage/LOG
        41 B  docs/_trabajo/temp_chrome_profile/Default/Session Storage/MANIFEST-000001
     2,181 B  docs/_trabajo/temp_chrome_profile/Default/Sessions/Session_13438113588865521
     2,165 B  docs/_trabajo/temp_chrome_profile/Default/Sessions/Session_13438113589758164
    41,360 B  docs/_trabajo/temp_chrome_profile/Default/Sessions/Tabs_13438113588874019
    41,464 B  docs/_trabajo/temp_chrome_profile/Default/Sessions/Tabs_13438113589772286
     3,072 B  docs/_trabajo/temp_chrome_profile/Default/Sessions_Encrypted/Session_13438113588873974
     3,056 B  docs/_trabajo/temp_chrome_profile/Default/Sessions_Encrypted/Session_13438113589777986
    43,868 B  docs/_trabajo/temp_chrome_profile/Default/Sessions_Encrypted/Tabs_13438113588884266
    43,972 B  docs/_trabajo/temp_chrome_profile/Default/Sessions_Encrypted/Tabs_13438113589784180
        24 B  docs/_trabajo/temp_chrome_profile/Default/Shared Dictionary/cache/index
        48 B  docs/_trabajo/temp_chrome_profile/Default/Shared Dictionary/cache/index-dir/the-real-index
    45,056 B  docs/_trabajo/temp_chrome_profile/Default/Shared Dictionary/db
         0 B  docs/_trabajo/temp_chrome_profile/Default/Shared Dictionary/db-journal
        40 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/LOCK
       408 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/LOG
       408 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/Site Characteristics Database/MANIFEST-000001
       118 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/LOCK
       384 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/LOG
       384 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/Sync Data/LevelDB/MANIFEST-000001
    20,480 B  docs/_trabajo/temp_chrome_profile/Default/Top Sites
         0 B  docs/_trabajo/temp_chrome_profile/Default/Top Sites-journal
   157,696 B  docs/_trabajo/temp_chrome_profile/Default/Web Data
         0 B  docs/_trabajo/temp_chrome_profile/Default/Web Data-journal
    40,960 B  docs/_trabajo/temp_chrome_profile/Default/WebStorage/QuotaManager
         0 B  docs/_trabajo/temp_chrome_profile/Default/WebStorage/QuotaManager-journal
         0 B  docs/_trabajo/temp_chrome_profile/Default/chrome_cart_db/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/chrome_cart_db/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/chrome_cart_db/LOG.old
         0 B  docs/_trabajo/temp_chrome_profile/Default/commerce_subscription_db/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/commerce_subscription_db/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/commerce_subscription_db/LOG.old
    32,768 B  docs/_trabajo/temp_chrome_profile/Default/declarative_performance_observer.db
         0 B  docs/_trabajo/temp_chrome_profile/Default/declarative_performance_observer.db-journal
         0 B  docs/_trabajo/temp_chrome_profile/Default/discount_infos_db/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/discount_infos_db/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/discount_infos_db/LOG.old
         0 B  docs/_trabajo/temp_chrome_profile/Default/discounts_db/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/discounts_db/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/discounts_db/LOG.old
         0 B  docs/_trabajo/temp_chrome_profile/Default/parcel_tracking_db/LOCK
         0 B  docs/_trabajo/temp_chrome_profile/Default/parcel_tracking_db/LOG
         0 B  docs/_trabajo/temp_chrome_profile/Default/parcel_tracking_db/LOG.old
   158,364 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/LOCK
       380 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/LOG
       380 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/MANIFEST-000001
     1,556 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/000003.log
        16 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/CURRENT
         0 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/LOCK
       398 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/LOG
       398 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/LOG.old
        41 B  docs/_trabajo/temp_chrome_profile/Default/shared_proto_db/metadata/MANIFEST-000001
         0 B  docs/_trabajo/temp_chrome_profile/GPUPersistentCache/DawnGraphiteCache/6ENT453JBM7P4HRBJFQZ6ZSIB2QSEPXH/cache.db
         0 B  docs/_trabajo/temp_chrome_profile/GPUPersistentCache/DawnGraphiteCache/6ENT453JBM7P4HRBJFQZ6ZSIB2QSEPXH/cache.db-wal
         0 B  docs/_trabajo/temp_chrome_profile/GPUPersistentCache/DawnGraphiteCache/6ENT453JBM7P4HRBJFQZ6ZSIB2QSEPXH/cache.journal
     8,192 B  docs/_trabajo/temp_chrome_profile/GrShaderCache/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/GrShaderCache/data_1
     8,192 B  docs/_trabajo/temp_chrome_profile/GrShaderCache/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/GrShaderCache/data_3
   262,512 B  docs/_trabajo/temp_chrome_profile/GrShaderCache/index
        13 B  docs/_trabajo/temp_chrome_profile/Last Version
    23,957 B  docs/_trabajo/temp_chrome_profile/Local State
     8,192 B  docs/_trabajo/temp_chrome_profile/ShaderCache/data_0
   270,336 B  docs/_trabajo/temp_chrome_profile/ShaderCache/data_1
     8,192 B  docs/_trabajo/temp_chrome_profile/ShaderCache/data_2
     8,192 B  docs/_trabajo/temp_chrome_profile/ShaderCache/data_3
   262,512 B  docs/_trabajo/temp_chrome_profile/ShaderCache/index
        85 B  docs/_trabajo/temp_chrome_profile/Variations
        11 B  docs/_trabajo/temp_chrome_profile/VariationsSafeSeedV2
        11 B  docs/_trabajo/temp_chrome_profile/VariationsSeedV2
   785,066 B  docs/_trabajo/temp_chrome_profile/es-ES-3-0.bdic
        13 B  docs/_trabajo/temp_chrome_profile/extensions_crx_cache/metadata.json
    49,152 B  docs/_trabajo/temp_chrome_profile/segmentation_platform/ukm_db
       562 B  local_server/.env
       425 B  local_server/.env.example
     1,378 B  local_server/Crear_Acceso_Directo.ps1
       856 B  local_server/Iniciar_Servidor.bat
     2,020 B  local_server/Instalar_Dependencias.bat
     2,987 B  local_server/LEEME_CAMPO.md
     2,639 B  local_server/app.py
       383 B  local_server/application/__init__.py
       630 B  local_server/application/services/__init__.py
    91,941 B  local_server/application/services/analytics_service.py
     5,241 B  local_server/application/services/audit_service.py
     1,509 B  local_server/application/services/conclusion_service.py
     2,654 B  local_server/application/services/system_service.py
     8,379 B  local_server/application/services/telemetry_service.py
     7,235 B  local_server/application/services/user_service.py
    21,561 B  local_server/application/services/vision_service.py
     6,038 B  local_server/application/services/weather_service.py
       104 B  local_server/blueprints/__init__.py
       430 B  local_server/blueprints/api_bp.py
       269 B  local_server/blueprints/dashboard_bp.py
       167 B  local_server/core/__init__.py
     2,499 B  local_server/core/config.py
     3,139 B  local_server/core/dependencies.py
       583 B  local_server/core/logger.py
     2,018 B  local_server/core/security.py
       263 B  local_server/core/vision/__init__.py
     2,007 B  local_server/core/vision/fruit_detector.py
     4,320 B  local_server/core/vision/metrics.py
     6,203 B  local_server/core/vision/pipeline.py
     3,672 B  local_server/core/vision/segmentation.py
       583 B  local_server/database.py
       903 B  local_server/domain/__init__.py
       636 B  local_server/domain/interfaces/__init__.py
     2,452 B  local_server/domain/interfaces/repositories.py
       451 B  local_server/domain/interfaces/telemetry.py
     1,436 B  local_server/domain/interfaces/vision.py
       528 B  local_server/domain/models/__init__.py
     1,639 B  local_server/domain/models/agronomic_conclusion.py
     4,752 B  local_server/domain/models/audit_log.py
     2,349 B  local_server/domain/models/biometric_metric.py
     1,513 B  local_server/domain/models/capture_session.py
     5,094 B  local_server/domain/models/config.py
     3,799 B  local_server/domain/models/crop_profile.py
     2,786 B  local_server/domain/models/sensor_reading.py
     7,253 B  local_server/domain/models/user.py
        54 B  local_server/infrastructure/__init__.py
        92 B  local_server/infrastructure/database/__init__.py
       119 B  local_server/infrastructure/database/connection.py
       546 B  local_server/infrastructure/database/repositories/__init__.py
     3,418 B  local_server/infrastructure/database/repositories/audit_repository.py
     1,185 B  local_server/infrastructure/database/repositories/conclusion_repository.py
       683 B  local_server/infrastructure/database/repositories/config_repository.py
     2,851 B  local_server/infrastructure/database/repositories/crop_repository.py
     2,382 B  local_server/infrastructure/database/repositories/sensor_repository.py
     2,590 B  local_server/infrastructure/database/repositories/session_repository.py
     1,020 B  local_server/infrastructure/database/repositories/user_repository.py
    13,348 B  local_server/infrastructure/database/seed.py
       237 B  local_server/infrastructure/telemetry/__init__.py
     9,923 B  local_server/infrastructure/telemetry/csv_importer.py
     1,576 B  local_server/infrastructure/telemetry/mock_adapter.py
    10,735 B  local_server/infrastructure/telemetry/serial_adapter.py
       255 B  local_server/infrastructure/vision/__init__.py
    11,042 B  local_server/infrastructure/vision/biometric_calculator.py
    20,764 B  local_server/infrastructure/vision/pipeline_manager.py
        93 B  local_server/infrastructure/vision/strategies/__init__.py
     4,236 B  local_server/infrastructure/vision/strategies/exg_segmentation.py
        92 B  local_server/presentation/__init__.py
       233 B  local_server/presentation/api/__init__.py
    12,718 B  local_server/presentation/api/batch_routes.py
     2,748 B  local_server/presentation/api/conclusion_routes.py
     3,519 B  local_server/presentation/api/session_routes.py
    11,917 B  local_server/presentation/api/telemetry_routes.py
    11,565 B  local_server/presentation/api/user_routes.py
        71 B  local_server/presentation/web/__init__.py
    36,266 B  local_server/presentation/web/dashboard_routes.py
       343 B  local_server/requirements.txt
    14,677 B  local_server/scratch/fase0_runner.py
     4,333 B  local_server/scratch/seed_telemetry_20261008.py
     5,853 B  local_server/scratch/test_all_local_server_endpoints.py
     6,143 B  local_server/scratch/test_authenticated_local_server.py
     1,807 B  local_server/scratch/test_dossier.py
       147 B  local_server/services/__init__.py
     1,561 B  local_server/services/analytics_service.py
       678 B  local_server/services/batch_processor.py
     1,300 B  local_server/services/db_service.py
       188 B  local_server/services/telemetry_service.py
   667,648 B  local_server/sifma.db
    32,768 B  local_server/sifma.db-shm
     4,152 B  local_server/sifma.db-wal
    39,868 B  local_server/static/css/index.css
11,412,684 B  local_server/static/data/processed/batch_20261008_190115/proc_cenital_1.png
11,876,961 B  local_server/static/data/processed/batch_20261008_190115/proc_cenital_2.png
11,722,589 B  local_server/static/data/processed/batch_20261008_190115/proc_cenital_3.png
11,703,914 B  local_server/static/data/processed/batch_20261008_190115/proc_cenital_4.png
11,897,572 B  local_server/static/data/processed/batch_20261008_190115/proc_cenital_5.png
10,078,896 B  local_server/static/data/processed/batch_20261008_190115/proc_lateral_1.png
10,531,745 B  local_server/static/data/processed/batch_20261008_190115/proc_lateral_2.png
 8,539,090 B  local_server/static/data/processed/batch_20261008_190115/proc_lateral_3.png
10,743,961 B  local_server/static/data/processed/batch_20261008_190115/proc_lateral_4.png
 9,555,850 B  local_server/static/data/processed/batch_20261008_190115/proc_lateral_5.png
11,914,410 B  local_server/static/data/processed/batch_20261008_191919/proc_cenital_1.png
11,822,632 B  local_server/static/data/processed/batch_20261008_191919/proc_cenital_2.png
12,073,612 B  local_server/static/data/processed/batch_20261008_191919/proc_cenital_3.png
12,203,468 B  local_server/static/data/processed/batch_20261008_191919/proc_cenital_4.png
 7,567,122 B  local_server/static/data/processed/batch_20261008_191919/proc_lateral_1.png
 7,642,449 B  local_server/static/data/processed/batch_20261008_191919/proc_lateral_2.png
 8,031,657 B  local_server/static/data/processed/batch_20261008_191919/proc_lateral_3.png
 7,558,421 B  local_server/static/data/processed/batch_20261008_191919/proc_lateral_4.png
 7,528,492 B  local_server/static/data/processed/batch_20261008_191919/proc_lateral_5.png
11,412,684 B  local_server/static/data/processed/batch_20261008_231043/proc_cenital_1.png
11,876,961 B  local_server/static/data/processed/batch_20261008_231043/proc_cenital_2.png
11,722,589 B  local_server/static/data/processed/batch_20261008_231043/proc_cenital_3.png
11,703,914 B  local_server/static/data/processed/batch_20261008_231043/proc_cenital_4.png
11,897,572 B  local_server/static/data/processed/batch_20261008_231043/proc_cenital_5.png
10,078,896 B  local_server/static/data/processed/batch_20261008_231043/proc_lateral_1.png
10,531,745 B  local_server/static/data/processed/batch_20261008_231043/proc_lateral_2.png
 8,539,090 B  local_server/static/data/processed/batch_20261008_231043/proc_lateral_3.png
10,743,961 B  local_server/static/data/processed/batch_20261008_231043/proc_lateral_4.png
 9,555,850 B  local_server/static/data/processed/batch_20261008_231043/proc_lateral_5.png
11,368,693 B  local_server/static/data/processed/batch_20261009_123838/proc_cenital_1.png
11,829,243 B  local_server/static/data/processed/batch_20261009_123838/proc_cenital_2.png
11,673,181 B  local_server/static/data/processed/batch_20261009_123838/proc_cenital_3.png
11,660,262 B  local_server/static/data/processed/batch_20261009_123838/proc_cenital_4.png
11,849,103 B  local_server/static/data/processed/batch_20261009_123838/proc_cenital_5.png
10,072,755 B  local_server/static/data/processed/batch_20261009_123838/proc_lateral_1.png
10,526,659 B  local_server/static/data/processed/batch_20261009_123838/proc_lateral_2.png
 8,532,316 B  local_server/static/data/processed/batch_20261009_123838/proc_lateral_3.png
10,738,701 B  local_server/static/data/processed/batch_20261009_123838/proc_lateral_4.png
 9,548,643 B  local_server/static/data/processed/batch_20261009_123838/proc_lateral_5.png
10,605,759 B  local_server/static/data/processed/batch_20261009_123907/proc_cenital_1.png
11,337,377 B  local_server/static/data/processed/batch_20261009_123907/proc_cenital_2.png
11,282,541 B  local_server/static/data/processed/batch_20261009_123907/proc_cenital_3.png
11,847,330 B  local_server/static/data/processed/batch_20261009_123907/proc_cenital_4.png
11,730,043 B  local_server/static/data/processed/batch_20261009_123907/proc_cenital_5.png
11,919,360 B  local_server/static/data/processed/batch_20261009_123907/proc_lateral_1.png
 9,661,268 B  local_server/static/data/processed/batch_20261009_123907/proc_lateral_2.png
 8,449,432 B  local_server/static/data/processed/batch_20261009_123907/proc_lateral_3.png
 9,671,267 B  local_server/static/data/processed/batch_20261009_123907/proc_lateral_4.png
10,322,549 B  local_server/static/data/processed/batch_20261009_123907/proc_lateral_5.png
10,751,417 B  local_server/static/data/processed/batch_20261009_124008/proc_cenital_1.png
10,787,324 B  local_server/static/data/processed/batch_20261009_124008/proc_cenital_2.png
10,816,445 B  local_server/static/data/processed/batch_20261009_124008/proc_cenital_3.png
10,878,131 B  local_server/static/data/processed/batch_20261009_124008/proc_cenital_4.png
11,016,543 B  local_server/static/data/processed/batch_20261009_124008/proc_cenital_5.png
 8,477,006 B  local_server/static/data/processed/batch_20261009_124008/proc_lateral_1.png
 8,389,428 B  local_server/static/data/processed/batch_20261009_124008/proc_lateral_2.png
 9,127,208 B  local_server/static/data/processed/batch_20261009_124008/proc_lateral_3.png
 9,045,764 B  local_server/static/data/processed/batch_20261009_124008/proc_lateral_4.png
10,096,762 B  local_server/static/data/processed/batch_20261009_124008/proc_lateral_5.png
10,666,843 B  local_server/static/data/processed/batch_20261009_200002/proc_cenital_1.png
10,677,257 B  local_server/static/data/processed/batch_20261009_200002/proc_cenital_2.png
10,667,590 B  local_server/static/data/processed/batch_20261009_200002/proc_cenital_3.png
10,667,166 B  local_server/static/data/processed/batch_20261009_200002/proc_cenital_4.png
10,732,740 B  local_server/static/data/processed/batch_20261009_200002/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200002/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200002/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200002/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200002/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200002/proc_lateral_5.png
10,666,843 B  local_server/static/data/processed/batch_20261009_200028/proc_cenital_1.png
10,677,257 B  local_server/static/data/processed/batch_20261009_200028/proc_cenital_2.png
10,667,590 B  local_server/static/data/processed/batch_20261009_200028/proc_cenital_3.png
10,667,166 B  local_server/static/data/processed/batch_20261009_200028/proc_cenital_4.png
10,732,740 B  local_server/static/data/processed/batch_20261009_200028/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200028/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200028/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200028/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200028/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200028/proc_lateral_5.png
10,666,843 B  local_server/static/data/processed/batch_20261009_200048/proc_cenital_1.png
10,677,257 B  local_server/static/data/processed/batch_20261009_200048/proc_cenital_2.png
10,667,590 B  local_server/static/data/processed/batch_20261009_200048/proc_cenital_3.png
10,667,166 B  local_server/static/data/processed/batch_20261009_200048/proc_cenital_4.png
10,732,740 B  local_server/static/data/processed/batch_20261009_200048/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200048/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200048/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200048/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200048/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200048/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_200512/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_200512/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_200512/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_200512/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_200512/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200512/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200512/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200512/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200512/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200512/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_200616/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_200616/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_200616/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_200616/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_200616/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200616/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200616/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200616/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200616/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200616/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_200659/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_200659/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_200659/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_200659/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_200659/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_200659/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_200659/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_200659/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_200659/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_200659/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_201835/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_201835/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_201835/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_201835/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_201835/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_201835/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_201835/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_201835/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_201835/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_201835/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_201940/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_201940/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_201940/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_201940/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_201940/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_201940/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_201940/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_201940/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_201940/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_201940/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_202043/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_202043/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_202043/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_202043/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_202043/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_202043/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_202043/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_202043/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_202043/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_202043/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_202755/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_202755/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_202755/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_202755/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_202755/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_202755/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_202755/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_202755/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_202755/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_202755/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_202857/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_202857/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_202857/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_202857/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_202857/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_202857/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_202857/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_202857/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_202857/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_202857/proc_lateral_5.png
10,667,649 B  local_server/static/data/processed/batch_20261009_203000/proc_cenital_1.png
10,679,054 B  local_server/static/data/processed/batch_20261009_203000/proc_cenital_2.png
10,671,886 B  local_server/static/data/processed/batch_20261009_203000/proc_cenital_3.png
10,668,386 B  local_server/static/data/processed/batch_20261009_203000/proc_cenital_4.png
10,734,664 B  local_server/static/data/processed/batch_20261009_203000/proc_cenital_5.png
 8,038,562 B  local_server/static/data/processed/batch_20261009_203000/proc_lateral_1.png
 8,036,015 B  local_server/static/data/processed/batch_20261009_203000/proc_lateral_2.png
 8,033,540 B  local_server/static/data/processed/batch_20261009_203000/proc_lateral_3.png
 8,037,533 B  local_server/static/data/processed/batch_20261009_203000/proc_lateral_4.png
 8,031,417 B  local_server/static/data/processed/batch_20261009_203000/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_204402/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_204402/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_204402/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_204402/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_204402/proc_cenital_5.png
 8,037,460 B  local_server/static/data/processed/batch_20261009_204402/proc_lateral_1.png
 8,034,952 B  local_server/static/data/processed/batch_20261009_204402/proc_lateral_2.png
 8,032,491 B  local_server/static/data/processed/batch_20261009_204402/proc_lateral_3.png
 8,036,598 B  local_server/static/data/processed/batch_20261009_204402/proc_lateral_4.png
 8,030,444 B  local_server/static/data/processed/batch_20261009_204402/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_204506/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_204506/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_204506/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_204506/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_204506/proc_cenital_5.png
 8,037,460 B  local_server/static/data/processed/batch_20261009_204506/proc_lateral_1.png
 8,034,952 B  local_server/static/data/processed/batch_20261009_204506/proc_lateral_2.png
 8,032,491 B  local_server/static/data/processed/batch_20261009_204506/proc_lateral_3.png
 8,036,598 B  local_server/static/data/processed/batch_20261009_204506/proc_lateral_4.png
 8,030,444 B  local_server/static/data/processed/batch_20261009_204506/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_204611/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_204611/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_204611/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_204611/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_204611/proc_cenital_5.png
 8,037,460 B  local_server/static/data/processed/batch_20261009_204611/proc_lateral_1.png
 8,034,952 B  local_server/static/data/processed/batch_20261009_204611/proc_lateral_2.png
 8,032,491 B  local_server/static/data/processed/batch_20261009_204611/proc_lateral_3.png
 8,036,598 B  local_server/static/data/processed/batch_20261009_204611/proc_lateral_4.png
 8,030,444 B  local_server/static/data/processed/batch_20261009_204611/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_223406/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_223406/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_223406/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_223406/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_223406/proc_cenital_5.png
 8,040,121 B  local_server/static/data/processed/batch_20261009_223406/proc_lateral_1.png
 8,037,020 B  local_server/static/data/processed/batch_20261009_223406/proc_lateral_2.png
 8,034,989 B  local_server/static/data/processed/batch_20261009_223406/proc_lateral_3.png
 8,039,083 B  local_server/static/data/processed/batch_20261009_223406/proc_lateral_4.png
 8,032,734 B  local_server/static/data/processed/batch_20261009_223406/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_223511/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_223511/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_223511/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_223511/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_223511/proc_cenital_5.png
 8,040,121 B  local_server/static/data/processed/batch_20261009_223511/proc_lateral_1.png
 8,037,020 B  local_server/static/data/processed/batch_20261009_223511/proc_lateral_2.png
 8,034,989 B  local_server/static/data/processed/batch_20261009_223511/proc_lateral_3.png
 8,039,083 B  local_server/static/data/processed/batch_20261009_223511/proc_lateral_4.png
 8,032,734 B  local_server/static/data/processed/batch_20261009_223511/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_223618/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_223618/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_223618/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_223618/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_223618/proc_cenital_5.png
 8,040,121 B  local_server/static/data/processed/batch_20261009_223618/proc_lateral_1.png
 8,037,020 B  local_server/static/data/processed/batch_20261009_223618/proc_lateral_2.png
 8,034,989 B  local_server/static/data/processed/batch_20261009_223618/proc_lateral_3.png
 8,039,083 B  local_server/static/data/processed/batch_20261009_223618/proc_lateral_4.png
 8,032,734 B  local_server/static/data/processed/batch_20261009_223618/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_231448/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_231448/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_231448/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_231448/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_231448/proc_cenital_5.png
 8,046,493 B  local_server/static/data/processed/batch_20261009_231448/proc_lateral_1.png
 8,043,409 B  local_server/static/data/processed/batch_20261009_231448/proc_lateral_2.png
 8,041,567 B  local_server/static/data/processed/batch_20261009_231448/proc_lateral_3.png
 8,045,484 B  local_server/static/data/processed/batch_20261009_231448/proc_lateral_4.png
 8,039,210 B  local_server/static/data/processed/batch_20261009_231448/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_231554/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_231554/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_231554/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_231554/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_231554/proc_cenital_5.png
 8,046,493 B  local_server/static/data/processed/batch_20261009_231554/proc_lateral_1.png
 8,043,409 B  local_server/static/data/processed/batch_20261009_231554/proc_lateral_2.png
 8,041,567 B  local_server/static/data/processed/batch_20261009_231554/proc_lateral_3.png
 8,045,484 B  local_server/static/data/processed/batch_20261009_231554/proc_lateral_4.png
 8,039,210 B  local_server/static/data/processed/batch_20261009_231554/proc_lateral_5.png
10,667,376 B  local_server/static/data/processed/batch_20261009_231656/proc_cenital_1.png
10,678,652 B  local_server/static/data/processed/batch_20261009_231656/proc_cenital_2.png
10,671,536 B  local_server/static/data/processed/batch_20261009_231656/proc_cenital_3.png
10,668,026 B  local_server/static/data/processed/batch_20261009_231656/proc_cenital_4.png
10,734,450 B  local_server/static/data/processed/batch_20261009_231656/proc_cenital_5.png
 8,046,493 B  local_server/static/data/processed/batch_20261009_231656/proc_lateral_1.png
 8,043,409 B  local_server/static/data/processed/batch_20261009_231656/proc_lateral_2.png
 8,041,567 B  local_server/static/data/processed/batch_20261009_231656/proc_lateral_3.png
 8,045,484 B  local_server/static/data/processed/batch_20261009_231656/proc_lateral_4.png
 8,039,210 B  local_server/static/data/processed/batch_20261009_231656/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_233530/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_233530/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_233530/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_233530/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_233530/proc_cenital_5.png
 8,053,333 B  local_server/static/data/processed/batch_20261009_233530/proc_lateral_1.png
 8,048,572 B  local_server/static/data/processed/batch_20261009_233530/proc_lateral_2.png
 8,046,178 B  local_server/static/data/processed/batch_20261009_233530/proc_lateral_3.png
 8,052,170 B  local_server/static/data/processed/batch_20261009_233530/proc_lateral_4.png
 8,044,541 B  local_server/static/data/processed/batch_20261009_233530/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_233603/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_233603/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_233603/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_233603/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_233603/proc_cenital_5.png
 8,053,333 B  local_server/static/data/processed/batch_20261009_233603/proc_lateral_1.png
 8,048,572 B  local_server/static/data/processed/batch_20261009_233603/proc_lateral_2.png
 8,046,178 B  local_server/static/data/processed/batch_20261009_233603/proc_lateral_3.png
 8,052,170 B  local_server/static/data/processed/batch_20261009_233603/proc_lateral_4.png
 8,044,541 B  local_server/static/data/processed/batch_20261009_233603/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_233633/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_233633/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_233633/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_233633/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_233633/proc_cenital_5.png
 8,053,333 B  local_server/static/data/processed/batch_20261009_233633/proc_lateral_1.png
 8,048,572 B  local_server/static/data/processed/batch_20261009_233633/proc_lateral_2.png
 8,046,178 B  local_server/static/data/processed/batch_20261009_233633/proc_lateral_3.png
 8,052,170 B  local_server/static/data/processed/batch_20261009_233633/proc_lateral_4.png
 8,044,541 B  local_server/static/data/processed/batch_20261009_233633/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_233921/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_233921/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_233921/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_233921/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_233921/proc_cenital_5.png
 8,052,897 B  local_server/static/data/processed/batch_20261009_233921/proc_lateral_1.png
 8,048,119 B  local_server/static/data/processed/batch_20261009_233921/proc_lateral_2.png
 8,045,732 B  local_server/static/data/processed/batch_20261009_233921/proc_lateral_3.png
 8,051,765 B  local_server/static/data/processed/batch_20261009_233921/proc_lateral_4.png
 8,044,096 B  local_server/static/data/processed/batch_20261009_233921/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_233952/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_233952/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_233952/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_233952/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_233952/proc_cenital_5.png
 8,052,897 B  local_server/static/data/processed/batch_20261009_233952/proc_lateral_1.png
 8,048,119 B  local_server/static/data/processed/batch_20261009_233952/proc_lateral_2.png
 8,045,732 B  local_server/static/data/processed/batch_20261009_233952/proc_lateral_3.png
 8,051,765 B  local_server/static/data/processed/batch_20261009_233952/proc_lateral_4.png
 8,044,096 B  local_server/static/data/processed/batch_20261009_233952/proc_lateral_5.png
10,666,054 B  local_server/static/data/processed/batch_20261009_234023/proc_cenital_1.png
10,677,281 B  local_server/static/data/processed/batch_20261009_234023/proc_cenital_2.png
10,670,240 B  local_server/static/data/processed/batch_20261009_234023/proc_cenital_3.png
10,666,757 B  local_server/static/data/processed/batch_20261009_234023/proc_cenital_4.png
10,733,215 B  local_server/static/data/processed/batch_20261009_234023/proc_cenital_5.png
 8,052,897 B  local_server/static/data/processed/batch_20261009_234023/proc_lateral_1.png
 8,048,119 B  local_server/static/data/processed/batch_20261009_234023/proc_lateral_2.png
 8,045,732 B  local_server/static/data/processed/batch_20261009_234023/proc_lateral_3.png
 8,051,765 B  local_server/static/data/processed/batch_20261009_234023/proc_lateral_4.png
 8,044,096 B  local_server/static/data/processed/batch_20261009_234023/proc_lateral_5.png
       555 B  local_server/static/data/telemetry/telemetria_sensores_2026-10-09.csv
11,352,380 B  local_server/static/data/uploads/batch_20261008_190115/cenital_1.png
11,816,166 B  local_server/static/data/uploads/batch_20261008_190115/cenital_2.png
11,659,859 B  local_server/static/data/uploads/batch_20261008_190115/cenital_3.png
11,644,195 B  local_server/static/data/uploads/batch_20261008_190115/cenital_4.png
11,836,843 B  local_server/static/data/uploads/batch_20261008_190115/cenital_5.png
10,064,161 B  local_server/static/data/uploads/batch_20261008_190115/lateral_1.png
10,518,807 B  local_server/static/data/uploads/batch_20261008_190115/lateral_2.png
 8,525,957 B  local_server/static/data/uploads/batch_20261008_190115/lateral_3.png
10,729,282 B  local_server/static/data/uploads/batch_20261008_190115/lateral_4.png
 9,539,388 B  local_server/static/data/uploads/batch_20261008_190115/lateral_5.png
11,823,842 B  local_server/static/data/uploads/batch_20261008_191919/cenital_1.png
11,763,352 B  local_server/static/data/uploads/batch_20261008_191919/cenital_2.png
12,043,364 B  local_server/static/data/uploads/batch_20261008_191919/cenital_3.png
12,172,677 B  local_server/static/data/uploads/batch_20261008_191919/cenital_4.png
 7,567,122 B  local_server/static/data/uploads/batch_20261008_191919/lateral_1.png
 7,642,449 B  local_server/static/data/uploads/batch_20261008_191919/lateral_2.png
 8,030,530 B  local_server/static/data/uploads/batch_20261008_191919/lateral_3.png
 7,558,421 B  local_server/static/data/uploads/batch_20261008_191919/lateral_4.png
 7,528,492 B  local_server/static/data/uploads/batch_20261008_191919/lateral_5.png
11,352,380 B  local_server/static/data/uploads/batch_20261008_231043/cenital_1.png
11,816,166 B  local_server/static/data/uploads/batch_20261008_231043/cenital_2.png
11,659,859 B  local_server/static/data/uploads/batch_20261008_231043/cenital_3.png
11,644,195 B  local_server/static/data/uploads/batch_20261008_231043/cenital_4.png
11,836,843 B  local_server/static/data/uploads/batch_20261008_231043/cenital_5.png
10,064,161 B  local_server/static/data/uploads/batch_20261008_231043/lateral_1.png
10,518,807 B  local_server/static/data/uploads/batch_20261008_231043/lateral_2.png
 8,525,957 B  local_server/static/data/uploads/batch_20261008_231043/lateral_3.png
10,729,282 B  local_server/static/data/uploads/batch_20261008_231043/lateral_4.png
 9,539,388 B  local_server/static/data/uploads/batch_20261008_231043/lateral_5.png
11,352,380 B  local_server/static/data/uploads/batch_20261009_123838/cenital_1.png
11,816,166 B  local_server/static/data/uploads/batch_20261009_123838/cenital_2.png
11,659,859 B  local_server/static/data/uploads/batch_20261009_123838/cenital_3.png
11,644,195 B  local_server/static/data/uploads/batch_20261009_123838/cenital_4.png
11,836,843 B  local_server/static/data/uploads/batch_20261009_123838/cenital_5.png
10,058,336 B  local_server/static/data/uploads/batch_20261009_123838/lateral_1.png
10,512,650 B  local_server/static/data/uploads/batch_20261009_123838/lateral_2.png
 8,520,338 B  local_server/static/data/uploads/batch_20261009_123838/lateral_3.png
10,724,373 B  local_server/static/data/uploads/batch_20261009_123838/lateral_4.png
 9,532,987 B  local_server/static/data/uploads/batch_20261009_123838/lateral_5.png
10,588,684 B  local_server/static/data/uploads/batch_20261009_123907/cenital_1.png
11,322,230 B  local_server/static/data/uploads/batch_20261009_123907/cenital_2.png
11,268,003 B  local_server/static/data/uploads/batch_20261009_123907/cenital_3.png
11,834,279 B  local_server/static/data/uploads/batch_20261009_123907/cenital_4.png
11,712,079 B  local_server/static/data/uploads/batch_20261009_123907/cenital_5.png
11,903,813 B  local_server/static/data/uploads/batch_20261009_123907/lateral_1.png
 9,648,876 B  local_server/static/data/uploads/batch_20261009_123907/lateral_2.png
 8,436,137 B  local_server/static/data/uploads/batch_20261009_123907/lateral_3.png
 9,658,922 B  local_server/static/data/uploads/batch_20261009_123907/lateral_4.png
10,309,234 B  local_server/static/data/uploads/batch_20261009_123907/lateral_5.png
10,733,918 B  local_server/static/data/uploads/batch_20261009_124008/cenital_1.png
10,767,760 B  local_server/static/data/uploads/batch_20261009_124008/cenital_2.png
10,800,997 B  local_server/static/data/uploads/batch_20261009_124008/cenital_3.png
10,862,559 B  local_server/static/data/uploads/batch_20261009_124008/cenital_4.png
11,002,889 B  local_server/static/data/uploads/batch_20261009_124008/cenital_5.png
 8,461,052 B  local_server/static/data/uploads/batch_20261009_124008/lateral_1.png
 8,374,188 B  local_server/static/data/uploads/batch_20261009_124008/lateral_2.png
 9,114,446 B  local_server/static/data/uploads/batch_20261009_124008/lateral_3.png
 9,033,140 B  local_server/static/data/uploads/batch_20261009_124008/lateral_4.png
10,082,854 B  local_server/static/data/uploads/batch_20261009_124008/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200002/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200002/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200002/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200002/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200002/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200002/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200002/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200002/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200002/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200002/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200028/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200028/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200028/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200028/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200028/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200028/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200028/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200028/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200028/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200028/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200048/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200048/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200048/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200048/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200048/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200048/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200048/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200048/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200048/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200048/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200512/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200512/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200512/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200512/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200512/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200512/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200512/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200512/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200512/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200512/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200616/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200616/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200616/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200616/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200616/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200616/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200616/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200616/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200616/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200616/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_200659/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_200659/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_200659/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_200659/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_200659/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_200659/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_200659/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_200659/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_200659/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_200659/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_201835/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_201835/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_201835/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_201835/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_201835/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_201835/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_201835/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_201835/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_201835/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_201835/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_201940/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_201940/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_201940/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_201940/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_201940/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_201940/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_201940/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_201940/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_201940/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_201940/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_202043/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_202043/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_202043/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_202043/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_202043/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_202043/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_202043/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_202043/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_202043/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_202043/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_202755/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_202755/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_202755/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_202755/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_202755/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_202755/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_202755/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_202755/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_202755/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_202755/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_202857/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_202857/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_202857/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_202857/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_202857/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_202857/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_202857/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_202857/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_202857/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_202857/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_203000/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_203000/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_203000/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_203000/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_203000/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_203000/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_203000/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_203000/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_203000/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_203000/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_204402/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_204402/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_204402/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_204402/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_204402/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_204402/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_204402/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_204402/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_204402/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_204402/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_204506/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_204506/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_204506/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_204506/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_204506/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_204506/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_204506/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_204506/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_204506/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_204506/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_204611/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_204611/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_204611/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_204611/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_204611/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_204611/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_204611/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_204611/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_204611/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_204611/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_223406/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_223406/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_223406/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_223406/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_223406/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_223406/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_223406/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_223406/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_223406/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_223406/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_223511/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_223511/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_223511/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_223511/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_223511/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_223511/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_223511/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_223511/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_223511/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_223511/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_223618/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_223618/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_223618/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_223618/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_223618/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_223618/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_223618/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_223618/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_223618/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_223618/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_231448/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_231448/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_231448/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_231448/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_231448/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_231448/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_231448/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_231448/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_231448/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_231448/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_231554/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_231554/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_231554/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_231554/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_231554/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_231554/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_231554/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_231554/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_231554/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_231554/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_231656/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_231656/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_231656/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_231656/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_231656/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_231656/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_231656/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_231656/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_231656/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_231656/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_233530/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_233530/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_233530/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_233530/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_233530/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_233530/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_233530/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_233530/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_233530/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_233530/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_233603/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_233603/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_233603/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_233603/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_233603/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_233603/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_233603/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_233603/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_233603/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_233603/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_233633/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_233633/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_233633/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_233633/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_233633/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_233633/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_233633/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_233633/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_233633/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_233633/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_233921/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_233921/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_233921/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_233921/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_233921/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_233921/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_233921/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_233921/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_233921/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_233921/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_233952/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_233952/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_233952/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_233952/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_233952/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_233952/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_233952/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_233952/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_233952/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_233952/lateral_5.png
10,641,223 B  local_server/static/data/uploads/batch_20261009_234023/cenital_1.png
10,651,608 B  local_server/static/data/uploads/batch_20261009_234023/cenital_2.png
10,641,576 B  local_server/static/data/uploads/batch_20261009_234023/cenital_3.png
10,641,830 B  local_server/static/data/uploads/batch_20261009_234023/cenital_4.png
10,707,323 B  local_server/static/data/uploads/batch_20261009_234023/cenital_5.png
 8,026,760 B  local_server/static/data/uploads/batch_20261009_234023/lateral_1.png
 8,021,999 B  local_server/static/data/uploads/batch_20261009_234023/lateral_2.png
 8,019,541 B  local_server/static/data/uploads/batch_20261009_234023/lateral_3.png
 8,025,654 B  local_server/static/data/uploads/batch_20261009_234023/lateral_4.png
 8,018,084 B  local_server/static/data/uploads/batch_20261009_234023/lateral_5.png
    73,611 B  local_server/static/img/blanco con texo (1).svg
 9,637,009 B  local_server/static/img/cenital_1.png
    73,680 B  local_server/static/img/sifma_con_texto.svg
    98,157 B  local_server/static/img/sifma_icon.ico
    61,558 B  local_server/static/img/sifma_icon.png
       507 B  local_server/static/img/sifma_investigacion_canastilla_1.csv
    69,391 B  local_server/static/img/sifma_logo.svg
    69,391 B  local_server/static/img/sifma_sin_texto.svg
    69,453 B  local_server/static/img/sin texto blanco.svg
   107,783 B  local_server/static/img/telemetria_actualizada_2026-10-08.csv
     7,608 B  local_server/static/js/dashboard.js
     4,906 B  local_server/static/js/processing.js
     4,424 B  local_server/static/js/sensors.js
    61,558 B  local_server/static/uploads/avatars/avatar_3_1791682057.png
 5,421,945 B  local_server/static/uploads/avatars/avatar_4_1791681738.png
    23,235 B  local_server/templates/about.html
    19,980 B  local_server/templates/audit_logs.html
    33,317 B  local_server/templates/base.html
    18,740 B  local_server/templates/benchmark.html
    31,856 B  local_server/templates/calendar.html
    80,769 B  local_server/templates/config.html
    87,864 B  local_server/templates/cross_analysis.html
    29,719 B  local_server/templates/dashboard.html
     1,414 B  local_server/templates/error.html
    42,036 B  local_server/templates/gallery.html
     4,189 B  local_server/templates/login.html
    44,645 B  local_server/templates/processing.html
    92,499 B  local_server/templates/scientific_report.html
    58,875 B  local_server/templates/sensors.html
    24,754 B  local_server/templates/timelapse.html
    36,994 B  local_server/templates/users.html
       139 B  raspi_node/.gitignore
     2,303 B  raspi_node/README.md
       303 B  raspi_node/SIFMA_Calibracion.desktop
       297 B  raspi_node/SIFMA_Control.desktop
    22,711 B  raspi_node/calibrate_cameras.py
       438 B  raspi_node/config.json
     2,380 B  raspi_node/configurar_camaras_dual.sh
     3,037 B  raspi_node/dependencies.py
     3,288 B  raspi_node/install_autostart.sh
    15,271 B  raspi_node/main_capture.py
    11,924 B  raspi_node/panel_app.py
    21,961 B  raspi_node/panel_touch_lite.py
       258 B  raspi_node/requirements.txt
       161 B  raspi_node/services/__init__.py
     8,184 B  raspi_node/services/camera_service.py
     5,643 B  raspi_node/services/storage_service.py
       409 B  raspi_node/sifma-capture.service
       395 B  raspi_node/sifma-panel.service
    35,000 B  raspi_node/templates/index.html
```
