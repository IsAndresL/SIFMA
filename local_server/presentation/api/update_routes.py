# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import os
import subprocess
import sys
from flask import jsonify, request, session, send_file, after_this_request
from application.services import AuditService, UpdateService, BackupService
from core.config import config
from . import api_bp

audit_service = AuditService.get_instance()


@api_bp.route("/api/system/update/check", methods=["GET"])
def check_system_updates():
    """Consulta si existe una nueva versión oficial en GitHub Releases y reporta el estado de protección de datos."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    result = UpdateService.check_for_updates()
    return jsonify(result)


@api_bp.route("/api/system/update/apply", methods=["POST"])
def apply_system_update():
    """Descarga y aplica una actualización del ejecutable preservando la base de datos e imágenes locales."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    is_admin = (
        session.get("user_role") == "admin"
        or session.get("is_admin") is True
        or session.get("is_super_admin") is True
    )
    if not is_admin:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Solo el Super Administrador puede instalar actualizaciones del sistema.",
                }
            ),
            403,
        )

    data = request.json or {}
    download_url = (data.get("download_url") or "").strip()
    if not download_url:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "No se especificó un paquete ejecutable (.exe) válido en el Release.",
                }
            ),
            400,
        )

    try:
        res = UpdateService.download_and_apply_update(download_url)
        audit_service.log(
            action="SYSTEM_UPDATE",
            module="SISTEMA",
            description=f"Inició actualización segura del ejecutable desde GitHub Releases ({download_url}).",
            level="info",
            action_display="Actualización de Software",
        )
        return jsonify(res)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fallo al aplicar actualización: {e}"}), 500


@api_bp.route("/api/system/open_data_folder", methods=["POST"])
def open_protected_data_folder():
    """Abre en el Explorador de Windows la carpeta protegida de datos locales (%APPDATA%\\SIFMA)."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    target_dir = os.path.abspath(config.USER_DATA_DIR)
    os.makedirs(target_dir, exist_ok=True)
    try:
        if sys.platform.startswith("win"):
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target_dir])
        else:
            subprocess.Popen(["xdg-open", target_dir])
        return jsonify(
            {
                "status": "success",
                "path": target_dir,
                "message": f"Carpeta de datos abierta: {target_dir}",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"No se pudo abrir la carpeta: {e}"}), 500


@api_bp.route("/api/system/backup/export", methods=["GET"])
def export_full_system_backup():
    """Genera y descarga un paquete .sifma-backup.zip con toda la base de datos SQLite, fotos y reportes PDF."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    try:
        zip_path, download_name = BackupService.create_full_backup_zip()
        temp_dir = os.path.dirname(zip_path)

        @after_this_request
        def _cleanup_temp_backup(response):
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
            return response

        audit_service.log(
            action="EXPORT_BACKUP",
            module="SISTEMA",
            description=f"Exportó respaldo completo de base de datos y archivos locales ({download_name}).",
            level="info",
            action_display="Exportación de Respaldo Completo",
        )
        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name=download_name,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al generar respaldo: {e}"}), 500


@api_bp.route("/api/system/backup/restore", methods=["POST"])
def restore_full_system_backup():
    """Restaura un respaldo completo (.sifma-backup.zip / .zip) en este PC."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No se seleccionó ningún archivo de respaldo (.zip)."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"status": "error", "message": "Archivo inválido."}), 400

    try:
        result = BackupService.restore_full_backup_zip(uploaded)
        audit_service.log(
            action="RESTORE_BACKUP",
            module="SISTEMA",
            description=f"Restauró respaldo completo desde '{uploaded.filename}' ({result.get('restored_files', 0)} archivos).",
            level="warning",
            action_display="Restauración de Respaldo Completo",
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al restaurar respaldo: {e}"}), 500


