import json
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from crud import ensure_due_doses, list_treatments, serialize_treatment
from database import get_db
from dependencies import get_current_user
from models import Dose, Medication, Treatment, User
from schemas.treatment import TreatmentCreate, TreatmentOut, DoseOut, TreatmentUpdate
from time_utils import get_app_now_naive, get_app_timezone

router = APIRouter(prefix="/treatments", tags=["Tratamientos"])


def response(data, message="Operación realizada"):
    return {"success": True, "data": data, "message": message}


def parse_dosage_quantity(dosage_str: str) -> int:
    """Extrae la cantidad numérica de la dosis para descontar stock (por defecto 1)."""
    match = re.search(r"(\d+)", dosage_str)
    if match:
        val = int(match.group(1))
        return val if 0 < val <= 1000 else 1
    return 1


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
    now = get_app_now_naive()
    tz = get_app_timezone()
    data = []
    
    for dose in doses:
        # Si una dosis pospuesta ya cumplió los 10 minutos de espera, se reactiva a pending
        if dose.status == "snoozed" and now >= dose.scheduled_at:
            dose.status = "pending"
            dose.created_at = now

        minutes_left = None
        is_due = False

        if dose.status == "pending":
            # Ventana de 5 minutos considerando tanto la hora programada como el momento de creación
            effective_start = max(dose.scheduled_at, dose.created_at if dose.created_at else dose.scheduled_at)
            deadline = effective_start + timedelta(minutes=5)

            if now < dose.scheduled_at:
                # Dosis futura del día de hoy
                is_due = False
                minutes_left = None
            elif now <= deadline:
                # Dosis activa en la ventana de 5 minutos
                is_due = True
                minutes_left = max(0, int((deadline - now).total_seconds() // 60))
            else:
                # Se vencieron los 5 minutos sin que el usuario interactuara
                dose.status = "missed"
                dose.decided_at = now
                is_due = False
                minutes_left = None

        iso_scheduled = dose.scheduled_at.replace(tzinfo=tz).isoformat()
        data.append({
            "id": dose.id,
            "treatment_id": dose.treatment_id,
            "medication_name": dose.treatment.medication.name if (dose.treatment and dose.treatment.medication) else "Desconocido",
            "dosage": dose.treatment.dosage if dose.treatment else "",
            "scheduled_at": iso_scheduled,
            "status": dose.status,
            "minutes_left": minutes_left,
            "is_due": is_due,
        })
        
    db.commit()
    return response(data, "Agenda del día")


@router.get("/{treatment_id}", response_model=dict)
def get_treatment(treatment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    treatment = db.scalar(select(Treatment).options(joinedload(Treatment.medication)).where(Treatment.id == treatment_id, Treatment.owner_id == user.id))
    if not treatment:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return response(serialize_treatment(treatment))


@router.post("/doses/{dose_id}/decision", response_model=dict)
def decide_dose(dose_id: int, decision: str = Query(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if decision not in {"taken", "snoozed"}:
        raise HTTPException(status_code=422, detail="La decisión debe ser taken o snoozed")
    dose = db.scalar(
        select(Dose)
        .options(joinedload(Dose.treatment).joinedload(Treatment.medication))
        .where(Dose.id == dose_id, Dose.user_id == user.id)
    )
    if not dose:
        raise HTTPException(status_code=404, detail="Dosis no encontrada")
    if dose.status == "missed" and decision == "snoozed":
        raise HTTPException(status_code=409, detail="No puedes posponer una dosis que ya fue omitida")
    
    now = get_app_now_naive()
    medication = dose.treatment.medication if dose.treatment else None
    qty = parse_dosage_quantity(dose.treatment.dosage) if dose.treatment else 1

    # Descontar stock si se toma la dosis, o restaurar si se cambia
    if decision == "taken" and dose.status != "taken":
        if medication:
            medication.stock = max(0, medication.stock - qty)
    elif dose.status == "taken" and decision != "taken":
        if medication:
            medication.stock += qty

    if decision == "snoozed":
        dose.status = "snoozed"
        # Reprogramar hora para 10 minutos en el futuro
        dose.scheduled_at = now + timedelta(minutes=10)
        dose.decided_at = now
    else:
        dose.status = decision
        dose.decided_at = now

    db.commit()
    if medication:
        db.refresh(medication)

    msg = "Dosis registrada como tomada" if decision == "taken" else "Dosis pospuesta 10 minutos"
    if decision == "taken" and medication:
        if medication.stock == 0:
            msg += f" (¡Existencias agotadas de {medication.name}!)"
        elif medication.stock <= 3:
            msg += f" (Quedan pocas existencias de {medication.name}: {medication.stock} disp.)"

    tz = get_app_timezone()
    return response({
        "id": dose.id,
        "status": dose.status,
        "scheduled_at": dose.scheduled_at.replace(tzinfo=tz).isoformat(),
        "medication_stock": medication.stock if medication else 0,
    }, msg)
