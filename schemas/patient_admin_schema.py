from datetime import date, datetime
import html

from pydantic import BaseModel, EmailStr, Field, field_validator

from schemas.dose_schema import DoseOut
from schemas.medication_schema import MedicationOut
from schemas.treatment_schema import TreatmentOut


def _sanitize_required_text(value: str) -> str:
    cleaned = html.unescape(value).strip()
    if not cleaned:
        raise ValueError("Este campo no puede estar vacío")
    return html.escape(cleaned)


def _sanitize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = html.unescape(value).strip()
    return html.escape(cleaned) if cleaned else None


def _validate_schedule_times(values: list[str]) -> list[str]:
    for value in values:
        parts = value.strip().split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("Cada hora debe usar el formato HH:MM")
        hour, minute = (int(part) for part in parts)
        if hour not in range(24) or minute not in range(60):
            raise ValueError("La hora debe estar entre 00:00 y 23:59")
    return sorted({f"{int(v.split(':')[0]):02d}:{int(v.split(':')[1]):02d}" for v in values})


class LinkRequestCreate(BaseModel):
    patient_email: EmailStr


class PatientLinkOut(BaseModel):
    id: int
    manager_id: int
    manager_name: str
    manager_email: str
    patient_id: int
    patient_name: str
    patient_email: str
    status: str
    created_at: datetime
    responded_at: datetime | None = None


class SchemaTemplateCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    medication_name: str = Field(min_length=2, max_length=120)
    presentation: str = Field(default="Tableta", min_length=2, max_length=80)
    default_stock: int = Field(default=30, ge=0, le=100000)
    dosage: str = Field(min_length=1, max_length=80)
    schedule_times: list[str] = Field(min_length=1, max_length=12)
    duration_days: int = Field(default=30, gt=0, le=3650)
    instructions: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("title", "medication_name", "presentation", "dosage")
    @classmethod
    def sanitize_text_fields(cls, value: str) -> str:
        return _sanitize_required_text(value)

    @field_validator("instructions", "notes")
    @classmethod
    def sanitize_optional_fields(cls, value: str | None) -> str | None:
        return _sanitize_optional_text(value)

    @field_validator("schedule_times")
    @classmethod
    def validate_times(cls, values: list[str]) -> list[str]:
        return _validate_schedule_times(values)


class SchemaTemplateOut(BaseModel):
    id: int
    title: str
    medication_name: str
    presentation: str
    default_stock: int
    dosage: str
    schedule_times: list[str]
    duration_days: int
    instructions: str | None = None
    notes: str | None = None


class ApplySchemaRequest(BaseModel):
    start_date: date | None = None


class ApplySchemaOut(BaseModel):
    medication: MedicationOut
    treatment: TreatmentOut
    today_doses: list[DoseOut]


class PatientStatsOut(BaseModel):
    medications_count: int = 0
    low_stock_count: int = 0
    active_treatments_count: int = 0
    today_total: int = 0
    today_taken: int = 0
    today_pending: int = 0
    today_snoozed: int = 0
    today_missed: int = 0
    today_progress_rate: int = 0
    adherence_rate: int = 100
    history_taken_doses: int = 0
    history_missed_doses: int = 0


class PatientOverviewOut(BaseModel):
    patient_id: int
    patient_name: str
    patient_email: str
    medications: list[MedicationOut]
    treatments: list[TreatmentOut]
    today_doses: list[DoseOut]
    stats: PatientStatsOut = Field(default_factory=PatientStatsOut)
