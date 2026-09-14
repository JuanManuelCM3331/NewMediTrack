from pydantic import BaseModel, Field, field_validator


class MedicationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    presentation: str = Field(default="Tableta", min_length=2, max_length=80)
    stock: int = Field(default=0, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("name", "presentation")
    @classmethod
    def text_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Este campo no puede estar vacío")
        return value.strip()


class MedicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    presentation: str | None = Field(default=None, min_length=2, max_length=80)
    stock: int | None = Field(default=None, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=500)


class MedicationOut(BaseModel):
    id: int
    name: str
    presentation: str
    stock: int
    notes: str | None

    model_config = {"from_attributes": True}
