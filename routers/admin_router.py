from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import require_admin
from models import User
from schemas.common_schema import ApiResponse
from services.user_service import get_admin_summary

router = APIRouter(prefix="/admin", tags=["Administración"])


@router.get("/summary", response_model=ApiResponse[dict[str, int]])
def admin_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    summary = get_admin_summary(db)
    return ApiResponse(success=True, data=summary, message="Resumen administrativo")
