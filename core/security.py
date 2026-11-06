from datetime import timedelta
import bcrypt
from jose import jwt

from core.config import settings
from core.time_utils import get_utc_now


def hash_password(password: str) -> str:
    """Genera un hash seguro bcrypt para la contraseña dada (máx 72 bytes)."""
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))


def create_access_token(user) -> str:
    """Genera un token JWT firmado con expiración en UTC."""
    expires = get_utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expires,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
