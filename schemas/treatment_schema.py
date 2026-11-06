from datetime import date
import html

from pydantic import BaseModel, Field, field_validator
from schemas.dose_schema import DoseOut


class TreatmentCreate(BaseModel):
    medication_id: int = Field(gt=0)
    dosage: str = Field(min_length=1, max_length=80)
    schedule_times: list[str] = Field(min_length=1, max_length=12)
    start_date: date
    duration_days: int = Field(gt=0, le=3650)
    instructions: str | None = Field(default=None, max_length=500)

    @field_validator("dosage")
    @classmethod
    def sanitize_dosage(cls, value: str) -> str:
        cleaned = html.unescape(value).strip()
        if not cleaned:
            raise ValueError("La dosis no puede estar vacía")
        return html.escape(cleaned)

    @field_validator("instructions")
    @classmethod
    def sanitize_instructions(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return html.escape(html.unescape(value).strip())

    @field_validator("schedule_times")
    @classmethod
    def times_are_valid(cls, values: list[str]) -> list[str]:
        for value in values:
            parts = value.split(":")
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise ValueError("Cada hora debe usar el formato HH:MM")
            hour, minute = (int(part) for part in parts)
            if hour not in range(24) or minute not in range(60):
                raise ValueError("La hora debe estar entre 00:00 y 23:59")
        return sorted(set(values))


class TreatmentUpdate(BaseModel):
    dosage: str | None = Field(default=None, min_length=1, max_length=80)
    schedule_times: list[str] | None = None
    duration_days: int | None = Field(default=None, gt=0, le=3650)
    instructions: str | None = Field(default=None, max_length=500)
    active: bool | None = None

    @field_validator("dosage")
    @classmethod
    def sanitize_dosage(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = html.unescape(value).strip()
        if not cleaned:
            raise ValueError("La dosis no puede estar vacía")
        return html.escape(cleaned)

    @field_validator("instructions")
    @classmethod
    def sanitize_instructions(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return html.escape(html.unescape(value).strip())

    @field_validator("schedule_times")
    @classmethod
    def updated_times_are_valid(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        for value in values:
            parts = value.split(":")
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise ValueError("Cada hora debe usar el formato HH:MM")
            hour, minute = (int(part) for part in parts)
            if hour not in range(24) or minute not in range(60):
                raise ValueError("La hora debe estar entre 00:00 y 23:59")
        return sorted(set(values))


class TreatmentOut(BaseModel):
    id: int
    medication_id: int
    medication_name: str
    dosage: str
    schedule_times: list[str]
    start_date: date
    duration_days: int
    instructions: str | None
    active: bool
