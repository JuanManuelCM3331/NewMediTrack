import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from crud import get_user_by_email, verify_password
from database import get_db
from dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from rate_limiter import limiter
from schemas.auth import LoginRequest, TokenOut, UserOut

router = APIRouter(prefix="/sessions", tags=["Autenticación"])


@router.post("", response_model=dict)
@limiter.limit("5/minute")
def create_session(request: Request, response: Response, payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El correo o la contraseña no coinciden")

    token_str = create_access_token(user)
    is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"

    # Inyección de cookie segura HttpOnly
    response.set_cookie(
        key="meditrack_token",
        value=token_str,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    token = TokenOut(access_token=token_str, user=UserOut.model_validate(user))
    return {"success": True, "data": token.model_dump(), "message": "Sesión iniciada"}


@router.post("/logout", response_model=dict)
def logout(response: Response):
    response.delete_cookie(key="meditrack_token", path="/")
    return {"success": True, "data": None, "message": "Sesión cerrada correctamente"}
