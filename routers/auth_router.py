from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.rate_limiter import limiter
from core.security import create_access_token
from core.dependencies import get_current_user
from models import User
from schemas.auth_schema import RegisterRequest, TokenOut, UserOut, UserUpdate
from schemas.common_schema import ApiResponse
from services.user_service import create_user, get_user_by_email, update_user_name

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.post("", response_model=ApiResponse[TokenOut], status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    user = create_user(db, payload.email, payload.full_name, payload.password)
    token_str = create_access_token(user)

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
    return ApiResponse(success=True, data=token, message="Cuenta creada correctamente")


@router.get("/me", response_model=ApiResponse[UserOut])
def me(current_user: User = Depends(get_current_user)):
    return ApiResponse(success=True, data=UserOut.model_validate(current_user), message="Usuario actual")


@router.put("/me", response_model=ApiResponse[UserOut])
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_user_name(db, current_user, payload.full_name)
    return ApiResponse(success=True, data=UserOut.model_validate(user), message="Nombre actualizado correctamente")
