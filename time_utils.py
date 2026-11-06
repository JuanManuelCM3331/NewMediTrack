"""Fachada de utilidades de tiempo para compatibilidad retroactiva.
Delega a core.time_utils.
"""

from core.time_utils import (
    get_app_now,
    get_app_now_naive,
    get_app_timezone,
    get_app_today,
    get_utc_now,
)

__all__ = [
    "get_app_now",
    "get_app_now_naive",
    "get_app_timezone",
    "get_app_today",
    "get_utc_now",
]
