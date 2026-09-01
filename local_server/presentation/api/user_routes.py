from flask import request, jsonify, session
from application.services import UserService
from core.security import SecurityService
from . import api_bp

user_service = UserService()

def require_admin():
    """Verifica si la sesión actual pertenece a un Administrador."""
    return session.get('user_role') == 'admin' or session.get('is_admin') is True

@api_bp.route('/api/users', methods=['GET'])
def get_users_list():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "No autorizado."}), 401
    users = user_service.get_all_users()
    return jsonify({
        "status": "success",
        "count": len(users),
        "users": [u.to_dict() for u in users]
    })

@api_bp.route('/api/users', methods=['POST'])
def create_new_user():
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    data = request.json or {}
    username = SecurityService.sanitize_text(data.get('username', ''), 40)
    full_name = SecurityService.sanitize_text(data.get('full_name', ''), 100)
    email = SecurityService.sanitize_text(data.get('email', ''), 100)
    password = data.get('password', '')
    role = SecurityService.sanitize_text(data.get('role', 'investigador'), 30)

    if not username or not full_name or not password:
        return jsonify({"status": "error", "message": "El nombre de usuario, nombre completo y contraseña son obligatorios."}), 400

    try:
        new_user = user_service.create_user(
            username=username,
            full_name=full_name,
            plain_password=password,
            role=role,
            email=email if email else None
        )
        return jsonify({
            "status": "success",
            "message": f"Usuario '{new_user.username}' creado con éxito.",
            "user": new_user.to_dict()
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Error interno al crear usuario."}), 500

@api_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user_details(user_id: int):
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    data = request.json or {}
    full_name = SecurityService.sanitize_text(data.get('full_name'), 100) if data.get('full_name') else None
    email = SecurityService.sanitize_text(data.get('email'), 100) if data.get('email') else None
    role = SecurityService.sanitize_text(data.get('role'), 30) if data.get('role') else None

    try:
        updated = user_service.update_user(user_id=user_id, full_name=full_name, email=email, role=role)
        if not updated:
            return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
        return jsonify({
            "status": "success",
            "message": "Usuario actualizado correctamente.",
            "user": updated.to_dict()
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route('/api/users/<int:user_id>/toggle_active', methods=['POST'])
def toggle_user_status(user_id: int):
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    user = user_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    try:
        new_status = not user.is_active
        updated = user_service.update_user(user_id=user_id, is_active=new_status)
        action_str = "activado" if new_status else "desactivado"
        return jsonify({
            "status": "success",
            "message": f"Usuario '{updated.username}' {action_str}.",
            "is_active": updated.is_active
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
def reset_user_password(user_id: int):
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    data = request.json or {}
    new_pass = data.get('password', '')
    if not new_pass or len(new_pass) < 4:
        return jsonify({"status": "error", "message": "La contraseña debe tener al menos 4 caracteres."}), 400

    success = user_service.update_password(user_id, new_pass)
    if not success:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    return jsonify({"status": "success", "message": "Contraseña restablecida exitosamente."})

@api_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    try:
        success = user_service.delete_user(user_id)
        if not success:
            return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
        return jsonify({"status": "success", "message": "Usuario eliminado correctamente."})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
