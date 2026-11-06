"""Módulo de fachada (Façade) para compatibilidad con código existente.
Delega a los servicios especializados en services/ y utilidades de core/.
"""

from core.security import hash_password, verify_password
from models import ROLE_USER
from services.dose_service import decide_dose, ensure_due_doses, parse_dosage_quantity
from services.medication_service import list_medications
from services.treatment_service import list_treatments, serialize_treatment
from services.user_service import create_user, get_admin_summary, get_user_by_email, get_user_by_id, update_user_name

__all__ = [
    "hash_password",
    "verify_password",
    "ROLE_USER",
    "get_user_by_email",
    "get_user_by_id",
    "create_user",
    "update_user_name",
    "get_admin_summary",
    "list_medications",
    "list_treatments",
    "serialize_treatment",
    "ensure_due_doses",
    "decide_dose",
    "parse_dosage_quantity",
]
