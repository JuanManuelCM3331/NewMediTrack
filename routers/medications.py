from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import Medication, User
from schemas.medication import MedicationCreate, MedicationOut, MedicationUpdate

router = APIRouter(prefix="/medications", tags=["Medicamentos"])


def response(data, message="Operación realizada"):
    return {"success": True, "data": data, "message": message}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_medication(payload: MedicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    medication = Medication(owner_id=user.id, **payload.model_dump())
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return response(MedicationOut.model_validate(medication).model_dump(), "Medicamento registrado")


@router.get("", response_model=dict)
def list_medications(search: str | None = Query(default=None), offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from crud import list_medications as fetch_medications
    data = [MedicationOut.model_validate(item).model_dump() for item in fetch_medications(db, user.id, search, offset, limit)]
    return response(data, "Medicamentos encontrados")


@router.get("/{medication_id}", response_model=dict)
def get_medication(medication_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    medication = db.get(Medication, medication_id)
    if not medication or medication.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    return response(MedicationOut.model_validate(medication).model_dump())


@router.put("/{medication_id}", response_model=dict)
def update_medication(medication_id: int, payload: MedicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    medication = db.get(Medication, medication_id)
    if not medication or medication.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(medication, key, value)
    db.commit()
    db.refresh(medication)
    return response(MedicationOut.model_validate(medication).model_dump(), "Medicamento actualizado")


@router.delete("/{medication_id}", response_model=dict)
def delete_medication(medication_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    medication = db.get(Medication, medication_id)
    if not medication or medication.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    db.delete(medication)
    db.commit()
    return response(None, "Medicamento eliminado")
