from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Esquema de respuesta estándar para toda la API de MediTrack."""
    success: bool = True
    data: T | None = None
    message: str = "Operación realizada"


class EmptyResponse(BaseModel):
    """Esquema de respuesta para operaciones que no retornan datos (ej. DELETE)."""
    success: bool = True
    data: None = None
    message: str = "Operación realizada"
