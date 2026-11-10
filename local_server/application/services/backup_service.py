# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from typing import Dict, Any, Tuple
from core.config import config as app_settings
from core.logger import logger
from infrastructure.database.connection import db


class BackupService:
    """
    Servicio para exportar y restaurar copias de seguridad completas de SIFMA (.zip).
    Empaqueta de forma atómica y consistente la base de datos SQLite (sifma.db),
    las fotografías originales y segmentadas (uploads, processed), archivos de telemetría
    y los reportes PDF archivados, permitiendo migrar todo el sistema entre equipos.
    """

    MANIFEST_NAME = "sifma_backup_manifest.json"

    @classmethod
    def get_backup_summary(cls) -> Dict[str, Any]:
        """Calcula el resumen actual de la base de datos y archivos locales que se incluirán en el respaldo."""
        db_path = os.path.abspath(app_settings.DB_PATH)
        data_dir = os.path.abspath(app_settings.DATA_DIR)

        db_size_kb = round(os.path.getsize(db_path) / 1024.0, 1) if os.path.exists(db_path) else 0.0

        file_counts = {"uploads": 0, "processed": 0, "reports": 0, "telemetry": 0, "other": 0}
        total_files = 0
        total_data_bytes = 0

        if os.path.exists(data_dir):
            for root, _, files in os.walk(data_dir):
                rel_root = os.path.relpath(root, data_dir).replace("\\", "/")
                for f in files:
                    fpath = os.path.join(root, f)
                    try:
                        total_data_bytes += os.path.getsize(fpath)
                        total_files += 1
                        if rel_root.startswith("uploads"):
                            file_counts["uploads"] += 1
                        elif rel_root.startswith("processed"):
                            file_counts["processed"] += 1
                        elif rel_root.startswith("reports") and f.lower().endswith(".pdf"):
                            file_counts["reports"] += 1
                        elif rel_root.startswith("telemetry"):
                            file_counts["telemetry"] += 1
                        else:
                            file_counts["other"] += 1
                    except Exception:
                        pass

        total_mb = round((total_data_bytes + (os.path.getsize(db_path) if os.path.exists(db_path) else 0)) / (1024.0 * 1024.0), 2)

        return {
            "db_path": db_path,
            "data_dir": data_dir,
            "db_size_kb": db_size_kb,
            "total_files": total_files,
            "total_size_mb": total_mb,
            "counts": file_counts,
        }

    @classmethod
    def create_full_backup_zip(cls) -> Tuple[str, str]:
        """
        Crea un archivo .zip temporal con la copia consistente de sifma.db (usando sqlite3.backup)
        y toda la estructura de DATA_DIR (uploads, processed, telemetry, reports, avatars).
        Retorna (ruta_al_zip, nombre_descarga).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_name = f"SIFMA_Respaldo_Completo_{timestamp}.sifma-backup.zip"

        temp_dir = tempfile.mkdtemp(prefix="sifma_bkp_")
        zip_path = os.path.join(temp_dir, download_name)
        db_snapshot_path = os.path.join(temp_dir, "sifma.db")

        # 1. Crear copia consistente en caliente de SQLite (incluyendo transacciones en WAL)
        src_db_path = os.path.abspath(app_settings.DB_PATH)
        if os.path.exists(src_db_path):
            src_conn = sqlite3.connect(src_db_path)
            dst_conn = sqlite3.connect(db_snapshot_path)
            try:
                with dst_conn:
                    src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

        summary = cls.get_backup_summary()
        manifest = {
            "system": "SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental",
            "app_version": app_settings.APP_VERSION,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "db_size_kb": summary["db_size_kb"],
            "total_files": summary["total_files"],
            "counts": summary["counts"],
        }

        # 2. Empaquetar manifiesto, sifma.db y todo el contenido de DATA_DIR
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(cls.MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))

            if os.path.exists(db_snapshot_path):
                zf.write(db_snapshot_path, arcname="sifma.db")

            data_dir = os.path.abspath(app_settings.DATA_DIR)
            if os.path.exists(data_dir):
                for root, _, files in os.walk(data_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, data_dir).replace("\\", "/")
                        zf.write(full_path, arcname=f"data/{rel_path}")

        try:
            if os.path.exists(db_snapshot_path):
                os.remove(db_snapshot_path)
        except Exception:
            pass

        logger.info(f"Respaldo completo generado exitosamente: {download_name}")
        return zip_path, download_name

    @classmethod
    def restore_full_backup_zip(cls, uploaded_file_storage) -> Dict[str, Any]:
        """
        Valida y restaura un paquete .sifma-backup.zip (o .zip) reemplazando de forma segura
        la base de datos SQLite y fusionando/restaurando las carpetas de imágenes, telemetría y reportes.
        """
        temp_dir = tempfile.mkdtemp(prefix="sifma_restore_")
        temp_zip_path = os.path.join(temp_dir, "uploaded_backup.zip")

        try:
            uploaded_file_storage.save(temp_zip_path)
            if not zipfile.is_zipfile(temp_zip_path):
                raise ValueError("El archivo seleccionado no es un paquete ZIP válido.")

            with zipfile.ZipFile(temp_zip_path, "r") as zf:
                namelist = zf.namelist()
                has_db = "sifma.db" in namelist
                if not has_db:
                    raise ValueError("El archivo ZIP no contiene una base de datos 'sifma.db' de SIFMA.")

                # Extraer a directorio temporal seguro verificando que no haya Path Traversal
                extract_root = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_root, exist_ok=True)
                for member in zf.infolist():
                    norm_name = os.path.normpath(member.filename)
                    if norm_name.startswith("..") or os.path.isabs(norm_name):
                        continue
                    zf.extract(member, extract_root)

            extracted_db = os.path.join(extract_root, "sifma.db")
            extracted_data = os.path.join(extract_root, "data")

            # Verificar que sifma.db extraído sea una base SQLite íntegra
            chk_conn = sqlite3.connect(extracted_db)
            try:
                cur = chk_conn.cursor()
                cur.execute("PRAGMA integrity_check;")
                res = cur.fetchone()
                if not res or res[0].lower() != "ok":
                    raise ValueError("La base de datos dentro del respaldo está dañada.")
            finally:
                chk_conn.close()

            # Cerrar conexiones activas de SQLAlchemy antes de restaurar la base de datos
            try:
                db.session.remove()
                db.engine.dispose()
            except Exception:
                pass

            target_db_path = os.path.abspath(app_settings.DB_PATH)
            os.makedirs(os.path.dirname(target_db_path), exist_ok=True)

            # Restaurar sifma.db usando la API nativa sqlite3.backup para evitar bloqueos de archivos en Windows
            src_conn = sqlite3.connect(extracted_db)
            dst_conn = sqlite3.connect(target_db_path)
            try:
                with dst_conn:
                    src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

            # Si fallara o quedaran archivos -wal / -shm antiguos desincronizados, sqlite3.backup ya sincronizó el estado
            restored_files_count = 0
            target_data_dir = os.path.abspath(app_settings.DATA_DIR)
            os.makedirs(target_data_dir, exist_ok=True)

            if os.path.exists(extracted_data):
                for root, _, files in os.walk(extracted_data):
                    rel_dir = os.path.relpath(root, extracted_data)
                    dest_dir = target_data_dir if rel_dir == "." else os.path.join(target_data_dir, rel_dir)
                    os.makedirs(dest_dir, exist_ok=True)
                    for f in files:
                        src_file = os.path.join(root, f)
                        dst_file = os.path.join(dest_dir, f)
                        shutil.copy2(src_file, dst_file)
                        restored_files_count += 1

            # Ejecutar migraciones suaves / semilla por si el respaldo proviene de una versión anterior
            try:
                from flask import current_app
                from infrastructure.database.seed import init_db_data
                init_db_data(current_app._get_current_object())
            except Exception as e:
                logger.warning(f"Verificación post-restauración: {e}")

            return {
                "status": "success",
                "restored_files": restored_files_count,
                "message": f"Base de datos y {restored_files_count} archivos operativos restaurados exitosamente en este PC.",
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
