# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

import os
from flask import jsonify, request, session
from application.services import AuditService, ReportArchiveService
from . import api_bp

audit_service = AuditService.get_instance()


@api_bp.route("/api/reports/archive", methods=["GET"])
def list_archived_reports():
    """Lista y filtra los reportes PDF guardados en la carpeta predeterminada de SIFMA."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    query = (request.args.get("q") or "").strip()
    date_filter = (request.args.get("date") or "").strip()

    reports = ReportArchiveService.list_reports(query=query, date_filter=date_filter)
    return jsonify({
        "status": "success",
        "reports_dir": ReportArchiveService.get_reports_dir(),
        "total": len(reports),
        "reports": reports,
    })


@api_bp.route("/api/reports/save_pdf", methods=["POST"])
def save_report_to_archive():
    """
    Exporta el reporte científico actual directamente a la carpeta predeterminada de reportes
    (%APPDATA%\\SIFMA\\data\\reports) con el nombre oficial INFORME ID (+ etiqueta opcional).
    """
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    data = request.json or {}
    report_id = (data.get("report_id") or "").strip()
    custom_name = (data.get("custom_name") or "").strip()
    target_date = (data.get("target_date") or "").strip()
    plant_id = int(data.get("plant_id") or 1)
    crop_name = (data.get("crop_name") or "").strip()
    author = (data.get("author") or session.get("user_name") or "Administrador SIFMA").strip()

    filename = ReportArchiveService.build_report_filename(report_id, custom_name)
    reports_dir = ReportArchiveService.get_reports_dir()
    output_path = os.path.join(reports_dir, filename)

    exported = ReportArchiveService.export_current_webview_to_pdf(output_path)
    if exported:
        entry = ReportArchiveService.register_saved_pdf(
            filename=filename,
            report_id=report_id,
            custom_name=custom_name,
            target_date=target_date,
            plant_id=plant_id,
            crop_name=crop_name,
            author=author,
        )
        audit_service.log(
            action="SAVE_REPORT_PDF",
            module="REPORTES",
            description=f"Guardó el reporte PDF '{filename}' en la carpeta predeterminada de reportes.",
            level="success",
            action_display="Guardado de Reporte PDF",
        )
        return jsonify({
            "status": "success",
            "mode": "direct_webview_pdf",
            "message": f"Reporte guardado en carpeta de reportes como {filename}",
            "report": entry,
            "reports_dir": reports_dir,
        })

    # Si se abrió desde un navegador externo fuera de PyWebView, devolver el nombre sugerido para window.print()
    return jsonify({
        "status": "fallback_print",
        "filename": filename,
        "suggested_title": filename[:-4] if filename.lower().endswith(".pdf") else filename,
        "reports_dir": reports_dir,
        "message": "Usa el diálogo de impresión para guardar el PDF en la carpeta de reportes.",
    })


@api_bp.route("/api/reports/upload_pdf", methods=["POST"])
def upload_external_report_pdf():
    """Permite importar o registrar un archivo PDF dentro de la carpeta predeterminada de reportes."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No se seleccionó ningún archivo PDF."}), 400

    file = request.files["file"]
    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"status": "error", "message": "El archivo debe tener formato .pdf"}), 400

    custom_name = (request.form.get("custom_name") or "").strip()
    target_date = (request.form.get("target_date") or "").strip()
    report_id = (request.form.get("report_id") or "").strip()

    raw_name = os.path.basename(file.filename)
    inferred = ReportArchiveService.extract_meta_from_filename(raw_name)
    effective_report_id = report_id or inferred["report_id"]
    effective_custom = custom_name if custom_name else inferred["custom_name"]

    final_filename = ReportArchiveService.build_report_filename(effective_report_id, effective_custom)
    reports_dir = ReportArchiveService.get_reports_dir()
    dest_path = os.path.join(reports_dir, final_filename)
    file.save(dest_path)

    entry = ReportArchiveService.register_saved_pdf(
        filename=final_filename,
        report_id=effective_report_id,
        custom_name=effective_custom,
        target_date=target_date or inferred["target_date"],
        plant_id=inferred["plant_id"],
        author=session.get("user_name") or "Administrador SIFMA",
    )
    return jsonify({
        "status": "success",
        "message": f"Reporte '{final_filename}' archivado correctamente.",
        "report": entry,
    })


@api_bp.route("/api/reports/rename", methods=["POST"])
def rename_archived_report():
    """Permite asignar o cambiar el nombre adicional de un reporte PDF guardado."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    data = request.json or {}
    filename = (data.get("filename") or "").strip()
    custom_name = (data.get("custom_name") or "").strip()
    if not filename:
        return jsonify({"status": "error", "message": "Nombre de archivo requerido."}), 400

    updated = ReportArchiveService.rename_report(filename, custom_name)
    if not updated:
        return jsonify({"status": "error", "message": "No se encontró el archivo PDF solicitado."}), 404

    return jsonify({
        "status": "success",
        "message": f"Reporte renombrado a '{updated['filename']}'.",
        "report": updated,
    })


@api_bp.route("/api/reports/delete", methods=["POST", "DELETE"])
def delete_archived_report():
    """Elimina un reporte PDF del archivo local."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    data = request.json or {}
    filename = (data.get("filename") or "").strip()
    if not filename:
        return jsonify({"status": "error", "message": "Nombre de archivo requerido."}), 400

    ok = ReportArchiveService.delete_report(filename)
    if not ok:
        return jsonify({"status": "error", "message": "No se pudo eliminar el archivo PDF."}), 404

    return jsonify({"status": "success", "message": f"Reporte '{filename}' eliminado."})


@api_bp.route("/api/reports/open_folder", methods=["POST"])
def open_reports_archive_folder():
    """Abre la carpeta predeterminada donde se guardan los reportes PDF en el Explorador de Windows."""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "No autorizado."}), 401

    ok = ReportArchiveService.open_reports_folder_in_explorer()
    return jsonify({
        "status": "success" if ok else "error",
        "reports_dir": ReportArchiveService.get_reports_dir(),
    })
