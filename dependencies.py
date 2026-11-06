import os
from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User
from time_utils import get_utc_now

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY debe estar definida en las variables de entorno")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: User) -> str:
    expires = get_utc_now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "email": user.email, "role": user.role, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    raw_token = None
    # 1. Intentar leer desde cabecera Authorization: Bearer <token>
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    # 2. Intentar leer desde Cookie HttpOnly segura
    elif "meditrack_token" in request.cookies:
        raw_token = request.cookies.get("meditrack_token")

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Debes iniciar sesión para continuar")

    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError
        parsed_id = int(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o expirada")

    user = db.get(User, parsed_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La cuenta no está disponible")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un administrador puede realizar esta acción")
    return current_user
