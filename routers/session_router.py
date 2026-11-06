from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.rate_limiter import limiter
from core.security import create_access_token, verify_password
from schemas.auth_schema import LoginRequest, TokenOut, UserOut
from schemas.common_schema import ApiResponse, EmptyResponse
from services.user_service import get_user_by_email

router = APIRouter(prefix="/sessions", tags=["Autenticación"])


@router.post("", response_model=ApiResponse[TokenOut])
@limiter.limit("5/minute")
def create_session(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El correo o la contraseña no coinciden")

    token_str = create_access_token(user)

    # Inyección de cookie segura HttpOnly
    response.set_cookie(
        key="meditrack_token",
        value=token_str,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )

    token = TokenOut(access_token=token_str, user=UserOut.model_validate(user))
    return ApiResponse(success=True, data=token, message="Sesión iniciada")


@router.post("/logout", response_model=EmptyResponse)
def logout(response: Response):
    response.delete_cookie(key="meditrack_token", path="/")
    return EmptyResponse(success=True, data=None, message="Sesión cerrada correctamente")
