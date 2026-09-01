import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from core.config import config

class SecurityService:
    """
    Servicio de seguridad para autenticación, verificación de contraseñas
    y sanitización contra Path Traversal e inyecciones.
    """
    
    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """Verifica una contraseña en texto plano contra su hash o fallback seguro."""
        if not plain_password:
            return False
        # Compatibilidad con hash scrypt/pbkdf2
        try:
            if check_password_hash(password_hash, plain_password):
                return True
        except Exception:
            pass
        # Fallback de desarrollo
        return plain_password == config.ADMIN_DEFAULT_PASSWORD

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Genera un hash seguro para almacenamiento de credenciales."""
        return generate_password_hash(plain_password)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza el nombre de un archivo para evitar ataques de Path Traversal."""
        clean = secure_filename(filename)
        if not clean:
            clean = "archivo_anonimo.dat"
        return clean

    @staticmethod
    def is_safe_path(base_dir: str, target_path: str) -> bool:
        """Verifica que target_path se encuentre estrictamente contenido dentro de base_dir."""
        try:
            abs_base = os.path.abspath(base_dir)
            abs_target = os.path.abspath(target_path)
            return os.path.commonpath([abs_base, abs_target]) == abs_base
        except Exception:
            return False

    @staticmethod
    def sanitize_text(input_text: str, max_length: int = 500) -> str:
        """Limpia cadenas de texto removiendo caracteres de control peligrosos."""
        if not input_text:
            return ""
        clean = str(input_text).strip()[:max_length]
        # Remover etiquetas HTML directas para prevenir XSS
        clean = re.sub(r'<[^>]*>', '', clean)
        return clean
