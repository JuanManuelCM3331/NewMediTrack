from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models import User
from schemas.common_schema import ApiResponse
from schemas.dose_schema import DoseDecisionResponse, DoseOut
from services.dose_service import (
    decide_dose as execute_dose_decision,
    get_today_schedule,
    get_upcoming_schedule,
)

router = APIRouter(prefix="/doses", tags=["Dosis"])


@router.get("/today", response_model=ApiResponse[list[DoseOut]])
def today_doses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Consulta la agenda completa de dosis del usuario para la jornada de hoy."""
    data = get_today_schedule(db, user.id)
    return ApiResponse(success=True, data=data, message="Agenda del día")


@router.get("/upcoming", response_model=ApiResponse[list[DoseOut]])
def upcoming_doses(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Consulta las próximas dosis a consumir en general (hoy y días posteriores)."""
    data = get_upcoming_schedule(db, user.id, limit=limit)
    return ApiResponse(success=True, data=data, message="Próximas dosis a consumir")


@router.post("/{dose_id}/decision", response_model=ApiResponse[DoseDecisionResponse])
def decide_dose_endpoint(
    dose_id: int,
    decision: str = Query(..., description="Decisión a aplicar: taken, snoozed o missed"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Registra la toma, posposición u omisión de una dosis y ajusta inventario de medicamentos."""
    if decision not in {"taken", "snoozed", "missed"}:
        raise HTTPException(status_code=422, detail="La decisión debe ser taken, snoozed o missed")

    data, message = execute_dose_decision(db, user.id, dose_id, decision)
    return ApiResponse(success=True, data=data, message=message)
