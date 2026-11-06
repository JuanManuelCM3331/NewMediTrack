"""Fachada de limitador de tasa para compatibilidad retroactiva.
Delega a core.rate_limiter.
"""

from core.rate_limiter import limiter

__all__ = ["limiter"]
