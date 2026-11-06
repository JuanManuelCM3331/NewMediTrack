import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from crud import create_user, get_user_by_email, update_user_name
from database import get_db
from dependencies import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from rate_limiter import limiter
from schemas.auth import RegisterRequest, TokenOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, response: Response, payload: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    user = create_user(db, payload.email, payload.full_name, payload.password)
    token_str = create_access_token(user)
    is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"

    # Inyección de cookie segura HttpOnly al registrarse
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
    return {"success": True, "data": token.model_dump(), "message": "Cuenta creada correctamente"}


@router.get("/me", response_model=dict)
def me(current_user=Depends(get_current_user)):
    return {"success": True, "data": UserOut.model_validate(current_user).model_dump(), "message": "Usuario actual"}


@router.put("/me", response_model=dict)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = update_user_name(db, current_user, payload.full_name)
    return {"success": True, "data": UserOut.model_validate(user).model_dump(), "message": "Nombre actualizado correctamente"}
