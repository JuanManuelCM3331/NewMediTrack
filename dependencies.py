"""Fachada de dependencias para compatibilidad retroactiva.
Delega a core.dependencies.
"""

from core.dependencies import bearer_scheme, get_current_user, require_admin
from core.security import create_access_token

__all__ = ["bearer_scheme", "get_current_user", "require_admin", "create_access_token"]
