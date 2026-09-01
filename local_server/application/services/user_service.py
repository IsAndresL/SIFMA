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
        # Buscar por username O por email
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

    def create_user(self, username: str, full_name: str, plain_password: str, role: str = "investigador", email: Optional[str] = None) -> User:
        username_clean = username.strip().lower()
        if self.user_repo.get_by_username(username_clean):
            raise ValueError(f"El nombre de usuario '{username_clean}' ya está en uso.")
        if email and self.user_repo.get_by_email(email):
            raise ValueError(f"El correo '{email}' ya está registrado.")
            
        allowed_roles = ["admin", "investigador", "operador"]
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
        return self.user_repo.save(new_user)

    def update_user(self, user_id: int, full_name: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[User]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
            
        if full_name is not None:
            user.full_name = full_name.strip()
        if role is not None and role in ["admin", "investigador", "operador"]:
            user.role = role
        if email is not None:
            user.email = email.strip().lower() if email else None
        if is_active is not None:
            if user.username == "admin" and not is_active:
                raise ValueError("No es posible desactivar la cuenta del Administrador Principal.")
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
        if user.username == "admin":
            raise ValueError("No es posible eliminar la cuenta del Administrador Principal.")
        self.user_repo.delete(user)
        return True
