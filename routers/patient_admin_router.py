from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_patient_admin
from models import User
from schemas.common_schema import ApiResponse, EmptyResponse
from schemas.medication_schema import MedicationCreate, MedicationOut
from schemas.patient_admin_schema import (
    ApplySchemaOut,
    ApplySchemaRequest,
    LinkRequestCreate,
    PatientLinkOut,
    PatientOverviewOut,
    SchemaTemplateCreate,
    SchemaTemplateOut,
)
from schemas.treatment_schema import TreatmentCreate, TreatmentOut
from services.dose_service import get_today_schedule
from services.medication_service import (
    create_medication as service_create_medication,
    delete_medication as service_delete_medication,
    get_medication as service_get_medication,
)
from services.patient_admin_service import (
    apply_schema_to_patient,
    create_link_request,
    create_schema_template,
    delete_link,
    delete_schema_template,
    get_patient_overview,
    list_manager_links,
    list_patient_links,
    list_schema_templates,
    require_accepted_patient,
    respond_link_request,
)
from services.treatment_service import (
    create_treatment as service_create_treatment,
    delete_treatment as service_delete_treatment,
    get_treatment as service_get_treatment,
    serialize_treatment,
)

router = APIRouter(tags=["Administrador de Pacientes"])


# ============================================================================
# Endpoints para el Usuario Paciente (Recibir y aceptar/rechazar solicitudes)
# ============================================================================

@router.get("/patient-links/my-requests", response_model=ApiResponse[list[PatientLinkOut]])
def my_link_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = list_patient_links(db, current_user.id)
    return ApiResponse(success=True, data=data, message="Solicitudes de enlace obtenidas")


@router.post("/patient-links/{link_id}/decision", response_model=ApiResponse[PatientLinkOut])
def decide_link_request(
    link_id: int,
    decision: str = Query(..., description="Decisión: accept o reject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = respond_link_request(db, current_user, link_id, decision)
    msg = "Enlace aceptado correctamente" if data["status"] == "accepted" else "Solicitud de enlace rechazada"
    return ApiResponse(success=True, data=data, message=msg)


@router.delete("/patient-links/{link_id}", response_model=EmptyResponse)
def remove_patient_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_link(db, current_user, link_id)
    return EmptyResponse(success=True, data=None, message="Enlace eliminado")


# ============================================================================
# Endpoints para el Administrador de Pacientes (Enlaces, Pacientes y Esquemas)
# ============================================================================

@router.get("/patient-admin/links", response_model=ApiResponse[list[PatientLinkOut]])
def get_sent_links(
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    data = list_manager_links(db, manager.id)
    return ApiResponse(success=True, data=data, message="Enlaces del administrador de pacientes")


@router.post(
    "/patient-admin/links",
    response_model=ApiResponse[PatientLinkOut],
    status_code=status.HTTP_201_CREATED,
)
def send_link_request(
    payload: LinkRequestCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    data = create_link_request(db, manager, payload.patient_email)
    return ApiResponse(
        success=True,
        data=data,
        message="Solicitud de enlace enviada al paciente",
    )


@router.get(
    "/patient-admin/patients/{patient_id}/overview",
    response_model=ApiResponse[PatientOverviewOut],
)
def patient_overview(
    patient_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    data = get_patient_overview(db, manager.id, patient_id)
    return ApiResponse(success=True, data=data, message="Resumen del paciente enlazado")


@router.post(
    "/patient-admin/patients/{patient_id}/medications",
    response_model=ApiResponse[MedicationOut],
    status_code=status.HTTP_201_CREATED,
)
def register_patient_medication(
    patient_id: int,
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    patient = require_accepted_patient(db, manager.id, patient_id)
    medication = service_create_medication(db, patient.id, payload)
    return ApiResponse(
        success=True,
        data=MedicationOut.model_validate(medication),
        message="Medicamento registrado al paciente",
    )


@router.delete(
    "/patient-admin/patients/{patient_id}/medications/{medication_id}",
    response_model=EmptyResponse,
)
def delete_patient_medication(
    patient_id: int,
    medication_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    patient = require_accepted_patient(db, manager.id, patient_id)
    medication = service_get_medication(db, medication_id, patient.id)
    if not medication:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado para este paciente")
    service_delete_medication(db, medication)
    return EmptyResponse(success=True, data=None, message="Medicamento del paciente eliminado")


@router.post(
    "/patient-admin/patients/{patient_id}/treatments",
    response_model=ApiResponse[TreatmentOut],
    status_code=status.HTTP_201_CREATED,
)
def register_patient_treatment(
    patient_id: int,
    payload: TreatmentCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    patient = require_accepted_patient(db, manager.id, patient_id)
    medication = service_get_medication(db, payload.medication_id, patient.id)
    if not medication:
        raise HTTPException(status_code=404, detail="El medicamento seleccionado no pertenece al paciente")
    treatment = service_create_treatment(db, patient.id, medication, payload)
    get_today_schedule(db, patient.id)
    return ApiResponse(
        success=True,
        data=serialize_treatment(treatment),
        message="Tratamiento y dosis registrados al paciente",
    )


@router.delete(
    "/patient-admin/patients/{patient_id}/treatments/{treatment_id}",
    response_model=EmptyResponse,
)
def delete_patient_treatment(
    patient_id: int,
    treatment_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    patient = require_accepted_patient(db, manager.id, patient_id)
    treatment = service_get_treatment(db, treatment_id, patient.id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado para este paciente")
    service_delete_treatment(db, treatment)
    return EmptyResponse(success=True, data=None, message="Tratamiento del paciente eliminado")


@router.get("/patient-admin/schemas", response_model=ApiResponse[list[SchemaTemplateOut]])
def get_schemas(
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    data = list_schema_templates(db, manager.id)
    return ApiResponse(success=True, data=data, message="Esquemas obtenidos")


@router.post(
    "/patient-admin/schemas",
    response_model=ApiResponse[SchemaTemplateOut],
    status_code=status.HTTP_201_CREATED,
)
def create_schema(
    payload: SchemaTemplateCreate,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    data = create_schema_template(db, manager.id, payload)
    return ApiResponse(
        success=True,
        data=data,
        message="Esquema configurado correctamente",
    )


@router.delete("/patient-admin/schemas/{schema_id}", response_model=EmptyResponse)
def remove_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    delete_schema_template(db, manager.id, schema_id)
    return EmptyResponse(success=True, data=None, message="Esquema eliminado")


@router.post(
    "/patient-admin/patients/{patient_id}/apply-schema/{schema_id}",
    response_model=ApiResponse[ApplySchemaOut],
    status_code=status.HTTP_201_CREATED,
)
def apply_schema_endpoint(
    patient_id: int,
    schema_id: int,
    payload: ApplySchemaRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    manager: User = Depends(require_patient_admin),
):
    start_date = payload.start_date if payload else None
    data = apply_schema_to_patient(db, manager.id, patient_id, schema_id, start_date=start_date)
    return ApiResponse(
        success=True,
        data=data,
        message="Esquema aplicado: medicamento y dosis registrados al paciente",
    )
