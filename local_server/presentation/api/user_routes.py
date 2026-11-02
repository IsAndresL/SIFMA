from flask import request, jsonify, session
from application.services import UserService, AuditService
from core.security import SecurityService
from . import api_bp

user_service = UserService()
audit_service = AuditService.get_instance()

def require_admin():
    """Verifica si la sesión actual pertenece a un Administrador."""
    return session.get('user_role') == 'admin' or session.get('is_admin') is True or session.get('is_super_admin') is True

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

    # Soportar payload JSON o FormData multipart
    data = {}
    if request.is_json:
        data = request.json or {}
    else:
        data = request.form.to_dict()
        if 'permissions' in data and isinstance(data['permissions'], str):
            import json
            try:
                data['permissions'] = json.loads(data['permissions'])
            except Exception:
                pass

    username = SecurityService.sanitize_text(data.get('username', ''), 40)
    full_name = SecurityService.sanitize_text(data.get('full_name', ''), 100)
    email = SecurityService.sanitize_text(data.get('email', ''), 100)
    password = data.get('password', '')
    role = SecurityService.sanitize_text(data.get('role', 'investigador'), 30)
    permissions = data.get('permissions')

    if not username or not full_name or not password:
        return jsonify({"status": "error", "message": "El nombre de usuario, nombre completo y contraseña son obligatorios."}), 400

    try:
        new_user = user_service.create_user(
            username=username,
            full_name=full_name,
            plain_password=password,
            role=role,
            email=email if email else None,
            permissions=permissions
        )

        # Si se adjuntó foto de perfil en el FormData
        avatar_file = request.files.get('avatar') or request.files.get('file')
        if avatar_file and avatar_file.filename:
            try:
                user_service.save_user_avatar(new_user.id, avatar_file)
            except Exception as e:
                pass
        
        # Registrar en logs de auditoría
        perms_count = sum(1 for v in (permissions or {}).values() if v) if permissions else "estándar"
        audit_service.log(
            action="CREATE_USER",
            module="USUARIOS",
            description=f"Creó al usuario '@{new_user.username}' ({new_user.full_name}) con rol '{new_user.role_display}' y {perms_count} funciones asignadas.",
            level="success",
            action_display="Creación de Usuario"
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
    permissions = data.get('permissions')

    try:
        updated = user_service.update_user(
            user_id=user_id, 
            full_name=full_name, 
            email=email, 
            role=role,
            permissions=permissions
        )
        if not updated:
            return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404
            
        audit_service.log(
            action="UPDATE_USER",
            module="USUARIOS",
            description=f"Modificó la cuenta del usuario '@{updated.username}' ({updated.full_name}) - Rol: {updated.role_display}.",
            level="info",
            action_display="Edición de Usuario"
        )

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
        action_str = "reactivado" if new_status else "pausado / desactivado"
        
        audit_service.log(
            action="TOGGLE_USER_STATUS",
            module="USUARIOS",
            description=f"{'Reactivó' if new_status else 'Pausó'} la cuenta del usuario '@{user.username}' ({user.full_name}).",
            level="warning" if not new_status else "info",
            action_display="Cambio de Estado de Usuario"
        )

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

    user = user_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    data = request.json or {}
    new_pass = data.get('password', '')
    if not new_pass or len(new_pass) < 4:
        return jsonify({"status": "error", "message": "La contraseña debe tener al menos 4 caracteres."}), 400

    success = user_service.update_password(user_id, new_pass)
    if not success:
        return jsonify({"status": "error", "message": "Error al actualizar contraseña."}), 500

    audit_service.log(
        action="CHANGE_PASSWORD",
        module="USUARIOS",
        description=f"Restableció la contraseña del usuario '@{user.username}' ({user.full_name}).",
        level="warning",
        action_display="Cambio de Contraseña"
    )

    return jsonify({"status": "success", "message": "Contraseña restablecida exitosamente."})

@api_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    if not require_admin():
        return jsonify({"status": "error", "message": "Acceso restringido a Administradores."}), 403

    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    target_name = target_user.username
    target_full = target_user.full_name

    try:
        success = user_service.delete_user(user_id)
        if not success:
            return jsonify({"status": "error", "message": "Error al eliminar usuario."}), 500

        audit_service.log(
            action="DELETE_USER",
            module="USUARIOS",
            description=f"Eliminó permanentemente la cuenta de usuario '@{target_name}' ({target_full}) con ID {user_id}.",
            level="danger",
            action_display="Eliminación de Usuario"
        )

        return jsonify({"status": "success", "message": "Usuario eliminado correctamente."})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route('/api/users/<int:user_id>/avatar', methods=['POST'])
def upload_user_avatar(user_id: int):
    # Solo el Super Admin o el propio usuario puede cambiar su avatar
    is_admin = require_admin()
    current_uid = session.get('user_id')
    if not is_admin and current_uid != user_id:
        return jsonify({"status": "error", "message": "No tienes permiso para modificar este avatar."}), 403

    avatar_file = request.files.get('avatar') or request.files.get('file') or request.files.get('image')
    if not avatar_file or not avatar_file.filename:
        return jsonify({"status": "error", "message": "No se recibió ningún archivo de imagen."}), 400

    try:
        avatar_url = user_service.save_user_avatar(user_id, avatar_file)
        target_user = user_service.get_user_by_id(user_id)

        # Si el usuario editado es el de la sesión actual, actualizar sesión
        if current_uid == user_id:
            session['user_avatar_url'] = avatar_url

        audit_service.log(
            action="UPDATE_AVATAR",
            module="USUARIOS",
            description=f"Actualizó la foto de perfil / avatar del usuario '@{target_user.username}'.",
            level="info",
            action_display="Cambio de Avatar"
        )

        return jsonify({
            "status": "success",
            "message": "Foto de perfil actualizada correctamente.",
            "avatar_url": avatar_url,
            "user": target_user.to_dict() if target_user else None
        })
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error interno al guardar avatar: {e}"}), 500

@api_bp.route('/api/users/<int:user_id>/avatar', methods=['DELETE'])
def remove_user_avatar(user_id: int):
    is_admin = require_admin()
    current_uid = session.get('user_id')
    if not is_admin and current_uid != user_id:
        return jsonify({"status": "error", "message": "No tienes permiso para modificar este avatar."}), 403

    target_user = user_service.get_user_by_id(user_id)
    if not target_user:
        return jsonify({"status": "error", "message": "Usuario no encontrado."}), 404

    success = user_service.remove_user_avatar(user_id)
    if not success:
        return jsonify({"status": "error", "message": "El usuario no tenía una foto de avatar personalizada."}), 400

    if current_uid == user_id:
        session.pop('user_avatar_url', None)

    audit_service.log(
        action="REMOVE_AVATAR",
        module="USUARIOS",
        description=f"Eliminó la foto de perfil del usuario '@{target_user.username}' (revertido a iniciales).",
        level="info",
        action_display="Eliminación de Avatar"
    )

    return jsonify({
        "status": "success",
        "message": "Foto de perfil eliminada. Se mostrarán las iniciales.",
        "avatar_initials": target_user.avatar_initials,
        "user": target_user.to_dict()
    })
