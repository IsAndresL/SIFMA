import os
from flask import request, jsonify, session, current_app
from infrastructure.database.repositories import CaptureSessionRepository, SensorRepository
from . import api_bp

session_repo = CaptureSessionRepository()
sensor_repo = SensorRepository()

@api_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_capture_session(session_id: int):
    session_record = session_repo.get_by_id(session_id)
    if not session_record:
        return jsonify({"status": "error", "message": "Sesión no encontrada."}), 404

    static_folder = current_app.static_folder
    batch_dirs_to_clean = set()
    
    for m in session_record.metrics:
        for path_attr in ['image_path_cenital_orig', 'image_path_cenital_proc', 'image_path_lateral_orig', 'image_path_lateral_proc']:
            rel_path = getattr(m, path_attr, None)
            if rel_path:
                full_path = os.path.join(static_folder, rel_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        batch_dirs_to_clean.add(os.path.dirname(full_path))
                    except Exception:
                        pass

    for b_dir in batch_dirs_to_clean:
        try:
            if os.path.exists(b_dir) and not os.listdir(b_dir):
                os.rmdir(b_dir)
        except Exception:
            pass

    session_repo.delete(session_record)
    return jsonify({"status": "success", "message": "Período de fotos y métricas eliminados exitosamente."})

@api_bp.route('/api/sessions/by_date', methods=['DELETE'])
def delete_sessions_by_date():
    date_str = request.args.get('date')
    plant_id = request.args.get('plant_id', session.get('active_plant_id', 1))

    if not date_str:
        return jsonify({"status": "error", "message": "Parámetro 'date' es requerido."}), 400

    count = session_repo.delete_by_date(date_str, int(plant_id))
    return jsonify({"status": "success", "message": f"Se eliminaron {count} períodos de fotos correspondientes a la fecha {date_str}."})

@api_bp.route('/api/telemetry/by_date', methods=['DELETE'])
def delete_telemetry_by_date():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"status": "error", "message": "Parámetro 'date' es requerido."}), 400

    deleted_count = sensor_repo.delete_by_date(date_str)
    return jsonify({"status": "success", "message": f"Se eliminaron {deleted_count} lecturas de sensores ({date_str}).", "deleted_count": deleted_count})
