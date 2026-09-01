from typing import List, Optional
from domain.models import User
from infrastructure.database.connection import db

class UserRepository:
    """Implementación SQLAlchemy para persistencia y gestión de usuarios y roles."""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None
        return User.query.filter_by(username=username.strip().lower()).first()

    def get_by_email(self, email: str) -> Optional[User]:
        if not email:
            return None
        return User.query.filter_by(email=email.strip().lower()).first()

    def get_all(self) -> List[User]:
        return User.query.order_by(User.created_at.asc()).all()

    def save(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def delete(self, user: User) -> None:
        db.session.delete(user)
        db.session.commit()
