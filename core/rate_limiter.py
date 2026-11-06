from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=not settings.testing,
)
