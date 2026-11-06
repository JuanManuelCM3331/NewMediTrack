from pydantic import BaseModel


class DoseOut(BaseModel):
    id: int
    treatment_id: int
    medication_name: str
    dosage: str
    notes: str | None = None
    instructions: str | None = None
    scheduled_at: str
    status: str
    minutes_left: int | None = None
    is_due: bool = False
    can_take: bool = False


class DoseDecisionResponse(BaseModel):
    id: int
    status: str
    scheduled_at: str
    medication_stock: int
