from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models import Medication, Treatment, User
from schemas.common_schema import ApiResponse, EmptyResponse
from schemas.dose_schema import DoseDecisionResponse, DoseOut
from schemas.treatment_schema import TreatmentCreate, TreatmentOut, TreatmentUpdate
from services.dose_service import decide_dose as execute_dose_decision, get_today_schedule
from services.treatment_service import (
    create_treatment as service_create_treatment,
    delete_treatment as service_delete_treatment,
    get_treatment as service_get_treatment,
    list_treatments as service_list_treatments,
    serialize_treatment,
    update_treatment as service_update_treatment,
)

router = APIRouter(prefix="/treatments", tags=["Tratamientos"])


@router.post("", response_model=ApiResponse[TreatmentOut], status_code=status.HTTP_201_CREATED)
def create_treatment(
    payload: TreatmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medication = db.get(Medication, payload.medication_id)
    if not medication or medication.owner_id != user.id:
        raise HTTPException(status_code=404, detail="El medicamento seleccionado no existe")
    treatment = service_create_treatment(db, user.id, medication, payload)
    return ApiResponse(success=True, data=serialize_treatment(treatment), message="Tratamiento creado")


@router.get("", response_model=ApiResponse[list[TreatmentOut]])
def get_treatments(
    active: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    treatments = service_list_treatments(db, user.id, active)
    return ApiResponse(
        success=True,
        data=[serialize_treatment(item) for item in treatments],
        message="Tratamientos encontrados",
    )


@router.get("/schedule/today", response_model=ApiResponse[list[DoseOut]])
def today_schedule_legacy(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ruta delegada para compatibilidad retroactiva."""
    data = get_today_schedule(db, user.id)
    return ApiResponse(success=True, data=data, message="Agenda del día")


@router.post("/doses/{dose_id}/decision", response_model=ApiResponse[DoseDecisionResponse])
def decide_dose_legacy(
    dose_id: int,
    decision: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ruta delegada para compatibilidad retroactiva."""
    if decision not in {"taken", "snoozed"}:
        raise HTTPException(status_code=422, detail="La decisión debe ser taken o snoozed")

    try:
        data, message = execute_dose_decision(db, user.id, dose_id, decision)
    except ValueError as err:
        err_msg = str(err)
        status_code = 404 if "no encontrada" in err_msg else 409
        raise HTTPException(status_code=status_code, detail=err_msg)

    return ApiResponse(success=True, data=data, message=message)


@router.get("/{treatment_id}", response_model=ApiResponse[TreatmentOut])
def get_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    treatment = service_get_treatment(db, treatment_id, user.id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return ApiResponse(success=True, data=serialize_treatment(treatment), message="Tratamiento obtenido")


@router.put("/{treatment_id}", response_model=ApiResponse[TreatmentOut])
def update_treatment(
    treatment_id: int,
    payload: TreatmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    treatment = db.get(Treatment, treatment_id)
    if not treatment or treatment.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    updated = service_update_treatment(db, treatment, payload)
    return ApiResponse(success=True, data=serialize_treatment(updated), message="Tratamiento actualizado")


@router.delete("/{treatment_id}", response_model=EmptyResponse)
def delete_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    treatment = db.get(Treatment, treatment_id)
    if not treatment or treatment.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    service_delete_treatment(db, treatment)
    return EmptyResponse(success=True, data=None, message="Tratamiento eliminado")
