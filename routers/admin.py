from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud import get_admin_summary
from database import get_db
from dependencies import require_admin
from models import User

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/summary", response_model=dict)
def admin_summary(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return {"success": True, "data": get_admin_summary(db), "message": "Resumen administrativo"}