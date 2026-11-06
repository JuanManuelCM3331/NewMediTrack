from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models import User
from schemas.common_schema import ApiResponse, EmptyResponse
from schemas.medication_schema import MedicationCreate, MedicationOut, MedicationUpdate
from services.medication_service import (
    create_medication as service_create_medication,
    delete_medication as service_delete_medication,
    get_medication as service_get_medication,
    list_medications as service_list_medications,
    update_medication as service_update_medication,
)

router = APIRouter(prefix="/medications", tags=["Medicamentos"])


@router.post("", response_model=ApiResponse[MedicationOut], status_code=status.HTTP_201_CREATED)
def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medication = service_create_medication(db, user.id, payload)
    return ApiResponse(
        success=True,
        data=MedicationOut.model_validate(medication),
        message="Medicamento registrado",
    )


@router.get("", response_model=ApiResponse[list[MedicationOut]])
def list_medications(
    search: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medications = service_list_medications(db, user.id, search, offset, limit)
    data = [MedicationOut.model_validate(item) for item in medications]
    return ApiResponse(success=True, data=data, message="Medicamentos encontrados")


@router.get("/{medication_id}", response_model=ApiResponse[MedicationOut])
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medication = service_get_medication(db, medication_id, user.id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    return ApiResponse(
        success=True,
        data=MedicationOut.model_validate(medication),
        message="Medicamento encontrado",
    )


@router.put("/{medication_id}", response_model=ApiResponse[MedicationOut])
def update_medication(
    medication_id: int,
    payload: MedicationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medication = service_get_medication(db, medication_id, user.id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    updated = service_update_medication(db, medication, payload)
    return ApiResponse(
        success=True,
        data=MedicationOut.model_validate(updated),
        message="Medicamento actualizado",
    )


@router.delete("/{medication_id}", response_model=EmptyResponse)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    medication = service_get_medication(db, medication_id, user.id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    service_delete_medication(db, medication)
    return EmptyResponse(success=True, data=None, message="Medicamento eliminado")
