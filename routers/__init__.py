from . import (
    admin_router,
    auth_router,
    dose_router,
    medication_router,
    session_router,
    treatment_router,
)

# Aliases for backward compatibility
admin = admin_router
auth = auth_router
doses = dose_router
medications = medication_router
sessions = session_router
treatments = treatment_router

__all__ = [
    "admin_router",
    "auth_router",
    "dose_router",
    "medication_router",
    "session_router",
    "treatment_router",
    "admin",
    "auth",
    "doses",
    "medications",
    "sessions",
    "treatments",
]
