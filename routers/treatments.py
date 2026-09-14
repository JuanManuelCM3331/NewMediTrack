import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from crud import ensure_due_doses, list_treatments, serialize_treatment
from database import get_db
from dependencies import get_current_user
from models import Dose, Medication, Treatment, User
from schemas.treatment import TreatmentCreate, TreatmentOut, DoseOut, TreatmentUpdate

router = APIRouter(prefix="/treatments", tags=["Tratamientos"])


def response(data, message="Operación realizada"):
    return {"success": True, "data": data, "message": message}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_treatment(payload: TreatmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    medication = db.get(Medication, payload.medication_id)
    if not medication or medication.owner_id != user.id:
        raise HTTPException(status_code=404, detail="El medicamento seleccionado no existe")
    treatment = Treatment(owner_id=user.id, schedule_times=json.dumps(payload.schedule_times), **payload.model_dump(exclude={"schedule_times"}))
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    treatment.medication = medication
    return response(serialize_treatment(treatment), "Tratamiento creado")


@router.get("", response_model=dict)
def get_treatments(active: bool | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return response([serialize_treatment(item) for item in list_treatments(db, user.id, active)], "Tratamientos encontrados")


@router.put("/{treatment_id}", response_model=dict)
def update_treatment(treatment_id: int, payload: TreatmentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    treatment = db.get(Treatment, treatment_id)
    if not treatment or treatment.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    values = payload.model_dump(exclude_unset=True)
    if "schedule_times" in values:
        treatment.schedule_times = json.dumps(values.pop("schedule_times"))
    for key, value in values.items():
        setattr(treatment, key, value)
    db.commit()
    db.refresh(treatment)
    treatment.medication = db.get(Medication, treatment.medication_id)
    return response(serialize_treatment(treatment), "Tratamiento actualizado")


@router.delete("/{treatment_id}", response_model=dict)
def delete_treatment(treatment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    treatment = db.get(Treatment, treatment_id)
    if not treatment or treatment.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    db.delete(treatment)
    db.commit()
    return response(None, "Tratamiento eliminado")


@router.get("/schedule/today", response_model=dict)
def today_schedule(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doses = ensure_due_doses(db, user.id)
    now = datetime.now()
    data = []
    for dose in doses:
        minutes_left = max(0, int((dose.scheduled_at + timedelta(minutes=5) - now).total_seconds() // 60)) if dose.status == "pending" else None
        if dose.status == "pending" and dose.scheduled_at + timedelta(minutes=5) < now:
            dose.status = "missed"
            dose.decided_at = now
        data.append({"id": dose.id, "treatment_id": dose.treatment_id, "medication_name": dose.treatment.medication.name, "dosage": dose.treatment.dosage, "scheduled_at": dose.scheduled_at.isoformat(), "status": dose.status, "minutes_left": minutes_left})
    db.commit()
    return response(data, "Agenda del día")


@router.get("/{treatment_id}", response_model=dict)
def get_treatment(treatment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    treatment = db.scalar(select(Treatment).options(joinedload(Treatment.medication)).where(Treatment.id == treatment_id, Treatment.owner_id == user.id))
    if not treatment:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return response(serialize_treatment(treatment))


@router.post("/doses/{dose_id}/decision", response_model=dict)
def decide_dose(dose_id: int, decision: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if decision not in {"taken", "snoozed"}:
        raise HTTPException(status_code=422, detail="La decisión debe ser taken o snoozed")
    dose = db.scalar(select(Dose).where(Dose.id == dose_id, Dose.user_id == user.id))
    if not dose:
        raise HTTPException(status_code=404, detail="Dosis no encontrada")
    if dose.status == "missed":
        raise HTTPException(status_code=409, detail="Esta dosis ya fue marcada como omitida")
    dose.status = decision
    dose.decided_at = datetime.now()
    db.commit()
    return response({"id": dose.id, "status": dose.status}, "Dosis actualizada")
