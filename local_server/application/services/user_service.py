# SIFMA — Sistema Integral de Fenotipado y Monitoreo Ambiental
# Autores: Andrés Felipe Luna Camargo, Cristian David Peña Martínez
# Año: 2026.

from datetime import datetime
from typing import List, Optional, Dict, Any
from domain.models import User
from infrastructure.database.repositories import UserRepository
from core.security import SecurityService
from core.config import config as app_settings

class UserService:
    """Caso de uso: Gestión de autenticación, usuarios y roles (RBAC)."""
    
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    def authenticate(self, identifier: str, plain_password: str) -> Optional[User]:
        if not identifier or not plain_password:
            return None
        clean_id = identifier.strip().lower()
        user = self.user_repo.get_by_username(clean_id) or self.user_repo.get_by_email(clean_id)
        if not user or not user.is_active:
            return None
        if SecurityService.verify_password(plain_password, user.password_hash):
            user.last_login = datetime.now()
            self.user_repo.save(user)
            return user
        return None

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.user_repo.get_by_id(user_id)

    def create_user(self, username: str, full_name: str, plain_password: str, role: str = "investigador", email: Optional[str] = None, permissions: Optional[Dict[str, bool]] = None) -> User:
        username_clean = username.strip().lower()
        if self.user_repo.get_by_username(username_clean):
            raise ValueError(f"El nombre de usuario '{username_clean}' ya está en uso.")
        if email and self.user_repo.get_by_email(email):
            raise ValueError(f"El correo '{email}' ya está registrado.")
            
        allowed_roles = ["investigador", "operador", "personalizado"]
        if role not in allowed_roles:
            role = "investigador"

        password_hash = SecurityService.hash_password(plain_password)
        new_user = User(
            username=username_clean,
            full_name=full_name.strip(),
            email=email.strip().lower() if email else None,
            password_hash=password_hash,
            role=role,
            is_active=True
        )
        if permissions is not None:
            new_user.set_permissions_dict(permissions)
        else:
            # Asigna los permisos por defecto según el rol elegido
            new_user.set_permissions_dict({})
            
        return self.user_repo.save(new_user)

    def update_user(self, user_id: int, full_name: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, is_active: Optional[bool] = None, permissions: Optional[Dict[str, bool]] = None) -> Optional[User]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
            
        if full_name is not None:
            user.full_name = full_name.strip()
        if role is not None:
            if user.is_super_admin:
                user.role = "admin"
            elif role in ["investigador", "operador", "personalizado"]:
                user.role = role
        if email is not None:
            user.email = email.strip().lower() if email else None
        if permissions is not None and not user.is_super_admin:
            user.set_permissions_dict(permissions)
        if is_active is not None:
            if user.is_super_admin and not is_active:
                raise ValueError("No es posible desactivar la cuenta del Super Usuario / Administrador Principal.")
            user.is_active = is_active

        return self.user_repo.save(user)

    def update_password(self, user_id: int, new_password: str) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user or not new_password:
            return False
        user.password_hash = SecurityService.hash_password(new_password)
        self.user_repo.save(user)
        return True

    def delete_user(self, user_id: int) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        if user.is_super_admin or user.role == "admin":
            raise ValueError("No es posible eliminar la cuenta del Super Usuario / Administrador Principal.")
        
        if user.avatar_path:
            self._delete_avatar_file_on_disk(user.avatar_path)
            
        self.user_repo.delete(user)
        return True

    def save_user_avatar(self, user_id: int, file_obj, static_folder: Optional[str] = None) -> str:
        """Guarda la foto de perfil en disco y actualiza el avatar_path del usuario."""
        import os
        import time

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado.")

        if not file_obj or not file_obj.filename:
            raise ValueError("No se recibió ningún archivo de imagen válido.")

        ext = file_obj.filename.rsplit('.', 1)[-1].lower() if '.' in file_obj.filename else 'png'
        if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            raise ValueError("Formato no soportado. Usa imágenes JPG, PNG o WebP.")

        from core.config import config as app_cfg
        avatars_dir = os.path.join(app_cfg.UPLOAD_DIR, 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)

        if user.avatar_path:
            self._delete_avatar_file_on_disk(user.avatar_path, static_folder)

        filename = f"avatar_{user.id}_{int(time.time())}.{ext}"
        full_dest = os.path.join(avatars_dir, filename)
        if hasattr(file_obj, 'save'):
            file_obj.save(full_dest)
        else:
            with open(full_dest, 'wb') as f:
                f.write(file_obj.read())

        relative_path = f"static/data/uploads/avatars/{filename}"
        user.avatar_path = relative_path
        self.user_repo.save(user)
        return user.avatar_url

    def remove_user_avatar(self, user_id: int, static_folder: Optional[str] = None) -> bool:
        """Elimina la foto de perfil del usuario y revierte a las iniciales."""
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.avatar_path:
            return False

        self._delete_avatar_file_on_disk(user.avatar_path, static_folder)
        user.avatar_path = None
        self.user_repo.save(user)
        return True

    def _delete_avatar_file_on_disk(self, avatar_path: str, static_folder: Optional[str] = None):
        """Elimina de forma segura el archivo del disco."""
        import os
        from core.config import config as app_cfg
        try:
            clean_rel = avatar_path.lstrip('/')
            if clean_rel.startswith('static/data/'):
                sub_rel = clean_rel.replace('static/data/', '', 1)
                full_path = os.path.join(app_cfg.DATA_DIR, sub_rel)
            else:
                if not static_folder:
                    static_folder = app_cfg.STATIC_DIR
                sub_rel = clean_rel.replace('static/', '', 1)
                full_path = os.path.join(static_folder, sub_rel)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass
