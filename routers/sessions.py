from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud import get_user_by_email, verify_password
from database import get_db
from dependencies import create_access_token
from schemas.auth import LoginRequest, TokenOut, UserOut

router = APIRouter(prefix="/sessions", tags=["Autenticación"])


@router.post("", response_model=dict)
def create_session(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El correo o la contraseña no coinciden")
    token = TokenOut(access_token=create_access_token(user), user=UserOut.model_validate(user))
    return {"success": True, "data": token.model_dump(), "message": "Sesión iniciada"}