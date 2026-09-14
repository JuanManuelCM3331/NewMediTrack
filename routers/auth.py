from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud import create_user, get_user_by_email, update_user_name, verify_password
from database import get_db
from dependencies import create_access_token, get_current_user
from schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    user = create_user(db, payload.email, payload.full_name, payload.password)
    token = TokenOut(access_token=create_access_token(user), user=UserOut.model_validate(user))
    return {"success": True, "data": token.model_dump(), "message": "Cuenta creada correctamente"}


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El correo o la contraseña no coinciden")
    token = TokenOut(access_token=create_access_token(user), user=UserOut.model_validate(user))
    return {"success": True, "data": token.model_dump(), "message": "Sesión iniciada"}


@router.get("/me", response_model=dict)
def me(current_user=Depends(get_current_user)):
    return {"success": True, "data": UserOut.model_validate(current_user).model_dump(), "message": "Usuario actual"}


@router.put("/me", response_model=dict)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user = update_user_name(db, current_user, payload.full_name)
    return {"success": True, "data": UserOut.model_validate(user).model_dump(), "message": "Nombre actualizado correctamente"}
