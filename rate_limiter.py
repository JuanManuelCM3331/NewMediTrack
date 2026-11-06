import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Configuramos el limiter. Si estamos en modo de test (TESTING=1), se desactiva para no bloquear los tests.
is_testing = os.getenv("TESTING", "0") == "1"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    enabled=not is_testing,
)
